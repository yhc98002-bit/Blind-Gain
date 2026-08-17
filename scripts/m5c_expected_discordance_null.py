#!/usr/bin/env python3
"""M5C Task B: expected-discordance null built from sampled per-item probabilities
at BOTH endpoints (step 100 and step 400).

The prior reference figure (0.21327735) estimated p_i from 16-sample temperature
decoding at step 100 ONLY and then assumed the same per-item rates hold at step
400. This script estimates p_i separately at each endpoint and computes

    E[disc] = mean_i [ p_i(100)(1-p_i(400)) + (1-p_i(100)) p_i(400) ]

with a bootstrap CI over items, compares it to the OBSERVED greedy discordance
(137/601), and tests observed > expected.

Writes reports/m5c_expected_discordance_null_v1.{json,md}.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")

SCHEMA = "blind-gains.m5c-expected-discordance-null.v1"
BOOT_DRAWS = 10_000
MC_DRAWS = 10_000
SEED = 20260729

SUBSTRATE = ROOT / "reports/m5c_item_substrate_v1.jsonl"
TURNOVER = ROOT / "reports/m5c_turnover_v1.json"
TASK_A_FLOOR = ROOT / "reports/m5c_noise_floor_replicate_v1.json"

# step-100 sampled protocol located by manifest search (see report)
S100_GUARDED = ROOT / "experiments/runs/blind_solvability_v2_anchor_step100_geo3k_guarded_real_an12_20260712T053344Z"
S100_RESCORE = ROOT / "experiments/runs/blind_solvability_v2_guarded_rescore_anchor_step100_geo3k_real_login_20260712T082107Z"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_test_rows(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for line in path.open(encoding="utf-8"):
        d = json.loads(line)
        if d.get("split") != "test":
            continue
        key = f'{d["split"]}:{d["row_index"]}'
        if key in out:
            raise ValueError(f"duplicate item key {key} in {path}")
        out[key] = d
    return out


def sampled_counts(rows: dict[str, dict], keys: list[str]) -> dict[str, Any]:
    """Per-item sampled success counts, lenient and strict-contract."""
    n_list, c_len, c_str = [], [], []
    n_correct_not_contract = 0
    for k in keys:
        d = rows[k]
        sc = [bool(x) for x in d["sample_correct"]]
        cv = [bool(x) for x in d["sampled_contract_valid"]]
        if len(sc) != len(cv):
            raise ValueError("sample/contract length mismatch")
        if int(d["sample_count"]) != len(sc):
            raise ValueError("sample_count disagrees with sample_correct length")
        if int(d["sample_correct_count"]) != sum(sc):
            raise ValueError("sample_correct_count disagrees with sample_correct")
        n_correct_not_contract += sum(1 for a, b in zip(sc, cv) if a and not b)
        n_list.append(len(sc))
        c_len.append(sum(sc))
        c_str.append(sum(1 for a, b in zip(sc, cv) if a and b))
    return {
        "n": np.asarray(n_list, dtype=float),
        "c_lenient": np.asarray(c_len, dtype=float),
        "c_strict": np.asarray(c_str, dtype=float),
        "n_sampled_rows_correct_but_not_contract_valid": n_correct_not_contract,
    }


def expected_discordance(p_a: np.ndarray, p_b: np.ndarray) -> np.ndarray:
    return p_a * (1.0 - p_b) + (1.0 - p_a) * p_b


def pct(a: np.ndarray, lo: float = 2.5, hi: float = 97.5) -> list[float]:
    return [float(np.percentile(a, lo)), float(np.percentile(a, hi))]


def analyse(
    label: str,
    c100: np.ndarray,
    c400: np.ndarray,
    n_s: np.ndarray,
    observed: np.ndarray,
    rng_seed: int,
) -> dict[str, Any]:
    """All Task-B quantities for one metric definition (lenient or strict)."""
    n_items = observed.size
    obs_count = int(observed.sum())
    obs_frac = obs_count / n_items

    out: dict[str, Any] = {
        "n_items": n_items,
        "samples_per_item": sorted({int(x) for x in n_s.tolist()}),
        "observed_greedy_discordance_count": obs_count,
        "observed_greedy_discordance_fraction": obs_frac,
    }

    for est_name, p100, p400 in (
        ("plugin_mle", c100 / n_s, c400 / n_s),
        ("jeffreys", (c100 + 0.5) / (n_s + 1.0), (c400 + 0.5) / (n_s + 1.0)),
    ):
        d_i = expected_discordance(p100, p400)
        exp_frac = float(d_i.mean())

        rng = np.random.default_rng(rng_seed)
        idx = rng.integers(0, n_items, size=(BOOT_DRAWS, n_items))
        exp_b = d_i[idx].mean(axis=1)
        obs_b = observed[idx].mean(axis=1)
        diff_b = obs_b - exp_b

        # Monte-Carlo null on the discordance COUNT: each step draws its own
        # independent Bernoulli per item, at the plug-in rate.
        rng_mc = np.random.default_rng(rng_seed + 1)
        a = rng_mc.random((MC_DRAWS, n_items)) < p100
        b = rng_mc.random((MC_DRAWS, n_items)) < p400
        null_counts = (a != b).sum(axis=1)
        ge = int((null_counts >= obs_count).sum())

        # Posterior-propagated null: also carries the 16-sample estimation error
        # in p_i through a Jeffreys Beta posterior at each endpoint.
        rng_pp = np.random.default_rng(rng_seed + 2)
        pa = rng_pp.beta(c100 + 0.5, n_s - c100 + 0.5, size=(MC_DRAWS, n_items))
        pb = rng_pp.beta(c400 + 0.5, n_s - c400 + 0.5, size=(MC_DRAWS, n_items))
        aa = rng_pp.random((MC_DRAWS, n_items)) < pa
        bb = rng_pp.random((MC_DRAWS, n_items)) < pb
        null_pp = (aa != bb).sum(axis=1)
        ge_pp = int((null_pp >= obs_count).sum())

        out[est_name] = {
            "p_estimator": (
                "p_i = c_i / n_i (16 sampled successes / 16 samples)"
                if est_name == "plugin_mle"
                else "p_i = (c_i + 0.5) / (n_i + 1)  [Jeffreys-smoothed]"
            ),
            "mean_p_i_step100": float(p100.mean()),
            "mean_p_i_step400": float(p400.mean()),
            "mean_p_i_step400_minus_step100": float(p400.mean() - p100.mean()),
            "pearson_r_p100_p400": float(np.corrcoef(p100, p400)[0, 1]),
            "mean_abs_p400_minus_p100": float(np.abs(p400 - p100).mean()),
            "n_items_p100_eq_0": int((c100 == 0).sum()),
            "n_items_p100_eq_1": int((c100 == n_s).sum()),
            "n_items_p400_eq_0": int((c400 == 0).sum()),
            "n_items_p400_eq_1": int((c400 == n_s).sum()),
            "expected_discordance_fraction": exp_frac,
            "expected_discordance_count": exp_frac * n_items,
            "expected_discordance_bootstrap_ci95": pct(exp_b),
            "expected_discordance_bootstrap_sd": float(exp_b.std(ddof=1)),
            "observed_bootstrap_ci95": pct(obs_b),
            "observed_minus_expected_fraction": obs_frac - exp_frac,
            "observed_minus_expected_count": (obs_frac - exp_frac) * n_items,
            "observed_minus_expected_bootstrap_ci95": pct(diff_b),
            "observed_minus_expected_bootstrap_sd": float(diff_b.std(ddof=1)),
            "bootstrap_draws": BOOT_DRAWS,
            "bootstrap_seed": rng_seed,
            "bootstrap_one_sided_p_observed_gt_expected": float((diff_b <= 0).mean()),
            "bootstrap_frac_draws_diff_gt_0": float((diff_b > 0).mean()),
            "mc_null_plugin": {
                "draws": MC_DRAWS,
                "seed": rng_seed + 1,
                "null_mean_count": float(null_counts.mean()),
                "null_sd_count": float(null_counts.std(ddof=1)),
                "null_ci95_count": pct(null_counts.astype(float)),
                "n_draws_ge_observed": ge,
                "p_one_sided_observed_ge_null": (ge + 1) / (MC_DRAWS + 1),
            },
            "mc_null_posterior_propagated": {
                "draws": MC_DRAWS,
                "seed": rng_seed + 2,
                "prior": "Jeffreys Beta(c+0.5, n-c+0.5) per item per endpoint",
                "null_mean_count": float(null_pp.mean()),
                "null_sd_count": float(null_pp.std(ddof=1)),
                "null_ci95_count": pct(null_pp.astype(float)),
                "n_draws_ge_observed": ge_pp,
                "p_one_sided_observed_ge_null": (ge_pp + 1) / (MC_DRAWS + 1),
            },
        }

    # single-endpoint reference variants (the prior agent's assumption, and its mirror)
    p100 = c100 / n_s
    p400 = c400 / n_s
    out["single_endpoint_reference_variants"] = {
        "p100_at_both_ends_fraction": float(expected_discordance(p100, p100).mean()),
        "p400_at_both_ends_fraction": float(expected_discordance(p400, p400).mean()),
        "note": (
            "p100_at_both_ends reproduces the prior REFERENCE figure recorded in "
            "reports/m5c_turnover_v1.json noise_reference_not_a_test."
        ),
    }
    out["metric"] = label

    # ---- direction of the result, decided from the numbers above ----
    a = out["plugin_mle"]
    lo, hi = a["observed_minus_expected_bootstrap_ci95"]
    p_mc = a["mc_null_plugin"]["p_one_sided_observed_ge_null"]
    p_pp = a["mc_null_posterior_propagated"]["p_one_sided_observed_ge_null"]
    if lo > 0 and p_mc < 0.05:
        direction = "observed_exceeds_expected"
    elif hi < 0:
        direction = "observed_below_expected"
    elif lo <= 0 <= hi:
        direction = "not_distinguishable"
    else:
        direction = "mixed_bootstrap_and_monte_carlo_disagree"
    out["direction_of_result"] = {
        "verdict": direction,
        "observed_fraction": obs_frac,
        "expected_fraction_plugin": a["expected_discordance_fraction"],
        "difference": a["observed_minus_expected_fraction"],
        "difference_bootstrap_ci95": [lo, hi],
        "p_one_sided_plugin_mc": p_mc,
        "p_one_sided_posterior_propagated_mc": p_pp,
        "expected_fraction_jeffreys": out["jeffreys"]["expected_discordance_fraction"],
        "licensed_statement": (
            "The TOTAL turnover between step 100 and step 400 exceeds what independent "
            "per-item temperature-1.0 draws at each endpoint's own rate would produce."
            if direction == "observed_exceeds_expected"
            else (
                "The TOTAL turnover between step 100 and step 400 is NOT shown to exceed what "
                "independent per-item temperature-1.0 draws at each endpoint's own rate would "
                "produce. The turnover COUNT is therefore consistent with per-item stochastic "
                "instability at this null, and a claim of hidden churn cannot rest on the "
                "turnover magnitude. A claim about WHICH items move is a separate quantity, "
                "measured in reports/m5c_lost_item_forensics_v1.json, and is not affected by "
                "this result: per-item noise would REDUCE cross-checkpoint agreement of the "
                "LOST sets, not manufacture it."
                if direction in {"not_distinguishable", "observed_below_expected"}
                else "The bootstrap CI on the difference and the Monte-Carlo count test "
                "disagree; no single directional statement is licensed."
            )
        ),
        "not_licensed": (
            "This does NOT measure the greedy harness's replicate determinism. Every geo3k "
            "greedy eval is single-pass temperature-0.0 decoding; a greedy replicate floor is "
            "a separate measurement (Task A)."
        ),
    }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--step400-run", required=True, type=Path)
    ap.add_argument("--step100-repro-run", type=Path)
    ap.add_argument(
        "--out-json",
        type=Path,
        default=ROOT / "reports/m5c_expected_discordance_null_v1.json",
        help="output path; override only for smoke tests",
    )
    args = ap.parse_args()

    s400_dir = args.step400_run if args.step400_run.is_absolute() else ROOT / args.step400_run
    repro_dir = None
    if args.step100_repro_run:
        repro_dir = (
            args.step100_repro_run
            if args.step100_repro_run.is_absolute()
            else ROOT / args.step100_repro_run
        )

    # ---- substrate: greedy labels ----
    sub: dict[str, dict] = {}
    for line in SUBSTRATE.open(encoding="utf-8"):
        d = json.loads(line)
        sub[d["item_key"]] = d
    keys = sorted(sub, key=lambda k: int(k.split(":")[1]))
    n_items = len(keys)

    s100 = load_test_rows(S100_RESCORE / "per_item.jsonl")
    s100_raw = load_test_rows(S100_GUARDED / "per_item.jsonl")
    s400 = load_test_rows(s400_dir / "per_item.jsonl")
    if not (set(s100) == set(s400) == set(sub) == set(s100_raw)):
        raise ValueError("item-key sets differ across sources")

    counts100 = sampled_counts(s100, keys)
    counts400 = sampled_counts(s400, keys)
    n_s = counts100["n"]
    if not np.array_equal(n_s, counts400["n"]):
        raise ValueError("sample counts differ between endpoints")

    obs_len = np.asarray(
        [1.0 if sub[k]["acc_final_step100"] != sub[k]["acc_final_step400"] else 0.0 for k in keys]
    )
    obs_str = np.asarray(
        [1.0 if sub[k]["acc_strict_step100"] != sub[k]["acc_strict_step400"] else 0.0 for k in keys]
    )

    results = {
        "acc_final_lenient": analyse(
            "acc_final (lenient, I7)",
            counts100["c_lenient"], counts400["c_lenient"], n_s, obs_len, SEED,
        ),
        "acc_strict_contract": analyse(
            "acc_strict (contract-strict, I7)",
            counts100["c_strict"], counts400["c_strict"], n_s, obs_str, SEED,
        ),
    }

    # ---- checks ----
    m100 = json.loads((S100_RESCORE / "run_manifest.json").read_text())
    m100g = json.loads((S100_GUARDED / "run_manifest.json").read_text())
    m400 = json.loads((s400_dir / "run_manifest.json").read_text())

    checks: dict[str, Any] = {
        "substrate_rows": n_items,
        "item_key_sets_identical": True,
        "samples_per_item_step100": sorted({int(x) for x in counts100["n"].tolist()}),
        "samples_per_item_step400": sorted({int(x) for x in counts400["n"].tolist()}),
        "step100_greedy_label_matches_substrate_acc_final": sum(
            1 for k in keys if bool(s100[k]["greedy_correct"]) == bool(sub[k]["acc_final_step100"])
        ),
        "step100_greedy_label_matches_substrate_acc_strict": sum(
            1 for k in keys
            if bool(s100[k]["greedy_acc_strict"]) == bool(sub[k]["acc_strict_step100"])
        ),
        "step400_sampledrun_greedy_matches_substrate_acc_final": sum(
            1 for k in keys if bool(s400[k]["greedy_correct"]) == bool(sub[k]["acc_final_step400"])
        ),
        "step400_sampledrun_greedy_matches_substrate_acc_strict": sum(
            1 for k in keys
            if bool(s400[k]["greedy_acc_strict"]) == bool(sub[k]["acc_strict_step400"])
        ),
        "step100_rescore_vs_guarded_sample_correct_identical": sum(
            1 for k in keys if s100[k]["sample_correct"] == s100_raw[k]["sample_correct"]
        ),
        "sampled_rows_correct_but_not_contract_valid_step100": counts100[
            "n_sampled_rows_correct_but_not_contract_valid"
        ],
        "sampled_rows_correct_but_not_contract_valid_step400": counts400[
            "n_sampled_rows_correct_but_not_contract_valid"
        ],
        "strict_equals_lenient_sampled_counts_step100": bool(
            np.array_equal(counts100["c_lenient"], counts100["c_strict"])
        ),
        "strict_equals_lenient_sampled_counts_step400": bool(
            np.array_equal(counts400["c_lenient"], counts400["c_strict"])
        ),
        "strict_equals_lenient_observed_greedy_discordance": bool(np.array_equal(obs_len, obs_str)),
        "decoding_settings_match_between_endpoints": (
            m100["decoding"]["sampled"] == m400["decoding"]["sampled"]
            and m100["decoding"]["seed"] == m400["decoding"]["seed"]
            and m100["decoding"]["max_tokens"] == m400["decoding"]["max_tokens"]
            and m100["sample_count"] == m400["sample_count"]
            and m100["sample_temperature"] == m400["sample_temperature"]
        ),
        "prompt_contract_sha256_match": (
            m100["prompt_contract_sha256"] == m400["prompt_contract_sha256"]
        ),
        "source_manifest_sha256_match": (
            m100["source_manifest_sha256"] == m400["source_manifest_sha256"]
        ),
        "format_prompt_sha256_match": m100["format_prompt_sha256"] == m400["format_prompt_sha256"],
        "parser_version_match": m100["parser_version"] == m400["parser_version"],
        "scoring_mode_match": m100["scoring_mode"] == m400["scoring_mode"],
        "step400_run_status": m400["status"],
        "step400_run_exit_code": m400.get("exit_code"),
        "turnover_report_observed_discordance": json.loads(TURNOVER.read_text())["transitions"][
            "100->400|acc_final"
        ]["discordant_pairs"],
    }

    # step-100 reproduction cell (validates the --splits test deviation)
    repro_block: dict[str, Any] = {"present": False}
    if repro_dir is not None and (repro_dir / "per_item.jsonl").exists():
        rp = load_test_rows(repro_dir / "per_item.jsonl")
        mrep = json.loads((repro_dir / "run_manifest.json").read_text())
        if set(rp) == set(keys):
            crep = sampled_counts(rp, keys)
            ident = sum(1 for k in keys if rp[k]["sample_correct"] == s100[k]["sample_correct"])
            repro_block = {
                "present": True,
                "run_id": mrep["run_id"],
                "run_dir": str(repro_dir.relative_to(ROOT)),
                "status": mrep["status"],
                "exit_code": mrep.get("exit_code"),
                "rows_test": len(rp),
                "items_with_identical_sample_correct_vector_vs_registered_step100": ident,
                "items_with_byte_identical_greedy_response": sum(
                    1 for k in keys if rp[k]["greedy_response"] == s100_raw[k]["greedy_response"]
                ),
                "items_with_byte_identical_all_16_sampled_responses": sum(
                    1 for k in keys
                    if rp[k]["sampled_responses"] == s100_raw[k]["sampled_responses"]
                ),
                "items_total": n_items,
                "sum_abs_count_difference": int(
                    np.abs(crep["c_lenient"] - counts100["c_lenient"]).sum()
                ),
                "mean_p_i_repro": float((crep["c_lenient"] / crep["n"]).mean()),
                "mean_p_i_registered": float((counts100["c_lenient"] / n_s).mean()),
                "greedy_matches_substrate_acc_final": sum(
                    1 for k in keys
                    if bool(rp[k]["greedy_correct"]) == bool(sub[k]["acc_final_step100"])
                ),
                "expected_discordance_using_repro_p100_and_step400": float(
                    expected_discordance(
                        crep["c_lenient"] / crep["n"], counts400["c_lenient"] / n_s
                    ).mean()
                ),
                "purpose": (
                    "cross-check that running the registered sampled protocol with "
                    "--splits test (instead of --splits train test) reproduces the "
                    "registered step-100 test-row sampled outcomes"
                ),
            }
        else:
            repro_block = {"present": True, "usable": False, "reason": "item-key set mismatch"}
    else:
        repro_block = {
            "present": False,
            "reason": "step-100 reproduction cell not supplied or not complete",
        }

    payload = {
        "schema_version": SCHEMA,
        "generated_utc": subprocess.run(
            ["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True, check=True
        ).stdout.strip(),
        "git_hash": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip(),
        "question": (
            "Does the OBSERVED greedy discordance between geo3k step 100 and step 400 "
            "(137/601) exceed what independent per-item stochastic draws at each "
            "endpoint's own sampled success rate would produce?"
        ),
        "item_key_definition": "(split, row_index) on the Geometry3K test split",
        "null_definition": (
            "E[disc] = mean_i [ p_i(100)(1-p_i(400)) + (1-p_i(100)) p_i(400) ], with "
            "p_i estimated separately at EACH endpoint from 16 temperature-1.0 samples."
        ),
        "sampled_protocol_step100_verbatim": {
            "run_id": m100g["run_id"],
            "run_dir_registered_generation": str(S100_GUARDED.relative_to(ROOT)),
            "run_dir_guarded_rescore_used_for_p_i": str(S100_RESCORE.relative_to(ROOT)),
            "decoding": m100g["decoding"],
            "sample_count": m100g["sample_count"],
            "sample_temperature": m100g["sample_temperature"],
            "seed": m100g["seed"],
            "max_tokens": m100g["max_tokens"],
            "group_size": m100g["group_size"],
            "format_weight": m100g["format_weight"],
            "symbolic_grader_timeout_seconds": m100g["symbolic_grader_timeout_seconds"],
            "model_revision": m100g["model_revision"],
            "prompt_contract_sha256": m100g["prompt_contract_sha256"],
            "source_manifest_sha256": m100g["source_manifest_sha256"],
            "parser_version": m100g["parser_version"],
            "scoring_mode": m100g["scoring_mode"],
            "command": m100g["command"],
            "per_item_sha256": sha256(S100_RESCORE / "per_item.jsonl"),
        },
        "sampled_protocol_step400_verbatim": {
            "run_id": m400["run_id"],
            "run_dir": str(s400_dir.relative_to(ROOT)),
            "decoding": m400["decoding"],
            "sample_count": m400["sample_count"],
            "sample_temperature": m400["sample_temperature"],
            "seed": m400["seed"],
            "max_tokens": m400["max_tokens"],
            "group_size": m400["group_size"],
            "format_weight": m400["format_weight"],
            "symbolic_grader_timeout_seconds": m400["symbolic_grader_timeout_seconds"],
            "model_revision": m400["model_revision"],
            "prompt_contract_sha256": m400["prompt_contract_sha256"],
            "source_manifest_sha256": m400["source_manifest_sha256"],
            "parser_version": m400["parser_version"],
            "scoring_mode": m400["scoring_mode"],
            "node": m400["node"],
            "gpu_allocation": m400["gpu_allocation"],
            "git_hash": m400["git_hash"],
            "command": m400["command"],
            "deviations": m400["deviations"],
            "per_item_sha256": sha256(s400_dir / "per_item.jsonl"),
        },
        "step100_reproduction_cell": repro_block,
        "greedy_source": {
            "substrate": "reports/m5c_item_substrate_v1.jsonl",
            "substrate_sha256": sha256(SUBSTRATE),
            "greedy_decoding": "temperature 0.0, top_p 1.0, n 1, seed 20260710, max_tokens 2048",
        },
        "prior_reference_figure_reproduced": {
            "value_in_m5c_turnover_v1": 0.21327735024958402,
            "recomputed_here_from_step100_p_i_at_both_ends": results["acc_final_lenient"][
                "single_endpoint_reference_variants"
            ]["p100_at_both_ends_fraction"],
        },
        "greedy_replicate_floor_cross_reference": (
            {
                "source": "reports/m5c_noise_floor_replicate_v1.json",
                "source_sha256": sha256(TASK_A_FLOOR),
                "measured_floor_is_zero": json.loads(TASK_A_FLOOR.read_text())["readout"][
                    "measured_floor_is_zero"
                ],
                "max_replicate_discordance_count_across_cells": json.loads(
                    TASK_A_FLOOR.read_text()
                )["readout"]["max_replicate_discordance_count_across_cells"],
                "response_text_byte_identical_across_all_pairs": json.loads(
                    TASK_A_FLOOR.read_text()
                )["readout"]["response_text_byte_identical_across_all_pairs"],
                "relation_to_this_null": (
                    "These are two different bars. The greedy replicate floor measured in Task A "
                    "is the HARNESS floor: re-running the same checkpoint gives 0/601 discordance "
                    "and byte-identical responses, so none of the observed 137 is measurement "
                    "noise. The null computed HERE is a strictly more permissive bar: it asks "
                    "whether 137 exceeds the per-item FRAGILITY implied by each checkpoint's own "
                    "temperature-1.0 output distribution. A result that clears the Task A floor "
                    "but not this null means the turnover is fully reproducible yet no larger "
                    "than each endpoint's own decoding-level answer instability."
                ),
            }
            if TASK_A_FLOOR.exists()
            else {"source": "reports/m5c_noise_floor_replicate_v1.json", "present": False}
        ),
        "results": results,
        "checks": checks,
        "caveats": [
            "Sampled variability at temperature 1.0 is NOT identical to greedy replicate "
            "variability. This null bounds STOCHASTIC INSTABILITY of each checkpoint under "
            "temperature decoding; it does not measure the greedy harness's determinism.",
            "Temperature 1.0 is strictly noisier than temperature 0.0, so this null is an "
            "UPPER bound on the per-item stochastic churn a greedy comparison could inherit "
            "from decoding randomness. A comparison that fails to clear it does not clear a "
            "greedy-replicate noise floor either.",
            "The sampled protocol is itself seeded (seed 20260710 on SamplingParams), and the "
            "step-100 reproduction cell confirms it is byte-reproducible. So p_i is estimated "
            "from ONE fixed seeded set of 16 samples per item per endpoint, not from a fresh "
            "random draw. A different seed would give a different 16-sample set and a slightly "
            "different p_i; that seed-level variability is NOT in the reported CIs.",
            "p_i is estimated from only 16 samples per item per endpoint; the posterior-"
            "propagated Monte-Carlo null carries that estimation error, the plug-in null "
            "does not.",
            "The null treats the two endpoints as independent draws. Any true shared item "
            "difficulty structure is already inside p_i(100) and p_i(400); the independence "
            "assumption concerns only the residual draw, which is exactly the null being tested.",
            "The step-400 sampled cell was run with --splits test instead of the registered "
            "--splits train test. Test rows begin at global row index 1288 in the registered "
            "run and 1288 % batch_size(4) == 0, so per-item 4-row batch grouping is unchanged; "
            "the step-100 reproduction cell tests this empirically.",
        ],
    }

    out_json = args.out_json
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print("wrote", out_json)
    print(json.dumps(results["acc_final_lenient"]["plugin_mle"], indent=2)[:2000])


if __name__ == "__main__":
    main()
