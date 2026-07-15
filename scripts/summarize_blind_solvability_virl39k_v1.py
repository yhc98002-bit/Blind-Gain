#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from scripts.summarize_blind_solvability_v2 import (
    SCORE_FIELDS,
    _equal,
    _expected_decoding,
    _parse_runs,
    _read_jsonl,
    _summarize_condition,
)
from src.analysis.blind_solvability import bootstrap_mean_ci, real_blind_quadrants
from src.eval.blind_solvability import (
    CONDITIONS,
    PILOT_ROW_SCHEMA_VERSION,
    PILOT_SCORING_MODE,
    load_geometry_rows,
    score_item_pilot,
)
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT, load_prompt_contract_from_run_manifest
from src.rewards.answer_reward import PARSER_VERSION
from src.rewards.pilot_reward import (
    DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
    PILOT_REWARD_VERSION,
    SYMBOLIC_GRADER_GUARD_VERSION,
)


DEFAULT_EXPECTED_JOB_TYPE = "l10_virl39k_blind_solvability_v1"
DEFAULT_EXPECTED_MODEL_REVISION = "artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _identity(row: dict[str, Any]) -> tuple[str, int]:
    return str(row["split"]), int(row["row_index"])


def _item_contract(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "qid": row.get("qid"),
        "problem": row.get("problem"),
        "ground_truth": row.get("ground_truth"),
        "image_sha256": row.get("image_sha256"),
        "source_metadata": row.get("source_metadata"),
    }


def _expected_contract(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "qid": row.get("qid"),
        "problem": row.get("problem"),
        "ground_truth": row.get("answer"),
        "image_sha256": [image["sha256"] for image in row.get("images", [])],
        "source_metadata": row.get("metadata"),
    }


def _source_statistics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    image_hashes = [image["sha256"] for row in rows for image in row.get("images", [])]
    return {
        "sample_size": len(rows),
        "source_counts": dict(sorted(Counter(str(row["metadata"]["source"]) for row in rows).items())),
        "category_counts": dict(sorted(Counter(str(row["metadata"]["category"]) for row in rows).items())),
        "answer_type_counts": dict(
            sorted(Counter(str(row["metadata"]["answer_type"]) for row in rows).items())
        ),
        "image_count_counts": {
            str(key): value
            for key, value in sorted(Counter(len(row.get("images", [])) for row in rows).items())
        },
        "image_references": len(image_hashes),
        "unique_images": len(set(image_hashes)),
        "max_images_per_item": max((len(row.get("images", [])) for row in rows), default=0),
    }


def _verify_source_images(rows: list[dict[str, Any]]) -> tuple[bool, int, int]:
    checked: dict[str, str] = {}
    mismatches = 0
    missing = 0
    for row in rows:
        for image in row.get("images", []):
            path = Path(str(image["path"]))
            expected = str(image["sha256"])
            if not path.is_file():
                missing += 1
                continue
            actual = checked.get(str(path))
            if actual is None:
                actual = _sha256(path)
                checked[str(path)] = actual
            if actual != expected:
                mismatches += 1
    return missing == 0 and mismatches == 0, missing, mismatches


