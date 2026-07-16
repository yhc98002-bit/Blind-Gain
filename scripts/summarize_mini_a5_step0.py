#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from src.rewards.cp_grpo_reward import compute_member_score, compute_score


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stats(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {
            "n": 0,
            "hit_rate": None,
            "population_variance": None,
            "sample_variance": None,
        }
    return {
        "n": len(values),
        "hit_rate": statistics.fmean(values),
        "population_variance": statistics.pvariance(values),
        "sample_variance": statistics.variance(values) if len(values) > 1 else 0.0,
    }


def build_summary(rows: list[dict[str, Any]], predictions_path: Path) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["pair_group_uid"])].append(row)
    errors: list[str] = []
    recompute_mismatches = 0
    unique_cp: list[float] = []
    member_rewards: list[float] = []
    by_template_cp: dict[str, list[float]] = defaultdict(list)
    by_template_member: dict[str, list[float]] = defaultdict(list)
    by_side: dict[str, list[float]] = defaultdict(list)
    reason_codes: Counter[str] = Counter()

    for uid, pair_rows in grouped.items():
        identities = sorted(
            (str(row["pair_member"]), int(row["pair_rollout_index"]))
            for row in pair_rows
        )
        expected = sorted((member, index) for member in ("a", "b") for index in range(5))
        if identities != expected:
            errors.append(f"{uid}: expected exact A/B x five rollout identities")
            continue
        ordered = sorted(
            pair_rows,
            key=lambda row: (str(row["pair_member"]), int(row["pair_rollout_index"])),
        )
        reward_inputs = [
            {
                "response": row["response"],
                "ground_truth": row["ground_truth"],
                "pair_group_uid": row["pair_group_uid"],
                "pair_member": row["pair_member"],
                "pair_rollout_index": row["pair_rollout_index"],
            }
            for row in ordered
        ]
        recomputed_cp = compute_score(reward_inputs)
        recomputed_member = compute_member_score(reward_inputs)
        for row, cp_score, member_score in zip(
            ordered, recomputed_cp, recomputed_member, strict=True
        ):
            if float(row["cp_joint_reward"]) != float(cp_score["overall"]):
                recompute_mismatches += 1
            if float(row["member_reward"]) != float(member_score["overall"]):
                recompute_mismatches += 1
            member = float(row["member_reward"])
            member_rewards.append(member)
            by_template_member[str(row["template_id"])].append(member)
            by_side[str(row["pair_member"])].append(member)
            reason_codes[str(row["reward_disagreement_reason_code"])] += 1
            if row["pair_member"] == "a":
                cp = float(row["cp_joint_reward"])
                unique_cp.append(cp)
                by_template_cp[str(row["template_id"])].append(cp)

    contracts = {
        key: sorted({json.dumps(row.get(key), sort_keys=True) for row in rows})
        for key in (
            "sample_manifest_sha256",
            "format_prompt_sha256",
            "model_revision",
            "seed",
            "rollout_n",
            "temperature",
            "top_p",
            "max_tokens",
            "parser_version",
            "pilot_reward_version",
            "cp_reward_version",
        )
    }
    checks = {
        "exact_row_count_1920": len(rows) == 1920,
        "exact_pair_count_192": len(grouped) == 192,
        "all_pairs_complete": not errors,
        "reward_recomputation_exact": recompute_mismatches == 0,
        "one_contract_value_per_field": all(len(values) == 1 for values in contracts.values()),
        "unique_cp_outcomes_exact_960": len(unique_cp) == 960,
        "member_outcomes_exact_1920": len(member_rewards) == 1920,
    }
    return {
        "schema_version": "blind-gains.mini-a5-step0-summary.v1",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "errors": errors[:100],
        "reward_recompute_mismatches": recompute_mismatches,
        "predictions_path": str(predictions_path),
        "predictions_sha256": sha256_file(predictions_path),
        "contracts": contracts,
        "overall": {
            "cp_unique_pair_outcomes": _stats(unique_cp),
            "member_outcomes": _stats(member_rewards),
        },
        "per_template": {
            template: {
                "cp_unique_pair_outcomes": _stats(by_template_cp[template]),
                "member_outcomes": _stats(by_template_member[template]),
            }
            for template in sorted(by_template_cp)
        },
        "pair_order_check": {
            "side_a": _stats(by_side["a"]),
            "side_b": _stats(by_side["b"]),
            "side_a_minus_b_hit_rate": (
                statistics.fmean(by_side["a"]) - statistics.fmean(by_side["b"])
                if by_side["a"] and by_side["b"]
                else None
            ),
        },
        "reward_disagreement_reason_code_counts": dict(sorted(reason_codes.items())),
        "scientific_gate_decision": None,
    }


def _atomic(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite step-0 summary: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def render_markdown(payload: dict[str, Any], machine_path: Path) -> str:
    rows = [
        f"| `{name}` | `{'pass' if value else 'fail'}` |"
        for name, value in payload["checks"].items()
    ]
    return "\n".join(
        [
            "# Mini-A5 Step-0 Reward Audit V1",
            "",
            "Status:",
            f"- Audit status: `{payload['status']}`.",
            "- Base-model diagnostic only; no optimizer step is taken and no PI gate is declared.",
            "",
            "Evidence:",
            f"- Machine summary: `{machine_path}`.",
            f"- Predictions: `{payload['predictions_path']}`; SHA256 `{payload['predictions_sha256']}`.",
            f"- Overall reward statistics: `{json.dumps(payload['overall'], sort_keys=True)}`.",
            f"- Pair-order check: `{json.dumps(payload['pair_order_check'], sort_keys=True)}`.",
            "",
            "Per-template statistics:",
            "```json",
            json.dumps(payload["per_template"], indent=2, sort_keys=True),
            "```",
            "",
            "Checks:",
            "| Check | Result |",
            "| --- | --- |",
            *rows,
            "",
            "Problems:",
            f"- Audit errors: `{payload['errors']}`.",
            "- A merged registration marker and EasyR1 GPU plumbing smoke remain separate prerequisites.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    with args.predictions.open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    payload = build_summary(rows, args.predictions)
    _atomic(args.json_output, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    _atomic(args.markdown_output, render_markdown(payload, args.json_output))
    print(json.dumps({"status": payload["status"], "checks": payload["checks"]}, sort_keys=True))
    raise SystemExit(0 if payload["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
