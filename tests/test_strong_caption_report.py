from pathlib import Path

import pytest

from scripts.build_strong_caption_stress_report import build_payload, render_report


TEMPLATES = {
    "header_cued_table_code_v02": 300,
    "coordinate_register_twenty_point_x_v02": 600,
    "starred_series_value_nine_v07": 300,
}


def _metrics(value: float) -> dict:
    return {
        "n_pairs": 1200,
        "pair_accuracy": value,
        "member_accuracy": value,
        "collapse_rate": 0.1,
        "per_template": {
            template: {
                "n_pairs": count,
                "pair_accuracy": value,
                "member_accuracy": value,
                "collapse_rate": 0.1,
            }
            for template, count in TEMPLATES.items()
        },
    }


def _artifact_paths(tmp_path: Path) -> dict[str, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name in ("baseline", "strong", "download", "checkout", "caption", "delete"):
        path = tmp_path / f"{name}.json"
        path.write_text("{}\n", encoding="utf-8")
        paths[name] = path
    return paths


def test_strong_caption_report_computes_headroom_and_requires_deletion(
    tmp_path: Path,
) -> None:
    checkout = {"status": "pass", "sha256_tree": "tree-hash"}
    caption = {
        "status": "complete",
        "tensor_parallel_width": 4,
        "replica_count": 1,
        "caption_prompt_contract": "question_blind_v1",
        "max_new_tokens": 384,
        "model_id": "Qwen/Qwen2.5-VL-72B-Instruct",
        "model_revision": "master",
    }
    deletion = {
        "status": "deleted",
        "path_absent_after_deletion": True,
        "model_sha256_tree": "tree-hash",
        "model_total_bytes": 147,
    }
    payload = build_payload(
        baseline={"r19": _metrics(0.02), "r20": _metrics(0.01)},
        strong={"r19": _metrics(0.08), "r20": _metrics(0.05)},
        download_manifest={"status": "complete"},
        checkout_manifest=checkout,
        caption_manifest=caption,
        deletion_record=deletion,
        artifact_paths=_artifact_paths(tmp_path),
    )
    report = render_report(payload, Path("strong.json"))

    assert payload["status"] == "complete"
    assert payload["rows"][0]["delta"] == pytest.approx(0.06)
    assert "does not repair the document template's 7B visual ceiling" in report
    assert payload["weights_deleted"] is True

    deletion["status"] = "deletion-authorized"
    with pytest.raises(ValueError, match="weights_deleted"):
        build_payload(
            baseline={"r19": _metrics(0.02), "r20": _metrics(0.01)},
            strong={"r19": _metrics(0.08), "r20": _metrics(0.05)},
            download_manifest={"status": "complete"},
            checkout_manifest=checkout,
            caption_manifest=caption,
            deletion_record=deletion,
            artifact_paths=_artifact_paths(tmp_path / "retry"),
        )


def test_strong_caption_report_rejects_selected_or_incomplete_package(
    tmp_path: Path,
) -> None:
    bad = _metrics(0.1)
    bad["n_pairs"] = 1199
    with pytest.raises(ValueError, match="1,200"):
        build_payload(
            baseline={"r19": bad, "r20": _metrics(0.1)},
            strong={"r19": _metrics(0.1), "r20": _metrics(0.1)},
            download_manifest={"status": "complete"},
            checkout_manifest={"status": "pass", "sha256_tree": "hash"},
            caption_manifest={
                "status": "complete",
                "tensor_parallel_width": 4,
                "replica_count": 1,
                "caption_prompt_contract": "question_blind_v1",
                "max_new_tokens": 384,
            },
            deletion_record={
                "status": "deleted",
                "path_absent_after_deletion": True,
                "model_sha256_tree": "hash",
            },
            artifact_paths=_artifact_paths(tmp_path),
        )
