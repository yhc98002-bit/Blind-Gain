#!/usr/bin/env python3
"""Four-arm Gate-1 endpoint readout instrument (registered).

Builds the Gate-1 completion endpoint readout over the four registered arms

    arm 1  std        (mini_a5_std_seed1)
    arm 2  member     (mini_a5_same_data_seed1)
    arm 3  necessity  (mini_a5_necessity_seed1)
    arm 4  cp         (mini_a5_cp_seed1)

on one held-out FlipTrack item set (the R19 primary set for the registered
readout), per docs/registered_mini_a5_gate1_completion_v1.md: "Same
instruments, harness, and procedure as
docs/registered_mini_a5_endpoint_readout_v1.md, extended to four arms;
nothing else changes."

It REUSES the F8 two-arm comparison engine
scripts.compare_fliptrack_runs.compare_rows verbatim (imported, never
modified, so the published F8 v1 outputs remain byte-stable) and composes the
registered contrasts from it:

    1. arm 2 - arm 1  ("is the paired data enough?")
    2. arm 3 - arm 2  ("is item selection enough?")
    3. arm 1 - base and arm 3 - base: absolute levels against the frozen base
       cells already cited in F8 section 6 (point differences, no interval).

The arm 4 - arm 2 contrast was read in F8 and is NOT re-decided; the F8
primary-endpoint block is carried verbatim under
carried_from_f8_not_re_decided.

Invariants: both contracts reported for every cell, never merged (I7); task
roles reported separately, pooled numbers only under keys labeled
NOT_AN_ENDPOINT (I13); output carries schema_version (I15); output contains
no timestamps and is byte-identical on rerun over identical inputs.

Fail-closed behavior (adversarial fixtures in
tests/test_build_mini_a5_gate1_endpoint_readout_fixture.py; the predecessor
instrument scripts/compare_fliptrack_runs.py fails all of them):
  - missing or unreadable run_manifest.json refused;
  - run_manifest status != "complete" refused (partial readouts prohibited);
  - arm label mismatch refused (run_manifest model_path must contain the
    arm's registered checkpoint token);
  - item-set mismatch between any two arms refused;
  - template mismatch for any shared pair_id refused;
  - registered R19 shape (3 templates, 600/300/300 pairs) enforced unless
    --expect any (fixtures only);
  - malformed frozen-base report or wrong-schema F8 report refused;
  - existing output (or .partial) never overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.compare_fliptrack_runs import compare_rows
from src.eval.fliptrack_metrics import (
    aggregate_pair_metrics,
    aggregate_pair_metrics_by_template,
)

SCHEMA_VERSION = "blind-gains.mini-a5-gate1-endpoint-readout.v1"
F8_SCHEMA_VERSION = "blind-gains.mini-a5-f8-endpoint-readout.v1"
DEFAULT_BOOTSTRAP_DRAWS = 10000
DEFAULT_SEED = 20260729

ARM_ORDER = ("std", "member", "necessity", "cp")
ARM_NUMBERS = {"std": 1, "member": 2, "necessity": 3, "cp": 4}
ARM_LABELS = {
    "std": "mini_a5_std_seed1_step120",
    "member": "mini_a5_same_data_seed1_step120",
    "necessity": "mini_a5_necessity_seed1_step120",
    "cp": "mini_a5_cp_seed1_step120",
}
ARM_CHECKPOINT_TOKENS = {
    "std": "mini_a5_std_seed1",
    "member": "mini_a5_same_data_seed1",
    "necessity": "mini_a5_necessity_seed1",
    "cp": "mini_a5_cp_seed1",
}

PRIMARY_TEMPLATE = "coordinate_register_twenty_point_x_v02"
HEADER_TEMPLATE = "header_cued_table_code_v02"
NINE_TEMPLATE = "starred_series_value_nine_v07"
ROLES = {
    PRIMARY_TEMPLATE: "primary visual anchor (search + binding + read)",
    HEADER_TEMPLATE: (
        "saturated positive control / retention canary -- a DROP signals damage"
    ),
    NINE_TEMPLATE: "oracle-localized readout control",
}
UNREGISTERED_ROLE = "unregistered template (fixture or extension set)"
REGISTERED_N_PAIRS = {PRIMARY_TEMPLATE: 600, HEADER_TEMPLATE: 300, NINE_TEMPLATE: 300}

REGISTERED_CONTRASTS = (
    {
        "key": "contrast_1_arm2_minus_arm1",
        "question": "is the paired data enough?",
        "left_arm": "std",
        "right_arm": "member",
    },
    {
        "key": "contrast_2_arm3_minus_arm2",
        "question": "is item selection enough?",
        "left_arm": "member",
        "right_arm": "necessity",
    },
)

_LENIENT_KEYS = (
    "left_pair_accuracy",
    "right_pair_accuracy",
    "pair_accuracy_delta",
    "pair_accuracy_delta_ci95_low",
    "pair_accuracy_delta_ci95_high",
    "mcnemar",
)
_STRICT_KEYS = (
    "left_strict_pair_accuracy",
    "right_strict_pair_accuracy",
    "strict_pair_accuracy_delta",
    "strict_pair_accuracy_delta_ci95_low",
    "strict_pair_accuracy_delta_ci95_high",
    "strict_mcnemar",
)


class ReadoutRefusal(RuntimeError):
    """Raised whenever the instrument refuses to produce a readout."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _decision_rule(ci_low: float, ci_high: float) -> str:
    """Registered rule: MOVED iff the 95% CI excludes zero on the positive side."""
    if ci_low > 0.0:
        return "MOVED"
    if ci_high < 0.0:
        return "MOVED_NEGATIVE_DIRECTION"
    return "NOT MOVED"


