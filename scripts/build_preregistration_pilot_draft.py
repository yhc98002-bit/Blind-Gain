#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from src.rewards.pilot_reward import (
    DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
    SYMBOLIC_GRADER_GUARD_VERSION,
)


ARM_CONFIGS = {
    "A1 real": Path("configs/train/mech_a1_real_3b_geo3k.yaml"),
    "A2 gray": Path("configs/train/mech_a2_gray_3b_geo3k.yaml"),
    "A2b no-image": Path("configs/train/mech_a2b_noimage_3b_geo3k.yaml"),
    "A3 caption": Path("configs/train/mech_a3_caption_3b_geo3k.yaml"),
}
ARM_CONDITIONS = {
    "A1 real": "real",
    "A2 gray": "gray",
    "A2b no-image": "none",
    "A3 caption": "caption",
}
BLIND_CONDITIONS = ("gray", "none", "caption")
ONE_SEED_SCOPE = (
    "These are pilot estimands and directional predictions, not definitive hypothesis tests "
    "of the training procedure; item-level paired intervals quantify evaluation uncertainty, "
    "not run-to-run RL variance."
)
FALSIFICATION = (
    "If A1 improves geo3k strongly and produces a material geometry-FlipTrack gain while "
    "blind arms do not, the shortcut-only account is disfavored."
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalized_config(config: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(config)
    normalized["data"].pop("image_condition")
    normalized["trainer"].pop("experiment_name")
    normalized["trainer"].pop("save_checkpoint_path")
    return normalized


def audit_arm_configs(root: Path) -> dict[str, Any]:
    loaded: dict[str, dict[str, Any]] = {}
    hashes: dict[str, str] = {}
    for arm, relative in ARM_CONFIGS.items():
        path = root / relative
        loaded[arm] = yaml.safe_load(path.read_text(encoding="utf-8"))
        hashes[arm] = _sha256(path)
    reference = _normalized_config(loaded["A1 real"])
    if any(_normalized_config(config) != reference for config in loaded.values()):
        raise ValueError("pilot configs differ outside registered arm identity fields")
    for arm, config in loaded.items():
        if config["data"]["image_condition"] != ARM_CONDITIONS[arm]:
            raise ValueError(f"pilot config image condition mismatch for {arm}")
        if config["worker"]["rollout"]["tensor_parallel_size"] != 1:
            raise ValueError(f"pilot config violates TP1 placement for {arm}")
        if config["trainer"]["n_gpus_per_node"] != 4:
            raise ValueError(f"pilot config must use four colocated GPUs for {arm}")
        if config["trainer"]["max_steps"] != 100:
            raise ValueError(f"pilot config max steps drifted for {arm}")
        if config["trainer"]["save_freq"] != 20 or config["trainer"]["val_freq"] != 10:
            raise ValueError(f"pilot checkpoint/evaluation cadence drifted for {arm}")
    return {"hashes": hashes, "normalized_config": reference}


def _q_row(summary: dict[str, Any], condition: str) -> str:
    aggregate = summary["aggregates"][condition]["train"]
    metric = aggregate["metrics"]["q_i"]
    distribution = aggregate["q_i_distribution"]
    return (
        f"| {condition} | {metric['mean']:.6f} | {metric['ci_low']:.6f} | "
        f"{metric['ci_high']:.6f} | {distribution['q25']:.6f} | "
        f"{distribution['median']:.6f} | {distribution['q75']:.6f} |"
    )


def build_draft(
    *,
    root: Path,
    l7_summary_path: Path,
    l7_audit_path: Path,
    filtered_ids_path: Path,
) -> str:
    summary = json.loads(l7_summary_path.read_text(encoding="utf-8"))
    audit = json.loads(l7_audit_path.read_text(encoding="utf-8"))
    if summary.get("status") != "complete" or audit.get("status") != "pass":
        raise ValueError("preregistration draft requires complete L7 summary and pass audit")
    if summary.get("audit", {}).get("status") != "pass":
        raise ValueError("L7 summary does not embed a passing audit")
    if summary.get("audit", {}).get("per_item_output_sha256") != audit.get(
        "per_item_output_sha256"
    ):
        raise ValueError("L7 summary/audit per-item output hashes differ")
    contract = summary.get("evaluation_contract", {})
    if (
        contract.get("symbolic_grader_guard_version")
        != SYMBOLIC_GRADER_GUARD_VERSION
        or contract.get("symbolic_grader_timeout_seconds")
        != DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS
        or contract.get("max_tokens") != 2048
        or contract.get("sample_count") != 16
        or contract.get("group_size") != 5
    ):
        raise ValueError("L7 summary does not use the registered pilot contract")
    for condition in BLIND_CONDITIONS:
        if condition not in summary.get("aggregates", {}):
            raise ValueError(f"L7 summary lacks preregistration condition: {condition}")

    config_audit = audit_arm_configs(root)
    filtered_hash = _sha256(filtered_ids_path)
    summary_hash = _sha256(l7_summary_path)
    audit_hash = _sha256(l7_audit_path)
    output_hashes = audit["per_item_output_sha256"]
    if set(output_hashes) != {"real", "gray", "noise", "none", "caption"} or any(
        not isinstance(digest, str) or len(digest) != 64
        for digest in output_hashes.values()
    ):
        raise ValueError("L7 audit does not pin one SHA256 per registered condition")
    q_rows = [_q_row(summary, condition) for condition in BLIND_CONDITIONS]
    config_rows = [
        f"| {arm} | `{ARM_CONDITIONS[arm]}` | `{ARM_CONFIGS[arm]}` | `{digest}` |"
        for arm, digest in config_audit["hashes"].items()
    ]
    source_rows = [
        f"| {condition} | `{output_hashes[condition]}` |"
        for condition in BLIND_CONDITIONS
    ]

    lines = [
        "# Four-Arm Mechanical Pilot Preregistration V1 Draft",
        "",
        "Status:",
        "- `draft only`; not approved, not merged as L12, and not authorization for a pilot optimizer step.",
        "- Required external actions remain the frozen R19 human contact-sheet audit and approval by both PIs.",
        "",
        "Frozen inputs:",
        f"- Filtered Geometry3K IDs: `{filtered_ids_path}`, SHA256 `{filtered_hash}`.",
        f"- L7 summary: `{l7_summary_path}`, SHA256 `{summary_hash}`.",
        f"- L7 independent audit: `{l7_audit_path}`, SHA256 `{audit_hash}`, machine status `pass`.",
        f"- Pilot reward guard: `{SYMBOLIC_GRADER_GUARD_VERSION}` at `{DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS}` seconds.",
        "",
        "| Arm | Image condition | Config | SHA256 |",
        "| --- | --- | --- | --- |",
        *config_rows,
        "",
        "The configs are structurally identical after removing only `data.image_condition`, `trainer.experiment_name`, and `trainer.save_checkpoint_path`.",
        "",
        "Design:",
        "- Four arms: A1 real, A2 gray, A2b no-image, and A3 fixed 3B question-blind captions.",
        "- Qwen2.5-VL-3B, frozen vision tower, seed 1, G=5, 100 optimizer steps, and identical configs except registered arm identity.",
        "- Synchronous EasyR1/GRPO stays on one node with four colocated GPUs; 3B rollout serving is TP1.",
        "- Checkpoints: steps 0, 20, 40, 60, 80, and 100. Step 0 is the base model already on disk and is not duplicated.",
        "- Greedy full Geometry3K-test validation every 10 steps under one locked prompt contract.",
        "- Pilot checkpoints save to shared arm directories and are swept under the latest-raw-only retention rule; only step-100 merged remains on shared storage.",
        "",
        "One-seed scope:",
        f"> {ONE_SEED_SCOPE}",
        "",
        "Primary estimands:",
        "- `D_gray = Delta_A1 - Delta_A2gray`.",
        "- `D_none = Delta_A1 - Delta_A2b`.",
        "- `D_caption = Delta_A1 - Delta_A3`.",
        "- `Delta` is final minus step-0 greedy `Acc_final` on Geometry3K test; each estimand uses a paired item-bootstrap confidence interval.",
        "",
        "Primary mechanistic prediction:",
        "- Within each blind arm, per-item gains concentrate on items with high initial q_i under that arm's condition.",
        "- Registered test: rank correlation between per-item gain and initial q_i is greater than zero, accompanied by a q_i-quartile gain table.",
        "- The per-item q_i values are frozen by these guarded L7 output hashes:",
        "",
        "| Condition | Per-item output SHA256 |",
        "| --- | --- |",
        *source_rows,
        "",
        "Computed filtered-train q_i anchors:",
        "| Condition | Mean | CI low | CI high | Q25 | Median | Q75 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        *q_rows,
        "",
        "Directional predictions:",
        "- `Delta_A3 >= Delta_A2gray` and `Delta_A3 >= Delta_A2b`.",
        "- `Delta_A1` and `Delta_A3` are closer to each other than either is to the zero-visual-bit arms.",
        "",
        "Secondary analyses:",
        "- Recovery ratios are reported only if `Delta_A1 >= 2 x paired SE`, labeled conditional descriptive intervals.",
        "- Equivalence of `Delta_A2gray - Delta_A2b` uses margin +/-0.05 and is supported only if the paired CI lies entirely inside the margin.",
        "- Format prediction: `DeltaFormat_blind >= DeltaFormat_A1 - 0.05` using `contract_valid`, conditional on a nontrivial A1 format gain.",
        "",
        "RQ2 FlipTrack R19 endpoints:",
        "- Checkpoints: 0, 60, and 100. Step 60 is scored from the scratch-resident merged checkpoint before cleanup.",
        "- PRIMARY: geometry-category pair accuracy.",
        "- SECONDARY: overall R19 pair accuracy.",
        "- Document category is calibration only because the 7B instrument is saturated.",
        "- SESOI is +/-0.05; no material change is supported only if the paired CI is entirely within [-0.05, +0.05].",
        "",
        "Falsification statement:",
        f"> {FALSIFICATION}",
        "",
        "Deviations log:",
        "| Time | Deviation | Reason | Effect on estimands | PI disposition |",
        "| --- | --- | --- | --- | --- |",
        "",
        "Approval state:",
        "- R19 human contact-sheet audit: pending.",
        "- PI 1 approval: pending.",
        "- PI 2 approval: pending.",
        "- Final L12 path `reports/preregistration_pilot_v1.md`: intentionally absent.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--l7-summary", type=Path, required=True)
    parser.add_argument("--l7-audit", type=Path, required=True)
    parser.add_argument(
        "--filtered-ids",
        type=Path,
        default=Path("data/geo3k_pilot_filtered_ids.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    if args.output.name == "preregistration_pilot_v1.md":
        raise ValueError("draft generator refuses the final L12 preregistration filename")
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite preregistration draft: {args.output}")
    text = build_draft(
        root=args.root,
        l7_summary_path=args.l7_summary,
        l7_audit_path=args.l7_audit,
        filtered_ids_path=args.filtered_ids,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
