from __future__ import annotations

import json
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from PIL import Image, ImageChops

from src.fliptrack.build_mini_a5_train import (
    TRAIN_TEMPLATE_IDS,
    audit_template_disjointness,
    build_corpus,
)


def _eval_manifest(path: Path) -> Path:
    image_a = path.parent / "eval_a.png"
    image_b = path.parent / "eval_b.png"
    Image.new("RGB", (4, 4), "white").save(image_a)
    Image.new("RGB", (4, 4), "black").save(image_b)
    row = {
        "template_id": "held_out_eval_template",
        "pair_id": "held_out_pair",
        "image_a_sha256": "a" * 64,
        "image_b_sha256": "b" * 64,
    }
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    return path


def _rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_small_corpus_is_exact_disjoint_and_pair_adjacent(tmp_path: Path) -> None:
    output = tmp_path / "corpus"
    artifact = build_corpus(
        output,
        n_per_template=1,
        seed=17,
        eval_manifests=[_eval_manifest(tmp_path / "eval.jsonl")],
    )

    pairs = _rows(Path(artifact["pairs"]))
    training = _rows(Path(artifact["train_jsonl"]))
    decon = json.loads(Path(artifact["decontamination"]).read_text(encoding="utf-8"))
    assert len(pairs) == len(TRAIN_TEMPLATE_IDS) == 3
    assert len(training) == 6
    assert decon["status"] == "pass"
    assert decon["training_pair_adjacency"] is True
    assert decon["disjointness"]["template_id_overlap"] == 0
    assert pq.read_table(artifact["train_parquet"]).num_rows == 6

    for index in range(0, len(training), 2):
        assert training[index]["pair_group_uid"] == training[index + 1]["pair_group_uid"]
        assert [training[index]["pair_member"], training[index + 1]["pair_member"]] == ["a", "b"]
    for pair in pairs:
        image_a = Image.open(pair["image_a_path"]).convert("RGB")
        image_b = Image.open(pair["image_b_path"]).convert("RGB")
        observed = ImageChops.difference(image_a, image_b).convert("L").point(
            lambda value: 255 if value else 0
        )
        mask = Image.open(pair["changed_region_mask_a"]).convert("L")
        assert ImageChops.difference(observed, mask).getbbox() is None
        assert pair["answer_a"] != pair["answer_b"]
        assert pair["provenance"]["answer_pointing_cue"] is False


def test_generator_refuses_to_overwrite_immutable_output(tmp_path: Path) -> None:
    output = tmp_path / "occupied"
    output.mkdir()
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        build_corpus(
            output,
            n_per_template=1,
            seed=17,
            eval_manifests=[_eval_manifest(tmp_path / "eval.jsonl")],
        )


def test_overlap_fixture_is_rejected() -> None:
    rows = [
        {
            "template_id": TRAIN_TEMPLATE_IDS[0],
            "pair_group_uid": "p1",
            "image_a_sha256": "c" * 64,
            "image_b_sha256": "d" * 64,
        }
    ]
    with pytest.raises(ValueError, match="training/evaluation overlap"):
        audit_template_disjointness(
            rows,
            {
                "template_ids": {TRAIN_TEMPLATE_IDS[0]},
                "pair_ids": set(),
                "image_hashes": set(),
            },
        )
