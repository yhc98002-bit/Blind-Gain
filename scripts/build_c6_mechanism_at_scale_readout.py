#!/usr/bin/env python3
"""C6 mechanism-at-scale readout instrument (registered).

Implements docs/registered_c6_mechanism_at_scale_v1.md: does the readout/anchor
dissociation established at 3B (F3 -> F8 -> Gate 1) still hold when the trained
model is 7B?

Six cells (3 models x 2 instruments), four contrasts, three task roles, two
contracts.  The comparison engine is REUSED verbatim
(scripts.compare_fliptrack_runs.compare_rows, seed 20260712, 2000 draws); the
Mini-A5 four-arm readout is deliberately NOT reused because its ARM_ORDER,
ARM_LABELS and ARM_CHECKPOINT_TOKENS are hard-coded to the 3B Mini-A5 arms.

Orientation is fixed by registration: every contrast is called with the 7B BASE
cell as `left` and the ARM cell as `right`, so every delta is arm-minus-base.

Invariants: both contracts reported and never merged (I7); the three task roles
never aggregated, pooled values only under a NOT_AN_ENDPOINT key (I13);
schema_version carried (I15); one-seed tag on every endpoint; no cross-scale
statistic; adversarial fixtures pass before real cells are touched (I10).

Acceptance checks 1-16 of registration section 9 are all hard refusals.
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
from src.eval.fliptrack_metrics import aggregate_pair_metrics_by_template

SCHEMA_VERSION = "blind-gains.c6-mechanism-at-scale-readout.v1"
REGISTERED_BOOTSTRAP_DRAWS = 2000
REGISTERED_SEED = 20260712
SEED_TAG = "one seed (data.seed 1; single 7B training pair)"

ANCHOR_ROLE = "coordinate_register_twenty_point_x_v02"
CANARY_ROLE = "header_cued_table_code_v02"
READOUT_ROLE = "starred_series_value_nine_v07"
ROLE_DESCRIPTIONS = {
    ANCHOR_ROLE: "primary visual anchor (search + binding + read)",
    CANARY_ROLE: "saturated positive control / retention canary -- a DROP signals damage",
    READOUT_ROLE: "oracle-localized readout control",
}

# Registration section 2 (models) and section 3 (instruments).
REGISTERED_REGISTRY: dict[str, Any] = {
    "models": {
        "base7b": "artifacts/models/Qwen/Qwen2.5-VL-7B-Instruct",
        "a1real": "checkpoints/c5/c5_a1_real_seed1_7b/global_step_100/actor/huggingface",
        "a2gray": "checkpoints/c5/c5_a2_gray_seed1_7b/global_step_100/actor/huggingface",
    },
    "instruments": {
        "r19": {
            "data_manifest": (
                "experiments/runs/caption_qa_pair_build_fliptrack_v02r19_qwen25vl3b_384_"
                "20260710T140200Z/shards/captions_shard_0.jsonl"
            ),
            "data_manifest_hash": (
                "e1dde98451e1c7473906637c029713ab4f95ab4f7c915bd035f697953bf2ffb2"
            ),
        },
        "r20": {
            "data_manifest": "data/fliptrack_r20_source_manifest.jsonl",
            "data_manifest_hash": (
                "20222e60201b4e116b4520f1aad8bd749bf49185a0a414087c1a8fe22dbf2ef3"
            ),
        },
    },
    "role_n_pairs": {
        ANCHOR_ROLE: 600,
        CANARY_ROLE: 300,
        READOUT_ROLE: 300,
    },
}

# Registration section 5, cell table.  label -> (instrument, model slot)
CELLS: tuple[tuple[str, str, str], ...] = (
    ("r19_base7b", "r19", "base7b"),
    ("r19_a1real", "r19", "a1real"),
    ("r19_a2gray", "r19", "a2gray"),
    ("r20_base7b", "r20", "base7b"),
    ("r20_a1real", "r20", "a1real"),
    ("r20_a2gray", "r20", "a2gray"),
)

# Registration section 7, the four registered contrasts.
CONTRASTS: tuple[dict[str, str], ...] = (
    {
        "key": "c6_1_a1real_minus_base_r19",
        "instrument": "r19",
        "left_cell": "r19_base7b",
        "right_cell": "r19_a1real",
        "arm": "A1-real",
        "arm_note": "recipe-matched arm (real images, outcome reward) -- the central reading",
    },
    {
        "key": "c6_2_a2gray_minus_base_r19",
        "instrument": "r19",
        "left_cell": "r19_base7b",
        "right_cell": "r19_a2gray",
        "arm": "A2-gray",
        "arm_note": "blind-trained arm (no visual information in training) -- read under its own label",
    },
    {
        "key": "c6_3_a1real_minus_base_r20",
        "instrument": "r20",
        "left_cell": "r20_base7b",
        "right_cell": "r20_a1real",
        "arm": "A1-real",
        "arm_note": "recipe-matched arm, private-twin replication",
    },
    {
        "key": "c6_4_a2gray_minus_base_r20",
        "instrument": "r20",
        "left_cell": "r20_base7b",
        "right_cell": "r20_a2gray",
        "arm": "A2-gray",
        "arm_note": "blind-trained arm, private-twin replication",
    },
)

# Registration section 5, locked evaluation contract, identical across all six cells.
LOCKED_CONTRACT = {
    "prompt_contract_id": "answer-tags-v1",
    "prompt_contract_sha256": (
        "7ac39f53a2a824490fc5ee22671a888d2d79d55e1d8351919006d7d71c7a8f3f"
    ),
    "decoding": {"n": 1, "temperature": 0.0, "top_p": 1.0},
    "max_new_tokens": 32,
    "image_mode": "real",
    "seed": 0,
}
REQUIRED_PARSER_VERSION = "canonical-v2"

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

# Registration section 10: cross-scale anchors are labelled descriptive strings only.
CROSS_SCALE_DESCRIPTIVE = {
    "note": (
        "Descriptive only. No cross-scale statistic is computed anywhere in C6 -- no "
        "cross-scale difference, ratio, interval or test."
    ),
    "gate1_3b_anchor": (
        "At 3B, all four Mini-A5 recipes left the primary visual anchor NOT MOVED in every "
        "contrast while moving the oracle-localized readout control +0.15 to +0.23 lenient "
        "(reports/mini_a5_gate1_endpoint_readout_v1.json)."
    ),
    "r4_scale_anchor": (
        "At 7B the blind-attainable share of the geo3k gain was 0.7785 [0.6418, 0.9214] "
        "canonical / 0.8402 [0.7457, 0.9456] strict, against a 3B pooled 0.487 [0.383, 0.588] "
        "(reports/c5_r4_readout_v1.json).  A different instrument and a different estimand "
        "from C6."
    ),
}


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


def _model_matches(manifest_value: str, registered_relative: str) -> bool:
    """The manifest records an absolute path; the registration a repo-relative one."""
    value = str(manifest_value).rstrip("/")
    registered = str(registered_relative).rstrip("/")
    return value == registered or value.endswith("/" + registered)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _resolve_pointer(pointer_dir: Path, label: str, root: Path) -> Path:
    pointer = pointer_dir / label
    if not pointer.is_file():
        raise ReadoutRefusal(f"check 1: missing cell pointer file for '{label}': {pointer}")
    target = pointer.read_text(encoding="utf-8").strip()
    if not target:
        raise ReadoutRefusal(f"check 1: empty cell pointer for '{label}'")
    run_dir = Path(target)
    if not run_dir.is_absolute():
        run_dir = root / run_dir
    if not run_dir.is_dir():
        raise ReadoutRefusal(
            f"check 1: cell pointer for '{label}' does not resolve to a directory: {run_dir}"
        )
    return run_dir


def _load_cell(
    label: str,
    instrument: str,
    model_slot: str,
    run_dir: Path,
    registry: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    manifest_path = run_dir / "run_manifest.json"
    if not manifest_path.is_file():
        raise ReadoutRefusal(f"check 4: {label}: missing run_manifest.json in {run_dir}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - exercised by fixture
        raise ReadoutRefusal(f"check 4: {label}: unreadable run_manifest.json: {exc}") from exc

    # ---- check 2: model identity -------------------------------------------
    registered_model = registry["models"][model_slot]
    revision = str(manifest.get("model_revision", ""))
    if not _model_matches(revision, registered_model):
        raise ReadoutRefusal(
            f"check 2: {label}: model_revision {revision!r} is not the registered "
            f"model for slot '{model_slot}' ({registered_model})"
        )

    # ---- check 3: manifest hash pins ---------------------------------------
    spec = registry["instruments"][instrument]
    if str(manifest.get("data_manifest", "")) != spec["data_manifest"]:
        raise ReadoutRefusal(
            f"check 3: {label}: data_manifest {manifest.get('data_manifest')!r} is not the "
            f"registered manifest for instrument '{instrument}' ({spec['data_manifest']})"
        )
    if str(manifest.get("data_manifest_hash", "")) != spec["data_manifest_hash"]:
        raise ReadoutRefusal(
            f"check 3: {label}: data_manifest_hash {manifest.get('data_manifest_hash')!r} "
            f"!= registered {spec['data_manifest_hash']}"
        )
    on_disk = root / spec["data_manifest"]
    if not on_disk.is_file():
        raise ReadoutRefusal(
            f"check 3: {label}: registered instrument manifest is not on disk: {on_disk}"
        )
    on_disk_hash = _sha256(on_disk)
    if on_disk_hash != spec["data_manifest_hash"]:
        raise ReadoutRefusal(
            f"check 3: {label}: on-disk instrument manifest re-hash {on_disk_hash} "
            f"!= registered {spec['data_manifest_hash']}"
        )

    # ---- check 4: complete run manifest ------------------------------------
    if str(manifest.get("status")) != "complete":
        raise ReadoutRefusal(
            f"check 4: {label}: run_manifest status is {manifest.get('status')!r}, not 'complete'"
        )
    if int(manifest.get("expected_shards", -1)) != 4:
        raise ReadoutRefusal(
            f"check 4: {label}: expected_shards is {manifest.get('expected_shards')!r}, not 4"
        )
    if manifest.get("performance_values_opened") is not False:
        raise ReadoutRefusal(
            f"check 4: {label}: performance_values_opened is "
            f"{manifest.get('performance_values_opened')!r}, not false"
        )
    shard_paths = sorted((run_dir / "shards").glob("shard_*.jsonl"))
    metric_paths = sorted((run_dir / "metrics").glob("shard_*.json"))
    if len(shard_paths) != 4:
        raise ReadoutRefusal(f"check 4: {label}: found {len(shard_paths)} shard files, expected 4")
    if len(metric_paths) != 4:
        raise ReadoutRefusal(
            f"check 4: {label}: found {len(metric_paths)} shard metric files, expected 4"
        )

    # ---- check 5: locked evaluation contract -------------------------------
    for key, expected in LOCKED_CONTRACT.items():
        actual = manifest.get(key)
        if key == "decoding":
            actual = {k: actual.get(k) for k in expected} if isinstance(actual, dict) else actual
        if actual != expected:
            raise ReadoutRefusal(
                f"check 5: {label}: locked contract field {key}={actual!r}, registered {expected!r}"
            )

    rows: list[dict[str, Any]] = []
    for shard_path in shard_paths:
        rows.extend(_read_jsonl(shard_path))
    if not rows:
        raise ReadoutRefusal(f"check 4: {label}: cell contains no prediction rows")

    # ---- checks 6 + 7: canonical contract fields, both contracts ------------
    for row in rows:
        if "contract_valid" not in row:
            raise ReadoutRefusal(
                f"check 6: {label}: a row lacks 'contract_valid' (pre-canonical schema; the "
                "2026-07-10/11 base cells are excluded by this check)"
            )
        if str(row.get("parser_version")) != REQUIRED_PARSER_VERSION:
            raise ReadoutRefusal(
                f"check 6: {label}: row parser_version={row.get('parser_version')!r}, "
                f"registered {REQUIRED_PARSER_VERSION!r}"
            )
        if str(row.get("prompt_contract_id")) != LOCKED_CONTRACT["prompt_contract_id"]:
            raise ReadoutRefusal(
                f"check 6: {label}: row prompt_contract_id={row.get('prompt_contract_id')!r}"
            )
        if "pair_correct" not in row or "strict_pair_correct" not in row:
            raise ReadoutRefusal(
                f"check 7: {label}: a row lacks pair_correct and/or strict_pair_correct"
            )

    pair_ids = [str(row["pair_id"]) for row in rows]
    duplicates = [pid for pid, n in Counter(pair_ids).items() if n > 1]
    if duplicates:
        raise ReadoutRefusal(
            f"check 8: {label}: duplicate pair_id in cell ({len(duplicates)}), "
            f"first={duplicates[0]}"
        )

    inputs = {"run_manifest.json": _sha256(manifest_path)}
    for shard_path in shard_paths:
        inputs[f"shards/{shard_path.name}"] = _sha256(shard_path)

    return {
        "label": label,
        "instrument": instrument,
        "model_slot": model_slot,
        "run_dir": str(run_dir.relative_to(root)) if run_dir.is_relative_to(root) else str(run_dir),
        "run_id": str(manifest.get("run_id", "")),
        "model_revision": revision,
        "registered_model": registered_model,
        "data_manifest": spec["data_manifest"],
        "data_manifest_hash": spec["data_manifest_hash"],
        "node": str(manifest.get("node", "")),
        "git_hash": str(manifest.get("git_hash", "")),
        "rows": rows,
        "pair_ids": set(pair_ids),
        "template_by_pair": {str(r["pair_id"]): str(r.get("template_id")) for r in rows},
        "inputs_sha256": inputs,
    }


def _check_item_sets(cells: dict[str, dict[str, Any]], registry: dict[str, Any]) -> None:
    for instrument in ("r19", "r20"):
        labels = [lab for lab, inst, _ in CELLS if inst == instrument]
        sets = {lab: cells[lab]["pair_ids"] for lab in labels}
        # check 8: pairwise and three-way identity
        common = set.intersection(*sets.values())
        union = set.union(*sets.values())
        if common != union:
            detail = {lab: len(sets[lab] - common) for lab in labels}
            raise ReadoutRefusal(
                f"check 8: {instrument}: item sets differ across the three models "
                f"(rows outside the three-way intersection: {detail})"
            )
        for a_idx, a in enumerate(labels):
            for b in labels[a_idx + 1 :]:
                if sets[a] != sets[b]:
                    raise ReadoutRefusal(f"check 8: {instrument}: item-set mismatch {a} vs {b}")
        # template_id per pair_id identical across the three models
        reference = cells[labels[0]]["template_by_pair"]
        for lab in labels[1:]:
            other = cells[lab]["template_by_pair"]
            mismatched = [pid for pid in reference if reference[pid] != other.get(pid)]
            if mismatched:
                raise ReadoutRefusal(
                    f"check 8: {instrument}: template_id differs between {labels[0]} and {lab} "
                    f"for {len(mismatched)} pair_id(s), first={mismatched[0]}"
                )
        # check 10: per-role n_pairs, always enforced against the registry in force
        counts = Counter(reference.values())
        expected = registry["role_n_pairs"]
        if dict(counts) != dict(expected):
            raise ReadoutRefusal(
                f"check 10: {instrument}: per-role composition {dict(counts)} != "
                f"registered {dict(expected)}"
            )

    # check 9: instrument separation
    r19_ids = cells["r19_base7b"]["pair_ids"]
    r20_ids = cells["r20_base7b"]["pair_ids"]
    overlap = r19_ids & r20_ids
    if overlap:
        raise ReadoutRefusal(
            f"check 9: R19 and R20 share {len(overlap)} pair_id(s); the two instruments are "
            "not separable and no estimand may combine them"
        )


def _contract_block(block: dict[str, Any], contract: str) -> dict[str, Any]:
    keys = _LENIENT_KEYS if contract == "lenient" else _STRICT_KEYS
    ci_low = block[keys[3]]
    ci_high = block[keys[4]]
    return {
        "contract": contract,
        "base_pair_accuracy": block[keys[0]],
        "arm_pair_accuracy": block[keys[1]],
        "arm_minus_base": block[keys[2]],
        "ci95_low": ci_low,
        "ci95_high": ci_high,
        "mcnemar": block[keys[5]],
        "decision": _decision_rule(ci_low, ci_high),
        "seed_tag": SEED_TAG,
    }


def _branch(anchor_decision: str, readout_decision: str) -> dict[str, str]:
    anchor_moved = anchor_decision == "MOVED"
    readout_moved = readout_decision == "MOVED"
    if readout_moved and not anchor_moved:
        return {
            "branch": "a",
            "statement": (
                "readout MOVED, anchor NOT MOVED -- the dissociation is scale-independent: "
                "outcome-reward RLVR at 7B moves the oracle-localized readout while leaving "
                "the primary visual anchor flat, as it does at 3B across four recipes"
            ),
        }
    if readout_moved and anchor_moved:
        return {
            "branch": "b",
            "statement": (
                "readout MOVED and anchor MOVED -- a scale-dependent mechanism: at 7B the "
                "same recipe reaches the primary anchor, which the 3B recipes did not"
            ),
        }
    if not readout_moved and not anchor_moved:
        return {
            "branch": "c",
            "statement": (
                "neither MOVED -- reported descriptively as 7B recipe transfer: the C5 recipe "
                "transferred to 7B on its own training distribution (R4) without moving either "
                "FlipTrack layer; no dissociation claim is made in either direction"
            ),
        }
    return {
        "branch": "d",
        "statement": (
            "anchor MOVED, readout NOT MOVED -- the remaining cell of the 2x2.  Not anticipated "
            "by any prior result and no interpretation was pre-committed; reported descriptively "
            "and explicitly flagged as an UNREGISTERED OUTCOME"
        ),
    }


def _audit_report(report: dict[str, Any]) -> None:
    """Checks 13 and 14, enforced on the emitted structure itself."""

    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                key_l = str(key).lower()
                if "shard" in key_l:
                    raise ReadoutRefusal(
                        f"check 13: emitted structure carries a shard-level key at {path}/{key}"
                    )
                if "pooled" in key_l and "NOT_AN_ENDPOINT" not in str(key):
                    raise ReadoutRefusal(
                        f"check 13: pooled-across-roles key without the NOT_AN_ENDPOINT label "
                        f"at {path}/{key}"
                    )
                walk(value, f"{path}/{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")

    # The estimand-bearing blocks. `inputs_sha256` is provenance (file paths, not
    # quantities) and `acceptance_checks` / `instrument` are the audit's own prose,
    # which names the very things it forbids.
    for key in ("cells", "contrasts", "replication_across_the_twin"):
        walk(report[key], f"/{key}")

    # check 14: every endpoint block carries the one-seed tag
    for contrast_key, contrast in report["contrasts"].items():
        for role, role_block in contrast["roles"].items():
            for contract in ("lenient", "strict"):
                if role_block[contract].get("seed_tag") != SEED_TAG:
                    raise ReadoutRefusal(
                        f"check 14: endpoint {contrast_key}/{role}/{contract} lacks the "
                        "registered one-seed tag"
                    )
    if report.get("seed_tag") != SEED_TAG:
        raise ReadoutRefusal("check 14: report lacks the top-level one-seed tag")
    if report.get("schema_version") != SCHEMA_VERSION:
        raise ReadoutRefusal("check 14: report lacks the registered schema_version")


def build_report(
    root: Path,
    pointer_dir: Path,
    registry: dict[str, Any],
    *,
    bootstrap_draws: int,
    seed: int,
    fixture_mode: bool,
) -> dict[str, Any]:
    # ---- check 11: bootstrap parameters as registered ----------------------
    if not fixture_mode:
        if bootstrap_draws != REGISTERED_BOOTSTRAP_DRAWS or seed != REGISTERED_SEED:
            raise ReadoutRefusal(
                f"check 11: bootstrap parameters (draws={bootstrap_draws}, seed={seed}) are not "
                f"the registered values (draws={REGISTERED_BOOTSTRAP_DRAWS}, "
                f"seed={REGISTERED_SEED})"
            )
        if registry != REGISTERED_REGISTRY:
            raise ReadoutRefusal(
                "check 11: a non-registered registry was supplied for a non-fixture run"
            )

    # ---- check 1: six cells bound, one directory each -----------------------
    resolved: dict[str, Path] = {}
    for label, _instrument, _slot in CELLS:
        resolved[label] = _resolve_pointer(pointer_dir, label, root)
    seen: dict[str, str] = {}
    for label, run_dir in resolved.items():
        key = str(run_dir)
        if key in seen:
            raise ReadoutRefusal(
                f"check 1: run directory {key} is bound to two slots ({seen[key]} and {label})"
            )
        seen[key] = label

    cells: dict[str, dict[str, Any]] = {}
    for label, instrument, slot in CELLS:
        cells[label] = _load_cell(label, instrument, slot, resolved[label], registry, root)

    _check_item_sets(cells, registry)

    # ---- descriptive cell levels (not endpoints) ---------------------------
    cell_report: dict[str, Any] = {}
    for label, instrument, slot in CELLS:
        cell = cells[label]
        by_template = aggregate_pair_metrics_by_template(cell["rows"])
        levels = {}
        for role in sorted(by_template):
            metrics = by_template[role]
            levels[role] = {
                "role": ROLE_DESCRIPTIONS.get(role, "unregistered template (fixture set)"),
                "n_pairs": metrics["n_pairs"],
                "lenient_pair_accuracy": metrics["pair_accuracy"],
                "strict_pair_accuracy": metrics["strict_pair_accuracy"],
                "seed_tag": SEED_TAG,
            }
        cell_report[label] = {
            "run_dir": cell["run_dir"],
            "run_id": cell["run_id"],
            "instrument": instrument,
            "model_slot": slot,
            "model_revision": cell["model_revision"],
            "registered_model": cell["registered_model"],
            "data_manifest": cell["data_manifest"],
            "data_manifest_hash": cell["data_manifest_hash"],
            "node": cell["node"],
            "git_hash": cell["git_hash"],
            "n_pairs": len(cell["pair_ids"]),
            "descriptive_levels_not_endpoints": levels,
        }

    # ---- the four registered contrasts -------------------------------------
    contrasts: dict[str, Any] = {}
    for spec in CONTRASTS:
        left = cells[spec["left_cell"]]
        right = cells[spec["right_cell"]]
        # check 12: orientation is base(left) minus arm(right) -> arm minus base
        if left["model_slot"] != "base7b":
            raise ReadoutRefusal(
                f"check 12: contrast {spec['key']} has left cell {left['label']} whose model "
                "slot is not the 7B base; every registered delta must be arm minus base"
            )
        if right["model_slot"] == "base7b":
            raise ReadoutRefusal(
                f"check 12: contrast {spec['key']} has a base cell on the right; every "
                "registered delta must be arm minus base"
            )
        comparison = compare_rows(
            left["rows"],
            right["rows"],
            left["label"],
            right["label"],
            seed=seed,
            bootstrap_draws=bootstrap_draws,
        )
        roles: dict[str, Any] = {}
        for role in sorted(comparison["per_template"]):
            block = comparison["per_template"][role]
            roles[role] = {
                "role": ROLE_DESCRIPTIONS.get(role, "unregistered template (fixture set)"),
                "n_pairs": block["n_pairs"],
                "lenient": _contract_block(block, "lenient"),
                "strict": _contract_block(block, "strict"),
            }
        entry: dict[str, Any] = {
            "instrument": spec["instrument"],
            "arm": spec["arm"],
            "arm_note": spec["arm_note"],
            "left_cell_base": spec["left_cell"],
            "right_cell_arm": spec["right_cell"],
            "orientation": "arm minus base (left = 7B base cell, right = arm cell)",
            "n_pairs": comparison["n_pairs"],
            "roles": roles,
            "POOLED_ACROSS_ROLES_NOT_AN_ENDPOINT": {
                "note": (
                    "I13: mixes the three task roles.  Emitted for auditability only; never "
                    "read as a C6 result."
                ),
                "lenient_arm_minus_base": comparison["pair_accuracy_delta"],
                "strict_arm_minus_base": comparison["strict_pair_accuracy_delta"],
                "seed_tag": SEED_TAG,
            },
        }
        # ---- the pre-committed reading, section 8 ---------------------------
        reading: dict[str, Any] = {}
        for contract in ("lenient", "strict"):
            anchor = roles.get(ANCHOR_ROLE)
            readout = roles.get(READOUT_ROLE)
            canary = roles.get(CANARY_ROLE)
            if anchor is None or readout is None:
                reading[contract] = {
                    "branch": "not evaluable",
                    "statement": "anchor and/or readout role absent from this instrument",
                }
                continue
            branch = _branch(anchor[contract]["decision"], readout[contract]["decision"])
            canary_decision = canary[contract]["decision"] if canary else "absent"
            canary_damage = canary_decision == "MOVED_NEGATIVE_DIRECTION"
            branch = dict(branch)
            branch["anchor_decision"] = anchor[contract]["decision"]
            branch["readout_decision"] = readout[contract]["decision"]
            branch["canary_decision"] = canary_decision
            branch["canary_damage"] = canary_damage
            if canary_damage:
                branch["statement"] = (
                    f"({branch['branch']}) with canary damage -- " + branch["statement"]
                )
            branch["seed_tag"] = SEED_TAG
            reading[contract] = branch
        if reading["lenient"]["branch"] != reading["strict"]["branch"]:
            reading["contract_disagreement"] = (
                "I7: lenient and contract-strict fire different branches.  Both are reported; "
                "the disagreement is the result and neither contract is the tie-breaker."
            )
        entry["pre_committed_reading"] = reading
        contrasts[spec["key"]] = entry

    # ---- replication reading across the twin -------------------------------
    replication: dict[str, Any] = {}
    for arm, r19_key, r20_key in (
        ("A1-real", "c6_1_a1real_minus_base_r19", "c6_3_a1real_minus_base_r20"),
        ("A2-gray", "c6_2_a2gray_minus_base_r19", "c6_4_a2gray_minus_base_r20"),
    ):
        per_contract = {}
        for contract in ("lenient", "strict"):
            b19 = contrasts[r19_key]["pre_committed_reading"][contract]["branch"]
            b20 = contrasts[r20_key]["pre_committed_reading"][contract]["branch"]
            per_contract[contract] = {
                "r19_branch": b19,
                "r20_branch": b20,
                "replicates": b19 == b20,
                "note": (
                    "R20 is a replication, not a vote.  A branch difference is reported as a "
                    "replication failure on the twin and is not resolved by pooling, averaging "
                    "or majority."
                ),
            }
        replication[arm] = per_contract

    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "seed_tag": SEED_TAG,
        "fixture_mode": fixture_mode,
        "registration": "docs/registered_c6_mechanism_at_scale_v1.md",
        "instrument": {
            "question": (
                "Does the readout/anchor dissociation established at 3B still hold when the "
                "trained model is 7B?"
            ),
            "engine": (
                "scripts.compare_fliptrack_runs.compare_rows (reused verbatim) + "
                "src.eval.fliptrack_metrics.aggregate_pair_metrics_by_template"
            ),
            "decision_rule": (
                "MOVED iff the 95% paired-bootstrap CI excludes zero in the positive direction; "
                "a positive point estimate whose interval contains zero is NOT MOVED, not a "
                "trend; MOVED_NEGATIVE_DIRECTION iff the CI lies entirely below zero"
            ),
            "orientation": "arm minus base, fixed by registration and asserted by check 12",
            "bootstrap": {
                "unit": "paired item (pair_id)",
                "draws": bootstrap_draws,
                "seed": seed,
                "interval": 0.95,
                "note": (
                    "Intervals quantify evaluation uncertainty on a fixed pair set.  They do "
                    "not estimate run-to-run RL variance; each arm is one run."
                ),
            },
            "role_seeds": {
                role: {"lenient": seed + 100 + 10 * k, "strict": seed + 100 + 10 * k + 1}
                for k, role in enumerate(sorted(ROLE_DESCRIPTIONS))
            },
            "contracts": "lenient and contract-strict, reported side by side, never merged (I7)",
            "roles_never_aggregated": ROLE_DESCRIPTIONS,
        },
        "registry": registry,
        "cells": cell_report,
        "contrasts": contrasts,
        "replication_across_the_twin": replication,
        "cross_scale_descriptive": CROSS_SCALE_DESCRIPTIVE,
        "acceptance_checks": {
            "1_six_cells_bound_one_directory_each": "pass",
            "2_model_identity": "pass",
            "3_manifest_hash_pins_and_on_disk_rehash": "pass",
            "4_complete_run_manifests": "pass",
            "5_locked_evaluation_contract_identical": "pass",
            "6_canonical_contract_fields_on_every_row": "pass",
            "7_both_contracts_present": "pass",
            "8_item_set_identity_across_models": "pass",
            "9_instrument_separation_r19_r20_disjoint": "pass",
            "10_per_role_n_pairs": "pass",
            "11_bootstrap_parameters_as_registered": "pass"
            if not fixture_mode
            else "n/a (fixture registry; registered values asserted only for real runs)",
            "12_orientation_arm_minus_base": "pass",
            "13_no_pooled_or_shard_level_endpoint": "pass",
            "14_one_seed_tagging_and_schema_version": "pass",
            "15_cross_scale_discipline": "pass (descriptive strings only; no cross-scale statistic)",
            "16_determinism_and_no_overwrite": "enforced at write time",
        },
        "inputs_sha256": {label: cells[label]["inputs_sha256"] for label, _i, _s in CELLS},
    }
    _audit_report(report)
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# C6 — does the readout/anchor dissociation hold at 7B?")
    lines.append("")
    lines.append(f"Registration: `{report['registration']}` — schema `{report['schema_version']}`.")
    lines.append(f"Seed scope: {report['seed_tag']}.")
    lines.append("")
    lines.append(
        "Decision rule: **MOVED** iff the 95% paired-bootstrap CI excludes zero in the positive "
        "direction. Both contracts are reported and never merged (I7); the three task roles are "
        "never aggregated (I13)."
    )
    lines.append("")
    for spec in CONTRASTS:
        entry = report["contrasts"][spec["key"]]
        lines.append(f"## {spec['key']} — {entry['arm']} minus 7B base on {entry['instrument'].upper()}")
        lines.append("")
        lines.append(f"_{entry['arm_note']}_")
        lines.append("")
        lines.append("| role | contract | base | arm | arm−base | 95% CI | decision |")
        lines.append("| --- | --- | ---: | ---: | ---: | --- | --- |")
        for role in (ANCHOR_ROLE, CANARY_ROLE, READOUT_ROLE):
            block = entry["roles"].get(role)
            if block is None:
                continue
            for contract in ("lenient", "strict"):
                cell = block[contract]
                lines.append(
                    f"| `{role}` ({block['n_pairs']}) | {contract} | "
                    f"{cell['base_pair_accuracy']:.4f} | {cell['arm_pair_accuracy']:.4f} | "
                    f"{cell['arm_minus_base']:+.4f} | "
                    f"[{cell['ci95_low']:+.4f}, {cell['ci95_high']:+.4f}] | "
                    f"**{cell['decision']}** |"
                )
        lines.append("")
        for contract in ("lenient", "strict"):
            reading = entry["pre_committed_reading"][contract]
            lines.append(f"- **{contract}** → branch **({reading['branch']})**: {reading['statement']}")
        if "contract_disagreement" in entry["pre_committed_reading"]:
            lines.append(f"- {entry['pre_committed_reading']['contract_disagreement']}")
        lines.append("")
    lines.append("## Replication across the private twin")
    lines.append("")
    lines.append("| arm | contract | R19 branch | R20 branch | replicates |")
    lines.append("| --- | --- | --- | --- | --- |")
    for arm, per_contract in report["replication_across_the_twin"].items():
        for contract in ("lenient", "strict"):
            row = per_contract[contract]
            lines.append(
                f"| {arm} | {contract} | ({row['r19_branch']}) | ({row['r20_branch']}) | "
                f"{'yes' if row['replicates'] else '**NO**'} |"
            )
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append(
        "One seed and one 7B training pair; two arms, not four; no cross-scale statistic is "
        "computed anywhere. C6 neither confirms nor overturns Gate 1 or R4."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--pointer-dir", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--bootstrap-draws", type=int, default=REGISTERED_BOOTSTRAP_DRAWS)
    parser.add_argument("--seed", type=int, default=REGISTERED_SEED)
    parser.add_argument(
        "--fixture-registry",
        type=Path,
        default=None,
        help="fixtures only: substitute the registered model/instrument pins",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    pointer_dir = args.pointer_dir if args.pointer_dir is not None else root / "logs" / "c6_cells"
    registry = REGISTERED_REGISTRY
    fixture_mode = False
    if args.fixture_registry is not None:
        registry = json.loads(args.fixture_registry.read_text(encoding="utf-8"))
        fixture_mode = True

    report = build_report(
        root,
        Path(pointer_dir),
        registry,
        bootstrap_draws=args.bootstrap_draws,
        seed=args.seed,
        fixture_mode=fixture_mode,
    )

    # ---- check 16: never overwrite ------------------------------------------
    args.output.parent.mkdir(parents=True, exist_ok=True)
    partial = Path(f"{args.output}.partial")
    if args.output.exists() or partial.exists():
        raise FileExistsError(f"refusing to overwrite C6 readout: {args.output}")
    partial.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(partial, args.output)

    if args.markdown_output is not None:
        md_partial = Path(f"{args.markdown_output}.partial")
        if args.markdown_output.exists() or md_partial.exists():
            raise FileExistsError(f"refusing to overwrite C6 readout: {args.markdown_output}")
        md_partial.write_text(render_markdown(report), encoding="utf-8")
        os.replace(md_partial, args.markdown_output)

    print(f"wrote {args.output}")
    if args.markdown_output is not None:
        print(f"wrote {args.markdown_output}")


if __name__ == "__main__":
    main()
