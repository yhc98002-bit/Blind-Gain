#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


TEMPLATE_COUNTS = {
    "header_cued_table_code_v02": 300,
    "coordinate_register_twenty_point_x_v02": 600,
    "starred_series_value_nine_v07": 300,
}
TEMPLATE_LABELS = {
    "header_cued_table_code_v02": "document",
    "coordinate_register_twenty_point_x_v02": "geometry",
    "starred_series_value_nine_v07": "chart",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_metrics(name: str, metrics: dict[str, Any]) -> None:
    if int(metrics.get("n_pairs", -1)) != 1200:
        raise ValueError(f"{name} does not contain 1,200 pairs")
    per_template = metrics.get("per_template")
    if not isinstance(per_template, dict) or set(per_template) != set(TEMPLATE_COUNTS):
        raise ValueError(f"{name} template set mismatch")
    for template, expected in TEMPLATE_COUNTS.items():
        if int(per_template[template].get("n_pairs", -1)) != expected:
            raise ValueError(f"{name} count mismatch for {template}")
    for cell in [metrics, *per_template.values()]:
        for field in ("pair_accuracy", "member_accuracy", "collapse_rate"):
            value = float(cell[field])
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} has invalid {field}: {value}")


def build_payload(
    *,
    baseline: dict[str, dict[str, Any]],
    strong: dict[str, dict[str, Any]],
    download_manifest: dict[str, Any],
    checkout_manifest: dict[str, Any],
    caption_manifest: dict[str, Any],
    deletion_record: dict[str, Any],
    artifact_paths: dict[str, Path],
) -> dict[str, Any]:
    if set(baseline) != {"r19", "r20"} or set(strong) != {"r19", "r20"}:
        raise ValueError("strong-caption report requires R19 and R20 baseline/strong metrics")
    for package in ("r19", "r20"):
        _validate_metrics(f"{package} baseline", baseline[package])
        _validate_metrics(f"{package} strong", strong[package])
    checks = {
        "download_complete": download_manifest.get("status") == "complete",
        "checkout_pass": checkout_manifest.get("status") == "pass",
        "caption_complete": caption_manifest.get("status") == "complete",
        "caption_tp4": caption_manifest.get("tensor_parallel_width") == 4
        and caption_manifest.get("replica_count") == 1,
        "question_blind_384": caption_manifest.get("caption_prompt_contract")
        == "question_blind_v1"
        and caption_manifest.get("max_new_tokens") == 384,
        "weights_deleted": deletion_record.get("status") == "deleted"
        and deletion_record.get("path_absent_after_deletion") is True,
        "model_hash_preserved": deletion_record.get("model_sha256_tree")
        == checkout_manifest.get("sha256_tree"),
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise ValueError(f"strong-caption artifact contract failed: {failed}")

    rows = []
    for package in ("r19", "r20"):
        rows.append(
            {
                "package": package,
                "template": "overall",
                "n_pairs": 1200,
                "baseline_pair_accuracy": float(baseline[package]["pair_accuracy"]),
                "strong_pair_accuracy": float(strong[package]["pair_accuracy"]),
                "delta": float(strong[package]["pair_accuracy"])
                - float(baseline[package]["pair_accuracy"]),
                "strong_member_accuracy": float(strong[package]["member_accuracy"]),
                "strong_collapse_rate": float(strong[package]["collapse_rate"]),
            }
        )
        for template in TEMPLATE_COUNTS:
            base_cell = baseline[package]["per_template"][template]
            strong_cell = strong[package]["per_template"][template]
            rows.append(
                {
                    "package": package,
                    "template": TEMPLATE_LABELS[template],
                    "template_id": template,
                    "n_pairs": TEMPLATE_COUNTS[template],
                    "baseline_pair_accuracy": float(base_cell["pair_accuracy"]),
                    "strong_pair_accuracy": float(strong_cell["pair_accuracy"]),
                    "delta": float(strong_cell["pair_accuracy"])
                    - float(base_cell["pair_accuracy"]),
                    "strong_member_accuracy": float(strong_cell["member_accuracy"]),
                    "strong_collapse_rate": float(strong_cell["collapse_rate"]),
                }
            )
    return {
        "schema_version": "blind-gains.strong-caption-stress.v1",
        "status": "complete",
        "checks": checks,
        "caption_model_id": caption_manifest.get("model_id"),
        "caption_model_revision": caption_manifest.get("model_revision"),
        "caption_tensor_parallel_width": 4,
        "caption_replica_count": 1,
        "caption_max_new_tokens": 384,
        "qa_model": "Qwen/Qwen2.5-VL-7B-Instruct",
        "rows": rows,
        "weights_deleted": True,
        "deleted_model_bytes": deletion_record.get("model_total_bytes"),
        "artifacts": {
            name: {"path": str(path), "sha256": _sha256(path)}
            for name, path in sorted(artifact_paths.items())
        },
    }


def render_report(payload: dict[str, Any], machine_path: Path) -> str:
    table = []
    for row in payload["rows"]:
        table.append(
            f"| {row['package'].upper()} | {row['template']} | {row['n_pairs']} | "
            f"{row['baseline_pair_accuracy']:.4f} | {row['strong_pair_accuracy']:.4f} | "
            f"{row['delta']:+.4f} | {row['strong_collapse_rate']:.4f} |"
        )
    return "\n".join(
        [
            "# Strong Caption Stress",
            "",
            "Status:",
            "- R19 and R20 were captioned once with the fixed question-blind 72B prompt at 384 tokens and answered with the standard 7B caption-only QA protocol.",
            "- This measures caption leakage headroom only; it does not repair the document template's 7B visual ceiling.",
            "- This is a stress-test result, not a PI gate declaration.",
            "",
            "Evidence:",
            f"- Captioner: `{payload['caption_model_id']}` revision `{payload['caption_model_revision']}`, one TP4 replica.",
            f"- Machine report: `{machine_path}`.",
            f"- Ephemeral model bytes deleted after caption-store commit: `{payload['deleted_model_bytes']}`.",
            "",
            "| Package | Template | Pairs | 7B-caption baseline | 72B-caption stress | Delta | Strong collapse |",
            "|---|---|---:|---:|---:|---:|---:|",
            *table,
            "",
            "Problems:",
            "- A stronger captioner can expose more visual facts, so low leakage under a 3B/7B captioner is not a universal text-channel guarantee.",
            "- Caption-only success remains a property of the fixed captioner-plus-QA protocol, not a proof that pixels are unnecessary for arbitrary policies.",
            "",
            "Decision:",
            "- Report per-template headroom and retain the original R19/R20 visual and caption baselines unchanged.",
            "- Treat the document 7B saturation as a separate instrument limitation.",
            "- Keep no model weights on shared storage; the guarded deletion record is required and included.",
            "",
            "Next actions:",
            "- Carry the strongest observed caption-only cell into the preregistration caveats and paper limitations.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--r19-baseline", type=Path, required=True)
    parser.add_argument("--r20-baseline", type=Path, required=True)
    parser.add_argument("--r19-strong", type=Path, required=True)
    parser.add_argument("--r20-strong", type=Path, required=True)
    parser.add_argument("--download-manifest", type=Path, required=True)
    parser.add_argument("--checkout-manifest", type=Path, required=True)
    parser.add_argument("--caption-manifest", type=Path, required=True)
    parser.add_argument("--deletion-record", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--machine-output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.machine_output.exists():
        raise FileExistsError("refusing to overwrite strong-caption reports")
    paths = {
        "r19_baseline": args.r19_baseline,
        "r20_baseline": args.r20_baseline,
        "r19_strong": args.r19_strong,
        "r20_strong": args.r20_strong,
        "download_manifest": args.download_manifest,
        "checkout_manifest": args.checkout_manifest,
        "caption_manifest": args.caption_manifest,
        "deletion_record": args.deletion_record,
    }
    payload = build_payload(
        baseline={
            "r19": json.loads(args.r19_baseline.read_text(encoding="utf-8")),
            "r20": json.loads(args.r20_baseline.read_text(encoding="utf-8")),
        },
        strong={
            "r19": json.loads(args.r19_strong.read_text(encoding="utf-8")),
            "r20": json.loads(args.r20_strong.read_text(encoding="utf-8")),
        },
        download_manifest=json.loads(args.download_manifest.read_text(encoding="utf-8")),
        checkout_manifest=json.loads(args.checkout_manifest.read_text(encoding="utf-8")),
        caption_manifest=json.loads(args.caption_manifest.read_text(encoding="utf-8")),
        deletion_record=json.loads(args.deletion_record.read_text(encoding="utf-8")),
        artifact_paths=paths,
    )
    args.machine_output.parent.mkdir(parents=True, exist_ok=True)
    args.machine_output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    args.output.write_text(render_report(payload, args.machine_output), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "rows": len(payload["rows"])}))


if __name__ == "__main__":
    main()
