from __future__ import annotations

import hashlib
import json
from typing import Any

from scipy.stats import beta


SCHEMA_VERSION = "blind-gains.support-sharpening.v1"
INITIAL_SAMPLE_COUNT = 16
EXTRA_SAMPLE_COUNT = 64
TOTAL_SAMPLE_COUNT = INITIAL_SAMPLE_COUNT + EXTRA_SAMPLE_COUNT


def _identity(row: dict[str, Any]) -> tuple[str, int]:
    split = row.get("split")
    row_index = row.get("row_index")
    if not isinstance(split, str) or not split:
        raise ValueError("support-sharpening row requires a nonempty split")
    if not isinstance(row_index, int) or isinstance(row_index, bool) or row_index < 0:
        raise ValueError("support-sharpening row requires a nonnegative integer row_index")
    return split, row_index


def _index_unique(rows: list[dict[str, Any]], label: str) -> dict[tuple[str, int], dict[str, Any]]:
    result: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows:
        identity = _identity(row)
        if identity in result:
            raise ValueError(f"duplicate {label} identity: {identity}")
        result[identity] = row
    return result


def _item_fingerprint(row: dict[str, Any]) -> str:
    payload = {
        "split": row["split"],
        "row_index": row["row_index"],
        "problem": row.get("problem"),
        "ground_truth": row.get("ground_truth"),
        "image_sha256": row.get("image_sha256"),
        "source_manifest_sha256": row.get("source_manifest_sha256"),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def build_resampling_candidates(
    baseline_rows: list[dict[str, Any]],
    readout_rows: list[dict[str, Any]],
    *,
    arm: str,
    condition: str,
    target_step: int,
) -> list[dict[str, Any]]:
    """Select fixed-protocol 0/16 items that change from greedy wrong to correct."""
    if not arm or not condition:
        raise ValueError("arm and condition are required")
    if not isinstance(target_step, int) or isinstance(target_step, bool) or target_step <= 0:
        raise ValueError("target_step must be a positive integer")
    baseline = _index_unique(baseline_rows, "baseline")
    readout = _index_unique(readout_rows, "readout")
    if baseline.keys() != readout.keys():
        raise ValueError("baseline and readout item identities differ")
    selected: list[dict[str, Any]] = []
    for identity in sorted(baseline):
        base = baseline[identity]
        result = readout[identity]
        if base.get("condition") != condition:
            raise ValueError(f"baseline condition mismatch for {identity}")
        if result.get("arm") != arm or result.get("condition") != condition:
            raise ValueError(f"readout arm/condition mismatch for {identity}")
        if base.get("sample_count") != INITIAL_SAMPLE_COUNT:
            raise ValueError(f"baseline is not a 16-sample audit for {identity}")
        correct_count = base.get("sample_correct_count")
        if not isinstance(correct_count, int) or isinstance(correct_count, bool):
            raise ValueError(f"invalid baseline correct count for {identity}")
        step0 = result.get("step0_acc_final")
        observed_target_step = result.get("target_step")
        target = result.get("target_acc_final")
        if observed_target_step != target_step:
            raise ValueError(f"readout target step mismatch for {identity}")
        if not isinstance(step0, bool) or not isinstance(target, bool):
            raise ValueError(f"readout correctness fields must be booleans for {identity}")
        if correct_count != 0 or step0 or not target:
            continue
        selected.append(
            {
                "schema_version": SCHEMA_VERSION,
                "arm": arm,
                "condition": condition,
                "split": identity[0],
                "row_index": identity[1],
                "target_step": target_step,
                "source_item_fingerprint": _item_fingerprint(base),
                "problem": base.get("problem"),
                "ground_truth": base.get("ground_truth"),
                "image_sha256": base.get("image_sha256"),
                "source_manifest_sha256": base.get("source_manifest_sha256"),
                "initial_sample_count": INITIAL_SAMPLE_COUNT,
                "initial_correct_count": 0,
                "extra_sample_count": EXTRA_SAMPLE_COUNT,
                "planned_total_sample_count": TOTAL_SAMPLE_COUNT,
                "baseline_decoding": base.get("decoding", {}).get("sampled"),
                "max_tokens": base.get("decoding", {}).get("max_tokens"),
                "prompt_contract_sha256": base.get("prompt_contract_sha256"),
                "parser_version": base.get("parser_version"),
                "pilot_reward_version": base.get("pilot_reward_version"),
                "selection_rule": (
                    "base_0_of_16_and_step0_greedy_wrong_and_"
                    f"step{target_step}_greedy_correct"
                ),
            }
        )
    return selected


def summarize_resampling(
    candidate: dict[str, Any],
    extra_sample_correct: list[bool],
) -> dict[str, Any]:
    if candidate.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported support-sharpening candidate schema")
    if candidate.get("initial_sample_count") != INITIAL_SAMPLE_COUNT:
        raise ValueError("candidate does not originate from the fixed 16-sample audit")
    if candidate.get("initial_correct_count") != 0:
        raise ValueError("candidate is not at the registered 0/16 floor")
    if len(extra_sample_correct) != EXTRA_SAMPLE_COUNT or any(
        not isinstance(value, bool) for value in extra_sample_correct
    ):
        raise ValueError("support sharpening requires exactly 64 boolean outcomes")
    extra_correct_count = sum(extra_sample_correct)
    total_correct_count = extra_correct_count
    posterior_alpha = total_correct_count + 0.5
    posterior_beta = TOTAL_SAMPLE_COUNT - total_correct_count + 0.5
    low, high = beta.ppf((0.025, 0.975), posterior_alpha, posterior_beta)
    absent = extra_correct_count == 0
    return {
        "schema_version": SCHEMA_VERSION,
        "arm": candidate["arm"],
        "condition": candidate["condition"],
        "split": candidate["split"],
        "row_index": candidate["row_index"],
        "target_step": candidate["target_step"],
        "source_item_fingerprint": candidate["source_item_fingerprint"],
        "initial_sample_count": INITIAL_SAMPLE_COUNT,
        "initial_correct_count": 0,
        "extra_sample_count": EXTRA_SAMPLE_COUNT,
        "extra_correct_count": extra_correct_count,
        "total_sample_count": TOTAL_SAMPLE_COUNT,
        "total_correct_count": total_correct_count,
        "jeffreys_posterior_alpha": posterior_alpha,
        "jeffreys_posterior_beta": posterior_beta,
        "jeffreys_ci95_low": float(low),
        "jeffreys_ci95_high": float(high),
        "classification": (
            "high-confidence support-expansion candidate"
            if absent
            else "observed in support-sharpening samples"
        ),
        "registered_language": (
            "not observed in the base K-sample set"
            if absent
            else "mass sharpening within observed support"
        ),
        "causal_capability_claim_permitted": False,
    }