def audit_runs(
    run_dirs: dict[str, Path],
    source_manifest: Path,
    sample_spec_path: Path,
    format_prompt: Path,
    *,
    expected_job_type: str = DEFAULT_EXPECTED_JOB_TYPE,
    expected_model_revision: str = DEFAULT_EXPECTED_MODEL_REVISION,
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    source_hash = _sha256(source_manifest)
    sample_spec_hash = _sha256(sample_spec_path)
    format_prompt_hash = _sha256(format_prompt)
    expected_rows = load_geometry_rows(source_manifest, ("audit",), train_filter_ids=None)
    expected_contracts = {_identity(row): _expected_contract(row) for row in expected_rows}
    expected_keys = set(expected_contracts)
    sample_spec = json.loads(sample_spec_path.read_text(encoding="utf-8"))
    observed_stats = _source_statistics(expected_rows)
    spec_fields = tuple(observed_stats)
    spec_matches = all(sample_spec.get(field) == observed_stats[field] for field in spec_fields)
    images_valid, missing_images, image_hash_mismatches = _verify_source_images(expected_rows)

    rows_by_condition: dict[str, list[dict[str, Any]]] = {}
    manifest_checks: dict[str, bool] = {}
    identity_unique: dict[str, bool] = {}
    item_contract_checks: dict[str, bool] = {}
    row_contract_checks: dict[str, bool] = {}
    decoding_checks: dict[str, bool] = {}
    mismatch_rows: dict[str, int] = {}
    mismatch_fields: Counter[str] = Counter()
    output_hashes: dict[str, str] = {}
    manifest_hashes: dict[str, str] = {}
    caption_contract_ok = True

    for condition in CONDITIONS:
        run_dir = run_dirs[condition]
        manifest_path = run_dir / "run_manifest.json"
        output_path = run_dir / "per_item.jsonl"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        rows = _read_jsonl(output_path)
        rows_by_condition[condition] = rows
        output_hashes[condition] = _sha256(output_path)
        manifest_hashes[condition] = _sha256(manifest_path)
        manifest_checks[condition] = bool(
            manifest.get("status") == "complete"
            and manifest.get("exit_code") == 0
            and manifest.get("job_type") == expected_job_type
            and manifest.get("condition") == condition
            and manifest.get("data_manifest") == str(source_manifest)
            and manifest.get("source_manifest_sha256") == source_hash
            and manifest.get("sample_spec") == str(sample_spec_path)
            and manifest.get("sample_spec_sha256") == sample_spec_hash
            and manifest.get("sample_size") == len(expected_rows)
            and manifest.get("max_images_per_item") == observed_stats["max_images_per_item"]
            and manifest.get("format_prompt_sha256") == format_prompt_hash
            and manifest.get("train_filter_ids") is None
            and manifest.get("train_filter_sha256") is None
            and manifest.get("model_revision") == expected_model_revision
            and manifest.get("parser_version") == PARSER_VERSION
            and manifest.get("pilot_reward_version") == PILOT_REWARD_VERSION
            and manifest.get("scoring_mode") == PILOT_SCORING_MODE
            and manifest.get("prompt_contract_sha256") == DEFAULT_PROMPT_CONTRACT.sha256
            and manifest.get("group_size") == 5
            and manifest.get("sample_count") == 16
            and manifest.get("sample_temperature") == 1
            and manifest.get("max_tokens") == 2048
            and manifest.get("format_weight") == 0.5
            and manifest.get("symbolic_grader_guard_version")
            == SYMBOLIC_GRADER_GUARD_VERSION
            and manifest.get("symbolic_grader_timeout_seconds")
            == DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS
            and manifest.get("seed") == 20260710
            and manifest.get("decoding") == _expected_decoding(20260710)
        )
        caption_source = manifest.get("caption_source_run")
        if condition == "caption":
            caption_manifest = Path(str(caption_source)) / "run_manifest.json" if caption_source else None
            if caption_manifest is None or not caption_manifest.is_file():
                caption_contract_ok = False
            else:
                caption_payload = json.loads(caption_manifest.read_text(encoding="utf-8"))
                caption_contract_ok = caption_contract_ok and bool(
                    caption_payload.get("status") == "complete"
                    and caption_payload.get("max_new_tokens") == 384
                )
        elif caption_source is not None:
            caption_contract_ok = False

        try:
            prompt_contract = load_prompt_contract_from_run_manifest(manifest_path)
        except Exception:
            prompt_contract = DEFAULT_PROMPT_CONTRACT
            manifest_checks[condition] = False

        seen: set[tuple[str, int]] = set()
        duplicate = False
        item_contract_ok = True
        row_contract_ok = True
        decoding_ok = True
        condition_mismatches = 0
        for row in rows:
            try:
                key = _identity(row)
            except Exception:
                row_contract_ok = False
                condition_mismatches += 1
                continue
            if key in seen:
                duplicate = True
            seen.add(key)
            if _item_contract(row) != expected_contracts.get(key):
                item_contract_ok = False
            if row.get("decoding") != _expected_decoding(20260710):
                decoding_ok = False
            fixed = bool(
                row.get("schema_version") == PILOT_ROW_SCHEMA_VERSION
                and row.get("condition") == condition
                and row.get("source_manifest_sha256") == source_hash
                and row.get("train_filter_sha256") is None
                and row.get("format_prompt_sha256") == format_prompt_hash
                and row.get("parser_version") == PARSER_VERSION
                and row.get("pilot_reward_version") == PILOT_REWARD_VERSION
                and row.get("scoring_mode") == PILOT_SCORING_MODE
                and row.get("prompt_contract_sha256") == DEFAULT_PROMPT_CONTRACT.sha256
                and row.get("symbolic_grader_guard_version")
                == SYMBOLIC_GRADER_GUARD_VERSION
                and row.get("symbolic_grader_timeout_seconds")
                == DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS
                and isinstance(row.get("greedy_native_r1v_shadow_valid"), bool)
                and isinstance(row.get("sampled_native_r1v_shadow_valid"), list)
                and len(row["sampled_native_r1v_shadow_valid"]) == 16
                and all(
                    isinstance(value, bool)
                    for value in row["sampled_native_r1v_shadow_valid"]
                )
            )
            sampled = row.get("sampled_responses")
            if not fixed or not isinstance(sampled, list) or len(sampled) != 16:
                row_contract_ok = False
                condition_mismatches += 1
                continue
            recomputed = score_item_pilot(
                str(row.get("ground_truth", "")),
                str(row.get("greedy_response", "")),
                [str(response) for response in sampled],
                group_size=5,
                prompt_contract=prompt_contract,
                format_weight=0.5,
                symbolic_grader_timeout_seconds=DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
            )
            differs = False
            for field in SCORE_FIELDS:
                if field not in row or not _equal(row.get(field), recomputed[field]):
                    mismatch_fields[field] += 1
                    differs = True
            if differs:
                condition_mismatches += 1
        identity_unique[condition] = not duplicate and len(seen) == len(rows)
        item_contract_checks[condition] = item_contract_ok and seen == expected_keys
        row_contract_checks[condition] = row_contract_ok
        decoding_checks[condition] = decoding_ok
        mismatch_rows[condition] = condition_mismatches

    condition_keys = {
        condition: {_identity(row) for row in rows if "split" in row and "row_index" in row}
        for condition, rows in rows_by_condition.items()
    }
    row_counts = {condition: len(rows) for condition, rows in rows_by_condition.items()}
    checks = {
        "all_run_manifests_complete_and_registered": all(manifest_checks.values()),
        "source_manifest_and_sample_spec_hashes_exact": bool(source_hash and sample_spec_hash),
        "sample_spec_recomputes_exactly": spec_matches,
        "source_images_present_and_hash_verified": images_valid,
        "row_count_exact_4096": len(expected_rows) == 4096
        and all(count == 4096 for count in row_counts.values()),
        "row_identity_unique": all(identity_unique.values()),
        "row_identity_equal_to_frozen_sample": all(keys == expected_keys for keys in condition_keys.values()),
        "scientific_item_contract_equal": all(item_contract_checks.values()),
        "multi_image_distribution_exact": observed_stats["image_count_counts"]
        == sample_spec.get("image_count_counts")
        and observed_stats["max_images_per_item"] == sample_spec.get("max_images_per_item"),
        "row_version_contract_valid": all(row_contract_checks.values()),
        "decoding_parameters_locked": all(decoding_checks.values()),
        "caption_store_question_blind_contract_pinned": caption_contract_ok,
        "symbolic_grader_guard_locked": all(manifest_checks.values())
        and all(row_contract_checks.values()),
        "recomputed_scores_match": sum(mismatch_rows.values()) == 0,
        "output_hashes_recorded": len(output_hashes) == len(CONDITIONS)
        and all(len(value) == 64 for value in output_hashes.values()),
    }
    audit = {
        "schema_version": "blind-gains.virl39k-blind-audit.v1",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "conditions": list(CONDITIONS),
        "expected_job_type": expected_job_type,
        "expected_model_revision": expected_model_revision,
        "row_counts": row_counts,
        "expected_row_count": len(expected_rows),
        "frozen_sample_statistics": observed_stats,
        "sample_spec_fields_checked": list(spec_fields),
        "missing_source_images": missing_images,
        "source_image_hash_mismatches": image_hash_mismatches,
        "recomputed_score_mismatch_count": sum(mismatch_rows.values()),
        "recomputed_score_mismatch_rows_by_condition": mismatch_rows,
        "recomputed_score_mismatch_fields": dict(sorted(mismatch_fields.items())),
        "decoding_parameters": _expected_decoding(20260710),
        "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
        "parser_version": PARSER_VERSION,
        "pilot_reward_version": PILOT_REWARD_VERSION,
        "symbolic_grader_guard_version": SYMBOLIC_GRADER_GUARD_VERSION,
        "symbolic_grader_timeout_seconds": DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
        "source_manifest": str(source_manifest),
        "source_manifest_sha256": source_hash,
        "sample_spec": str(sample_spec_path),
        "sample_spec_sha256": sample_spec_hash,
        "format_prompt_sha256": format_prompt_hash,
        "per_item_output_sha256": output_hashes,
        "run_manifest_sha256": manifest_hashes,
        "runs": {condition: str(run_dirs[condition]) for condition in CONDITIONS},
    }
    return audit, rows_by_condition


def _group_breakdown(rows: list[dict[str, Any]], field: str, seed: int) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str((row.get("source_metadata") or {}).get(field, "unknown"))].append(row)
    result = {}
    for offset, (name, group) in enumerate(sorted(grouped.items())):
        result[name] = {
            "n": len(group),
            "p_greedy": bootstrap_mean_ci(
                (float(row["p_greedy"]) for row in group), seed=seed + offset * 10
            ),
            "p_i_jeffreys": bootstrap_mean_ci(
                (float(row["p_i_jeffreys"]) for row in group), seed=seed + offset * 10 + 1
            ),
            "q_i": bootstrap_mean_ci(
                (float(row["q_i"]) for row in group), seed=seed + offset * 10 + 2
            ),
        }
    return result


