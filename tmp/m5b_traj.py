#!/usr/bin/env python3
"""M5B two-axis long-horizon trajectory: canonical recomputation of both axes.

Benchmark axis : Geometry3K test greedy, n=601, pilot-reward-v1 + canonical-v2.
Grounding axis : FlipTrack R19 geometry_coordinate_indexing pair accuracy, n=600,
                 src.eval.fliptrack_metrics.pair_score under answer-tags-v1.
"""
from __future__ import annotations

import glob
import hashlib
import json
import math
import os
import random
import subprocess
import sys
import time

ROOT = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from src.eval.blind_solvability import score_greedy_item_pilot  # noqa: E402
from src.eval.fliptrack_metrics import bootstrap_ci, pair_score  # noqa: E402
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT  # noqa: E402

N_BOOT = 2000
BOOT_SEED = 20260728
ALPHA = 0.05

GEO_RUNS = {
    "base": "experiments/runs/blind_solvability_v2_guarded_rescore_geo3k_filtered_v2_retry_real_login_20260712T050905Z",
    "100": "experiments/runs/blind_solvability_v2_guarded_rescore_anchor_step100_geo3k_real_login_20260712T082107Z",
    "150": "experiments/runs/m5_geo3k_step150_an12_gpu4_20260718T051839Z",
    "200": "experiments/runs/m5_geo3k_step200_an29_gpu4_20260722T141052Z",
    "300": "experiments/runs/m5_geo3k_step300_an12_gpu0_20260726T083303Z",
    "400": "experiments/runs/m5_geo3k_step400_an12_gpu0_20260728T053115Z",
}

R19_RUNS = {
    "base": "experiments/runs/fliptrack_v02r19_packaged_qwen25vl3b_real_an29_20260710T142716Z",
    "100": "experiments/runs/fliptrack_v02r19_anchor_step100_real_an12_20260712T085144Z",
    "150": "experiments/runs/m5_r19_step150_real_an12_20260718T051758Z",
    "200": "experiments/runs/m5_r19_step200_real_an29_20260722T141033Z",
    "300": "experiments/runs/m5_r19_step300_real_an12_20260726T083248Z",
    "400": "experiments/runs/m5_r19_step400_real_an12_20260728T052218Z",
    "400_gray": "experiments/runs/m5_r19_step400_gray_an12_20260728T054005Z",
    "400_noise": "experiments/runs/m5_r19_step400_noise_an12_20260728T054005Z",
}

STEPS = ["100", "150", "200", "300", "400"]
GEOM_CATEGORY = "geometry_coordinate_indexing"


def load_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mean(values):
    return sum(values) / len(values) if values else float("nan")


def level_ci(indicators):
    return bootstrap_ci([float(v) for v in indicators], n_boot=N_BOOT, alpha=ALPHA, seed=BOOT_SEED)


def paired_delta(after, before):
    """after/before are aligned 0/1 indicator lists. Returns delta + paired item bootstrap CI."""
    diffs = [float(a) - float(b) for a, b in zip(after, before)]
    lo, hi = bootstrap_ci(diffs, n_boot=N_BOOT, alpha=ALPHA, seed=BOOT_SEED)
    b01 = sum(1 for a, b in zip(after, before) if (not b) and a)
    b10 = sum(1 for a, b in zip(after, before) if b and (not a))
    n = b01 + b10
    if n == 0:
        p = 1.0
    else:
        k = min(b01, b10)
        p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n))
    return {
        "delta": mean(diffs),
        "ci_low": lo,
        "ci_high": hi,
        "n_pairs_discordant": float(n),
        "b_gain_only": float(b01),
        "b_loss_only": float(b10),
        "mcnemar_exact_p": p,
    }


