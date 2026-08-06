#!/usr/bin/env python3
"""Summarize and audit one Gate-1 step-0 reward diagnostic (T7).

Mirrors scripts/summarize_mini_a5_step0.py for the per-member v2 schema:
groups the predictions by pseudo-pair, requires the exact a/b x five-rollout
identity set, recomputes both the member reward and the CP joint diagnostic
from the raw responses with the registered reward implementation, and refuses
on any recompute mismatch. Writes the per-arm step-0 reward audit.

Adversarial fixture (I10): tests/test_summarize_mini_a5_gate1_step0_fixture.py.
"""
from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from src.fliptrack.schema import sha256_file
from src.rewards.cp_grpo_reward import compute_member_score, compute_score

SCHEMA_VERSION = "blind-gains.mini-a5-gate1-step0-audit.v1"
EXPECTED_PAIRS = 192
ROLLOUT_N = 5


def _stats(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0, "hit_rate": None, "population_variance": None}
    return {
        "n": len(values),
        "hit_rate": statistics.fmean(values),
        "population_variance": statistics.pvariance(values),
    }


def build_summary(rows: list[dict[str, Any]], arm: str) -> dict[str, Any]:
    errors: list[str] = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if str(row.get("arm")) != arm:
            errors.append(f"row arm {row.get('arm')!r} != audited arm {arm!r}")
        grouped[str(row["pair_group_uid"])].append(row)

    recompute_mismatches = 0
    member_rewards: list[float] = []
    contract_valid: list[float] = []
    by_template: dict[str, list[float]] = defaultdict(list)
    by_member: dict[str, list[float]] = defaultdict(list)
    reason_codes: Counter[str] = Counter()
    pairs_checked = 0

    for uid, pair_rows in sorted(grouped.items()):
        identities = sorted(
            (str(row["pair_member"]), int(row["pair_rollout_index"]))
            for row in pair_rows
        )
        expected = sorted(
            (member, index) for member in ("a", "b") for index in range(ROLLOUT_N)
        )
        if identities != expected:
            errors.append(f"{uid}: expected exact a/b x {ROLLOUT_N} rollout identities")
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
            if float(row["contract_valid"]) != float(member_score["format"]):
                recompute_mismatches += 1
            member_reward = float(row["member_reward"])
            member_rewards.append(member_reward)
            contract_valid.append(float(row["contract_valid"]))
            by_template[str(row["template_id"])].append(member_reward)
            by_member[str(row["pair_member"])].append(member_reward)
            reason_codes[str(row["reward_disagreement_reason_code"])] += 1
        pairs_checked += 1

    checks = {
        "row_count_exact": len(rows) == EXPECTED_PAIRS * 2 * ROLLOUT_N,
        "pair_count_exact": pairs_checked == EXPECTED_PAIRS,
        "identity_sets_complete": not any(
            "rollout identities" in error for error in errors
        ),
        "reward_recompute_identical": recompute_mismatches == 0,
        "single_arm": not any("audited arm" in error for error in errors),
    }
    if not checks["row_count_exact"]:
        errors.append(
            f"row count {len(rows)} != {EXPECTED_PAIRS * 2 * ROLLOUT_N}"
        )
    if recompute_mismatches:
        errors.append(f"{recompute_mismatches} reward recompute mismatches")

    return {
        "schema_version": SCHEMA_VERSION,
        "arm": arm,
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "errors": errors,
        "pairs": pairs_checked,
        "rows": len(rows),
        "recompute_mismatches": recompute_mismatches,
        "member_reward": _stats(member_rewards),
        "contract_valid": _stats(contract_valid),
        "member_reward_by_template": {
            template: _stats(values) for template, values in sorted(by_template.items())
        },
        "member_reward_by_pseudo_member": {
            member: _stats(values) for member, values in sorted(by_member.items())
        },
        "reward_disagreement_reason_codes": dict(sorted(reason_codes.items())),
        "optimizer_steps": 0,
        "main_optimizer_steps_authorized_by_this_audit": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=("std", "necessity"), required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    for output in (args.json_output, args.markdown_output):
        if output.exists():
            raise FileExistsError(f"refusing to overwrite audit: {output}")

    rows = [
        json.loads(line)
        for line in args.predictions.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    manifest = json.loads(args.run_manifest.read_text(encoding="utf-8"))
    summary = build_summary(rows, args.arm)
    summary["provenance"] = {
        "run_id": manifest.get("run_id"),
        "run_manifest": str(args.run_manifest),
        "run_status": manifest.get("status"),
        "run_exit_code": manifest.get("exit_code"),
        "predictions": str(args.predictions),
        "predictions_sha256": sha256_file(args.predictions),
        "node": manifest.get("node"),
        "gpu_ids": manifest.get("gpu_ids"),
    }
    if manifest.get("status") != "complete" or manifest.get("exit_code") != 0:
        summary["status"] = "fail"
        summary["errors"].append("run manifest is not complete/exit0")

    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        f"# Mini-A5 Gate-1 step-0 reward audit -- {args.arm} (v1)",
        "",
        f"Status: `{summary['status']}`. Zero optimizer steps; this audit",
        "authorizes no main-arm steps and opens no endpoint value.",
        "",
        f"- Machine artifact: `{args.json_output}`.",
        f"- Run: `{summary['provenance']['run_id']}`.",
        f"- Pairs `{summary['pairs']}`, rows `{summary['rows']}`, recompute mismatches `{summary['recompute_mismatches']}`.",
        f"- Member-reward hit rate: `{summary['member_reward']['hit_rate']}`.",
        f"- Contract validity: `{summary['contract_valid']['hit_rate']}`.",
        "",
        "| Check | Result |",
        "| --- | --- |",
    ]
    lines += [
        f"| `{name}` | `{'pass' if result else 'fail'}` |"
        for name, result in summary["checks"].items()
    ]
    lines += ["", f"Errors: `{summary['errors']}`.", ""]
    args.markdown_output.write_text("\n".join(lines), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": summary["status"],
                "arm": args.arm,
                "member_reward_hit_rate": summary["member_reward"]["hit_rate"],
            }
        )
    )
    if summary["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