def build_summary(
    rows_by_condition: dict[str, list[dict[str, Any]]], audit: dict[str, Any]
) -> dict[str, Any]:
    if audit.get("status") != "pass":
        raise ValueError("refusing to summarize ViRL39K outputs before audit pass")
    aggregates = {}
    for condition_index, condition in enumerate(CONDITIONS):
        rows = rows_by_condition[condition]
        seed = 20260710 + condition_index * 10000
        aggregates[condition] = {
            "overall": _summarize_condition(rows, seed),
            "by_category": _group_breakdown(rows, "category", seed + 1000),
            "by_answer_type": _group_breakdown(rows, "answer_type", seed + 2000),
            "by_source": _group_breakdown(rows, "source", seed + 3000),
            "by_image_count_bucket": _group_breakdown(rows, "image_count_bucket", seed + 4000),
        }
    quadrants = {
        condition: real_blind_quadrants(rows_by_condition["real"], rows_by_condition[condition])
        for condition in CONDITIONS
        if condition != "real"
    }
    return {
        "schema_version": "blind-gains.virl39k-blind-summary.v1",
        "status": "pass",
        "dataset_name": "ViRL39K frozen stratified sample",
        "n_items": audit["expected_row_count"],
        "evaluation_contract": {
            "model_revision": audit["expected_model_revision"],
            "max_tokens": 2048,
            "sample_count": 16,
            "sample_temperature": 1.0,
            "group_size": 5,
            "format_weight": 0.5,
            "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
            "parser_version": PARSER_VERSION,
            "pilot_reward_version": PILOT_REWARD_VERSION,
            "symbolic_grader_guard_version": SYMBOLIC_GRADER_GUARD_VERSION,
            "symbolic_grader_timeout_seconds": DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
            "scoring_mode": PILOT_SCORING_MODE,
        },
        "audit": audit,
        "aggregates": aggregates,
        "real_blind_greedy_quadrants": quadrants,
    }