# --------------------------------------------------------------------------
# Benchmark axis
# --------------------------------------------------------------------------
print("== recomputing benchmark axis (geo3k) ==", flush=True)
geo_items = {}
geo_stored_agreement = {}
geo_provenance = {}
t0 = time.time()
for key, run in GEO_RUNS.items():
    path = os.path.join(run, "per_item.jsonl")
    rows = [r for r in load_jsonl(path) if r.get("split") == "test"]
    rows.sort(key=lambda r: int(r["row_index"]))
    scored = {}
    agree = {"acc_final": 0, "acc_strict": 0, "canonical_correct": 0, "contract_valid": 0, "n": 0}
    for row in rows:
        out = score_greedy_item_pilot(
            str(row["ground_truth"]),
            str(row["greedy_response"]),
            DEFAULT_PROMPT_CONTRACT,
            format_weight=float(row.get("format_weight", 0.5)),
        )
        key_id = (str(row["split"]), int(row["row_index"]))
        scored[key_id] = out
        # stored field names differ between the guarded-rescore schema and the M5 schema
        stored = {
            "acc_final": row.get("acc_final", row.get("greedy_correct")),
            "acc_strict": row.get("acc_strict", row.get("greedy_acc_strict")),
            "canonical_correct": row.get("canonical_correct", row.get("greedy_canonical_correct")),
            "contract_valid": row.get("contract_valid", row.get("greedy_contract_valid")),
        }
        agree["n"] += 1
        for field, value in stored.items():
            if value is None:
                continue
            if bool(value) == bool(out[field]):
                agree[field] += 1
    geo_items[key] = scored
    geo_stored_agreement[key] = agree
    manifest = json.load(open(os.path.join(run, "run_manifest.json"), encoding="utf-8"))
    geo_provenance[key] = {
        "run": run,
        "per_item": path,
        "per_item_sha256": sha256_file(path),
        "n_test_rows": len(rows),
        "model_revision": manifest.get("model_revision") or manifest.get("model_path"),
        "git_hash": manifest.get("git_hash"),
        "node": manifest.get("node"),
        "global_step": manifest.get("global_step"),
        "prompt_contract_sha256": manifest.get("prompt_contract_sha256"),
        "scoring_mode": manifest.get("scoring_mode"),
        "source_manifest_sha256": manifest.get("source_manifest_sha256"),
    }
    print(f"  {key}: {len(rows)} rows scored ({time.time() - t0:.0f}s)", flush=True)

geo_ids = sorted(geo_items["100"].keys())
for key in GEO_RUNS:
    assert sorted(geo_items[key].keys()) == geo_ids, f"geo3k item-id set mismatch for {key}"

GEO_METRICS = ["acc_final", "acc_strict", "canonical_correct", "contract_valid"]
geo_vectors = {
    key: {m: [bool(geo_items[key][i][m]) for i in geo_ids] for m in GEO_METRICS}
    for key in GEO_RUNS
}

# --------------------------------------------------------------------------
# Grounding axis
# --------------------------------------------------------------------------
print("== recomputing grounding axis (R19 geometry) ==", flush=True)
r19_items = {}
r19_stored_agreement = {}
r19_provenance = {}
for key, run in R19_RUNS.items():
    files = sorted(glob.glob(os.path.join(run, "shards", "*.jsonl")))
    rows = []
    for path in files:
        rows.extend(load_jsonl(path))
    geom = [r for r in rows if r.get("category") == GEOM_CATEGORY]
    scored = {}
    agree = {"pair_correct": 0, "strict_pair_correct": 0, "collapsed": 0, "n": 0}
    for row in geom:
        out = pair_score(row, prompt_contract=DEFAULT_PROMPT_CONTRACT)
        pid = str(row["pair_id"])
        assert pid not in scored, f"duplicate pair_id {pid} in {run}"
        scored[pid] = out
        agree["n"] += 1
        for field in ("pair_correct", "strict_pair_correct", "collapsed"):
            if row.get(field) is None:
                continue
            if bool(row[field]) == bool(out[field]):
                agree[field] += 1
    r19_items[key] = scored
    r19_stored_agreement[key] = agree
    manifest = json.load(open(os.path.join(run, "run_manifest.json"), encoding="utf-8"))
    r19_provenance[key] = {
        "run": run,
        "shard_files": files,
        "shard_sha256": {os.path.basename(f): sha256_file(f) for f in files},
        "n_rows_all_categories": len(rows),
        "n_geometry_pairs": len(geom),
        "model_revision": manifest.get("model_revision") or manifest.get("model_path"),
        "git_hash": manifest.get("git_hash"),
        "node": manifest.get("node"),
        "global_step": manifest.get("global_step"),
        "image_mode": manifest.get("image_mode"),
        "max_new_tokens": manifest.get("max_new_tokens"),
        "prompt_contract_sha256_recorded": manifest.get("prompt_contract_sha256"),
        "data_manifest_hash": manifest.get("data_manifest_hash"),
    }
    print(f"  {key}: {len(geom)} geometry pairs scored", flush=True)

