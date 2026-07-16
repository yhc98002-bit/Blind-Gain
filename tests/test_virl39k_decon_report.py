from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.build_virl39k_decon_report import (
    EXPECTED_EVAL_RECORDS,
    EXPECTED_LAYERS,
    build_report,
)
from src.decon.core import DEFAULT_THRESHOLDS


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixtures(tmp_path: Path) -> tuple[Path, Path, Path]:
    records = tmp_path / "records.json"
    records.write_text(
        json.dumps(
            {
                "status": "pass",
                "n_train_items": 38_870,
                "n_train_records": 42_908,
                "n_eval_records": sum(EXPECTED_EVAL_RECORDS.values()),
                "eval_dataset_record_counts": EXPECTED_EVAL_RECORDS,
            }
        ),
        encoding="utf-8",
    )
    filtering = tmp_path / "filter.json"
    filtering.write_text(
        json.dumps(
            {
                "complete": True,
                "pending_layers": [],
                "completed_layers": sorted(EXPECTED_LAYERS),
                "thresholds": DEFAULT_THRESHOLDS,
                "n_train_records": 42_908,
                "n_remove_edges": 12,
                "n_inspect_edges": 20,
                "n_remove_train_records": 10,
                "remove_train_records_by_eval_dataset": {"mmstar": 10},
            }
        ),
        encoding="utf-8",
    )
    frozen = tmp_path / "frozen.json"
    frozen.write_text(
        json.dumps(
            {
                "status": "pass",
                "filter_manifest_sha256": _sha(filtering),
                "candidate_language": "conservative contamination candidates",
                "n_remove_items": 8,
                "n_retained_items": 38_862,
                "n_retained_image_references": 42_895,
                "ids_output": "ids.json",
                "ids_sha256": "a" * 64,
                "dataset_output": "dataset.jsonl",
                "dataset_sha256": "b" * 64,
                "image_index_dir": "caption_images",
                "image_index_manifest_sha256": "c" * 64,
                "n_retained_unique_images": 42_000,
            }
        ),
        encoding="utf-8",
    )
    return records, filtering, frozen


def test_report_passes_only_for_complete_exact_pipeline(tmp_path: Path) -> None:
    records, filtering, frozen = _fixtures(tmp_path)

    report = build_report(
        record_summary_path=records,
        filter_manifest_path=filtering,
        freeze_summary_path=frozen,
    )

    assert report["status"] == "pass"
    assert all(report["checks"].values())


def test_report_fails_when_ocr_is_pending_even_if_filter_claims_complete(tmp_path: Path) -> None:
    records, filtering, frozen = _fixtures(tmp_path)
    payload = json.loads(filtering.read_text())
    payload["pending_layers"] = ["ocr_text_overlap"]
    payload["completed_layers"].remove("ocr_text_overlap")
    filtering.write_text(json.dumps(payload), encoding="utf-8")
    frozen_payload = json.loads(frozen.read_text())
    frozen_payload["filter_manifest_sha256"] = _sha(filtering)
    frozen.write_text(json.dumps(frozen_payload), encoding="utf-8")

    report = build_report(
        record_summary_path=records,
        filter_manifest_path=filtering,
        freeze_summary_path=frozen,
    )

    assert report["status"] == "fail"
    assert report["checks"]["no_pending_layers"] is False
    assert report["checks"]["all_registered_layers_complete"] is False


def test_finalize_launcher_is_guarded_and_tmux_detached() -> None:
    source = (
        Path(__file__).resolve().parents[1] / "scripts" / "launch_virl39k_decon_finalize.sh"
    ).read_text(encoding="utf-8")

    assert "scripts/storage_guard.py --tier S" in source
    assert "scripts/summarize_decon.py" in source
    assert "scripts/freeze_virl39k_training_subset.py" in source
    assert "scripts/build_virl39k_decon_report.py" in source
    assert 'tmux new-session -d -s "${RUN_ID}"' in source
    assert "gpu_ids: []" in source