def _metric(summary: dict[str, Any], condition: str, field: str) -> str:
    value = summary["aggregates"][condition]["overall"]["metrics"][field]
    return f"{value['mean']:.4f} [{value['ci_low']:.4f}, {value['ci_high']:.4f}]"


def render_summary(summary: dict[str, Any], audit_json: Path) -> str:
    lines = [
        "# ViRL39K Blind-Solvability Sample V1",
        "",
        "Status:",
        "- Complete for the frozen 4,096-item stratified sample under all five conditions.",
        f"- Machine status JSON: `{audit_json}`.",
        "- This is a base-model corpus audit, not a pilot-arm result or PI gate decision.",
        "",
        "Evidence:",
        f"- Model revision: `{summary['evaluation_contract']['model_revision']}`.",
        "- Decoding: greedy plus n=16 at temperature 1.0, 2,048 maximum tokens, G=5.",
        f"- Symbolic grading: `{summary['evaluation_contract']['symbolic_grader_guard_version']}` at `{summary['evaluation_contract']['symbolic_grader_timeout_seconds']}` seconds per bounded call.",
        f"- Frozen source SHA256: `{summary['audit']['source_manifest_sha256']}`.",
        f"- Multi-image distribution: `{summary['audit']['frozen_sample_statistics']['image_count_counts']}`; maximum 8 images.",
        "",
        "Overall results with item-bootstrap 95% CIs:",
        "| Condition | Pilot greedy accuracy | Canonical greedy accuracy | Mean p_i | Mean q_i | Mean pilot reward | Format rate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for condition in CONDITIONS:
        lines.append(
            f"| {condition} | {_metric(summary, condition, 'p_greedy')} | "
            f"{_metric(summary, condition, 'greedy_canonical_correct')} | "
            f"{_metric(summary, condition, 'p_i_jeffreys')} | "
            f"{_metric(summary, condition, 'q_i')} | "
            f"{_metric(summary, condition, 'mean_sampled_training_reward')} | "
            f"{_metric(summary, condition, 'mean_sampled_format_reward')} |"
        )
    lines.extend(
        [
            "",
            "Per-category pilot greedy accuracy and mean q_i:",
            "| Condition | Category | n | Greedy accuracy | Mean q_i |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for condition in CONDITIONS:
        for category, record in summary["aggregates"][condition]["by_category"].items():
            greedy = record["p_greedy"]
            q_i = record["q_i"]
            lines.append(
                f"| {condition} | {category} | {record['n']} | "
                f"{greedy['mean']:.4f} [{greedy['ci_low']:.4f}, {greedy['ci_high']:.4f}] | "
                f"{q_i['mean']:.4f} [{q_i['ci_low']:.4f}, {q_i['ci_high']:.4f}] |"
            )
    lines.extend(
        [
            "",
            "Problems:",
            "- Item-bootstrap intervals quantify sample uncertainty, not run-to-run RL variance.",
            "- Question-blind captions measure caption-channel solvability; they are not claims about all possible captioners.",
            "",
            "Decision:",
            "- Retain these audited p_i and q_i values as corpus diagnostics. No gate decision is made here.",
            "",
            "Next actions:",
            "- Compare the ViRL39K pattern with filtered Geometry3K v2 and use discrepancies to scope corpus-specific sensitivity analyses.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_audit(audit: dict[str, Any], audit_json: Path) -> str:
    task_label = (
        "M8"
        if audit.get("expected_job_type") == "m8_virl39k_7b_blind_solvability_v1"
        else "L10"
    )
    lines = [
        "# ViRL39K Blind-Solvability V1 Independent Audit",
        "",
        "Status:",
        f"- Machine audit status: `{audit['status']}`.",
        f"- Machine status JSON: `{audit_json}`.",
        "",
        "Evidence:",
    ]
    lines.extend(f"- `{name}`: `{str(value).lower()}`." for name, value in audit["checks"].items())
    lines.extend(
        [
            f"- Row counts: `{audit['row_counts']}`.",
            f"- Recomputed score mismatches: `{audit['recomputed_score_mismatch_count']}`.",
            f"- Missing/hash-mismatched source images: `{audit['missing_source_images']}` / `{audit['source_image_hash_mismatches']}`.",
            "",
            "Problems:",
            "- Any false sub-check makes the logical-AND audit fail; no waiver is encoded here.",
            "",
            "Decision:",
            f"- This artifact certifies measurement integrity only and does not declare {task_label} or a PI gate passed.",
            "",
            "Next actions:",
            f"- Use the summary only when this machine status is pass and the {task_label} ledger has its named reports.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="append", required=True, help="condition=run_directory")
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--sample-spec", type=Path, required=True)
    parser.add_argument("--format-prompt", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--audit-json-output", type=Path, required=True)
    parser.add_argument("--audit-markdown-output", type=Path, required=True)
    parser.add_argument(
        "--expected-job-type",
        default=DEFAULT_EXPECTED_JOB_TYPE,
    )
    parser.add_argument(
        "--expected-model-revision",
        default=DEFAULT_EXPECTED_MODEL_REVISION,
    )
    args = parser.parse_args()
    outputs = (
        args.json_output,
        args.markdown_output,
        args.audit_json_output,
        args.audit_markdown_output,
    )
    if any(path.exists() for path in outputs):
        raise FileExistsError("refusing to overwrite a ViRL39K summary or audit artifact")
    for path in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
    audit, rows = audit_runs(
        _parse_runs(args.run),
        args.source_manifest,
        args.sample_spec,
        args.format_prompt,
        expected_job_type=args.expected_job_type,
        expected_model_revision=args.expected_model_revision,
    )
    args.audit_json_output.write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    args.audit_markdown_output.write_text(
        render_audit(audit, args.audit_json_output), encoding="utf-8"
    )
    if audit["status"] != "pass":
        raise SystemExit(1)
    summary = build_summary(rows, audit)
    args.json_output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    args.markdown_output.write_text(
        render_summary(summary, args.audit_json_output), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