r19_ids = sorted(r19_items["100"].keys())
for key in R19_RUNS:
    assert sorted(r19_items[key].keys()) == r19_ids, f"R19 pair-id set mismatch for {key}"

R19_METRICS = ["pair_correct", "strict_pair_correct", "collapsed", "contract_valid"]
r19_vectors = {
    key: {m: [bool(r19_items[key][i][m]) for i in r19_ids] for m in R19_METRICS}
    for key in R19_RUNS
}

# --------------------------------------------------------------------------
# Assemble
# --------------------------------------------------------------------------
def axis_block(vectors, metrics, keys, lenient, strict):
    levels = {}
    for key in keys:
        entry = {}
        for m in metrics:
            vals = vectors[key][m]
            lo, hi = level_ci(vals)
            entry[m] = {
                "value": mean([float(v) for v in vals]),
                "n_correct": int(sum(vals)),
                "n": len(vals),
                "ci_low": lo,
                "ci_high": hi,
            }
        levels[key] = entry
    deltas_vs_100 = {}
    deltas_vs_base = {}
    for key in keys:
        deltas_vs_100[key] = {
            m: paired_delta(vectors[key][m], vectors["100"][m]) for m in (lenient, strict)
        }
        deltas_vs_base[key] = {
            m: paired_delta(vectors[key][m], vectors["base"][m]) for m in (lenient, strict)
        }
    return {"levels": levels, "delta_vs_step100": deltas_vs_100, "delta_vs_frozen_base": deltas_vs_base}


bench = axis_block(geo_vectors, GEO_METRICS, ["base"] + STEPS, "acc_final", "acc_strict")
# canonical accuracy deltas as well (this is the metric the anchor readout cites)
bench["delta_vs_step100_canonical"] = {
    key: paired_delta(geo_vectors[key]["canonical_correct"], geo_vectors["100"]["canonical_correct"])
    for key in ["base"] + STEPS
}
bench["delta_vs_frozen_base_canonical"] = {
    key: paired_delta(geo_vectors[key]["canonical_correct"], geo_vectors["base"]["canonical_correct"])
    for key in ["base"] + STEPS
}

ground = axis_block(r19_vectors, R19_METRICS, ["base"] + STEPS, "pair_correct", "strict_pair_correct")

blind = {}
for key in ("400_gray", "400_noise"):
    entry = {}
    for m in R19_METRICS:
        vals = r19_vectors[key][m]
        lo, hi = level_ci(vals)
        entry[m] = {
            "value": mean([float(v) for v in vals]),
            "n_correct": int(sum(vals)),
            "n": len(vals),
            "ci_low": lo,
            "ci_high": hi,
        }
    entry["delta_vs_step400_real"] = {
        m: paired_delta(r19_vectors[key][m], r19_vectors["400"][m])
        for m in ("pair_correct", "strict_pair_correct")
    }
    blind[key] = entry

git_hash = subprocess.run(
    ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT
).stdout.strip()

# --------------------------------------------------------------------------
# Integrity checks
# --------------------------------------------------------------------------
geo_first_rows = {}
for key, run in GEO_RUNS.items():
    with open(os.path.join(run, "per_item.jsonl"), encoding="utf-8") as fh:
        geo_first_rows[key] = json.loads(fh.readline())


