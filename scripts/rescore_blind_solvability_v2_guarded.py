#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from src.eval.blind_solvability import (
    CONDITIONS,
    GUARDED_RESCORE_VERSION,
    PILOT_ROW_SCHEMA_VERSION,
    score_item_pilot,
)
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT
from src.rewards.pilot_reward import (
    DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
    SYMBOLIC_GRADER_GUARD_VERSION,
)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rescore_rows(
    raw_lines: list[str],
    *,
    condition: str,
    source_run: str,
) -> tuple[list[str], dict[str, Any]]:
    if condition not in CONDITIONS:
        raise ValueError(f"unsupported L7 condition: {condition}")
    if not raw_lines or any(not line.strip() for line in raw_lines):
        raise ValueError("guarded L7 rescore requires non-empty JSONL without blank rows")

    identities: set[tuple[str, int]] = set()
    output_lines: list[str] = []
    native_invalid = 0
    mathruler_errors = 0
    for line_number, raw_line in enumerate(raw_lines, start=1):
        row = json.loads(raw_line)
        if row.get("schema_version") != PILOT_ROW_SCHEMA_VERSION:
            raise ValueError(f"source row {line_number} has an unsupported schema")
        if row.get("condition") != condition:
            raise ValueError(f"source row {line_number} condition mismatch")
        identity = (str(row.get("split")), int(row.get("row_index", -1)))
        if identity in identities:
            raise ValueError(f"duplicate source row identity: {identity}")
        identities.add(identity)
        sampled = row.get("sampled_responses")
        if not isinstance(sampled, list) or len(sampled) != 16:
            raise ValueError(f"source row {line_number} does not contain 16 samples")

        rescored = score_item_pilot(
            str(row.get("ground_truth", "")),
            str(row.get("greedy_response", "")),
            [str(response) for response in sampled],
            group_size=5,
            prompt_contract=DEFAULT_PROMPT_CONTRACT,
            format_weight=0.5,
            symbolic_grader_timeout_seconds=DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
        )
        if (
            rescored.get("symbolic_grader_guard_version")
            != SYMBOLIC_GRADER_GUARD_VERSION
            or rescored.get("symbolic_grader_timeout_seconds")
            != DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS
        ):
            raise RuntimeError("guarded L7 rescore did not use the registered symbolic guard")
        native_invalid += int(not rescored["greedy_native_r1v_shadow_valid"])
        native_invalid += sum(
            int(not value) for value in rescored["sampled_native_r1v_shadow_valid"]
        )
        reasons = [
            rescored["greedy_reward_disagreement_reason"],
            *rescored["sampled_reward_disagreement_reasons"],
        ]
        mathruler_errors += sum(
            int(str(reason).startswith("mathruler_error_")) for reason in reasons
        )

        normalized = {
            **row,
            **rescored,
            "guarded_rescore_version": GUARDED_RESCORE_VERSION,
            "guarded_rescore_source_run": source_run,
            "guarded_rescore_source_row_sha256": _sha256_bytes(
                raw_line.encode("utf-8")
            ),
        }
        output_lines.append(
            json.dumps(
                normalized,
                sort_keys=True,
                ensure_ascii=True,
                separators=(",", ":"),
            )
        )

    return output_lines, {
        "guarded_rescore_version": GUARDED_RESCORE_VERSION,
        "symbolic_grader_guard_version": SYMBOLIC_GRADER_GUARD_VERSION,
        "symbolic_grader_timeout_seconds": DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
        "n_rows": len(output_lines),
        "n_responses": len(output_lines) * 17,
        "native_r1v_shadow_invalid_count": native_invalid,
        "mathruler_error_count": mathruler_errors,
    }


def _update_manifest_stats(path: Path, stats: dict[str, Any], output: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["guarded_rescore_stats"] = stats
    payload["output_sha256"] = _sha256_file(output)
    temporary = path.with_name(f".{path.name}.rescore.{os.getpid()}")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--condition", required=True, choices=CONDITIONS)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite guarded L7 output: {args.output}")

    source_manifest_path = args.source_run / "run_manifest.json"
    source_output = args.source_run / "per_item.jsonl"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    run_manifest = json.loads(args.run_manifest.read_text(encoding="utf-8"))
    if source_manifest.get("status") != "complete":
        raise ValueError("guarded L7 rescore source run is not complete")
    if source_manifest.get("condition") != args.condition:
        raise ValueError("guarded L7 rescore source condition mismatch")
    expected = {
        "job_type": "l7_blind_solvability_geo3k_v2_guarded_rescore",
        "condition": args.condition,
        "guarded_rescore_version": GUARDED_RESCORE_VERSION,
        "rescore_source_run": str(args.source_run),
        "rescore_source_output_sha256": _sha256_file(source_output),
        "rescore_source_manifest_sha256": _sha256_file(source_manifest_path),
        "symbolic_grader_guard_version": SYMBOLIC_GRADER_GUARD_VERSION,
        "symbolic_grader_timeout_seconds": DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
    }
    mismatches = {
        key: {"expected": value, "found": run_manifest.get(key)}
        for key, value in expected.items()
        if run_manifest.get(key) != value
    }
    if mismatches:
        raise ValueError(f"guarded L7 rescore manifest mismatch: {mismatches}")

    raw_lines = source_output.read_text(encoding="utf-8").splitlines()
    output_lines, stats = rescore_rows(
        raw_lines,
        condition=args.condition,
        source_run=str(args.source_run),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(f".{args.output.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        for line in output_lines:
            handle.write(line + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, args.output)
    _update_manifest_stats(args.run_manifest, stats, args.output)
    print(json.dumps(stats, sort_keys=True))


if __name__ == "__main__":
    main()
