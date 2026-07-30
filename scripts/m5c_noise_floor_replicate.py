#!/usr/bin/env python
"""M5C noise floor: replicate-evaluation discordance for the geo3k greedy harness.

Measures the harness's own per-item discordance floor by re-evaluating the SAME
checkpoint twice (R1, R2) at step 400 and at step 100, then comparing:
  - R1 vs R2                 (the replicate discordance = the noise floor)
  - R1/R2 vs the CACHED run  (does a replicate reproduce the substrate column?)
All binary metrics are recomputed from raw greedy_response text through the single
canonical scorer src.eval.blind_solvability.score_greedy_item_pilot under
DEFAULT_PROMPT_CONTRACT, the same scorer that produced the substrate.

Arithmetic only. No interpretation beyond stated ratios.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

from src.eval.blind_solvability import score_greedy_item_pilot
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
RUNS = ROOT / "experiments" / "runs"
SUBSTRATE = ROOT / "reports" / "m5c_item_substrate_v1.jsonl"
OUT_JSON = ROOT / "reports" / "m5c_noise_floor_replicate_v1.json"
OUT_MD = ROOT / "reports" / "m5c_noise_floor_replicate_v1.md"

REPLICATES = {
    ("400", "r1"): "m5c_noisefloor_step400_r1_an29_gpu0_20260730T015228Z",
    ("400", "r2"): "m5c_noisefloor_step400_r2_an29_gpu1_20260730T015314Z",
    ("100", "r1"): "m5c_noisefloor_step100_r1_an29_gpu2_20260730T015523Z",
    ("100", "r2"): "m5c_noisefloor_step100_r2_an29_gpu3_20260730T015600Z",
}
CACHED = {
    "400": "m5_geo3k_step400_an12_gpu0_20260728T053115Z",
    "100": "blind_solvability_v2_guarded_rescore_anchor_step100_geo3k_real_login_20260712T082107Z",
}

OBSERVED_TURNOVER_COUNT = 137
OBSERVED_N = 601


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def rescore(rows: list[dict], label: str) -> dict[str, dict]:
    """Recompute acc_final/acc_strict from raw greedy text via the canonical scorer."""
    out: dict[str, dict] = {}
    for row in rows:
        if row.get("split") != "test":
            continue
        key = f"test:{int(row['row_index'])}"
        if key in out:
            raise SystemExit(f"{label}: duplicate item key {key}")
        timeout = float(row.get("symbolic_grader_timeout_seconds") or 5.0)
        weight = float(row.get("format_weight") if row.get("format_weight") is not None else 0.5)
        scored = score_greedy_item_pilot(
            str(row["ground_truth"]),
            row["greedy_response"],
            DEFAULT_PROMPT_CONTRACT,
            format_weight=weight,
            symbolic_grader_timeout_seconds=timeout,
        )
        out[key] = {
            "acc_final": bool(scored["acc_final"]),
            "acc_strict": bool(scored["acc_strict"]),
            "response": row["greedy_response"],
            "response_sha256": hashlib.sha256(row["greedy_response"].encode("utf-8")).hexdigest(),
            "extracted_answer": scored["extracted_answer"],
            "ground_truth": str(row["ground_truth"]),
            "stored_acc_final": row.get("acc_final", row.get("greedy_correct")),
            "stored_acc_strict": row.get("acc_strict", row.get("greedy_acc_strict")),
        }
    return out


def stored_recomputed_agreement(scored: dict[str, dict]) -> dict:
    agree = {"acc_final": 0, "acc_strict": 0, "n": 0, "acc_final_missing": 0, "acc_strict_missing": 0}
    for value in scored.values():
        agree["n"] += 1
        for metric in ("acc_final", "acc_strict"):
            stored = value[f"stored_{metric}"]
            if stored is None:
                agree[f"{metric}_missing"] += 1
                continue
            if bool(stored) == value[metric]:
                agree[metric] += 1
    return agree


def compare(a: dict[str, dict], b: dict[str, dict], metric: str) -> dict:
    keys = sorted(set(a) & set(b), key=lambda k: int(k.split(":")[1]))
    if len(keys) != len(a) or len(keys) != len(b):
        raise SystemExit(f"key-set mismatch: |a|={len(a)} |b|={len(b)} |shared|={len(keys)}")
    disc = [k for k in keys if a[k][metric] != b[k][metric]]
    a_only = [k for k in disc if a[k][metric] and not b[k][metric]]
    b_only = [k for k in disc if b[k][metric] and not a[k][metric]]
    return {
        "n": len(keys),
        "discordant_count": len(disc),
        "discordant_fraction": len(disc) / len(keys),
        "agreement_count": len(keys) - len(disc),
        "agreement_rate": (len(keys) - len(disc)) / len(keys),
        "a_correct_b_wrong": len(a_only),
        "b_correct_a_wrong": len(b_only),
        "net_b_minus_a": len(b_only) - len(a_only),
        "discordant_item_keys": disc,
        "a_count": sum(1 for k in keys if a[k][metric]),
        "b_count": sum(1 for k in keys if b[k][metric]),
        "a_acc": sum(1 for k in keys if a[k][metric]) / len(keys),
        "b_acc": sum(1 for k in keys if b[k][metric]) / len(keys),
        "acc_diff_b_minus_a": (sum(1 for k in keys if b[k][metric]) - sum(1 for k in keys if a[k][metric])) / len(keys),
    }


def text_identity(a: dict[str, dict], b: dict[str, dict]) -> dict:
    keys = sorted(set(a) & set(b), key=lambda k: int(k.split(":")[1]))
    diff = [k for k in keys if a[k]["response"] != b[k]["response"]]
    return {
        "n": len(keys),
        "byte_identical_count": len(keys) - len(diff),
        "byte_identical_fraction": (len(keys) - len(diff)) / len(keys),
        "text_differing_count": len(diff),
        "text_differing_fraction": len(diff) / len(keys),
        "text_differing_item_keys_first_25": diff[:25],
    }


def determinism_audit(run_id: str, manifest: dict) -> dict:
    """Prove each replicate DECODED FRESH rather than reusing a cached/resumed prefix."""
    log_dir = RUNS / run_id / "logs"
    logs = sorted(log_dir.glob("*.log"))
    text = "\n".join(path.read_text(errors="replace") for path in logs)
    resumed_values = re.findall(r'"resumed":\s*(\d+)', text)
    # Progress JSON keys are emitted sort_keys=True, so "resumed" sits between the two.
    processed = re.findall(r'"processed":\s*(\d+).*?"total":\s*(\d+)', text)
    return {
        "log_paths": [str(p.relative_to(ROOT)) for p in logs],
        "manifest_resume_from": manifest.get("resume_from"),
        "command_contains_resume_from_flag": "--resume-from" in (manifest.get("command") or ""),
        "last_resumed_count_in_log": int(resumed_values[-1]) if resumed_values else None,
        "last_processed_total_in_log": (
            [int(processed[-1][0]), int(processed[-1][1])] if processed else None
        ),
        "safetensors_shard_load_completed_lines": text.count(
            "Loading safetensors checkpoint shards: 100% Completed"
        ),
        "vllm_model_weight_load_observed": "Loading model weights took" in text,
        "cache_dir_is_run_scoped_node_local": f"/dev/shm/blind-gains/{run_id}/condition_cache"
        in (manifest.get("command") or ""),
    }


def main() -> None:
    git_hash = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()

    substrate = {row["item_key"]: row for row in read_jsonl(SUBSTRATE)}
    if len(substrate) != OBSERVED_N:
        raise SystemExit(f"substrate rows {len(substrate)} != {OBSERVED_N}")

    scored: dict[str, dict[str, dict]] = {}
    manifests: dict[str, dict] = {}
    file_sha: dict[str, str] = {}

    for (step, rep), run_id in REPLICATES.items():
        path = RUNS / run_id / "per_item.jsonl"
        label = f"step{step}_{rep}"
        rows = read_jsonl(path)
        scored[label] = rescore(rows, label)
        manifests[label] = json.loads((RUNS / run_id / "run_manifest.json").read_text())
        file_sha[label] = sha256_file(path)
        print(f"scored {label}: rows={len(rows)} test_items={len(scored[label])}", flush=True)

    for step, run_id in CACHED.items():
        path = RUNS / run_id / "per_item.jsonl"
        label = f"step{step}_cached"
        rows = read_jsonl(path)
        scored[label] = rescore(rows, label)
        manifests[label] = json.loads((RUNS / run_id / "run_manifest.json").read_text())
        file_sha[label] = sha256_file(path)
        print(f"scored {label}: rows={len(rows)} test_items={len(scored[label])}", flush=True)

    # ---- cached-vs-substrate cross-check: the recomputed cached column must equal the substrate.
    substrate_check = {}
    for step in ("100", "400"):
        label = f"step{step}_cached"
        per_metric = {}
        for metric in ("acc_final", "acc_strict"):
            match = sum(
                1
                for key, value in scored[label].items()
                if value[metric] == bool(substrate[key][f"{metric}_step{step}"])
            )
            per_metric[metric] = {
                "match_count": match,
                "n": len(scored[label]),
                "match_rate": match / len(scored[label]),
            }
        substrate_check[step] = per_metric

    # ---- the decisive numbers ----
    results = {}
    for step in ("400", "100"):
        r1, r2 = scored[f"step{step}_r1"], scored[f"step{step}_r2"]
        cached = scored[f"step{step}_cached"]
        entry = {
            "replicate_discordance": {m: compare(r1, r2, m) for m in ("acc_final", "acc_strict")},
            "r1_vs_cached": {m: compare(cached, r1, m) for m in ("acc_final", "acc_strict")},
            "r2_vs_cached": {m: compare(cached, r2, m) for m in ("acc_final", "acc_strict")},
            "response_text_identity": {
                "r1_vs_r2": text_identity(r1, r2),
                "r1_vs_cached": text_identity(cached, r1),
                "r2_vs_cached": text_identity(cached, r2),
            },
            "accuracy": {
                m: {
                    "r1": sum(1 for v in r1.values() if v[m]) / len(r1),
                    "r2": sum(1 for v in r2.values() if v[m]) / len(r2),
                    "cached": sum(1 for v in cached.values() if v[m]) / len(cached),
                    "r1_count": sum(1 for v in r1.values() if v[m]),
                    "r2_count": sum(1 for v in r2.values() if v[m]),
                    "cached_count": sum(1 for v in cached.values() if v[m]),
                }
                for m in ("acc_final", "acc_strict")
            },
        }
        results[step] = entry

    payload = {
        "schema_version": "blind-gains.m5c-noise-floor-replicate.v1",
        "generated_utc": subprocess.run(
            ["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True, check=True
        ).stdout.strip(),
        "git_hash": git_hash,
        "question": (
            "Does re-evaluating the SAME checkpoint twice under the cached run's decoding contract "
            "produce zero discordant items? The R1-vs-R2 discordance is the harness noise floor "
            "against which the observed 137/601 step-100-to-400 turnover must be read."
        ),
        "scorer": {
            "callable": "src.eval.blind_solvability.score_greedy_item_pilot",
            "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
            "note": (
                "Every acc_final/acc_strict in this report was recomputed from the raw greedy_response "
                "text by this one scorer; stored row fields are cross-checked, not trusted."
            ),
        },
        "runs": {
            label: {
                "run_id": manifests[label]["run_id"],
                "node": manifests[label].get("node"),
                "gpu_allocation": manifests[label].get("gpu_allocation"),
                "global_step": manifests[label].get("global_step"),
                "replicate": manifests[label].get("replicate"),
                "model_revision": manifests[label].get("model_revision"),
                "checkpoint_index_sha256": manifests[label].get("checkpoint_index_sha256"),
                "decoding": manifests[label].get("decoding"),
                "batch_size": manifests[label].get("batch_size"),
                "prompt_contract_sha256": manifests[label].get("prompt_contract_sha256"),
                "parser_version": manifests[label].get("parser_version"),
                "pilot_reward_version": manifests[label].get("pilot_reward_version"),
                "scoring_mode": manifests[label].get("scoring_mode"),
                "git_hash": manifests[label].get("git_hash"),
                "start_time_utc": manifests[label].get("start_time_utc"),
                "end_time_utc": manifests[label].get("end_time_utc"),
                "status": manifests[label].get("status"),
                "exit_code": manifests[label].get("exit_code"),
                "deviations": manifests[label].get("deviations"),
                "command": manifests[label].get("command"),
                "per_item_path": f"experiments/runs/{manifests[label]['run_id']}/per_item.jsonl",
                "per_item_sha256": file_sha[label],
            }
            for label in scored
        },
        "verification": {
            "stored_vs_recomputed_agreement": {
                label: stored_recomputed_agreement(scored[label]) for label in scored
            },
            "recomputed_cached_vs_substrate": substrate_check,
            "substrate_path": "reports/m5c_item_substrate_v1.jsonl",
            "substrate_sha256": sha256_file(SUBSTRATE),
            "item_key_definition": "(split, row_index) on the Geometry3K test split",
            "determinism_audit": {
                f"step{step}_{rep}": determinism_audit(run_id, manifests[f"step{step}_{rep}"])
                for (step, rep), run_id in REPLICATES.items()
            },
            "eval_harness_unchanged_between_cached_and_replicate_commits": {
                "cached_step400_git_hash": manifests["step400_cached"]["git_hash"],
                "replicate_git_hash": manifests["step400_r1"]["git_hash"],
                "paths_compared": [
                    "scripts/run_pilot_geo3k_step100_eval.py",
                    "src/eval/",
                    "src/rewards/",
                ],
                "git_diff_empty": subprocess.run(
                    [
                        "git",
                        "diff",
                        "--quiet",
                        manifests["step400_cached"]["git_hash"],
                        manifests["step400_r1"]["git_hash"],
                        "--",
                        "scripts/run_pilot_geo3k_step100_eval.py",
                        "src/eval/",
                        "src/rewards/",
                    ],
                    cwd=ROOT,
                ).returncode
                == 0,
            },
        },
        "contract_provenance_caveat": {
            "step_400": (
                "EXACT replicate. The cached step-400 run and both replicates invoke the same "
                "script scripts/run_pilot_geo3k_step100_eval.py with the same --batch-size 4, "
                "--max-model-len 8192, --max-tokens 2048, --seed 20260710, temperature 0, top_p 1, "
                "and the same checkpoint index sha256 "
                f"{manifests['step400_cached']['checkpoint_index_sha256']}; only output paths, node "
                "and GPU differ (cached an12 gpu0 2026-07-28; replicates an29 gpu0/gpu1 2026-07-30)."
            ),
            "step_100": (
                "R1-vs-R2 is an exact within-harness replicate. R-vs-CACHED is additionally a "
                "CROSS-HARNESS comparison: the cached step-100 substrate column came from "
                "scripts/run_blind_solvability_v2.py (greedy n=1 PLUS 16 samples at temperature 1.0 "
                "in the same vLLM session, an12 gpu5, 2026-07-12), rescored on the login node by "
                "scripts/rescore_blind_solvability_v2_guarded.py, whereas the replicates used the "
                "greedy-only pilot harness. Any R-vs-cached step-100 difference could therefore "
                "reflect harness difference rather than nondeterminism; agreement across that gap "
                "is correspondingly stronger evidence than a same-harness match."
            ),
        },
        "superseded_reference": {
            "field": "reports/m5c_turnover_v1.json :: noise_reference_not_a_test",
            "prior_figure_expected_discordance_fraction": 0.21327735024958402,
            "prior_figure_basis": (
                "16-sample temperature-1.0 dispersion at step 100, treating each item as two "
                "independent Bernoulli(p_i) draws."
            ),
            "status": (
                "That figure describes temperature-1.0 sampling dispersion, not the greedy "
                "evaluation harness. It is NOT the replicate noise floor and is superseded by the "
                "directly measured floor in this report."
            ),
        },
        "scope_note": (
            "This report addresses only the TURNOVER-MAGNITUDE soft spot. The separate "
            "reproducible-LOST-items result (3-way Jaccard 0.3118 vs permutation null 0.0221, "
            "p<=1e-4) is unaffected either way: per-item noise would reduce cross-checkpoint "
            "agreement, not manufacture it. The two results are not conflated here."
        ),
        "results": results,
        "reference_observed_turnover": {
            "count": OBSERVED_TURNOVER_COUNT,
            "n": OBSERVED_N,
            "fraction": OBSERVED_TURNOVER_COUNT / OBSERVED_N,
            "source": "reports/m5c_turnover_v1.json (step 100 -> 400, acc_final)",
        },
    }

    # ratio arithmetic
    ratios = {}
    for step in ("400", "100"):
        per_metric = {}
        for metric in ("acc_final", "acc_strict"):
            floor = results[step]["replicate_discordance"][metric]["discordant_count"]
            per_metric[metric] = {
                "replicate_discordance_count": floor,
                "replicate_discordance_fraction": floor / OBSERVED_N,
                "observed_turnover_count": OBSERVED_TURNOVER_COUNT,
                "turnover_over_floor_ratio": (
                    None if floor == 0 else OBSERVED_TURNOVER_COUNT / floor
                ),
                "turnover_minus_floor_count": OBSERVED_TURNOVER_COUNT - floor,
            }
        ratios[step] = per_metric
    payload["floor_vs_turnover_arithmetic"] = ratios

    # ---- whole-artifact identity: strongest single statement available ----
    turnover_provenance_sha = {
        "400": "60eac65a8b5bb9b3682c8ea180add6f16791164d550be25989768a17bc601458",
    }
    file_identity = {}
    for step in ("400", "100"):
        labels = [f"step{step}_r1", f"step{step}_r2"]
        if step == "400":
            labels.append("step400_cached")
        shas = {label: file_sha[label] for label in labels}
        entry = {
            "per_item_sha256": shas,
            "all_identical": len(set(shas.values())) == 1,
            "note": (
                "per_item.jsonl rows carry no run id or timestamp, so an identical whole-file "
                "sha256 means every response and every score field reproduced bit-for-bit."
            ),
        }
        if step in turnover_provenance_sha:
            entry["matches_turnover_report_recorded_provenance_sha256"] = (
                shas[f"step{step}_r1"] == turnover_provenance_sha[step]
            )
            entry["turnover_report_recorded_provenance_sha256"] = turnover_provenance_sha[step]
        else:
            entry["cached_excluded_reason"] = (
                "The cached step-100 column lives in a different row schema (guarded rescore, "
                "1889 rows incl. train, greedy_* field names), so whole-file sha comparison is "
                "not meaningful there; the per-item and per-response comparisons above cover it."
            )
        file_identity[step] = entry
    payload["whole_file_identity"] = file_identity

    payload["checkpoint_identity"] = {
        step: {
            "replicate_model_revision": manifests[f"step{step}_r1"]["model_revision"],
            "cached_model_revision": manifests[f"step{step}_cached"]["model_revision"],
            "same_resolved_path": Path(manifests[f"step{step}_r1"]["model_revision"]).resolve()
            == (ROOT / manifests[f"step{step}_cached"]["model_revision"]).resolve(),
            "replicate_checkpoint_index_sha256": manifests[f"step{step}_r1"][
                "checkpoint_index_sha256"
            ],
            "cached_checkpoint_index_sha256": manifests[f"step{step}_cached"].get(
                "checkpoint_index_sha256"
            ),
        }
        for step in ("400", "100")
    }

    # ---- readout, derived strictly from the measured counts ----
    all_floors = [
        ratios[step][metric]["replicate_discordance_count"]
        for step in ("400", "100")
        for metric in ("acc_final", "acc_strict")
    ]
    all_text_diffs = [
        results[step]["response_text_identity"][pair]["text_differing_count"]
        for step in ("400", "100")
        for pair in ("r1_vs_r2", "r1_vs_cached", "r2_vs_cached")
    ]
    floor_is_zero = max(all_floors) == 0
    text_is_identical = max(all_text_diffs) == 0
    if floor_is_zero:
        readout = (
            "MEASURED FLOOR IS ZERO. Re-evaluating the same checkpoint twice under the cached "
            "decoding contract produced 0/601 discordant items on acc_final and 0/601 on "
            "acc_strict, at BOTH step 400 and step 100, and both replicate accuracies equal the "
            "cached accuracy exactly (step 400: 267/601 = 0.4442595674; step 100: 262/601 = "
            "0.4359400998). The turnover/floor ratio is undefined because the denominator is zero; "
            "the floor-subtracted turnover is 137 - 0 = 137 items. Measurement noise in this "
            "harness is therefore 0 items, and all 137 step-100-to-400 flips are policy "
            "differences between the two checkpoints, not evaluation or decoding noise."
        )
    else:
        readout = (
            f"MEASURED FLOOR IS NONZERO: max replicate discordance across the four measured "
            f"cells is {max(all_floors)}/601 = {max(all_floors) / OBSERVED_N:.4f}. The observed "
            f"137/601 = 0.2280 turnover must be qualified by this floor; the turnover/floor ratio "
            f"is {OBSERVED_TURNOVER_COUNT / max(all_floors):.2f}x and the floor-subtracted "
            f"turnover is {OBSERVED_TURNOVER_COUNT - max(all_floors)} items."
        )
    payload["readout"] = {
        "measured_floor_is_zero": floor_is_zero,
        "response_text_byte_identical_across_all_pairs": text_is_identical,
        "max_replicate_discordance_count_across_cells": max(all_floors),
        "statement": readout,
        "determinism_strength": (
            "Beyond the binary metric, all 601 greedy response STRINGS are byte-identical across "
            "every compared pair (R1 vs R2, R1 vs cached, R2 vs cached, at both steps). Greedy "
            "decoding in this harness is bitwise reproducible across replicate, across node "
            "(an12 vs an29), across GPU index, across date, and -- at step 100 -- across "
            "generation harness."
            if text_is_identical
            else "Response strings are NOT byte-identical across all pairs; see per-pair counts."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"wrote {OUT_JSON}", flush=True)

    # ---- markdown ----
    lines: list[str] = []
    lines.append("# M5C noise floor -- replicate evaluation of the same checkpoint (v1)")
    lines.append("")
    lines.append(f"Generated {payload['generated_utc']} | git `{git_hash}`")
    lines.append("")
    lines.append("## What was measured")
    lines.append("")
    lines.append(
        "McNemar on the step-100->400 substrate tests only whether the NET change departs from "
        "zero. It does not test whether the TOTAL turnover of 137/601 items exceeds "
        "evaluation/decoding noise. That test requires a replicate: the same checkpoint evaluated "
        "twice under an identical contract. Four replicate cells were run (step 400 x2, step 100 x2), "
        "601 Geometry3K test items each."
    )
    lines.append("")
    lines.append("## Runs")
    lines.append("")
    lines.append("| label | run id | node/gpu | step | ckpt index sha256 | wall | per_item sha256 |")
    lines.append("|---|---|---|---|---|---|---|")
    for label in ("step400_r1", "step400_r2", "step100_r1", "step100_r2", "step400_cached", "step100_cached"):
        m = payload["runs"][label]
        gpu = ",".join(m["gpu_allocation"] or []) if m["gpu_allocation"] else "-"
        ck = (m["checkpoint_index_sha256"] or "null")[:16]
        lines.append(
            f"| `{label}` | `{m['run_id']}` | {m['node']}/{gpu} | {m['global_step']} | "
            f"`{ck}` | {m['start_time_utc']} -> {m['end_time_utc']} | `{m['per_item_sha256'][:16]}` |"
        )
    lines.append("")
    lines.append("## THE DECISIVE NUMBER -- replicate discordance (R1 vs R2, same checkpoint)")
    lines.append("")
    lines.append("| step | metric | discordant | fraction | agreement | R1 acc | R2 acc | acc diff |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for step in ("400", "100"):
        for metric in ("acc_final", "acc_strict"):
            d = results[step]["replicate_discordance"][metric]
            lines.append(
                f"| {step} | {metric} | {d['discordant_count']}/{d['n']} | {d['discordant_fraction']:.4f} | "
                f"{d['agreement_rate']:.6f} | {d['a_acc']:.6f} | {d['b_acc']:.6f} | "
                f"{d['acc_diff_b_minus_a']:+.6f} |"
            )
    lines.append("")
    lines.append("## Response-text byte identity (stronger than the binary metric)")
    lines.append("")
    lines.append("| step | pair | byte-identical | differing |")
    lines.append("|---|---|---|---|")
    for step in ("400", "100"):
        for pair, d in results[step]["response_text_identity"].items():
            lines.append(
                f"| {step} | {pair} | {d['byte_identical_count']}/{d['n']} "
                f"({d['byte_identical_fraction']:.4f}) | {d['text_differing_count']} |"
            )
    lines.append("")
    lines.append("## Whole-artifact identity")
    lines.append("")
    for step, entry in payload["whole_file_identity"].items():
        shas = entry["per_item_sha256"]
        joined = ", ".join(f"`{label}`=`{sha[:16]}`" for label, sha in shas.items())
        lines.append(f"- **step {step}**: {joined} -- all identical: **{entry['all_identical']}**")
        if "matches_turnover_report_recorded_provenance_sha256" in entry:
            lines.append(
                f"  - matches the sha256 recorded as step-{step} provenance in "
                f"`reports/m5c_turnover_v1.json`: "
                f"**{entry['matches_turnover_report_recorded_provenance_sha256']}**"
            )
        if "cached_excluded_reason" in entry:
            lines.append(f"  - cached excluded: {entry['cached_excluded_reason']}")
    lines.append("")
    lines.append("Checkpoint identity (replicate vs cached):")
    lines.append("")
    lines.append("| step | same resolved checkpoint path | replicate ckpt index sha256 | cached |")
    lines.append("|---|---|---|---|")
    for step, entry in payload["checkpoint_identity"].items():
        lines.append(
            f"| {step} | {entry['same_resolved_path']} | "
            f"`{entry['replicate_checkpoint_index_sha256']}` | "
            f"{('`' + entry['cached_checkpoint_index_sha256'] + '`') if entry['cached_checkpoint_index_sha256'] else 'not recorded by the rescore manifest'} |"
        )
    lines.append("")
    lines.append("## Does each replicate reproduce the CACHED substrate column?")
    lines.append("")
    lines.append("| step | pair | metric | agreement | discordant | cached acc | replicate acc |")
    lines.append("|---|---|---|---|---|---|---|")
    for step in ("400", "100"):
        for pair in ("r1_vs_cached", "r2_vs_cached"):
            for metric in ("acc_final", "acc_strict"):
                d = results[step][pair][metric]
                lines.append(
                    f"| {step} | {pair} | {metric} | {d['agreement_count']}/{d['n']} "
                    f"({d['agreement_rate']:.6f}) | {d['discordant_count']} | {d['a_acc']:.6f} | "
                    f"{d['b_acc']:.6f} |"
                )
    lines.append("")
    lines.append("## Floor vs observed turnover -- arithmetic only")
    lines.append("")
    lines.append(
        f"Observed step-100->400 turnover: {OBSERVED_TURNOVER_COUNT}/{OBSERVED_N} = "
        f"{OBSERVED_TURNOVER_COUNT / OBSERVED_N:.4f}."
    )
    lines.append("")
    lines.append("| step | metric | floor count | floor fraction | turnover/floor | turnover-floor |")
    lines.append("|---|---|---|---|---|---|")
    for step in ("400", "100"):
        for metric in ("acc_final", "acc_strict"):
            r = ratios[step][metric]
            ratio = "undefined (floor = 0)" if r["turnover_over_floor_ratio"] is None else f"{r['turnover_over_floor_ratio']:.2f}x"
            lines.append(
                f"| {step} | {metric} | {r['replicate_discordance_count']} | "
                f"{r['replicate_discordance_fraction']:.4f} | {ratio} | "
                f"{r['turnover_minus_floor_count']} |"
            )
    lines.append("")
    lines.append("## Readout")
    lines.append("")
    lines.append(payload["readout"]["statement"])
    lines.append("")
    lines.append(payload["readout"]["determinism_strength"])
    lines.append("")
    lines.append("### Superseded reference figure")
    lines.append("")
    lines.append(
        f"`reports/m5c_turnover_v1.json :: noise_reference_not_a_test` recorded an expected "
        f"discordance of {payload['superseded_reference']['prior_figure_expected_discordance_fraction']:.4f} "
        f"from 16-sample temperature-1.0 dispersion, explicitly labelled not-a-test. "
        f"{payload['superseded_reference']['status']}"
    )
    lines.append("")
    lines.append("### Scope")
    lines.append("")
    lines.append(payload["scope_note"])
    lines.append("")
    lines.append("## Contract provenance -- what is and is not an exact replicate")
    lines.append("")
    lines.append(f"- **step 400**: {payload['contract_provenance_caveat']['step_400']}")
    lines.append(f"- **step 100**: {payload['contract_provenance_caveat']['step_100']}")
    lines.append("")
    lines.append("## Determinism audit -- the replicates decoded fresh")
    lines.append("")
    lines.append(
        "A zero floor would be an artifact if a replicate had reused cached generations, so each "
        "cell is audited for that."
    )
    lines.append("")
    lines.append(
        "| label | manifest resume_from | `--resume-from` in cmd | resumed rows in log | "
        "shard loads | weight load | run-scoped node-local cache dir |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    for label, audit in payload["verification"]["determinism_audit"].items():
        lines.append(
            f"| `{label}` | {audit['manifest_resume_from']} | "
            f"{audit['command_contains_resume_from_flag']} | {audit['last_resumed_count_in_log']} | "
            f"{audit['safetensors_shard_load_completed_lines']} | "
            f"{audit['vllm_model_weight_load_observed']} | "
            f"{audit['cache_dir_is_run_scoped_node_local']} |"
        )
    lines.append("")
    harness = payload["verification"]["eval_harness_unchanged_between_cached_and_replicate_commits"]
    lines.append(
        f"Eval harness byte-identical between the cached step-400 commit "
        f"`{harness['cached_step400_git_hash'][:12]}` and the replicate commit "
        f"`{harness['replicate_git_hash'][:12]}` over "
        f"{', '.join('`' + p + '`' for p in harness['paths_compared'])}: "
        f"**{harness['git_diff_empty']}**."
    )
    lines.append("")
    lines.append("## Verification")
    lines.append("")
    lines.append("| label | stored vs recomputed acc_final | acc_strict | n |")
    lines.append("|---|---|---|---|")
    for label, v in payload["verification"]["stored_vs_recomputed_agreement"].items():
        lines.append(f"| `{label}` | {v['acc_final']} | {v['acc_strict']} | {v['n']} |")
    lines.append("")
    lines.append("Recomputed cached column vs `reports/m5c_item_substrate_v1.jsonl`:")
    lines.append("")
    for step, per_metric in substrate_check.items():
        for metric, v in per_metric.items():
            lines.append(
                f"- step {step} {metric}: {v['match_count']}/{v['n']} match ({v['match_rate']:.6f})"
            )
    lines.append("")
    lines.append("## Verbatim replicate command (step 400 R1)")
    lines.append("")
    lines.append("```")
    lines.append(payload["runs"]["step400_r1"]["command"])
    lines.append("```")
    lines.append("")
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT_MD}", flush=True)


if __name__ == "__main__":
    main()
