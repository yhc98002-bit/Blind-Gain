from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.build_chart_v08_mechanical_audit_v2 import build_sidecar
from src.fliptrack.render_chart_v08 import generate_chart_v08_pairs
from src.fliptrack.schema import write_jsonl


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    manifest = tmp_path / "manifest.jsonl"
    rows = generate_chart_v08_pairs(
        tmp_path / "pairs", n_per_subfamily=1, seed=20260713
    )
    write_jsonl(manifest, rows)
    return tmp_path, manifest


def test_chart_v08_audit_builds_member_specific_diagnostics(tmp_path: Path) -> None:
    root, manifest = _fixture(tmp_path)
    sidecar_path = root / "diagnostics.jsonl"

    sidecar, audit = build_sidecar(
        root,
        manifest,
        root / "diagnostic_images",
        sidecar_path,
        expected_per_template=1,
    )

    assert audit["status"] == "pass"
    assert all(audit["checks"].values())
    assert len(sidecar) == 2
    for row in sidecar:
        assert row["scoring_rule"] == (
            "score_each_intervention_against_original_member_answer"
        )
        assert row["random_star"]["implied_answer_a"] != row["answer_a"]
        assert row["random_star"]["implied_answer_b"] != row["answer_b"]
        for intervention in ("no_star", "random_star"):
            assert (root / row[intervention]["image_a_path"]).is_file()
            assert (root / row[intervention]["image_b_path"]).is_file()


def test_chart_v08_audit_rejects_metadata_that_cannot_reconstruct_image(
    tmp_path: Path,
) -> None:
    root, manifest = _fixture(tmp_path)
    rows = [json.loads(line) for line in manifest.read_text().splitlines()]
    rows[0]["verifier_results"]["values_a"][0][0] += 5
    tampered = root / "tampered.jsonl"
    write_jsonl(tampered, rows)

    with pytest.raises(ValueError, match="does not reconstruct image A"):
        build_sidecar(
            root,
            tampered,
            root / "diagnostic_images",
            root / "diagnostics.jsonl",
            expected_per_template=1,
        )


def test_chart_v08_audit_refuses_to_overwrite_sidecars(tmp_path: Path) -> None:
    root, manifest = _fixture(tmp_path)
    output_dir = root / "diagnostic_images"
    sidecar = root / "diagnostics.jsonl"
    build_sidecar(
        root,
        manifest,
        output_dir,
        sidecar,
        expected_per_template=1,
    )

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        build_sidecar(
            root,
            manifest,
            output_dir,
            sidecar,
            expected_per_template=1,
        )