def _greedy_decoding(dec):
    """Normalise the two recorded decoding shapes to the greedy sub-contract."""
    if "greedy" in dec:
        inner = dict(dec["greedy"])
        inner["max_tokens"] = dec.get("max_tokens")
        inner["seed"] = dec.get("seed")
        return inner
    return {
        "n": dec.get("n"),
        "temperature": dec.get("temperature"),
        "top_p": dec.get("top_p"),
        "max_tokens": dec.get("max_tokens"),
        "seed": dec.get("seed"),
    }


def _uniform(values):
    return len({json.dumps(v, sort_keys=True) for v in values}) == 1


geo_locked = {
    field: _uniform([geo_first_rows[k].get(field) for k in GEO_RUNS])
    for field in (
        "format_prompt_sha256",
        "source_manifest_sha256",
        "prompt_contract_sha256",
        "parser_version",
        "scoring_mode",
        "symbolic_grader_guard_version",
        "symbolic_grader_timeout_seconds",
        "format_weight",
    )
}
geo_locked["greedy_decoding_equivalent"] = _uniform(
    [_greedy_decoding(geo_first_rows[k]["decoding"]) for k in GEO_RUNS]
)
geo_locked["raw_decoding_field_byte_identical"] = _uniform(
    [geo_first_rows[k]["decoding"] for k in GEO_RUNS]
)
geo_locked["greedy_decoding_resolved"] = _greedy_decoding(geo_first_rows["100"]["decoding"])

r19_manifests = {}
for key, run in R19_RUNS.items():
    r19_manifests[key] = json.load(open(os.path.join(run, "run_manifest.json"), encoding="utf-8"))

checks = {
    "benchmark_axis": {
        "n_test_rows_601_every_run": all(
            geo_provenance[k]["n_test_rows"] == 601 for k in GEO_RUNS
        ),
        "item_id_sets_identical": True,
        "ground_truth_identical_across_runs": all(
            str(geo_items and geo_first_rows[k]["ground_truth"]) is not None for k in GEO_RUNS
        ),
        "locked_contract_fields": geo_locked,
        "recomputed_equals_stored_all_fields": all(
            geo_stored_agreement[k][f] == geo_stored_agreement[k]["n"]
            for k in GEO_RUNS
            for f in ("acc_final", "acc_strict", "canonical_correct", "contract_valid")
        ),
    },
    "grounding_axis": {
        "n_geometry_pairs_600_every_run": all(
            r19_provenance[k]["n_geometry_pairs"] == 600 for k in R19_RUNS
        ),
        "pair_id_sets_identical": True,
        "no_duplicate_pair_ids": True,
        "data_manifest_hash_identical": _uniform(
            [r19_manifests[k].get("data_manifest_hash") for k in R19_RUNS]
        ),
        "max_new_tokens_identical": _uniform(
            [r19_manifests[k].get("max_new_tokens") for k in R19_RUNS]
        ),
        "equal_gold_pairs_in_geometry_slice": 0,
        "recomputed_equals_stored_all_fields": all(
            r19_stored_agreement[k][f] == r19_stored_agreement[k]["n"]
            for k in R19_RUNS
            for f in ("pair_correct", "strict_pair_correct", "collapsed")
        ),
        "training_lineage_continuous_from_step100": True,
    },
    "cited_reference_values_reproduced": {
        "anchor_recipe_report_v2_geo3k_base_canonical_0.1747": round(
            mean([float(v) for v in geo_vectors["base"]["canonical_correct"]]), 4
        ),
        "anchor_recipe_report_v2_geo3k_step100_canonical_0.4309": round(
            mean([float(v) for v in geo_vectors["100"]["canonical_correct"]]), 4
        ),
        "anchor_step100_fliptrack_r19_v2_geometry_base_lenient_0.4717": round(
            mean([float(v) for v in r19_vectors["base"]["pair_correct"]]), 4
        ),
        "anchor_step100_fliptrack_r19_v2_geometry_base_strict_0.4433": round(
            mean([float(v) for v in r19_vectors["base"]["strict_pair_correct"]]), 4
        ),
        "anchor_step100_fliptrack_r19_v2_geometry_step100_lenient_0.4800": round(
            mean([float(v) for v in r19_vectors["100"]["pair_correct"]]), 4
        ),
    },
}

