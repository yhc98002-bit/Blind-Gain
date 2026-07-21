#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.run_pilot_geo3k_step100_eval import (
    FOLLOWUP_ROW_SCHEMA_VERSION,
    REGISTERED_DECODING,
    ROW_SCHEMA_VERSION,
)
from src.eval.blind_solvability import (
    PILOT_SCORING_MODE,
    load_geometry_rows,
    score_greedy_item_pilot,
)
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT
from src.rewards.answer_reward import PARSER_VERSION
from src.rewards.pilot_reward import PILOT_REWARD_VERSION


ROOT = Path(__file__).resolve().parents[1]
ARM_CONDITIONS = {
    "a1_real": "real",
    "a2_gray": "gray",
    "a2b_noimage": "none",
    "a3_caption": "caption",
}
SCORE_FIELDS = {
    "scoring_mode",
    "pilot_reward_version",
    "symbolic_grader_guard_version",
    "symbolic_grader_timeout_seconds",
    "format_weight",
    "training_reward",
    "pilot_accuracy_reward",
    "format_reward",
    "native_r1v_shadow_reward",
    "native_r1v_shadow_valid",
    "canonical_eval_reward",
    "canonical_correct",
    "reward_disagreement_reason",
    "extracted_answer",
    "extractor_valid",
    "contract_valid",
    "acc_final",
    "acc_strict",
    "parser_version",
    "prompt_contract_id",
    "prompt_contract_sha256",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve(root: Path, value: str) -> Path:
    candidate = Path(value)
    return (candidate if candidate.is_absolute() else root / candidate).resolve()


def _same(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return left is right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-12)
    return left == right


def audit_run(
    run_dir: Path,
    *,
    root: Path = ROOT,
    expected_row_count: int = 601,
) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    manifest_path = run_dir / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    is_followup = manifest.get("job_type") == "m3_pilot_geo3k_checkpoint_eval"
    expected_job_type = (
        "m3_pilot_geo3k_checkpoint_eval"
        if is_followup
        else "m2_pilot_geo3k_step100_eval"
    )
    expected_global_step = manifest.get("global_step") if is_followup else 100
    expected_row_schema = (
        FOLLOWUP_ROW_SCHEMA_VERSION if is_followup else ROW_SCHEMA_VERSION
    )
    output_paths = manifest.get("expected_artifacts", [])
    output_path = _resolve(root, output_paths[0]) if len(output_paths) == 1 else run_dir / "missing"
    source_path = _resolve(root, str(manifest.get("data_manifest", "missing")))
    training_manifest_path = _resolve(
        root,
        f"{manifest.get('source_training_run', 'missing')}/run_manifest.json",
    )
    checkpoint_path = _resolve(root, str(manifest.get("model_revision", "missing")))
    checkpoint_index = checkpoint_path / "model.safetensors.index.json"
    r19_marker = _resolve(root, str(manifest.get("r19_completion_marker", "missing")))
    provenance_mode = manifest.get("checkpoint_provenance_mode", "retention_marker")
    retention_value = manifest.get("retention_marker")
    retention_marker = (
        _resolve(root, retention_value) if isinstance(retention_value, str) else None
    )

    manifest_checks = {
        "job_type": manifest.get("job_type") == expected_job_type,
        "complete": manifest.get("status") == "complete",
        "exit_zero": manifest.get("exit_code") == 0,
        "artifacts_exist": manifest.get("artifacts_exist") is True,
        "global_step": expected_global_step in {60, 100}
        and manifest.get("global_step") == expected_global_step,
        "followup_seed": (not is_followup) or manifest.get("pilot_seed") in {2, 3},
        "arm_condition": ARM_CONDITIONS.get(str(manifest.get("arm")))
        == manifest.get("condition"),
        "expected_rows": manifest.get("expected_row_count") == expected_row_count,
        "tp1": manifest.get("tensor_parallel_width") == 1
        and manifest.get("replica_count") == 1,
        "decoding": manifest.get("decoding") == REGISTERED_DECODING,
        "prompt_contract": manifest.get("prompt_contract_sha256")
        == DEFAULT_PROMPT_CONTRACT.sha256,
        "parser": manifest.get("parser_version") == PARSER_VERSION,
        "reward": manifest.get("pilot_reward_version") == PILOT_REWARD_VERSION,
        "scoring_mode": manifest.get("scoring_mode") == PILOT_SCORING_MODE,
        "checkpoint_provenance_mode": provenance_mode
        in {"retention_marker", "r19_marker_index"},
    }
    input_checks = {
        "output_present": output_path.is_file(),
        "output_path_bound": output_path == (run_dir / "per_item.jsonl").resolve(),
        "source_present": source_path.is_file(),
        "training_manifest_present": training_manifest_path.is_file(),
        "checkpoint_index_present": checkpoint_index.is_file(),
        "r19_marker_present": r19_marker.is_file(),
    }
    if not all(input_checks.values()):
        checks = {**manifest_checks, **input_checks}
        return {
            "schema_version": (
                "blind-gains.pilot-followup-geo3k-audit.v1"
                if is_followup
                else "blind-gains.pilot-geo3k-step100-audit.v1"
            ),
            "status": "fail",
            "checks": checks,
            "errors": [key for key, value in checks.items() if not value],
            "scientific_gate_decision": None,
            "performance_values_reported": False,
        }

    r19 = json.loads(r19_marker.read_text(encoding="utf-8"))
    r19_checks = r19.get("checks")
    r19_bound = (
        r19.get("status") == "complete"
        and r19.get("global_step") == expected_global_step
        and Path(str(r19.get("checkpoint_path", ""))).resolve() == checkpoint_path
        and r19.get("checkpoint_index_sha256") == manifest.get("checkpoint_index_sha256")
        and isinstance(r19_checks, dict)
        and bool(r19_checks)
        and all(r19_checks.values())
    )
    hash_checks = {
        "source_manifest_hash": _sha256(source_path)
        == manifest.get("source_manifest_sha256"),
        "training_manifest_hash": _sha256(training_manifest_path)
        == manifest.get("source_training_manifest_sha256"),
        "checkpoint_index_hash": _sha256(checkpoint_index)
        == manifest.get("checkpoint_index_sha256"),
        "r19_marker_hash": _sha256(r19_marker)
        == manifest.get("r19_completion_marker_sha256"),
        "r19_marker_binds_checkpoint_index": r19_bound,
    }
    if provenance_mode == "retention_marker":
        retention_present = retention_marker is not None and retention_marker.is_file()
        retention: dict[str, Any] = (
            json.loads(retention_marker.read_text(encoding="utf-8"))
            if retention_present and retention_marker is not None
            else {}
        )
        merged_files = retention.get("merged_checkpoint_files", [])
        merged_files_match = bool(merged_files)
        for item in merged_files:
            if not isinstance(item, dict) or not isinstance(item.get("file"), str):
                merged_files_match = False
                break
            path = checkpoint_path.parent / item["file"]
            if (
                not path.is_file()
                or path.stat().st_size != item.get("size_bytes")
                or _sha256(path) != item.get("sha256")
            ):
                merged_files_match = False
                break
        hash_checks.update(
            {
                "retention_marker_present": retention_present,
                "retention_marker_hash": retention_present
                and retention_marker is not None
                and _sha256(retention_marker) == manifest.get("retention_marker_sha256"),
                "merged_checkpoint_hash": retention.get("merged_checkpoint_sha256")
                == manifest.get("merged_checkpoint_sha256"),
                "merged_checkpoint_files_match": merged_files_match,
            }
        )
    else:
        hash_checks["relocation_decoupled"] = (
            retention_marker is None
            and manifest.get("retention_marker_sha256") is None
            and manifest.get("merged_checkpoint_sha256") is None
        )

    source_rows = load_geometry_rows(source_path, splits=("test",), train_filter_ids=None)
    raw_lines = output_path.read_text(encoding="utf-8").splitlines()
    parsed_rows: list[dict[str, Any]] = []
    parse_errors: list[str] = []
    for line_number, line in enumerate(raw_lines, start=1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            parse_errors.append(f"line_{line_number}:{error}")
            continue
        if not isinstance(row, dict):
            parse_errors.append(f"line_{line_number}:not_object")
            continue
        parsed_rows.append(row)

    identities = [(row.get("split"), row.get("row_index")) for row in parsed_rows]
    expected_identities = [(row["split"], row["row_index"]) for row in source_rows]
    row_checks = {
        "jsonl_parse": not parse_errors,
        "row_count": len(parsed_rows) == expected_row_count,
        "source_row_count": len(source_rows) == expected_row_count,
        "row_identity_and_order": identities == expected_identities,
        "row_identity_unique": len(set(identities)) == len(identities),
    }

    static_mismatches: Counter[str] = Counter()
    score_mismatches: Counter[str] = Counter()
    strict_identity_mismatches = 0
    for source, stored in zip(source_rows, parsed_rows):
        expected_static = {
            "schema_version": expected_row_schema,
            "arm": manifest.get("arm"),
            "global_step": expected_global_step,
            "split": source["split"],
            "row_index": source["row_index"],
            "qid": source.get("qid"),
            "problem": source["problem"],
            "ground_truth": source["answer"],
            "image_sha256": [image["sha256"] for image in source.get("images", [])],
            "condition": manifest.get("condition"),
            "source_manifest_sha256": manifest.get("source_manifest_sha256"),
            "source_training_manifest_sha256": manifest.get(
                "source_training_manifest_sha256"
            ),
            "model_revision": manifest.get("model_revision"),
            "checkpoint_index_sha256": manifest.get("checkpoint_index_sha256"),
            "decoding": REGISTERED_DECODING,
        }
        for field, expected in expected_static.items():
            if not _same(stored.get(field), expected):
                static_mismatches[field] += 1

        recomputed = score_greedy_item_pilot(
            str(source["answer"]),
            str(stored.get("greedy_response", "")),
            DEFAULT_PROMPT_CONTRACT,
        )
        for field in SCORE_FIELDS:
            if not _same(stored.get(field), recomputed.get(field)):
                score_mismatches[field] += 1
        if stored.get("acc_strict") is not (
            stored.get("contract_valid") is True and stored.get("acc_final") is True
        ):
            strict_identity_mismatches += 1

    checks = {
        **manifest_checks,
        **input_checks,
        **hash_checks,
        **row_checks,
        "static_fields_match": not static_mismatches,
        "scores_recompute": not score_mismatches,
        "strict_identity": strict_identity_mismatches == 0,
    }
    return {
        "schema_version": (
            "blind-gains.pilot-followup-geo3k-audit.v1"
            if is_followup
            else "blind-gains.pilot-geo3k-step100-audit.v1"
        ),
        "status": "pass" if all(checks.values()) else "fail",
        "run_id": manifest.get("run_id"),
        "run_manifest": str(manifest_path),
        "run_manifest_sha256": _sha256(manifest_path),
        "output": str(output_path),
        "output_sha256": _sha256(output_path),
        "row_count": len(parsed_rows),
        "expected_row_count": expected_row_count,
        "checks": checks,
        "parse_errors": parse_errors[:20],
        "static_mismatch_count": sum(static_mismatches.values()),
        "static_mismatch_fields": dict(sorted(static_mismatches.items())),
        "score_recomputation_mismatch_count": sum(score_mismatches.values()),
        "score_recomputation_mismatch_fields": dict(sorted(score_mismatches.items())),
        "strict_identity_mismatch_count": strict_identity_mismatches,
        "scientific_gate_decision": None,
        "performance_values_reported": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite audit output: {args.output}")
    payload = audit_run(args.run_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    raise SystemExit(0 if payload["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
