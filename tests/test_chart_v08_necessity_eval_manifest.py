from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.build_chart_v08_necessity_eval_manifest import build_manifest


def _jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source.jsonl"
    _jsonl(
        source,
        [
            {
                "pair_id": "pair-1",
                "template_id": "chart_v08_legend_target_flip",
                "category": "chart",
                "question": "What value?",
                "answer_a": "10",
                "answer_b": "20",
            }
        ],
    )
    interventions: dict[str, dict] = {}
    for intervention in ("no_star", "random_star"):
        row: dict[str, str] = {}
        for member in ("a", "b"):
            path = tmp_path / f"{intervention}_{member}.png"
            path.write_bytes(f"{intervention}-{member}".encode())
            row[f"image_{member}_path"] = path.name
            row[f"image_{member}_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        interventions[intervention] = row
    interventions["random_star"].update(
        implied_answer_a="20", implied_answer_b="10"
    )
    sidecar = tmp_path / "sidecar.jsonl"
    _jsonl(
        sidecar,
        [
            {
                "schema_version": "blind-gains.chart-v08-necessity-sidecar.v2",
                "source_manifest_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "pair_id": "pair-1",
                "question": "What value?",
                "answer_a": "10",
                "answer_b": "20",
                **interventions,
            }
        ],
    )
    return source, sidecar


def test_manifest_scores_both_interventions_against_original_answers(
    tmp_path: Path,
) -> None:
    source, sidecar = _fixture(tmp_path)
    output = tmp_path / "output.jsonl"
    metadata = tmp_path / "metadata.json"

    result = build_manifest(
        root=tmp_path,
        source_manifest=source,
        sidecar=sidecar,
        output=output,
        metadata_output=metadata,
    )
    rows = [json.loads(line) for line in output.read_text().splitlines()]

    assert result["status"] == "pass"
    assert result["evaluation_rows"] == 2
    assert {row["intervention"] for row in rows} == {"no_star", "random_star"}
    assert all(row["answer_a"] == "10" and row["answer_b"] == "20" for row in rows)
    assert all(row["scoring_target"] == "original_member_answer" for row in rows)


def test_tampered_diagnostic_image_fails_before_any_output(
    tmp_path: Path,
) -> None:
    source, sidecar = _fixture(tmp_path)
    (tmp_path / "no_star_a.png").write_bytes(b"tampered")
    output = tmp_path / "output.jsonl"
    metadata = tmp_path / "metadata.json"

    with pytest.raises(ValueError, match="image hash mismatch"):
        build_manifest(
            root=tmp_path,
            source_manifest=source,
            sidecar=sidecar,
            output=output,
            metadata_output=metadata,
        )

    assert not output.exists()
    assert not metadata.exists()


def test_sidecar_bound_to_another_source_manifest_is_rejected(
    tmp_path: Path,
) -> None:
    source, sidecar = _fixture(tmp_path)
    rows = [json.loads(line) for line in sidecar.read_text().splitlines()]
    rows[0]["source_manifest_sha256"] = "0" * 64
    _jsonl(sidecar, rows)

    with pytest.raises(ValueError, match="source hash mismatch"):
        build_manifest(
            root=tmp_path,
            source_manifest=source,
            sidecar=sidecar,
            output=tmp_path / "output.jsonl",
            metadata_output=tmp_path / "metadata.json",
        )
