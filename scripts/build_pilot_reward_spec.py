#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PRECEDENCE_RULE = (
    "if mathruler and canonical numeric-equivalence disagree, mathruler's verdict is the reward "
    "and the disagreement is logged with a reason code."
)


def build_report(audit: dict[str, Any], manifest: dict[str, Any], audit_path: Path) -> str:
    if audit.get("status") != "pass":
        raise ValueError("refusing to publish pilot reward spec from a non-pass smoke audit")
    if manifest.get("status") != "complete" or manifest.get("exit_code") != 0:
        raise ValueError("pilot reward smoke manifest is not complete with exit code zero")
    if (
        audit.get("n_rows") != 13401
        or audit.get("n_training_shadow_rows") != 12800
        or audit.get("n_validation_shadow_rows") != 601
        or audit.get("expected_steps") != 5
    ):
        raise ValueError(
            "pilot reward smoke does not satisfy the exact five-step training/final-validation contract"
        )
    checks = audit.get("checks", {})
    training_checks = audit.get("training_contract_checks", {})
    partition_audit = audit.get("partition_audit", {})
    partition_checks = partition_audit.get("checks", {})
    if (
        not checks
        or not training_checks
        or not partition_checks
        or not all(checks.values())
        or not all(training_checks.values())
        or not all(partition_checks.values())
        or partition_audit.get("training_audit", {}).get("status") != "pass"
        or partition_audit.get("validation_audit", {}).get("status") != "pass"
    ):
        raise ValueError("pilot reward smoke audit contains a false sub-check")

    training_partition = partition_audit["training_audit"]
    validation_partition = partition_audit["validation_audit"]
    reward_counts = training_partition["training_reward_counts"]
    reason_counts = training_partition["reward_disagreement_reason_counts"]
    lines = [
        "# Pilot Reward Specification",
        "",
        "Status:",
        "- Complete. The custom pilot reward passed the exact five-step plumbing smoke and shadow audit.",
        f"- Machine status JSON: `{audit_path}`.",
        "- The native anchor reward path remains separate; this reward is bound only by pilot-arm configs.",
        "",
        "Evidence:",
        f"- Smoke run: `{manifest['run_id']}` on `{manifest['node']}` GPUs `{manifest['gpu_allocation']}`.",
        f"- Git/config/data hashes: `{manifest['git_hash']}` / `{manifest['config_hash']}` / `{manifest['data_manifest_hash']}`.",
        "- Exact training shadow rows: `12800` = 5 steps x 512 rollout prompts x group size 5.",
        "- Exact final-validation shadow rows: `601`, matching the frozen Geometry3K test answers in sequence.",
        f"- Training-partition reward counts: `{reward_counts}`.",
        f"- Training-partition disagreement reason counts: `{reason_counts}`.",
        f"- Validation-partition reward counts: `{validation_partition['training_reward_counts']}`.",
        "- All shadow values are finite; every training-reward identity recomputes exactly; parser/reward versions are canonical-v2/pilot-reward-v1.",
        "- Image-grid regression evidence: `reports/easyr1_image_grid_audit_v1.md` (0/1,288 mismatches after the payload fix).",
        "",
        "Reward contract:",
        "1. Extract the final answer span with canonical-v2.",
        "2. Grade that extracted span with mathruler.",
        "3. Compute `contract_valid` independently from exact `<answer>...</answer>` compliance.",
        "4. Set accuracy weight to 0.5 and format weight to 0.5, matching the reference recipe split.",
        f"5. Precedence rule: {PRECEDENCE_RULE}",
        "6. Log `training_reward`, `native_r1v_shadow_reward`, `canonical_eval_reward`, and `reward_disagreement_reason` per rollout.",
        "",
        "Problems:",
        "- The first full-path smoke exposed double-resized visual-grid drift before optimizer step 1. That run remains preserved in `reports/pilot_reward_smoke_failure_20260711.md`; the repaired run is the evidence above.",
        "- EasyR1 always performs a final validation pass and calls the same reward function. The failed v1 audit expected only training rows; v2 partitions the append-only shadow log using the exact 601-row test-answer sequence.",
        "- A five-step smoke certifies reward plumbing and nondegeneracy, not training stability or scientific efficacy.",
        "",
        "Decision:",
        "- Pin `pilot-reward-v1`, canonical-v2, mathruler precedence, and the 0.5/0.5 split for L7 and all four pilot arms.",
        "- Keep the anchor config bound to EasyR1 native `r1v.py`; do not retroactively rescore or modify anchor optimization.",
        "",
        "Next actions:",
        "- Run the five-condition L7 audit under this exact reward and fill preregistration quantities only from its audited outputs.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite pilot reward report: {args.output}")
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    manifest = json.loads(args.run_manifest.read_text(encoding="utf-8"))
    text = build_report(audit, manifest, args.audit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
