#!/usr/bin/env python3
"""Registered R3 readout for M7: eight held-out evaluations -> R3 result.

Registered specification (no free parameters):
- docs/registered_m7_amendment_v1.md      estimands, stability rule, bootstrap
- docs/registered_m7_seed_scope_v1.md     seed 1 only; every number tagged "one seed"
- docs/registered_m7_single_image_v2.md   single-image restriction statement
- docs/registered_extensions_v1.md        Extension 3: pooled-only readout prohibited

Data contracts:
- Strata are the joint (metadata.source, metadata.category) labels read directly
  off each row of data/virl39k_m7_heldout_v3.jsonl. Eligibility (>= 30 held-out
  items) is RECOUNTED from that file; the recount must give exactly 22 eligible
  strata. data/virl39k_m7_split_manifest_v2.json's n_strata_rank_eligible=21 is
  NOT used: it counts component labels, not items.
- Step-0 and step-100 sides are per_item.jsonl files from the blind-solvability
  harness (schema blind-gains.blind-solvability-pilot.v1): q_i, p_i_jeffreys,
  sample_correct_count, greedy_canonical_correct, condition, qid, row_index.
- Pairing is by (qid, row_index) across step 0 and step 100 within each arm;
  item sets must be identical or the readout fails loudly.

This script reports numbers and provenance only; it makes no interpretation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.pilot_fourarm import (  # noqa: E402
    deterministic_seed,
    mean_with_paired_bootstrap,
    paired_ratio,
    percentile_interval,
    tied_spearman,
)
from src.analysis.support_sharpening import (  # noqa: E402
    INITIAL_SAMPLE_COUNT,
    build_resampling_candidates,
)

SCHEMA_VERSION = "blind-gains.m7-r3-readout.v1"
ARMS = ("a1_real", "a2_gray", "a2b_noimage", "a3_caption")
BLIND_ARMS = ("a2_gray", "a2b_noimage", "a3_caption")
CONDITIONS = {
    "a1_real": "real",
    "a2_gray": "gray",
    "a2b_noimage": "none",
    "a3_caption": "caption",
}
DISPLAY_NAMES = {
    "a1_real": "A1 real",
    "a2_gray": "A2 gray",
    "a2b_noimage": "A2b no-image",
    "a3_caption": "A3 caption",
}
REGISTERED_HELDOUT_PATH = "data/virl39k_m7_heldout_v3.jsonl"
REGISTERED_HELDOUT_SHA256 = (
    "50f3b85c11c4046ef2512c544faec04286648688bb6d47548995f18cab40716c"
)
REGISTERED_HELDOUT_ROWS = 4239
REGISTERED_ELIGIBLE_STRATA = 22
REGISTERED_SMALL_N_STRATA = 38
ELIGIBILITY_THRESHOLD = 30
REGISTERED_BOOTSTRAP_DRAWS = 5000
REGISTERED_BOOTSTRAP_SEED = 20260716
UNSTABLE_UNDEFINED_FRACTION = 0.05
TARGET_STEP = 100
GEO3K_ANCHORS = {"a2_gray": 0.0789, "a2b_noimage": 0.1184}
SEED_SCOPE_TAG = "one seed (seed 1)"
SEED_SCOPE_STATEMENT = (
    "Seed scope: seed 1 only for all four arms; every gain, recovery, and "
    "correlation below is a per-seed (one seed) number and no between-seed "
    "variance claim is made (docs/registered_m7_seed_scope_v1.md)."
)
SINGLE_IMAGE_STATEMENT = (
    "Single-image restriction: M7 is restricted to single-image rows "
    "(worker.rollout.limit_images=1); retained 23,542/25,255 train rows "
    "(93.2%) and 4,239/4,501 held-out rows (94.2%) "
    "(docs/registered_m7_single_image_v2.md)."
)
POOLING_STATEMENT = (
    "Pooled-only readout is prohibited; corpus aggregate, every joint stratum, "
    "and source-only/category-only descriptive tables are all published; "
    "A2/A2b/A3 are never pooled into one generic blind arm "
    "(docs/registered_extensions_v1.md Extension 3, "
    "docs/registered_m7_amendment_v1.md)."
)
REGISTERED_DOCUMENTS = (
    "docs/registered_m7_amendment_v1.md",
    "docs/registered_m7_seed_scope_v1.md",
    "docs/registered_m7_single_image_v2.md",
    "docs/registered_extensions_v1.md",
)
REFUSED_IN_PARTIAL = (
    "gain",
    "recovery",
    "rho_gain",
    "rho_recovery",
    "aggregate_recovery",
    "geometry3k_anchor_comparison",
    "m10_support_sharpening",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid JSONL at {path}:{line_number}") from error
        if not isinstance(row, dict):
            raise ValueError(f"non-object JSONL row at {path}:{line_number}")
        rows.append(row)
    return rows


def _write_text(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def _resolve(root: Path, value: str) -> Path:
    candidate = Path(value)
    result = (candidate if candidate.is_absolute() else root / candidate).resolve()
    try:
        result.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"input path escapes the analysis root: {value}") from error
    return result


def _git_head(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _stratum_label(stratum: tuple[str, str]) -> str:
    return f"{stratum[0]}||{stratum[1]}"


# --------------------------------------------------------------------------
# Loading and hard gates
# --------------------------------------------------------------------------

def load_heldout(
    path: Path,
    *,
    expected_sha256: str,
    expected_rows: int,
    expected_eligible: int,
    expected_small_n: int,
) -> dict[str, Any]:
    observed_sha = _sha256(path)
    if observed_sha != expected_sha256:
        raise ValueError(
            f"held-out manifest sha256 mismatch for {path}: "
            f"expected {expected_sha256}, found {observed_sha}"
        )
    if observed_sha == REGISTERED_HELDOUT_SHA256 and (
        expected_rows != REGISTERED_HELDOUT_ROWS
        or expected_eligible != REGISTERED_ELIGIBLE_STRATA
        or expected_small_n != REGISTERED_SMALL_N_STRATA
    ):
        # The registered manifest carries non-negotiable expectations; CLI
        # overrides exist only for synthetic fixtures with a different sha256.
        raise ValueError(
            "the registered held-out manifest requires the registered "
            f"expectations ({REGISTERED_HELDOUT_ROWS} rows, "
            f"{REGISTERED_ELIGIBLE_STRATA} eligible strata, "
            f"{REGISTERED_SMALL_N_STRATA} descriptive-small-n strata); "
            "CLI overrides are refused on the registered file"
        )
    rows = _read_jsonl(path)
    if len(rows) != expected_rows:
        raise ValueError(
            f"held-out manifest row count mismatch: expected {expected_rows}, "
            f"found {len(rows)}"
        )
    stratum_of: dict[tuple[str, int], tuple[str, str]] = {}
    row_indices: set[int] = set()
    qids: set[str] = set()
    for line_number, row in enumerate(rows, 1):
        qid = row.get("qid")
        row_index = row.get("row_index")
        metadata = row.get("metadata")
        if not isinstance(qid, str) or not qid:
            raise ValueError(f"held-out row {line_number}: invalid qid")
        if not isinstance(row_index, int) or isinstance(row_index, bool):
            raise ValueError(f"held-out row {line_number}: invalid row_index")
        if not isinstance(metadata, dict):
            raise ValueError(f"held-out row {line_number}: missing metadata")
        source = metadata.get("source")
        category = metadata.get("category")
        if not isinstance(source, str) or not source:
            raise ValueError(f"held-out row {line_number}: invalid metadata.source")
        if not isinstance(category, str) or not category:
            raise ValueError(f"held-out row {line_number}: invalid metadata.category")
        key = (qid, row_index)
        if key in stratum_of:
            raise ValueError(f"duplicate held-out item identity: {key}")
        if row_index in row_indices:
            raise ValueError(f"duplicate held-out row_index: {row_index}")
        if qid in qids:
            raise ValueError(f"duplicate held-out qid: {qid}")
        stratum_of[key] = (source, category)
        row_indices.add(row_index)
        qids.add(qid)

    items_by_stratum: dict[tuple[str, str], list[tuple[str, int]]] = {}
    for key in sorted(stratum_of):
        items_by_stratum.setdefault(stratum_of[key], []).append(key)
    eligible = sorted(
        stratum for stratum, items in items_by_stratum.items()
        if len(items) >= ELIGIBILITY_THRESHOLD
    )
    small_n = sorted(
        stratum for stratum, items in items_by_stratum.items()
        if len(items) < ELIGIBILITY_THRESHOLD
    )
    # Hard assertion: eligibility is recounted from the held-out jsonl itself.
    # data/virl39k_m7_split_manifest_v2.json's n_strata_rank_eligible=21 is a
    # component-label count, not an item count, and must never be substituted.
    if len(eligible) != expected_eligible or len(small_n) != expected_small_n:
        raise ValueError(
            "stratum eligibility recount mismatch: counted "
            f"{len(eligible)} eligible (>= {ELIGIBILITY_THRESHOLD} items) and "
            f"{len(small_n)} descriptive-small-n strata; expected "
            f"{expected_eligible} eligible and {expected_small_n} small-n. "
            "The recount is taken directly from the held-out jsonl; do not "
            "substitute the split manifest's n_strata_rank_eligible, which "
            "counts component labels, not items."
        )
    return {
        "path": path,
        "sha256": observed_sha,
        "row_count": len(rows),
        "stratum_of": stratum_of,
        "items_by_stratum": items_by_stratum,
        "eligible": eligible,
        "small_n": small_n,
    }


def load_run(
    root: Path,
    run_value: str,
    *,
    arm: str,
    step_label: str,
    require_step0_fields: bool,
) -> dict[str, Any]:
    run_dir = _resolve(root, run_value)
    per_item_path = run_dir / "per_item.jsonl"
    manifest_path = run_dir / "run_manifest.json"
    if not per_item_path.is_file():
        raise ValueError(f"{arm} {step_label}: per_item.jsonl is absent in {run_dir}")
    if not manifest_path.is_file():
        raise ValueError(f"{arm} {step_label}: run_manifest.json is absent in {run_dir}")
    manifest = _read_json(manifest_path)
    expected_condition = CONDITIONS[arm]
    rows = _read_jsonl(per_item_path)
    indexed: dict[tuple[str, int], dict[str, Any]] = {}
    for line_number, row in enumerate(rows, 1):
        qid = row.get("qid")
        row_index = row.get("row_index")
        if not isinstance(qid, str) or not qid:
            raise ValueError(f"{arm} {step_label} row {line_number}: invalid qid")
        if not isinstance(row_index, int) or isinstance(row_index, bool):
            raise ValueError(f"{arm} {step_label} row {line_number}: invalid row_index")
        key = (qid, row_index)
        if key in indexed:
            raise ValueError(f"{arm} {step_label}: duplicate item identity {key}")
        if row.get("condition") != expected_condition:
            raise ValueError(
                f"{arm} {step_label} item {key}: condition mismatch: expected "
                f"{expected_condition!r}, found {row.get('condition')!r}"
            )
        greedy = row.get("greedy_canonical_correct")
        if not isinstance(greedy, bool):
            raise ValueError(
                f"{arm} {step_label} item {key}: greedy_canonical_correct must be a boolean"
            )
        if require_step0_fields:
            if row.get("sample_count") != INITIAL_SAMPLE_COUNT:
                raise ValueError(
                    f"{arm} {step_label} item {key}: sample_count must be "
                    f"{INITIAL_SAMPLE_COUNT}, found {row.get('sample_count')!r}"
                )
            correct_count = row.get("sample_correct_count")
            if (
                not isinstance(correct_count, int)
                or isinstance(correct_count, bool)
                or not 0 <= correct_count <= INITIAL_SAMPLE_COUNT
            ):
                raise ValueError(
                    f"{arm} {step_label} item {key}: invalid sample_correct_count"
                )
            for field in ("q_i", "p_i_jeffreys"):
                value = row.get(field)
                if (
                    not isinstance(value, (int, float))
                    or isinstance(value, bool)
                    or not math.isfinite(float(value))
                    or not 0.0 <= float(value) <= 1.0
                ):
                    raise ValueError(
                        f"{arm} {step_label} item {key}: invalid {field}: {value!r}"
                    )
        indexed[key] = row
    return {
        "arm": arm,
        "step_label": step_label,
        "run_dir": run_dir,
        "run_id": str(manifest.get("run_id") or run_dir.name),
        "manifest": manifest,
        "manifest_sha256": _sha256(manifest_path),
        "per_item_sha256": _sha256(per_item_path),
        "rows": indexed,
    }


def readiness_gate(
    runs: dict[str, dict[str, dict[str, Any]]],
    heldout_keys: set[tuple[str, int]],
) -> None:
    """Fail loudly when any run manifest is not complete or step-0 coverage
    does not exactly match the frozen held-out item set."""
    failures: list[str] = []
    for arm in ARMS:
        for step_label, run in sorted(runs.get(arm, {}).items()):
            status = run["manifest"].get("status")
            if status != "complete":
                failures.append(
                    f"{arm} {step_label}: run_manifest status is {status!r}, "
                    f"not 'complete' ({run['run_id']})"
                )
        step0 = runs.get(arm, {}).get("step0")
        if step0 is not None:
            observed = set(step0["rows"])
            missing = sorted(heldout_keys - observed)
            extra = sorted(observed - heldout_keys)
            if missing or extra:
                failures.append(
                    f"{arm} step0: held-out coverage mismatch: "
                    f"{len(observed)}/{len(heldout_keys)} items present, "
                    f"{len(missing)} missing (examples {missing[:3]}), "
                    f"{len(extra)} not in the frozen held-out set "
                    f"(examples {extra[:3]})"
                )
    if failures:
        raise ValueError(
            "readiness gate failed; refusing to compute any estimand:\n- "
            + "\n- ".join(failures)
        )


def pairing_gate(runs: dict[str, dict[str, dict[str, Any]]]) -> None:
    failures: list[str] = []
    for arm in ARMS:
        step0 = runs[arm]["step0"]["rows"]
        step100 = runs[arm]["step100"]["rows"]
        missing = sorted(set(step0) - set(step100))
        extra = sorted(set(step100) - set(step0))
        if missing or extra:
            failures.append(
                f"{arm}: step-0/step-100 pairing mismatch: {len(missing)} items "
                f"present at step 0 but missing at step {TARGET_STEP} "
                f"(examples {missing[:3]}); {len(extra)} items present at step "
                f"{TARGET_STEP} but not at step 0 (examples {extra[:3]})"
            )
    if failures:
        raise ValueError(
            "step-0/step-100 pairing gate failed; items are never silently "
            "dropped:\n- " + "\n- ".join(failures)
        )


# --------------------------------------------------------------------------
# Bootstrap machinery (registered mechanism: seed 20260716, deterministic
# statistic/arm labels hashed into independent streams via deterministic_seed)
# --------------------------------------------------------------------------

def _metric_seed(base_seed: int, label: str) -> int:
    return deterministic_seed(base_seed, label)


def _rank_statistic_bootstrap(
    stratum_arrays: list[dict[str, Any]],
    *,
    kind: str,
    draws: int,
    seed: int,
    chunk: int = 500,
) -> dict[str, Any]:
    """Within-stratum item bootstrap for one rank statistic.

    In every draw, items are resampled with replacement within every eligible
    stratum (one shared resample per draw across all quantities), and stratum
    q_bar, gains, A1 denominator stability, recoveries, and the tie-corrected
    Spearman statistic are recomputed. Undefined draws are counted, never
    replaced with zero.
    """
    if kind not in {"rho_gain", "rho_recovery"}:
        raise ValueError(f"unknown rank statistic kind: {kind}")
    rng = np.random.default_rng(seed)
    count = len(stratum_arrays)
    values: list[float] = []
    undefined = 0
    for start in range(0, draws, chunk):
        stop = min(draws, start + chunk)
        size = stop - start
        q_bar = np.empty((size, count), dtype=np.float64)
        gain = np.empty((size, count), dtype=np.float64)
        gain_a1 = np.empty((size, count), dtype=np.float64)
        se_a1 = np.empty((size, count), dtype=np.float64)
        for column, arrays in enumerate(stratum_arrays):
            n = int(arrays["q"].size)
            indices = rng.integers(0, n, size=(size, n))
            q_bar[:, column] = arrays["q"][indices].mean(axis=1)
            gain[:, column] = arrays["gain"][indices].mean(axis=1)
            resampled_a1 = arrays["gain_a1"][indices]
            gain_a1[:, column] = resampled_a1.mean(axis=1)
            if n > 1:
                se_a1[:, column] = resampled_a1.std(axis=1, ddof=1) / math.sqrt(n)
            else:
                se_a1[:, column] = 0.0
        for draw in range(size):
            if kind == "rho_gain":
                value = tied_spearman(q_bar[draw], gain[draw])
            else:
                stable = (gain_a1[draw] > 0) & (gain_a1[draw] >= 2 * se_a1[draw])
                if int(stable.sum()) < 2:
                    value = None
                else:
                    value = tied_spearman(
                        q_bar[draw][stable],
                        gain[draw][stable] / gain_a1[draw][stable],
                    )
            if value is None:
                undefined += 1
            else:
                values.append(float(value))
    undefined_fraction = undefined / draws if draws else 0.0
    return {
        "draws": draws,
        "undefined_draw_count": undefined,
        "undefined_fraction": undefined_fraction,
        "defined_draw_count": len(values),
        "ci95": percentile_interval(values) if values else None,
        "interval_label": (
            "unstable"
            if undefined_fraction > UNSTABLE_UNDEFINED_FRACTION
            else "stable"
        ),
        "undefined_draw_policy": "undefined draws are counted, not replaced with zero",
    }


def _aggregate_recovery_bootstrap(
    gain_blind: np.ndarray,
    gain_a1: np.ndarray,
    *,
    draws: int,
    seed: int,
    chunk: int = 250,
) -> tuple[dict[str, Any], list[float]]:
    """Item-paired bootstrap of aggregate recovery across the full held-out
    corpus, conditional on the registered stable-A1-denominator rule in every
    draw."""
    rng = np.random.default_rng(seed)
    n = int(gain_blind.size)
    ratios: list[float] = []
    undefined = 0
    for start in range(0, draws, chunk):
        stop = min(draws, start + chunk)
        size = stop - start
        indices = rng.integers(0, n, size=(size, n))
        blind = gain_blind[indices]
        a1 = gain_a1[indices]
        a1_mean = a1.mean(axis=1)
        a1_se = a1.std(axis=1, ddof=1) / math.sqrt(n)
        stable = (a1_mean > 0) & (a1_mean >= 2 * a1_se)
        undefined += int((~stable).sum())
        ratios.extend((blind.mean(axis=1)[stable] / a1_mean[stable]).tolist())
    undefined_fraction = undefined / draws if draws else 0.0
    summary = {
        "draws": draws,
        "undefined_draw_count": undefined,
        "undefined_fraction": undefined_fraction,
        "defined_draw_count": len(ratios),
        "ci95": percentile_interval(ratios) if ratios else None,
        "interval_label": (
            "unstable"
            if undefined_fraction > UNSTABLE_UNDEFINED_FRACTION
            else "stable"
        ),
        "undefined_draw_policy": "undefined draws are counted, not replaced with zero",
    }
    return summary, ratios


# --------------------------------------------------------------------------
# Estimand computation
# --------------------------------------------------------------------------

def _rate(values: list[bool]) -> float:
    return float(sum(values) / len(values))


def _join_items(
    heldout: dict[str, Any],
    runs: dict[str, dict[str, dict[str, Any]]],
    *,
    partial: bool,
) -> dict[str, Any]:
    """Per-arm, per-stratum aligned arrays in deterministic (qid, row_index)
    order."""
    joined: dict[str, Any] = {"corpus": {}, "strata": {}}
    ordered_keys = sorted(heldout["stratum_of"])
    stratum_keys = sorted(heldout["items_by_stratum"])
    for arm in ARMS:
        step0 = runs[arm]["step0"]["rows"]
        step100 = runs[arm]["step100"]["rows"] if not partial else None
        q_values = np.array(
            [float(step0[key]["q_i"]) for key in ordered_keys], dtype=np.float64
        )
        acc0 = [bool(step0[key]["greedy_canonical_correct"]) for key in ordered_keys]
        corpus: dict[str, Any] = {"keys": ordered_keys, "q": q_values, "acc0": acc0}
        if step100 is not None:
            acc100 = [
                bool(step100[key]["greedy_canonical_correct"]) for key in ordered_keys
            ]
            corpus["acc100"] = acc100
            corpus["gain"] = np.array(
                [float(after) - float(before) for before, after in zip(acc0, acc100)],
                dtype=np.float64,
            )
        joined["corpus"][arm] = corpus
    for stratum in stratum_keys:
        keys = heldout["items_by_stratum"][stratum]
        per_arm: dict[str, Any] = {}
        for arm in ARMS:
            step0 = runs[arm]["step0"]["rows"]
            q_values = np.array(
                [float(step0[key]["q_i"]) for key in keys], dtype=np.float64
            )
            acc0 = [bool(step0[key]["greedy_canonical_correct"]) for key in keys]
            entry: dict[str, Any] = {"q": q_values, "acc0": acc0}
            if not partial:
                step100 = runs[arm]["step100"]["rows"]
                acc100 = [
                    bool(step100[key]["greedy_canonical_correct"]) for key in keys
                ]
                entry["acc100"] = acc100
                entry["gain"] = np.array(
                    [
                        float(after) - float(before)
                        for before, after in zip(acc0, acc100)
                    ],
                    dtype=np.float64,
                )
            per_arm[arm] = entry
        joined["strata"][stratum] = {"keys": keys, "arms": per_arm}
    return joined


def _stratum_table(
    heldout: dict[str, Any],
    joined: dict[str, Any],
    *,
    partial: bool,
    draws: int,
    base_seed: int,
) -> list[dict[str, Any]]:
    table: list[dict[str, Any]] = []
    eligible = set(heldout["eligible"])
    for stratum in sorted(heldout["items_by_stratum"]):
        entry_arms = joined["strata"][stratum]["arms"]
        n = len(joined["strata"][stratum]["keys"])
        row: dict[str, Any] = {
            "source": stratum[0],
            "category": stratum[1],
            "n": n,
            "eligible": stratum in eligible,
            "label": "eligible" if stratum in eligible else "descriptive-small-n",
            "q_bar": {
                arm: float(entry_arms[arm]["q"].mean()) for arm in ARMS
            },
            "acc_final_step0": {arm: _rate(entry_arms[arm]["acc0"]) for arm in ARMS},
        }
        if not partial:
            label = _stratum_label(stratum)
            row["acc_final_step100"] = {
                arm: _rate(entry_arms[arm]["acc100"]) for arm in ARMS
            }
            row["gain"] = {
                arm: mean_with_paired_bootstrap(
                    entry_arms[arm]["gain"].tolist(),
                    draws=draws,
                    seed=_metric_seed(base_seed, f"stratum_gain:{arm}:{label}"),
                )
                for arm in ARMS
            }
            a1 = row["gain"]["a1_real"]
            stable = a1["estimate"] > 0 and a1["estimate"] >= 2 * a1["paired_se"]
            row["a1_denominator"] = {
                "estimate": a1["estimate"],
                "paired_se": a1["paired_se"],
                "stable": bool(stable),
                "rule": "gain[A1,s] > 0 and gain[A1,s] >= 2 * paired_se",
            }
            if stratum in eligible:
                recovery: dict[str, Any] = {}
                for arm in BLIND_ARMS:
                    if stable:
                        ratio = paired_ratio(
                            entry_arms[arm]["gain"].tolist(),
                            entry_arms["a1_real"]["gain"].tolist(),
                            draws=draws,
                            seed=_metric_seed(
                                base_seed, f"stratum_recovery:{arm}:{label}"
                            ),
                        )
                        ratio["status"] = "stable"
                        recovery[arm] = ratio
                    else:
                        recovery[arm] = {"status": "undefined-unstable-denominator"}
                row["recovery"] = recovery
            else:
                row["recovery"] = None
        table.append(row)
    return table


def _rank_statistics(
    heldout: dict[str, Any],
    joined: dict[str, Any],
    *,
    draws: int,
    base_seed: int,
) -> dict[str, Any]:
    eligible = heldout["eligible"]
    results: dict[str, Any] = {}
    for arm in BLIND_ARMS:
        stratum_arrays = [
            {
                "q": joined["strata"][stratum]["arms"][arm]["q"],
                "gain": joined["strata"][stratum]["arms"][arm]["gain"],
                "gain_a1": joined["strata"][stratum]["arms"]["a1_real"]["gain"],
            }
            for stratum in eligible
        ]
        q_bar = [float(arrays["q"].mean()) for arrays in stratum_arrays]
        gain = [float(arrays["gain"].mean()) for arrays in stratum_arrays]
        gain_a1 = [float(arrays["gain_a1"].mean()) for arrays in stratum_arrays]
        se_a1 = [
            float(
                arrays["gain_a1"].std(ddof=1) / math.sqrt(arrays["gain_a1"].size)
            )
            if arrays["gain_a1"].size > 1
            else 0.0
            for arrays in stratum_arrays
        ]
        stable_flags = [
            mean > 0 and mean >= 2 * se for mean, se in zip(gain_a1, se_a1)
        ]
        stable_strata = [
            stratum for stratum, flag in zip(eligible, stable_flags) if flag
        ]
        unstable_strata = [
            stratum for stratum, flag in zip(eligible, stable_flags) if not flag
        ]

        if len(eligible) < 2:
            rho_gain: dict[str, Any] = {
                "estimate": None,
                "status": "undefined-insufficient-strata",
                "n_strata": len(eligible),
                "bootstrap": None,
            }
        else:
            estimate = tied_spearman(q_bar, gain)
            rho_gain = {
                "estimate": estimate,
                "status": (
                    "computed" if estimate is not None
                    else "undefined-constant-rank-vector"
                ),
                "n_strata": len(eligible),
                "direction_registered": "rho_gain > 0",
                "direction_holds": (estimate > 0) if estimate is not None else None,
                "bootstrap": _rank_statistic_bootstrap(
                    stratum_arrays,
                    kind="rho_gain",
                    draws=draws,
                    seed=_metric_seed(base_seed, f"rho_gain:{arm}"),
                ),
            }
            rho_gain["bootstrap"]["seed_label"] = f"rho_gain:{arm}"

        recovery_values = [
            g / a for g, a, flag in zip(gain, gain_a1, stable_flags) if flag
        ]
        recovery_q = [
            q for q, flag in zip(q_bar, stable_flags) if flag
        ]
        if len(recovery_values) < 2:
            rho_recovery: dict[str, Any] = {
                "estimate": None,
                "status": "undefined-insufficient-recovery-strata",
                "n_strata": len(eligible),
                "n_recovery_strata": len(recovery_values),
                "recovery_strata": [_stratum_label(s) for s in stable_strata],
                "excluded_unstable_strata": [
                    _stratum_label(s) for s in unstable_strata
                ],
                "bootstrap": None,
            }
        else:
            estimate = tied_spearman(recovery_q, recovery_values)
            rho_recovery = {
                "estimate": estimate,
                "status": (
                    "computed" if estimate is not None
                    else "undefined-constant-rank-vector"
                ),
                "n_strata": len(eligible),
                "n_recovery_strata": len(recovery_values),
                "recovery_strata": [_stratum_label(s) for s in stable_strata],
                "excluded_unstable_strata": [
                    _stratum_label(s) for s in unstable_strata
                ],
                "direction_registered": "rho_recovery > 0",
                "direction_holds": (estimate > 0) if estimate is not None else None,
            }
        if len(eligible) >= 2:
            rho_recovery["bootstrap"] = _rank_statistic_bootstrap(
                stratum_arrays,
                kind="rho_recovery",
                draws=draws,
                seed=_metric_seed(base_seed, f"rho_recovery:{arm}"),
            )
            rho_recovery["bootstrap"]["seed_label"] = f"rho_recovery:{arm}"

        results[arm] = {"rho_gain": rho_gain, "rho_recovery": rho_recovery}
    return results


def _corpus_results(
    joined: dict[str, Any],
    *,
    partial: bool,
    draws: int,
    base_seed: int,
) -> dict[str, Any]:
    results: dict[str, Any] = {"arms": {}}
    for arm in ARMS:
        corpus = joined["corpus"][arm]
        entry: dict[str, Any] = {
            "n": len(corpus["keys"]),
            "q_bar": float(corpus["q"].mean()),
            "acc_final_step0": _rate(corpus["acc0"]),
        }
        if not partial:
            entry["acc_final_step100"] = _rate(corpus["acc100"])
            entry["gain"] = mean_with_paired_bootstrap(
                corpus["gain"].tolist(),
                draws=draws,
                seed=_metric_seed(base_seed, f"aggregate_gain:{arm}"),
            )
        results["arms"][arm] = entry
    if partial:
        return results

    a1 = results["arms"]["a1_real"]["gain"]
    a1_stable = a1["estimate"] > 0 and a1["estimate"] >= 2 * a1["paired_se"]
    results["a1_denominator"] = {
        "estimate": a1["estimate"],
        "paired_se": a1["paired_se"],
        "stable": bool(a1_stable),
        "rule": "gain[A1] > 0 and gain[A1] >= 2 * paired_se",
    }
    recovery: dict[str, Any] = {}
    anchors: dict[str, Any] = {}
    gain_a1 = joined["corpus"]["a1_real"]["gain"]
    for arm in BLIND_ARMS:
        gain_blind = joined["corpus"][arm]["gain"]
        bootstrap, ratios = _aggregate_recovery_bootstrap(
            gain_blind,
            gain_a1,
            draws=draws,
            seed=_metric_seed(base_seed, f"aggregate_recovery:{arm}"),
        )
        bootstrap["seed_label"] = f"aggregate_recovery:{arm}"
        if a1_stable:
            estimate = float(gain_blind.mean() / gain_a1.mean())
            status = "stable"
        else:
            estimate = None
            status = "undefined-unstable-denominator"
        recovery[arm] = {
            "estimate": estimate,
            "status": status,
            "bootstrap": bootstrap,
        }
        if arm in GEO3K_ANCHORS:
            anchor = GEO3K_ANCHORS[arm]
            difference = None if estimate is None else estimate - anchor
            difference_ci = (
                percentile_interval([value - anchor for value in ratios])
                if ratios
                else None
            )
            anchors[arm] = {
                "informed_comparison": True,
                "informed_comparison_statement": (
                    "The Geometry3K anchors are the completed seed-1 recovery "
                    "readout; the registered direction was written after that "
                    "readout (Informed-Prediction Disclosure, "
                    "docs/registered_m7_amendment_v1.md)."
                ),
                "geometry3k_seed1_anchor": anchor,
                "virl_recovery": estimate,
                "difference_from_anchor": difference,
                "difference_ci95": difference_ci,
                "direction_registered": "greater than the anchor",
                "direction_holds": (
                    None if difference is None else bool(difference > 0)
                ),
                "interval_label": bootstrap["interval_label"],
            }
    results["aggregate_recovery"] = recovery
    results["geometry3k_anchor_comparison"] = anchors
    return results


def _descriptive_views(
    heldout: dict[str, Any],
    runs: dict[str, dict[str, dict[str, Any]]],
    *,
    partial: bool,
    draws: int,
    base_seed: int,
) -> dict[str, Any]:
    views: dict[str, Any] = {}
    for axis, index in (("source_only", 0), ("category_only", 1)):
        groups: dict[str, list[tuple[str, int]]] = {}
        for key in sorted(heldout["stratum_of"]):
            groups.setdefault(heldout["stratum_of"][key][index], []).append(key)
        rows: list[dict[str, Any]] = []
        for group in sorted(groups):
            keys = groups[group]
            row: dict[str, Any] = {"group": group, "n": len(keys)}
            for arm in ARMS:
                step0 = runs[arm]["step0"]["rows"]
                acc0 = [bool(step0[key]["greedy_canonical_correct"]) for key in keys]
                q_values = [float(step0[key]["q_i"]) for key in keys]
                arm_entry: dict[str, Any] = {
                    "q_bar": float(np.mean(q_values)),
                    "acc_final_step0": _rate(acc0),
                }
                if not partial:
                    step100 = runs[arm]["step100"]["rows"]
                    acc100 = [
                        bool(step100[key]["greedy_canonical_correct"]) for key in keys
                    ]
                    gain = [
                        float(after) - float(before)
                        for before, after in zip(acc0, acc100)
                    ]
                    arm_entry["acc_final_step100"] = _rate(acc100)
                    arm_entry["gain"] = mean_with_paired_bootstrap(
                        gain,
                        draws=draws,
                        seed=_metric_seed(base_seed, f"{axis}_gain:{arm}:{group}"),
                    )
                row[arm] = arm_entry
            rows.append(row)
        views[axis] = {
            "role": (
                "descriptive robustness view; does not replace the registered "
                "joint-stratum analysis"
            ),
            "rows": rows,
        }
    return views


def _support_sharpening(
    runs: dict[str, dict[str, dict[str, Any]]],
    heldout: dict[str, Any],
    *,
    artifact_dir: Path,
    root: Path,
) -> dict[str, Any]:
    results: dict[str, Any] = {
        "rule": (
            "base 0/16 under the arm's own condition, step-0 greedy wrong, "
            f"step-{TARGET_STEP} greedy correct; 64-sample frozen-base "
            "follow-up is reported separately under M10"
        ),
        "causal_capability_claim_permitted": False,
        "arms": {},
    }
    ordered_keys = sorted(heldout["stratum_of"])
    for arm in ARMS:
        step0 = runs[arm]["step0"]["rows"]
        step100 = runs[arm]["step100"]["rows"]
        baseline_rows = [step0[key] for key in ordered_keys]
        readout_rows = [
            {
                "split": step0[key]["split"],
                "row_index": key[1],
                "arm": arm,
                "condition": CONDITIONS[arm],
                "step0_acc_final": bool(step0[key]["greedy_canonical_correct"]),
                "target_step": TARGET_STEP,
                "target_acc_final": bool(step100[key]["greedy_canonical_correct"]),
            }
            for key in ordered_keys
        ]
        candidates = build_resampling_candidates(
            baseline_rows,
            readout_rows,
            arm=arm,
            condition=CONDITIONS[arm],
            target_step=TARGET_STEP,
        )
        candidate_path = artifact_dir / f"support_candidates_{arm}.jsonl"
        candidate_path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in candidates),
            encoding="utf-8",
        )
        results["arms"][arm] = {
            "candidate_count": len(candidates),
            "candidate_artifact": str(candidate_path.relative_to(root)),
            "candidate_sha256": _sha256(candidate_path),
            "followup_samples_per_candidate": 64,
            "followup_status": "pending",
        }
    return results


# --------------------------------------------------------------------------
# Payload assembly and rendering
# --------------------------------------------------------------------------

def _provenance(
    heldout: dict[str, Any],
    runs: dict[str, dict[str, dict[str, Any]]],
    *,
    root: Path,
    draws: int,
    base_seed: int,
) -> dict[str, Any]:
    run_block: dict[str, Any] = {}
    for arm in ARMS:
        if arm not in runs:
            continue
        run_block[arm] = {}
        for step_label in sorted(runs[arm]):
            run = runs[arm][step_label]
            manifest = run["manifest"]
            run_block[arm][step_label] = {
                "run_dir": str(run["run_dir"].relative_to(root)),
                "run_id": run["run_id"],
                "job_type": manifest.get("job_type"),
                "node": manifest.get("node"),
                "training_git_hash": manifest.get("git_hash"),
                "config_hash": manifest.get("config_hash"),
                "run_manifest_sha256": run["manifest_sha256"],
                "per_item_sha256": run["per_item_sha256"],
            }
    return {
        "heldout_manifest": str(heldout["path"].relative_to(root)),
        "heldout_sha256": heldout["sha256"],
        "heldout_row_count": heldout["row_count"],
        "runs": run_block,
        "analysis_git_head": _git_head(root),
        "bootstrap": {
            "draws": draws,
            "seed": base_seed,
            "stream_mechanism": (
                "deterministic statistic/arm labels hashed into independent "
                "streams via src.analysis.pilot_fourarm.deterministic_seed"
            ),
        },
        "registered_documents": list(REGISTERED_DOCUMENTS),
        "split_manifest_v2_note": (
            "data/virl39k_m7_split_manifest_v2.json n_strata_rank_eligible=21 "
            "counts component labels, not items, and was not used; eligibility "
            "was recounted directly from the held-out jsonl"
        ),
    }


def build_payload(args: argparse.Namespace, root: Path) -> dict[str, Any]:
    heldout = load_heldout(
        _resolve(root, args.heldout),
        expected_sha256=args.expected_heldout_sha256,
        expected_rows=args.expected_heldout_rows,
        expected_eligible=args.expected_eligible_strata,
        expected_small_n=args.expected_small_n_strata,
    )
    runs: dict[str, dict[str, dict[str, Any]]] = {}
    for arm in ARMS:
        runs[arm] = {
            "step0": load_run(
                root,
                args.step0[arm],
                arm=arm,
                step_label="step0",
                require_step0_fields=True,
            )
        }
        if not args.partial:
            runs[arm]["step100"] = load_run(
                root,
                args.step100[arm],
                arm=arm,
                step_label="step100",
                require_step0_fields=False,
            )
    readiness_gate(runs, set(heldout["stratum_of"]))
    if not args.partial:
        pairing_gate(runs)

    draws = int(args.bootstrap_draws)
    base_seed = int(args.bootstrap_seed)
    joined = _join_items(heldout, runs, partial=args.partial)
    corpus = _corpus_results(
        joined, partial=args.partial, draws=draws, base_seed=base_seed
    )
    stratum_table = _stratum_table(
        heldout, joined, partial=args.partial, draws=draws, base_seed=base_seed
    )
    views = _descriptive_views(
        heldout, runs, partial=args.partial, draws=draws, base_seed=base_seed
    )

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "partial-step0-only" if args.partial else "complete",
        "seed_scope": {
            "tag": SEED_SCOPE_TAG,
            "statement": SEED_SCOPE_STATEMENT,
            "between_seed_dispersion": (
                "unmeasured: seed 1 only; seed 2 deferred, not abandoned "
                "(docs/registered_m7_seed_scope_v1.md)"
            ),
        },
        "single_image_restriction": {
            "statement": SINGLE_IMAGE_STATEMENT,
            "retained_train_fraction": 0.932,
            "retained_heldout_fraction": 0.942,
        },
        "pooling_discipline": POOLING_STATEMENT,
        "strata": {
            "definition": "joint (metadata.source, metadata.category)",
            "eligibility_threshold_items": ELIGIBILITY_THRESHOLD,
            "total": len(heldout["items_by_stratum"]),
            "eligible_count": len(heldout["eligible"]),
            "small_n_count": len(heldout["small_n"]),
            "recount_source": str(heldout["path"].relative_to(root)),
        },
        "bootstrap": {
            "draws": draws,
            "seed": base_seed,
            "registered_draws": REGISTERED_BOOTSTRAP_DRAWS,
            "registered_seed": REGISTERED_BOOTSTRAP_SEED,
            "unit": (
                "paired items resampled within every frozen joint stratum for "
                "rank statistics; paired items across the corpus for aggregates"
            ),
        },
        "checks": {
            "heldout_sha256_matches_registered": (
                heldout["sha256"] == REGISTERED_HELDOUT_SHA256
            ),
            "eligible_strata_recount": len(heldout["eligible"]),
            "small_n_strata_recount": len(heldout["small_n"]),
            "step0_coverage_complete_all_arms": True,
            "step0_step100_pairing_exact_all_arms": (not args.partial) or None,
            "conditions_match_arms": True,
            "bootstrap_draws_registered_5000": draws == REGISTERED_BOOTSTRAP_DRAWS,
            "bootstrap_seed_registered_20260716": (
                base_seed == REGISTERED_BOOTSTRAP_SEED
            ),
            "pooled_only_readout": False,
            "blind_arms_pooled": False,
        },
        "corpus": corpus,
        "stratum_table": stratum_table,
        "descriptive_views": views,
    }
    if args.partial:
        payload["partial_mode"] = {
            "computes": [
                "q_bar per arm per stratum",
                "Acc_final(step_0) per arm (corpus, strata, descriptive views)",
            ],
            "refused_estimands": list(REFUSED_IN_PARTIAL),
            "reason": (
                "step-100 evaluations are not provided; this output is a "
                "plumbing readout of the step-0 side only and is not the "
                "registered R3 result"
            ),
        }
    else:
        artifact_dir = _resolve(root, args.artifact_dir)
        if artifact_dir.exists():
            raise FileExistsError(
                f"refusing to overwrite artifact directory: {artifact_dir}"
            )
        artifact_dir.mkdir(parents=True)
        payload["rank_statistics"] = _rank_statistics(
            heldout, joined, draws=draws, base_seed=base_seed
        )
        payload["support_sharpening"] = _support_sharpening(
            runs, heldout, artifact_dir=artifact_dir, root=root
        )
        joined_path = artifact_dir / "m7_joined_items.jsonl"
        joined_path.write_text(
            "".join(
                json.dumps(
                    {
                        "arm": arm,
                        "qid": key[0],
                        "row_index": key[1],
                        "source": heldout["stratum_of"][key][0],
                        "category": heldout["stratum_of"][key][1],
                        "q_i": float(joined["corpus"][arm]["q"][position]),
                        "acc_final_step0": joined["corpus"][arm]["acc0"][position],
                        "acc_final_step100": joined["corpus"][arm]["acc100"][position],
                        "gain": float(joined["corpus"][arm]["gain"][position]),
                    },
                    sort_keys=True,
                )
                + "\n"
                for arm in ARMS
                for position, key in enumerate(joined["corpus"][arm]["keys"])
            ),
            encoding="utf-8",
        )
        payload["joined_items_artifact"] = str(joined_path.relative_to(root))
        payload["joined_items_sha256"] = _sha256(joined_path)
    payload["provenance"] = _provenance(
        heldout, runs, root=root, draws=draws, base_seed=base_seed
    )
    return payload


def _fmt(value: float | None) -> str:
    return "NA" if value is None else f"{value:.4f}"


def _fmt_ci(summary: dict[str, Any] | None) -> str:
    if summary is None or summary.get("estimate") is None:
        return "NA"
    interval = summary.get("ci95")
    if interval is None:
        return f"{summary['estimate']:.4f} [NA]"
    return f"{summary['estimate']:.4f} [{interval[0]:.4f}, {interval[1]:.4f}]"


def render_markdown(payload: dict[str, Any], json_relpath: str) -> str:
    partial = payload["status"] == "partial-step0-only"
    lines = [
        "# M7 R3 Readout V1" + (" - PARTIAL (step-0 only)" if partial else ""),
        "",
        f"Status: `{payload['status']}`.",
        "",
        "Scope:",
        f"- {payload['seed_scope']['statement']}",
        f"- {payload['single_image_restriction']['statement']}",
        f"- {payload['pooling_discipline']}",
        "- This report contains numbers and provenance only; interpretation is "
        "reserved to the PIs.",
        "",
        f"Machine artifact: `{json_relpath}`.",
        "",
    ]
    if partial:
        lines.extend(
            [
                "## PARTIAL MODE",
                "",
                "- This output is a step-0-only plumbing readout; it is NOT the "
                "registered R3 result.",
                "- Refused estimands (require the step-100 side): "
                + ", ".join(payload["partial_mode"]["refused_estimands"])
                + ".",
                "",
            ]
        )
    strata = payload["strata"]
    lines.extend(
        [
            "## Strata accounting",
            "",
            f"- Joint (source, category) strata recounted from "
            f"`{strata['recount_source']}`: {strata['total']} total, "
            f"{strata['eligible_count']} eligible "
            f"(>= {strata['eligibility_threshold_items']} held-out items), "
            f"{strata['small_n_count']} descriptive-small-n.",
            "- Eligibility depends only on sample count, never on a model "
            "outcome; descriptive-small-n strata are published, not merged or "
            "discarded, and enter no rank statistic.",
            "",
            f"## Corpus aggregate ({SEED_SCOPE_TAG})",
            "",
        ]
    )
    if partial:
        lines.extend(
            [
                "| Arm | n | q_bar | Acc_final step 0 |",
                "|---|---:|---:|---:|",
            ]
        )
        for arm in ARMS:
            row = payload["corpus"]["arms"][arm]
            lines.append(
                f"| {DISPLAY_NAMES[arm]} | {row['n']} | {_fmt(row['q_bar'])} | "
                f"{_fmt(row['acc_final_step0'])} |"
            )
    else:
        lines.extend(
            [
                "| Arm | n | q_bar | Acc_final step 0 | Acc_final step 100 | "
                "Gain (95% CI) |",
                "|---|---:|---:|---:|---:|---:|",
            ]
        )
        for arm in ARMS:
            row = payload["corpus"]["arms"][arm]
            lines.append(
                f"| {DISPLAY_NAMES[arm]} | {row['n']} | {_fmt(row['q_bar'])} | "
                f"{_fmt(row['acc_final_step0'])} | "
                f"{_fmt(row['acc_final_step100'])} | {_fmt_ci(row['gain'])} |"
            )
        denominator = payload["corpus"]["a1_denominator"]
        lines.extend(
            [
                "",
                f"Corpus A1 denominator: estimate {_fmt(denominator['estimate'])}, "
                f"paired SE {_fmt(denominator['paired_se'])}, stable "
                f"`{str(denominator['stable']).lower()}` "
                f"(rule: {denominator['rule']}).",
                "",
                f"| Blind arm | Aggregate recovery (95% CI) | Status | "
                f"Undefined draws | Interval label |",
                "|---|---:|---|---:|---|",
            ]
        )
        for arm in BLIND_ARMS:
            row = payload["corpus"]["aggregate_recovery"][arm]
            bootstrap = row["bootstrap"]
            lines.append(
                f"| {DISPLAY_NAMES[arm]} | {_fmt_ci(row)} | {row['status']} | "
                f"{bootstrap['undefined_draw_count']}/{bootstrap['draws']} | "
                f"{bootstrap['interval_label']} |"
            )
    eligible_rows = [row for row in payload["stratum_table"] if row["eligible"]]
    small_rows = [row for row in payload["stratum_table"] if not row["eligible"]]
    lines.extend(
        [
            "",
            f"## Registered joint strata: q_bar ({len(eligible_rows)} eligible)",
            "",
            "| Source | Category | n | q_bar A1 | q_bar A2 | q_bar A2b | "
            "q_bar A3 |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in eligible_rows:
        lines.append(
            f"| {row['source']} | {row['category']} | {row['n']} | "
            + " | ".join(_fmt(row["q_bar"][arm]) for arm in ARMS)
            + " |"
        )
    if not partial:
        lines.extend(
            [
                "",
                f"## Registered joint strata: gains ({SEED_SCOPE_TAG})",
                "",
                "| Source | Category | n | A1 gain (95% CI) | A2 gain (95% CI) | "
                "A2b gain (95% CI) | A3 gain (95% CI) | A1 stable |",
                "|---|---|---:|---:|---:|---:|---:|---|",
            ]
        )
        for row in eligible_rows:
            lines.append(
                f"| {row['source']} | {row['category']} | {row['n']} | "
                + " | ".join(_fmt_ci(row["gain"][arm]) for arm in ARMS)
                + f" | {str(row['a1_denominator']['stable']).lower()} |"
            )
        lines.extend(
            [
                "",
                f"## Registered joint strata: recovery ({SEED_SCOPE_TAG})",
                "",
                "Recovery is `gain[b,s] / gain[A1,s]` only when the A1 "
                "denominator is stable (gain[A1,s] > 0 and >= 2 paired SE); "
                "otherwise `undefined-unstable-denominator`. Unstable strata "
                "stay in the gain analysis and are omitted from the recovery "
                "rank statistic.",
                "",
                "| Source | Category | A2 recovery (95% CI) | "
                "A2b recovery (95% CI) | A3 recovery (95% CI) |",
                "|---|---|---:|---:|---:|",
            ]
        )
        for row in eligible_rows:
            cells = []
            for arm in BLIND_ARMS:
                entry = row["recovery"][arm]
                if entry["status"] != "stable":
                    cells.append(entry["status"])
                else:
                    cells.append(_fmt_ci(entry))
            lines.append(
                f"| {row['source']} | {row['category']} | " + " | ".join(cells) + " |"
            )
    lines.extend(
        [
            "",
            f"## Descriptive small-n strata ({len(small_rows)})",
            "",
            "Published per registration; not merged, not discarded, not in any "
            "rank statistic.",
            "",
        ]
    )
    if partial:
        lines.extend(
            [
                "| Source | Category | n | q_bar A1 | q_bar A2 | q_bar A2b | "
                "q_bar A3 |",
                "|---|---|---:|---:|---:|---:|---:|",
            ]
        )
        for row in small_rows:
            lines.append(
                f"| {row['source']} | {row['category']} | {row['n']} | "
                + " | ".join(_fmt(row["q_bar"][arm]) for arm in ARMS)
                + " |"
            )
    else:
        lines.extend(
            [
                "| Source | Category | n | A1 gain (95% CI) | A2 gain (95% CI) | "
                "A2b gain (95% CI) | A3 gain (95% CI) |",
                "|---|---|---:|---:|---:|---:|---:|",
            ]
        )
        for row in small_rows:
            lines.append(
                f"| {row['source']} | {row['category']} | {row['n']} | "
                + " | ".join(_fmt_ci(row["gain"][arm]) for arm in ARMS)
                + " |"
            )
        lines.extend(
            [
                "",
                f"## Rank statistics ({SEED_SCOPE_TAG})",
                "",
                "Tie-corrected Spearman across eligible strata; undefined "
                "bootstrap draws are counted, never replaced with zero; an "
                "interval with more than 5% undefined draws is labeled "
                "unstable.",
                "",
                "| Blind arm | rho_gain (95% CI) | Undefined | Label | "
                "Direction > 0 holds | rho_recovery (95% CI) | Recovery strata | "
                "Undefined | Label | Direction > 0 holds |",
                "|---|---:|---:|---|---|---:|---:|---:|---|---|",
            ]
        )
        for arm in BLIND_ARMS:
            gain_stat = payload["rank_statistics"][arm]["rho_gain"]
            recovery_stat = payload["rank_statistics"][arm]["rho_recovery"]

            def _stat_cells(stat: dict[str, Any]) -> tuple[str, str, str, str]:
                bootstrap = stat.get("bootstrap")
                if stat.get("estimate") is None:
                    shown = stat["status"]
                else:
                    interval = bootstrap["ci95"] if bootstrap else None
                    shown = (
                        f"{stat['estimate']:.4f} "
                        + (
                            f"[{interval[0]:.4f}, {interval[1]:.4f}]"
                            if interval
                            else "[NA]"
                        )
                    )
                undefined = (
                    f"{bootstrap['undefined_draw_count']}/{bootstrap['draws']}"
                    if bootstrap
                    else "NA"
                )
                label = bootstrap["interval_label"] if bootstrap else "NA"
                holds = stat.get("direction_holds")
                holds_text = "NA" if holds is None else str(holds).lower()
                return shown, undefined, label, holds_text

            g_shown, g_undef, g_label, g_holds = _stat_cells(gain_stat)
            r_shown, r_undef, r_label, r_holds = _stat_cells(recovery_stat)
            recovery_count = (
                f"{recovery_stat.get('n_recovery_strata', 'NA')}/"
                f"{recovery_stat.get('n_strata', 'NA')}"
            )
            lines.append(
                f"| {DISPLAY_NAMES[arm]} | {g_shown} | {g_undef} | {g_label} | "
                f"{g_holds} | {r_shown} | {recovery_count} | {r_undef} | "
                f"{r_label} | {r_holds} |"
            )
    for axis, title in (
        ("source_only", "Source-only descriptive table"),
        ("category_only", "Category-only descriptive table"),
    ):
        view = payload["descriptive_views"][axis]
        lines.extend(
            [
                "",
                f"## {title}",
                "",
                f"Role: {view['role']}.",
                "",
            ]
        )
        if partial:
            lines.extend(
                [
                    "| Group | n | q_bar A1 | q_bar A2 | q_bar A2b | q_bar A3 | "
                    "Acc0 A1 | Acc0 A2 | Acc0 A2b | Acc0 A3 |",
                    "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
                ]
            )
            for row in view["rows"]:
                lines.append(
                    f"| {row['group']} | {row['n']} | "
                    + " | ".join(_fmt(row[arm]["q_bar"]) for arm in ARMS)
                    + " | "
                    + " | ".join(
                        _fmt(row[arm]["acc_final_step0"]) for arm in ARMS
                    )
                    + " |"
                )
        else:
            lines.extend(
                [
                    "| Group | n | A1 gain (95% CI) | A2 gain (95% CI) | "
                    "A2b gain (95% CI) | A3 gain (95% CI) |",
                    "|---|---:|---:|---:|---:|---:|",
                ]
            )
            for row in view["rows"]:
                lines.append(
                    f"| {row['group']} | {row['n']} | "
                    + " | ".join(_fmt_ci(row[arm]["gain"]) for arm in ARMS)
                    + " |"
                )
    if not partial:
        lines.extend(
            [
                "",
                f"## Geometry3K anchor comparison ({SEED_SCOPE_TAG}; informed "
                "comparison)",
                "",
                "This comparison is informed, not fully prospective: the "
                "anchors are the completed Geometry3K seed-1 recovery readout "
                "(Informed-Prediction Disclosure, "
                "docs/registered_m7_amendment_v1.md).",
                "",
                "| Blind arm | Geometry3K anchor | ViRL recovery (95% CI) | "
                "Difference (95% CI) | Direction (> anchor) holds | "
                "Interval label |",
                "|---|---:|---:|---:|---|---|",
            ]
        )
        anchors = payload["corpus"]["geometry3k_anchor_comparison"]
        for arm in BLIND_ARMS:
            if arm not in anchors:
                lines.append(
                    f"| {DISPLAY_NAMES[arm]} | no registered anchor | "
                    f"{_fmt_ci(payload['corpus']['aggregate_recovery'][arm])} | "
                    "NA | NA | "
                    f"{payload['corpus']['aggregate_recovery'][arm]['bootstrap']['interval_label']} |"
                )
                continue
            row = anchors[arm]
            difference_ci = row["difference_ci95"]
            difference_text = (
                "NA"
                if row["difference_from_anchor"] is None
                else (
                    f"{row['difference_from_anchor']:.4f} "
                    + (
                        f"[{difference_ci[0]:.4f}, {difference_ci[1]:.4f}]"
                        if difference_ci
                        else "[NA]"
                    )
                )
            )
            holds = row["direction_holds"]
            lines.append(
                f"| {DISPLAY_NAMES[arm]} | {row['geometry3k_seed1_anchor']:.4f} | "
                f"{_fmt(row['virl_recovery'])} | {difference_text} | "
                f"{'NA' if holds is None else str(holds).lower()} | "
                f"{row['interval_label']} |"
            )
        support = payload["support_sharpening"]
        lines.extend(
            [
                "",
                "## M10 support-sharpening candidates",
                "",
                f"Rule: {support['rule']}.",
                "",
                "| Arm | Candidates | Artifact |",
                "|---|---:|---|",
            ]
        )
        for arm in ARMS:
            row = support["arms"][arm]
            lines.append(
                f"| {DISPLAY_NAMES[arm]} | {row['candidate_count']} | "
                f"`{row['candidate_artifact']}` |"
            )
        lines.extend(
            [
                "",
                "Candidate selection does not claim that RL created or taught "
                "a capability; M10 language remains non-causal.",
            ]
        )
    provenance = payload["provenance"]
    lines.extend(
        [
            "",
            "## Provenance",
            "",
            f"- Held-out manifest: `{provenance['heldout_manifest']}` "
            f"(sha256 `{provenance['heldout_sha256']}`, "
            f"{provenance['heldout_row_count']} rows).",
            f"- Analysis git head: `{provenance['analysis_git_head']}`.",
            f"- Bootstrap: {provenance['bootstrap']['draws']} draws, seed "
            f"{provenance['bootstrap']['seed']}; "
            f"{provenance['bootstrap']['stream_mechanism']}.",
            f"- {provenance['split_manifest_v2_note']}.",
            "- Registered documents: "
            + ", ".join(f"`{doc}`" for doc in provenance["registered_documents"])
            + ".",
            "",
            "| Arm | Step | Run dir | per_item sha256 |",
            "|---|---|---|---|",
        ]
    )
    for arm in ARMS:
        for step_label in sorted(provenance["runs"].get(arm, {})):
            row = provenance["runs"][arm][step_label]
            lines.append(
                f"| {DISPLAY_NAMES[arm]} | {step_label} | `{row['run_dir']}` | "
                f"`{row['per_item_sha256']}` |"
            )
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _parse_arm_runs(values: list[str] | None, flag: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values or []:
        if "=" not in value:
            raise SystemExit(f"{flag} expects ARM=RUN_DIR, got {value!r}")
        arm, _, run_dir = value.partition("=")
        if arm not in ARMS:
            raise SystemExit(
                f"{flag}: unknown arm {arm!r}; registered arms are {ARMS}"
            )
        if arm in result:
            raise SystemExit(f"{flag}: duplicate arm {arm!r}")
        if not run_dir:
            raise SystemExit(f"{flag}: empty run dir for arm {arm!r}")
        result[arm] = run_dir
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--heldout", default=REGISTERED_HELDOUT_PATH)
    parser.add_argument(
        "--step0",
        action="append",
        metavar="ARM=RUN_DIR",
        help="step-0 evaluation run directory for one arm (repeat four times)",
    )
    parser.add_argument(
        "--step100",
        action="append",
        metavar="ARM=RUN_DIR",
        help=(
            "step-100 evaluation run directory for one arm (repeat four "
            "times; forbidden with --partial)"
        ),
    )
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--markdown-output", required=True)
    parser.add_argument(
        "--artifact-dir",
        default=None,
        help="directory for candidate/joined-item artifacts (full mode only)",
    )
    parser.add_argument(
        "--partial",
        action="store_true",
        help=(
            "step-0-only plumbing mode: computes q_bar and step-0 accuracies "
            "only and refuses every gain/recovery/rank estimand"
        ),
    )
    parser.add_argument(
        "--bootstrap-draws", type=int, default=REGISTERED_BOOTSTRAP_DRAWS
    )
    parser.add_argument(
        "--bootstrap-seed", type=int, default=REGISTERED_BOOTSTRAP_SEED
    )
    parser.add_argument(
        "--expected-heldout-sha256", default=REGISTERED_HELDOUT_SHA256
    )
    parser.add_argument(
        "--expected-heldout-rows", type=int, default=REGISTERED_HELDOUT_ROWS
    )
    parser.add_argument(
        "--expected-eligible-strata", type=int, default=REGISTERED_ELIGIBLE_STRATA
    )
    parser.add_argument(
        "--expected-small-n-strata", type=int, default=REGISTERED_SMALL_N_STRATA
    )
    args = parser.parse_args()

    args.step0 = _parse_arm_runs(args.step0, "--step0")
    args.step100 = _parse_arm_runs(args.step100, "--step100")
    missing_step0 = [arm for arm in ARMS if arm not in args.step0]
    if missing_step0:
        parser.error(f"--step0 missing for arms: {missing_step0}")
    if args.partial:
        if args.step100:
            parser.error("--partial forbids --step100 runs")
        if args.artifact_dir is not None:
            parser.error("--partial forbids --artifact-dir")
    else:
        missing_step100 = [arm for arm in ARMS if arm not in args.step100]
        if missing_step100:
            parser.error(
                f"--step100 missing for arms: {missing_step100} "
                "(pass --partial for the step-0-only plumbing mode)"
            )
        if args.artifact_dir is None:
            parser.error("--artifact-dir is required in full mode")
    if args.bootstrap_draws < 100:
        parser.error("--bootstrap-draws must be at least 100")

    root = args.root.resolve()
    json_output = _resolve(root, args.json_output)
    markdown_output = _resolve(root, args.markdown_output)
    if json_output.exists() or markdown_output.exists():
        raise FileExistsError("refusing to overwrite R3 readout artifacts")

    payload = build_payload(args, root)
    markdown = render_markdown(payload, str(json_output.relative_to(root)))
    _write_text(json_output, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    _write_text(markdown_output, markdown)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "json": str(json_output.relative_to(root)),
                "markdown": str(markdown_output.relative_to(root)),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
