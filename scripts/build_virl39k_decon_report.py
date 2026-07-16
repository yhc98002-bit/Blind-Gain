#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from src.decon.core import DEFAULT_THRESHOLDS


EXPECTED_LAYERS = {
    "sha256_and_provenance",
    "phash_dhash",
    "dinov2_image_embedding",
    "normalized_exact_text",
    "question_5gram_jaccard",
    "bge_text_embedding",
    "ocr_text_overlap",
}
EXPECTED_EVAL_RECORDS = {
    "blink": 3_675,
    "hallusionbench": 1_129,
    "mathverse": 3_940,
    "mathvista": 999,
    "mmmu": 1_140,
    "mmstar": 1_500,
    "mmvp": 300,
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_report(
    *,
    record_summary_path: Path,
    filter_manifest_path: Path,
    freeze_summary_path: Path,
) -> dict[str, Any]:
    record_summary = json.loads(record_summary_path.read_text(encoding="utf-8"))
    filtering = json.loads(filter_manifest_path.read_text(encoding="utf-8"))
    frozen = json.loads(freeze_summary_path.read_text(encoding="utf-8"))
    checks = {
        "record_build_pass": record_summary.get("status") == "pass",
        "source_item_count_exact": record_summary.get("n_train_items") == 38_870,
        "source_record_count_exact": record_summary.get("n_train_records") == 42_908,
        "seven_suite_record_counts_exact": (
            record_summary.get("eval_dataset_record_counts") == EXPECTED_EVAL_RECORDS
        ),
        "filter_complete": filtering.get("complete") is True,
        "no_pending_layers": filtering.get("pending_layers") == [],
        "all_registered_layers_complete": set(filtering.get("completed_layers", []))
        == EXPECTED_LAYERS,
        "frozen_thresholds_exact": filtering.get("thresholds") == DEFAULT_THRESHOLDS,
        "filter_source_count_exact": filtering.get("n_train_records") == 42_908,
        "freeze_pass": frozen.get("status") == "pass",
        "freeze_uses_exact_filter": frozen.get("filter_manifest_sha256")
        == _sha256(filter_manifest_path),
        "whole_item_accounting_exact": (
            int(frozen.get("n_retained_items", -1))
            + int(frozen.get("n_remove_items", -1))
            == 38_870
        ),
        "frozen_outputs_hashed": bool(frozen.get("ids_sha256"))
        and bool(frozen.get("dataset_sha256")),
        "caption_image_index_exact": bool(frozen.get("image_index_manifest_sha256"))
        and int(frozen.get("n_retained_unique_images", -1)) > 0,
        "conservative_candidate_language": frozen.get("candidate_language")
        == "conservative contamination candidates",
    }
    return {
        "schema_version": "blind-gains.virl39k-layer1-decon-audit.v1",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "record_summary": str(record_summary_path),
        "record_summary_sha256": _sha256(record_summary_path),
        "filter_manifest": str(filter_manifest_path),
        "filter_manifest_sha256": _sha256(filter_manifest_path),
        "freeze_summary": str(freeze_summary_path),
        "freeze_summary_sha256": _sha256(freeze_summary_path),
        "counts": {
            "source_items": record_summary.get("n_train_items"),
            "source_image_records": record_summary.get("n_train_records"),
            "eval_image_records": record_summary.get("n_eval_records"),
            "remove_edges": filtering.get("n_remove_edges"),
            "inspect_edges": filtering.get("n_inspect_edges"),
            "remove_image_records": filtering.get("n_remove_train_records"),
            "remove_items": frozen.get("n_remove_items"),
            "retained_items": frozen.get("n_retained_items"),
            "retained_image_references": frozen.get("n_retained_image_references"),
        },
        "remove_records_by_eval_dataset": filtering.get(
            "remove_train_records_by_eval_dataset", {}
        ),
        "frozen_outputs": {
            "ids": frozen.get("ids_output"),
            "ids_sha256": frozen.get("ids_sha256"),
            "dataset": frozen.get("dataset_output"),
            "dataset_sha256": frozen.get("dataset_sha256"),
            "image_index": frozen.get("image_index_dir"),
            "image_index_manifest_sha256": frozen.get("image_index_manifest_sha256"),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    counts = report["counts"]
    checks = report["checks"]
    rows = "\n".join(
        f"| `{name}` | `{'pass' if passed else 'fail'}` |" for name, passed in checks.items()
    )
    dataset_rows = "\n".join(
        f"| {name} | {count:,} |" for name, count in EXPECTED_EVAL_RECORDS.items()
    )
    return f"""# ViRL39K vs Layer-1 Decontamination V1

Status:
- `{report['status']}` for the machine conjunction below.
- This is a data-readiness audit, not a PI scientific-gate decision and not M7
  training authorization.

Evidence:
- Source: 38,870 ViRL39K items / 42,908 image records.
- Layer-1 evaluation side: {counts['eval_image_records']:,} image records across
  all seven registered suites.
- Automatic filtering marks {counts['remove_image_records']:,} image records
  spanning {counts['remove_items']:,} whole items as conservative contamination
  candidates; {counts['retained_items']:,} items remain.
- Filter manifest SHA256: `{report['filter_manifest_sha256']}`.
- Frozen dataset SHA256: `{report['frozen_outputs']['dataset_sha256']}`.

| Layer-1 suite | Image records |
| --- | ---: |
{dataset_rows}

Audit:
| Check | Result |
| --- | --- |
{rows}

Problems:
- Inspect-band records are retained because calibrated inspect thresholds admit
  false positives. They are not confirmed duplicates.
- This report does not establish full 3B/7B caption-store coverage or matched
  training-config readiness.

Decision:
- Freeze by whole item: one automatic-remove image record removes all images and
  the question for that ViRL39K item.
- Preserve source/category strata for the registered H-mixed analysis.

Next actions:
- Generate and audit the full-subset 3B and 7B own-caption stores.
- Fill registered M7/M9 config fields and keep launchers fail-closed until those
  hashes are committed.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-summary", type=Path, required=True)
    parser.add_argument("--filter-manifest", type=Path, required=True)
    parser.add_argument("--freeze-summary", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    for output in (args.json_output, args.markdown_output):
        if output.exists():
            raise FileExistsError(f"refusing to overwrite ViRL39K decontamination report: {output}")
    report = build_report(
        record_summary_path=args.record_summary,
        filter_manifest_path=args.filter_manifest,
        freeze_summary_path=args.freeze_summary,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    args.markdown_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks": report["checks"]}, sort_keys=True))
    raise SystemExit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