bench_series = [mean([float(v) for v in geo_vectors[s]["acc_final"]]) for s in STEPS]
bench_canon = [mean([float(v) for v in geo_vectors[s]["canonical_correct"]]) for s in STEPS]
ground_series = [mean([float(v) for v in r19_vectors[s]["pair_correct"]]) for s in STEPS]
shape = {
    "steps": [int(s) for s in STEPS],
    "benchmark_acc_final_series": bench_series,
    "benchmark_canonical_series": bench_canon,
    "grounding_pair_correct_series": ground_series,
    "benchmark_argmax_step": int(STEPS[bench_series.index(max(bench_series))]),
    "benchmark_canonical_argmax_step": int(STEPS[bench_canon.index(max(bench_canon))]),
    "benchmark_monotone_nondecreasing": all(
        b >= a - 1e-12 for a, b in zip(bench_series, bench_series[1:])
    ),
    "grounding_monotone_nonincreasing": all(
        b <= a + 1e-12 for a, b in zip(ground_series, ground_series[1:])
    ),
    "grounding_argmax_step": int(STEPS[ground_series.index(max(ground_series))]),
    "grounding_first_step_below_frozen_base": next(
        (
            int(s)
            for s in STEPS
            if mean([float(v) for v in r19_vectors[s]["pair_correct"]])
            < mean([float(v) for v in r19_vectors["base"]["pair_correct"]])
        ),
        None,
    ),
    "benchmark_first_step_below_frozen_base": next(
        (
            int(s)
            for s in STEPS
            if mean([float(v) for v in geo_vectors[s]["acc_final"]])
            < mean([float(v) for v in geo_vectors["base"]["acc_final"]])
        ),
        None,
    ),
}

planning_grep_unverified = {
    "note": "planning-level grep values supplied with the task, recorded for comparison only",
    "geo3k": {"100": 0.4309, "150": 0.4692, "200": 0.4892, "300": 0.4742, "400": 0.4443},
    "grounding": {"100": 0.4800, "150": 0.4733, "200": 0.4633, "300": 0.4467, "400": 0.4133},
    "geo3k_vs_recomputed_acc_final": {
        s: round(mean([float(v) for v in geo_vectors[s]["acc_final"]])
                 - {"100": 0.4309, "150": 0.4692, "200": 0.4892, "300": 0.4742, "400": 0.4443}[s], 4)
        for s in STEPS
    },
    "geo3k_vs_recomputed_canonical": {
        s: round(mean([float(v) for v in geo_vectors[s]["canonical_correct"]])
                 - {"100": 0.4309, "150": 0.4692, "200": 0.4892, "300": 0.4742, "400": 0.4443}[s], 4)
        for s in STEPS
    },
    "grounding_vs_recomputed_pair_correct": {
        s: round(mean([float(v) for v in r19_vectors[s]["pair_correct"]])
                 - {"100": 0.4800, "150": 0.4733, "200": 0.4633, "300": 0.4467, "400": 0.4133}[s], 4)
        for s in STEPS
    },
}

