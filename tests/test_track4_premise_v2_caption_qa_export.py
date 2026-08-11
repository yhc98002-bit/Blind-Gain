"""Adversarial fixtures for scripts/build_track4_premise_v2_caption_qa_inputs.py (I10).

Every fixture runs on planted synthetic rows only; none of them touches
data/track4_premise_v2_dev_v1.  The last fixture feeds the exporter's own output
into src/captioning/qa_pairs.py::build_caption_qa_rows, so the emitted shape is
checked against the real consumer rather than against a restatement of it.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from scripts.build_track4_premise_v2_caption_qa_inputs import (
    KEY_SCHEMA_VERSION,
    RELEASE_SCHEMA_VERSION,
    ExportError,
    export_caption_qa_inputs,
    main,
)
from src.captioning.qa_pairs import build_caption_qa_rows


def _write_image(path: Path, payload: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def _plant_batch(tmp_path: Path) -> tuple[Path, list[dict[str, Any]]]:
    """A two-pair batch mirroring the real one: absolute image paths, null
    catch_twin_id, and one pair whose provenance carries
    semantic_side_assignment_swapped=true.  The real manifest carries no
    source_pair_id key at all, so pair two omits it entirely while pair one
    carries an explicit null; both must take the pair_id fallback."""
    batch = tmp_path / "batch"
    images = batch / "images"
    rows: list[dict[str, Any]] = []
    for index, (pair_id, swapped) in enumerate(
        (("t4v2c_pair_one", True), ("t4v2c_pair_two", False))
    ):
        sha_a = _write_image(images / f"{pair_id}_a.png", f"bytes-{index}-a".encode())
        sha_b = _write_image(images / f"{pair_id}_b.png", f"bytes-{index}-b".encode())
        rows.append(
            {
                "schema_version": "fliptrack.v0",
                "pair_id": pair_id,
                "question": f"question for {pair_id}?",
                "answer_a": f"{index}1",
                "answer_b": f"{index}9",
                "image_a_path": str(images / f"{pair_id}_a.png"),
                "image_b_path": str(images / f"{pair_id}_b.png"),
                "image_a_sha256": sha_a,
                "image_b_sha256": sha_b,
                "template_id": "t4v2_coordinate_register_n20_v1",
                "category": "t4v2_premise_construct",
                "catch_twin_id": None,
                "source_pair_id": None,
                "split": "development",
                "intervention_type": "premise_transition",
                "provenance": {"semantic_side_assignment_swapped": swapped},
            }
        )
    # mirror the real batch, which has no source_pair_id key whatsoever
    rows[1].pop("source_pair_id")
    return batch, rows


def _write_source(batch: Path, rows: list[dict[str, Any]]) -> Path:
    batch.mkdir(parents=True, exist_ok=True)
    path = batch / "manifest_causal_pairs.jsonl"
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8"
    )
    return path


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_planted_rows_round_trip_exactly(tmp_path: Path) -> None:
    batch, rows = _plant_batch(tmp_path)
    source = _write_source(batch, rows)
    out_dir = batch / "caption_qa_inputs"

    provenance = export_caption_qa_inputs(source, out_dir)

    release = _read_jsonl(out_dir / "manifest.jsonl")
    key = _read_jsonl(out_dir / "key.jsonl")
    assert len(release) == len(key) == 2

    for source_row, release_row, key_row in zip(rows, release, key):
        pair_id = source_row["pair_id"]
        assert release_row["schema_version"] == RELEASE_SCHEMA_VERSION
        assert key_row["schema_version"] == KEY_SCHEMA_VERSION
        # every value is the source's own value
        assert release_row["pair_id"] == pair_id
        assert release_row["question"] == source_row["question"]
        assert key_row["pair_id"] == pair_id
        assert key_row["template_id"] == source_row["template_id"]
        assert key_row["category"] == source_row["category"]
        assert key_row["catch_twin_id"] is None
        # null source_pair_id falls back to pair_id (recorded), never to "None"
        assert key_row["source_pair_id"] == pair_id
        members = {m["member_id"]: m for m in release_row["members"]}
        key_members = {m["member_id"]: m for m in key_row["members"]}
        assert set(members) == set(key_members) == {f"{pair_id}_a", f"{pair_id}_b"}
        for side in ("a", "b"):
            member_id = f"{pair_id}_{side}"
            assert members[member_id]["image_sha256"] == source_row[f"image_{side}_sha256"]
            # relativized, and it resolves back to the source's own absolute path
            assert not Path(members[member_id]["image_path"]).is_absolute()
            resolved = (out_dir / members[member_id]["image_path"]).resolve()
            assert resolved == Path(source_row[f"image_{side}_path"]).resolve()
            # THE side-binding invariant: the answer travels with its own image
            assert key_members[member_id]["source_side"] == side
            assert key_members[member_id]["answer"] == source_row[f"answer_{side}"]

    # the swapped pair is NOT inverted by the export
    swapped_pair = next(r for r in key if r["pair_id"] == "t4v2c_pair_one")
    swapped_source = next(r for r in rows if r["pair_id"] == "t4v2c_pair_one")
    answers = {m["source_side"]: m["answer"] for m in swapped_pair["members"]}
    assert answers == {"a": swapped_source["answer_a"], "b": swapped_source["answer_b"]}

    stored = json.loads((out_dir / "provenance.json").read_text(encoding="utf-8"))
    assert stored == provenance
    assert stored["source_manifest_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert stored["source_rows"] == 2
    assert stored["n_pairs"] == 2
    assert stored["n_members"] == 4
    assert stored["n_distinct_image_sha256"] == 4
    assert stored["source_pair_id_fallback_to_pair_id"] == 2
    assert stored["source_pair_id_null_in_source"] == 1
    assert stored["source_pair_id_absent_in_source"] == 1
    assert stored["semantic_side_assignment_swapped_counts"] == {
        "true": 1,
        "false": 1,
        "absent": 0,
    }
    assert stored["template_counts"] == {"t4v2_coordinate_register_n20_v1": 2}
    assert stored["image_hashes_verified_against_disk"] is True
    assert stored["mutates_source_batch"] is False
    assert "field_mapping" in stored and "release_row" in stored["field_mapping"]


@pytest.mark.parametrize(
    "dropped",
    ["question", "answer_b", "image_a_sha256", "image_b_path", "template_id", "category"],
)
def test_missing_source_field_is_refused_and_nothing_is_written(
    tmp_path: Path, dropped: str
) -> None:
    batch, rows = _plant_batch(tmp_path)
    broken = copy.deepcopy(rows)
    broken[1].pop(dropped)
    source = _write_source(batch, broken)
    out_dir = batch / "caption_qa_inputs"

    with pytest.raises(ExportError) as excinfo:
        export_caption_qa_inputs(source, out_dir)
    assert dropped in str(excinfo.value)
    assert not (out_dir / "manifest.jsonl").exists()
    assert not (out_dir / "key.jsonl").exists()
    assert not (out_dir / "provenance.json").exists()


def test_null_required_field_is_refused(tmp_path: Path) -> None:
    batch, rows = _plant_batch(tmp_path)
    broken = copy.deepcopy(rows)
    broken[0]["question"] = None
    source = _write_source(batch, broken)
    with pytest.raises(ExportError, match="null/empty"):
        export_caption_qa_inputs(source, batch / "caption_qa_inputs")
    assert not (batch / "caption_qa_inputs" / "manifest.jsonl").exists()


def test_duplicate_pair_id_is_refused(tmp_path: Path) -> None:
    batch, rows = _plant_batch(tmp_path)
    broken = copy.deepcopy(rows)
    broken[1]["pair_id"] = broken[0]["pair_id"]
    source = _write_source(batch, broken)
    out_dir = batch / "caption_qa_inputs"
    with pytest.raises(ExportError, match="duplicate pair_id"):
        export_caption_qa_inputs(source, out_dir)
    assert not out_dir.exists() or not any(out_dir.iterdir())


def test_nonexistent_image_path_is_refused(tmp_path: Path) -> None:
    batch, rows = _plant_batch(tmp_path)
    broken = copy.deepcopy(rows)
    broken[1]["image_b_path"] = str(batch / "images" / "not_on_disk.png")
    source = _write_source(batch, broken)
    out_dir = batch / "caption_qa_inputs"
    with pytest.raises(ExportError, match="not a file on disk"):
        export_caption_qa_inputs(source, out_dir)
    assert not (out_dir / "manifest.jsonl").exists()


def test_reused_image_hash_is_refused(tmp_path: Path) -> None:
    """qa_pairs.py rejects a hash reused across members globally; refuse at export."""
    batch, rows = _plant_batch(tmp_path)
    broken = copy.deepcopy(rows)
    broken[1]["image_a_sha256"] = broken[0]["image_a_sha256"]
    source = _write_source(batch, broken)
    with pytest.raises(ExportError, match="already used by"):
        export_caption_qa_inputs(source, batch / "caption_qa_inputs", verify_image_hashes=False)


def test_hash_disagreeing_with_disk_is_refused(tmp_path: Path) -> None:
    batch, rows = _plant_batch(tmp_path)
    broken = copy.deepcopy(rows)
    broken[0]["image_a_sha256"] = "0" * 64
    source = _write_source(batch, broken)
    with pytest.raises(ExportError, match="on-disk sha256"):
        export_caption_qa_inputs(source, batch / "caption_qa_inputs")


def test_refuses_to_overwrite_existing_output(tmp_path: Path) -> None:
    batch, rows = _plant_batch(tmp_path)
    source = _write_source(batch, rows)
    out_dir = batch / "caption_qa_inputs"
    export_caption_qa_inputs(source, out_dir)
    before = (out_dir / "manifest.jsonl").read_bytes()
    with pytest.raises(ExportError, match="refusing to overwrite"):
        export_caption_qa_inputs(source, out_dir)
    assert (out_dir / "manifest.jsonl").read_bytes() == before


def test_export_is_byte_identical_on_rerun(tmp_path: Path) -> None:
    batch, rows = _plant_batch(tmp_path)
    source = _write_source(batch, rows)
    first = batch / "out_one"
    second = batch / "out_two"
    export_caption_qa_inputs(source, first)
    export_caption_qa_inputs(source, second)
    for name in ("manifest.jsonl", "key.jsonl", "provenance.json"):
        assert (first / name).read_bytes() == (second / name).read_bytes(), name


def test_cli_returns_nonzero_and_writes_nothing_on_refusal(tmp_path: Path) -> None:
    batch, rows = _plant_batch(tmp_path)
    broken = copy.deepcopy(rows)
    broken[0].pop("answer_a")
    source = _write_source(batch, broken)
    out_dir = batch / "caption_qa_inputs"
    rc = main(["--source-manifest", str(source), "--output-dir", str(out_dir)])
    assert rc != 0
    assert not (out_dir / "manifest.jsonl").exists()
    ok_source = _write_source(batch, rows)
    assert main(["--source-manifest", str(ok_source), "--output-dir", str(out_dir)]) == 0
    assert (out_dir / "manifest.jsonl").exists()


def test_emitted_shape_satisfies_build_caption_qa_pairs_reader(tmp_path: Path) -> None:
    """Feed the exporter's own output to the real consumer with a synthetic store."""
    batch, rows = _plant_batch(tmp_path)
    source = _write_source(batch, rows)
    out_dir = batch / "caption_qa_inputs"
    export_caption_qa_inputs(source, out_dir)

    release = _read_jsonl(out_dir / "manifest.jsonl")
    key = _read_jsonl(out_dir / "key.jsonl")
    captions = [
        {"image_sha256": member["image_sha256"], "caption": f"caption for {member['member_id']}"}
        for release_row in release
        for member in release_row["members"]
    ]

    qa_rows = build_caption_qa_rows(release, key, captions, out_dir)

    assert len(qa_rows) == 2
    by_pair = {row["pair_id"]: row for row in qa_rows}
    for source_row in rows:
        pair_id = source_row["pair_id"]
        qa = by_pair[pair_id]
        assert qa["schema_version"] == "blind-gains.fliptrack-caption-qa-input.v1"
        assert qa["source_pair_id"] == pair_id
        assert qa["question"] == source_row["question"]
        assert qa["template_id"] == source_row["template_id"]
        assert qa["category"] == source_row["category"]
        assert qa["catch_twin_id"] is None
        for side in ("a", "b"):
            assert qa[f"answer_{side}"] == source_row[f"answer_{side}"]
            assert qa[f"image_{side}_sha256"] == source_row[f"image_{side}_sha256"]
            assert qa[f"member_id_{side}"] == f"{pair_id}_{side}"
            assert qa[f"caption_{side}"] == f"caption for {pair_id}_{side}"
            # the joined path the consumer emits points at the real file
            assert Path(qa[f"image_{side}_path"]).resolve() == Path(
                source_row[f"image_{side}_path"]
            ).resolve()

    # a caption store wider than the release (the real E3 case) still needs the flag
    wider = captions + [{"image_sha256": "f" * 64, "caption": "unrelated image"}]
    with pytest.raises(ValueError, match="hashes outside the release"):
        build_caption_qa_rows(release, key, wider, out_dir)
    assert len(build_caption_qa_rows(release, key, wider, out_dir, allow_extra_captions=True)) == 2