def _contract_cell(block: dict[str, Any], contract: str) -> dict[str, Any]:
    keys = _LENIENT_KEYS if contract == "lenient" else _STRICT_KEYS
    ci_low = block[keys[3]]
    ci_high = block[keys[4]]
    mcnemar = block[keys[5]]
    return {
        "left_accuracy": block[keys[0]],
        "right_accuracy": block[keys[1]],
        "right_minus_left": block[keys[2]],
        "ci95_low": ci_low,
        "ci95_high": ci_high,
        "ci_excludes_zero": bool(ci_low > 0.0 or ci_high < 0.0),
        "mcnemar_exact_two_sided_p": mcnemar["p_value"],
        "mcnemar_b01_left_wrong_right_correct": mcnemar["b01"],
        "mcnemar_b10_left_correct_right_wrong": mcnemar["b10"],
        "decision_rule_outcome": _decision_rule(ci_low, ci_high),
    }


def _load_arm(arm: str, run_dir: Path) -> dict[str, Any]:
    run_dir = Path(run_dir)
    manifest_path = run_dir / "run_manifest.json"
    if not manifest_path.is_file():
        raise ReadoutRefusal(
            f"missing run manifest for arm '{arm}': {manifest_path} (fail-closed)"
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ReadoutRefusal(
            f"unreadable run manifest for arm '{arm}': {manifest_path}: {exc}"
        ) from exc
    status = manifest.get("status")
    if status != "complete":
        raise ReadoutRefusal(
            f"run manifest for arm '{arm}' has status {status!r}, not 'complete'"
            " -- partial readouts are prohibited, fail-closed"
        )
    token = ARM_CHECKPOINT_TOKENS[arm]
    model_path = str(manifest.get("model_path") or "")
    if token not in model_path:
        raise ReadoutRefusal(
            f"arm label mismatch for arm '{arm}': registered checkpoint token"
            f" '{token}' not found in run_manifest model_path {model_path!r}"
        )
    shard_paths = sorted((run_dir / "shards").glob("shard_*.jsonl"))
    if not shard_paths:
        raise ReadoutRefusal(
            f"no shard files for arm '{arm}' under {run_dir / 'shards'} (fail-closed)"
        )
    rows: list[dict[str, Any]] = []
    for path in shard_paths:
        with path.open(encoding="utf-8") as handle:
            rows.extend(json.loads(line) for line in handle if line.strip())
    if not rows:
        raise ReadoutRefusal(f"shard files for arm '{arm}' contain no rows (fail-closed)")
    seen: set[str] = set()
    for row in rows:
        pair_id = str(row["pair_id"])
        if pair_id in seen:
            raise ReadoutRefusal(f"duplicate pair_id {pair_id!r} in arm '{arm}'")
        seen.add(pair_id)
    return {
        "run_dir": run_dir,
        "manifest_path": manifest_path,
        "manifest": manifest,
        "shard_paths": shard_paths,
        "rows": rows,
    }


def _check_item_sets(arms: dict[str, dict[str, Any]]) -> dict[str, int]:
    reference_arm = ARM_ORDER[0]
    reference = {
        str(row["pair_id"]): str(row.get("template_id"))
        for row in arms[reference_arm]["rows"]
    }
    for arm in ARM_ORDER[1:]:
        current = {
            str(row["pair_id"]): str(row.get("template_id"))
            for row in arms[arm]["rows"]
        }
        if set(current) != set(reference):
            only_ref = sorted(set(reference) - set(current))[:5]
            only_cur = sorted(set(current) - set(reference))[:5]
            raise ReadoutRefusal(
                f"item-set mismatch between arms '{reference_arm}'"
                f" ({len(reference)} pairs) and '{arm}' ({len(current)} pairs);"
                f" only_{reference_arm} sample={only_ref}"
                f" only_{arm} sample={only_cur} (fail-closed)"
            )
        for pair_id in sorted(current):
            if current[pair_id] != reference[pair_id]:
                raise ReadoutRefusal(
                    f"template mismatch for pair_id {pair_id!r} between arms"
                    f" '{reference_arm}' and '{arm}' (fail-closed)"
                )
    return dict(sorted(Counter(reference.values()).items()))


def _check_registered_shape(template_counts: dict[str, int], expect: str) -> None:
    if expect == "any":
        return
    if template_counts != REGISTERED_N_PAIRS:
        raise ReadoutRefusal(
            f"registered R19 shape violated: expected {REGISTERED_N_PAIRS},"
            f" got {template_counts}; --expect any is for fixtures only"
        )


def _load_base(base_report: Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(base_report).read_text(encoding="utf-8"))
    except OSError as exc:
        raise ReadoutRefusal(f"missing frozen base report: {base_report}: {exc}") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ReadoutRefusal(
            f"unreadable frozen base report: {base_report}: {exc}"
        ) from exc
    base = payload.get("base")
    if not isinstance(base, dict) or not base:
        raise ReadoutRefusal(
            f"frozen base report missing 'base' table: {base_report}"
        )
    for template, cell in base.items():
        for key in ("pair_accuracy", "strict_pair_accuracy", "n_pairs"):
            if key not in cell:
                raise ReadoutRefusal(
                    f"frozen base cell '{template}' missing '{key}': {base_report}"
                )
    return base


def _load_f8(f8_report: Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(f8_report).read_text(encoding="utf-8"))
    except OSError as exc:
        raise ReadoutRefusal(f"missing F8 report: {f8_report}: {exc}") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ReadoutRefusal(f"unreadable F8 report: {f8_report}: {exc}") from exc
    schema = payload.get("schema_version")
    if schema != F8_SCHEMA_VERSION:
        raise ReadoutRefusal(
            f"F8 report schema mismatch: expected {F8_SCHEMA_VERSION!r},"
            f" got {schema!r} ({f8_report})"
        )
    if "primary_endpoint" not in payload:
        raise ReadoutRefusal(f"F8 report missing primary_endpoint: {f8_report}")
    return payload


def _arm_template_levels(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "n_pairs": int(metrics["n_pairs"]),
        "lenient_pair_accuracy": metrics["pair_accuracy"],
        "strict_pair_accuracy": metrics["strict_pair_accuracy"],
        "lenient_member_accuracy": metrics["member_accuracy"],
        "strict_member_accuracy": metrics["strict_member_accuracy"],
        "contract_valid_rate": metrics["contract_valid_rate"],
        "extraction_fallback_rate": metrics["extraction_fallback_rate"],
    }


def _vs_base(
    arm: str, arm_levels: dict[str, dict[str, Any]], base: dict[str, Any]
) -> dict[str, Any]:
    if set(base) != set(arm_levels):
        raise ReadoutRefusal(
            f"template set mismatch between arm '{arm}' and frozen base cells:"
            f" arm={sorted(arm_levels)} base={sorted(base)} (fail-closed)"
        )
    out: dict[str, Any] = {}
    for template in sorted(base):
        base_cell = base[template]
        level = arm_levels[template]
        if int(base_cell["n_pairs"]) != int(level["n_pairs"]):
            raise ReadoutRefusal(
                f"n_pairs mismatch vs frozen base for template '{template}'"
                f" (arm '{arm}'): base {int(base_cell['n_pairs'])}"
                f" arm {int(level['n_pairs'])} (fail-closed)"
            )
        out[template] = {
            "role": ROLES.get(template, UNREGISTERED_ROLE),
            "n_pairs": int(level["n_pairs"]),
            "base_lenient_pair_accuracy": base_cell["pair_accuracy"],
            "base_strict_pair_accuracy": base_cell["strict_pair_accuracy"],
            "arm_lenient_pair_accuracy": level["lenient_pair_accuracy"],
            "arm_strict_pair_accuracy": level["strict_pair_accuracy"],
            "arm_minus_base_lenient": (
                level["lenient_pair_accuracy"] - base_cell["pair_accuracy"]
            ),
            "arm_minus_base_strict": (
                level["strict_pair_accuracy"] - base_cell["strict_pair_accuracy"]
            ),
        }
    return out


def build_readout(
    arm_run_dirs: dict[str, Path],
    base_report: Path,
    f8_report: Path,
    *,
    seed: int = DEFAULT_SEED,
    bootstrap_draws: int = DEFAULT_BOOTSTRAP_DRAWS,
    expect: str = "registered",
) -> dict[str, Any]:
    missing = [arm for arm in ARM_ORDER if arm not in arm_run_dirs]
    if missing:
        raise ReadoutRefusal(f"missing arm run dirs: {missing} (fail-closed)")
    arms = {arm: _load_arm(arm, arm_run_dirs[arm]) for arm in ARM_ORDER}
    template_counts = _check_item_sets(arms)
    _check_registered_shape(template_counts, expect)
    base = _load_base(base_report)
    f8 = _load_f8(f8_report)
    base_sha256 = _sha256(base_report)
    f8_sha256 = _sha256(f8_report)

    arms_block: dict[str, Any] = {}
    arm_levels: dict[str, dict[str, Any]] = {}
    for arm in ARM_ORDER:
        per_template = aggregate_pair_metrics_by_template(arms[arm]["rows"])
        levels = {
            template: _arm_template_levels(metrics)
            for template, metrics in per_template.items()
        }
        arm_levels[arm] = levels
        pooled = aggregate_pair_metrics(arms[arm]["rows"])
        arms_block[arm] = {
            "arm_number": ARM_NUMBERS[arm],
            "label": ARM_LABELS[arm],
            "run_dir": str(arms[arm]["run_dir"]),
            "run_manifest_status": "complete",
            "model_path": arms[arm]["manifest"].get("model_path"),
            "n_pairs_total": int(pooled["n_pairs"]),
            "per_task_role": {
                template: {"role": ROLES.get(template, UNREGISTERED_ROLE), **levels[template]}
                for template in sorted(levels)
            },
            "pooled_all_roles_NOT_AN_ENDPOINT": {
                "lenient_pair_accuracy": pooled["pair_accuracy"],
                "strict_pair_accuracy": pooled["strict_pair_accuracy"],
            },
        }

    contrasts: dict[str, Any] = {}
    for spec in REGISTERED_CONTRASTS:
        left_arm = spec["left_arm"]
        right_arm = spec["right_arm"]
        comparison = compare_rows(
            arms[left_arm]["rows"],
            arms[right_arm]["rows"],
            ARM_LABELS[left_arm],
            ARM_LABELS[right_arm],
            seed=seed,
            bootstrap_draws=bootstrap_draws,
        )
        per_role: dict[str, Any] = {}
        for template in sorted(comparison["per_template"]):
            block = comparison["per_template"][template]
            per_role[template] = {
                "role": ROLES.get(template, UNREGISTERED_ROLE),
                "n_pairs": block["n_pairs"],
                "lenient_pair_correct": _contract_cell(block, "lenient"),
                "contract_strict_strict_pair_correct": _contract_cell(block, "strict"),
            }
        contrasts[spec["key"]] = {
            "question": spec["question"],
            "left_arm": left_arm,
            "left_label": ARM_LABELS[left_arm],
            "right_arm": right_arm,
            "right_label": ARM_LABELS[right_arm],
            "sign_convention": (
                f"delta = {ARM_LABELS[right_arm]} minus {ARM_LABELS[left_arm]}"
            ),
            "comparison_schema_version": comparison["schema_version"],
            "per_task_role": per_role,
            "pooled_all_roles_NOT_AN_ENDPOINT": {
                "lenient_pair_correct": _contract_cell(comparison, "lenient"),
                "contract_strict_strict_pair_correct": _contract_cell(comparison, "strict"),
            },
        }
    contrasts["contrast_3_absolute_levels_vs_frozen_base"] = {
        "question": (
            "absolute levels against the frozen base cells already cited in F8"
            " section 6"
        ),
        "base_source": str(base_report),
        "base_source_sha256": base_sha256,
        "interval": (
            "none -- frozen aggregate base cells; point differences only"
        ),
        "arm1_std_minus_base": _vs_base("std", arm_levels["std"], base),
        "arm3_necessity_minus_base": _vs_base(
            "necessity", arm_levels["necessity"], base
        ),
    }

    inputs_sha256: dict[str, str] = {}
    for arm in ARM_ORDER:
        inputs_sha256[str(arms[arm]["manifest_path"])] = _sha256(
            arms[arm]["manifest_path"]
        )
        for path in arms[arm]["shard_paths"]:
            inputs_sha256[str(path)] = _sha256(path)
    inputs_sha256[str(base_report)] = base_sha256
    inputs_sha256[str(f8_report)] = f8_sha256

    return {
        "schema_version": SCHEMA_VERSION,
        "title": (
            "Gate-1 four-arm endpoint readout: held-out FlipTrack, arms"
            " std/member/necessity/cp at global_step_120"
        ),
        "governing_documents": [
            "docs/registered_mini_a5_gate1_completion_v1.md",
            "docs/registered_mini_a5_endpoint_readout_v1.md",
            "docs/registered_mini_a5_main_v1.md",
            "docs/registered_gate1_four_arm_v1.md",
        ],
        "instrument": {
            "comparison_engine": (
                "scripts.compare_fliptrack_runs.compare_rows"
                " (F8 instrument, imported unchanged)"
            ),
            "scorer": "src.eval.fliptrack_metrics.pair_score",
            "bootstrap": {
                "unit": "paired item (pair_id)",
                "draws": bootstrap_draws,
                "seed": seed,
                "interval": 0.95,
                "seed_derivation": (
                    "per contrast: pooled lenient seed=seed, pooled strict"
                    " seed=seed+1, k-th template in sorted order"
                    " seed=seed+100+10k (lenient) / +1 (strict); both sides"
                    " resampled on the same pair indices per replicate"
                ),
            },
            "mcnemar": "scripts.compare_fliptrack_runs._paired_exact (exact two-sided)",
            "decision_rule": (
                "MOVED iff the 95% paired-bootstrap CI excludes zero in the"
                " positive direction; a positive point estimate whose interval"
                " contains zero is NOT MOVED; MOVED_NEGATIVE_DIRECTION iff the"
                " CI lies entirely below zero"
            ),
            "expectation_mode": expect,
            "variance_note": (
                "intervals quantify evaluation uncertainty on a fixed pair set,"
                " not run-to-run RL variance; each arm is one run"
            ),
        },
        "invariants": {
            "I7": (
                "both contracts (lenient pair_correct, contract-strict"
                " strict_pair_correct) reported for every cell; never merged or"
                " averaged; if they disagree, the disagreement is the result"
            ),
            "I13": (
                "task roles reported separately and never pooled as endpoints;"
                " pooled numbers appear only under keys labeled NOT_AN_ENDPOINT"
            ),
            "I15": "schema_version carried at top level",
        },
        "arms": arms_block,
        "registered_contrasts": contrasts,
        "carried_from_f8_not_re_decided": {
            "contrast": "arm4_cp_minus_arm2_member",
            "statement": (
                "the arm 4 - arm 2 contrast was read in F8 and is not"
                " re-decided; its numbers stand"
                " (docs/registered_mini_a5_gate1_completion_v1.md)"
            ),
            "source_report": str(f8_report),
            "source_report_sha256": f8_sha256,
            "f8_schema_version": f8["schema_version"],
            "f8_branch_fired": f8.get("branch_determination", {}).get("branch_fired"),
            "f8_primary_endpoint": f8["primary_endpoint"],
        },
        "inputs_sha256": inputs_sha256,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Four-arm Gate-1 endpoint readout (registered instrument)."
    )
    parser.add_argument("--arm-std", type=Path, required=True)
    parser.add_argument("--arm-member", type=Path, required=True)
    parser.add_argument("--arm-necessity", type=Path, required=True)
    parser.add_argument("--arm-cp", type=Path, required=True)
    parser.add_argument(
        "--base-report",
        type=Path,
        required=True,
        help="frozen base cells (reports/f2d_template_decomposition_v1.json)",
    )
    parser.add_argument(
        "--f8-report",
        type=Path,
        required=True,
        help="F8 endpoint readout (reports/f8_mini_a5_endpoint_readout_v1.json)",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap-draws", type=int, default=DEFAULT_BOOTSTRAP_DRAWS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--expect", choices=("registered", "any"), default="registered")
    args = parser.parse_args(argv)

    partial = Path(f"{args.output}.partial")
    if args.output.exists() or partial.exists():
        raise FileExistsError(
            f"refusing to overwrite endpoint readout: {args.output}"
        )
    result = build_readout(
        {
            "std": args.arm_std,
            "member": args.arm_member,
            "necessity": args.arm_necessity,
            "cp": args.arm_cp,
        },
        args.base_report,
        args.f8_report,
        seed=args.seed,
        bootstrap_draws=args.bootstrap_draws,
        expect=args.expect,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists() or partial.exists():
        raise FileExistsError(
            f"refusing to overwrite endpoint readout: {args.output}"
        )
    partial.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(partial, args.output)
    print(
        json.dumps(
            {"output": str(args.output), "schema_version": result["schema_version"]},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