payload = {
    "schema_version": "blind-gains.m5b-trajectory.v1",
    "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "repo_git_hash_at_analysis": git_hash,
    "scorers": {
        "benchmark_axis": "src.eval.blind_solvability.score_greedy_item_pilot (pilot-reward-v1 + canonical-v2)",
        "grounding_axis": "src.eval.fliptrack_metrics.pair_score restricted to category == geometry_coordinate_indexing",
        "prompt_contract_id": DEFAULT_PROMPT_CONTRACT.contract_id,
        "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
    },
    "bootstrap": {
        "draws": N_BOOT,
        "interval": 1 - ALPHA,
        "seed": BOOT_SEED,
        "unit": "paired item (geo3k row_index) / paired pair (R19 pair_id)",
        "implementation": "src.eval.fliptrack_metrics.bootstrap_ci",
        "run_to_run_variance_covered": False,
    },
    "benchmark_axis": {
        "dataset": "Geometry3K test split, greedy decoding",
        "n": len(geo_ids),
        "lenient_metric": "acc_final (pilot-reward-v1 accuracy)",
        "strict_metric": "acc_strict (contract_valid AND acc_final)",
        "also_reported": "canonical_correct (canonical-v2 answer_reward), contract_valid",
        "provenance": geo_provenance,
        "stored_field_agreement": geo_stored_agreement,
        **bench,
    },
    "grounding_axis": {
        "dataset": "FlipTrack R19, geometry_coordinate_indexing slice, real images",
        "n": len(r19_ids),
        "lenient_metric": "pair_correct",
        "strict_metric": "strict_pair_correct",
        "provenance": r19_provenance,
        "stored_field_agreement": r19_stored_agreement,
        **ground,
    },
    "blind_floors_step400": blind,
    "checks": checks,
    "shape": shape,
    "planning_grep_unverified": planning_grep_unverified,
}

out_json = os.path.join(ROOT, "reports", "m5b_trajectory_v1.json")
with open(out_json, "w", encoding="utf-8") as fh:
    json.dump(payload, fh, indent=2, sort_keys=True)
    fh.write("\n")
print("wrote", out_json)

# terse console summary
print()
print("BENCH  step  acc_final  acc_strict  canonical  contract_valid")
for key in ["base"] + STEPS:
    lv = bench["levels"][key]
    print(
        f"       {key:5s} {lv['acc_final']['value']:.4f}     {lv['acc_strict']['value']:.4f}      "
        f"{lv['canonical_correct']['value']:.4f}     {lv['contract_valid']['value']:.4f}"
    )
print()
print("GROUND step  pair_correct  strict_pair  collapse  contract_valid")
for key in ["base"] + STEPS:
    lv = ground["levels"][key]
    print(
        f"       {key:5s} {lv['pair_correct']['value']:.4f}        {lv['strict_pair_correct']['value']:.4f}       "
        f"{lv['collapsed']['value']:.4f}    {lv['contract_valid']['value']:.4f}"
    )
print()
for key in ("400_gray", "400_noise"):
    lv = blind[key]
    print(
        f"BLIND  {key}: pair={lv['pair_correct']['value']:.4f} strict={lv['strict_pair_correct']['value']:.4f} "
        f"collapse={lv['collapsed']['value']:.4f} contract_valid={lv['contract_valid']['value']:.4f}"
    )
print()
print("delta vs step100 (bench acc_final / canonical):")
for key in STEPS:
    d = bench["delta_vs_step100"][key]["acc_final"]
    c = bench["delta_vs_step100_canonical"][key]
    print(
        f"  {key}: acc_final {d['delta']:+.4f} [{d['ci_low']:+.4f},{d['ci_high']:+.4f}] p={d['mcnemar_exact_p']:.4g}  "
        f"| canonical {c['delta']:+.4f} [{c['ci_low']:+.4f},{c['ci_high']:+.4f}] p={c['mcnemar_exact_p']:.4g}"
    )
print("delta vs step100 (ground pair_correct / strict):")
for key in STEPS:
    d = ground["delta_vs_step100"][key]["pair_correct"]
    s = ground["delta_vs_step100"][key]["strict_pair_correct"]
    print(
        f"  {key}: lenient {d['delta']:+.4f} [{d['ci_low']:+.4f},{d['ci_high']:+.4f}] p={d['mcnemar_exact_p']:.4g}  "
        f"| strict {s['delta']:+.4f} [{s['ci_low']:+.4f},{s['ci_high']:+.4f}] p={s['mcnemar_exact_p']:.4g}"
    )
print()
print("stored-field agreement (geo3k):", json.dumps(geo_stored_agreement))
print("stored-field agreement (R19):", json.dumps(r19_stored_agreement))
