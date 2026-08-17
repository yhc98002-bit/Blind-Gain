#!/usr/bin/env python3
"""Independent verification of the six F8 Mini-A5 endpoint evaluation cells.

Checks per cell:
  - run_manifest status / expected_shards / artifact_sha256
  - data_manifest_hash recorded AND equal to a freshly computed sha256
  - checkpoint_index_sha256 recorded (reports null when the unbound launcher
    path leaves it null) plus a freshly computed index sha256
  - shard row counts, per-shard and total, against the manifest sharding rule
  - pair_id coverage: exactly the manifest pair_id set, no duplicates
  - worker termination evidence (log tail is the metrics JSON, no traceback)
  - no leftover .partial artifacts
  - re-scores every row from the raw prediction text and compares to the
    stored per-row scores and to the per-shard metrics files
Reports lenient AND strict pair accuracy, pooled and per template (I7, I13).
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
sys.path.insert(0, str(ROOT))

from src.eval.fliptrack_metrics import pair_score  # noqa: E402

RUN_TS = sys.argv[1]

CELLS = [
    ("F8-C1", "cp", "R19", f"experiments/runs/mini_a5_f8_r19_cp_step120_real_an29_{RUN_TS}",
     "experiments/runs/caption_qa_pair_build_fliptrack_v02r19_qwen25vl3b_384_20260710T140200Z/shards/captions_shard_0.jsonl",
     "checkpoints/mini_a5/mini_a5_cp_seed1/global_step_120/actor/huggingface", 1200, "0 1 2 3"),
    ("F8-C2", "member", "R19", f"experiments/runs/mini_a5_f8_r19_member_step120_real_an29_{RUN_TS}",
     "experiments/runs/caption_qa_pair_build_fliptrack_v02r19_qwen25vl3b_384_20260710T140200Z/shards/captions_shard_0.jsonl",
     "checkpoints/mini_a5/mini_a5_same_data_seed1/global_step_120/actor/huggingface", 1200, "4 5 6 7"),
    ("F8-C3", "cp", "R20", f"experiments/runs/mini_a5_f8_r20_cp_step120_real_an29_{RUN_TS}",
     "data/fliptrack_r20_source_manifest.jsonl",
     "checkpoints/mini_a5/mini_a5_cp_seed1/global_step_120/actor/huggingface", 1200, "0 1 2 3"),
    ("F8-C4", "member", "R20", f"experiments/runs/mini_a5_f8_r20_member_step120_real_an29_{RUN_TS}",
     "data/fliptrack_r20_source_manifest.jsonl",
     "checkpoints/mini_a5/mini_a5_same_data_seed1/global_step_120/actor/huggingface", 1200, "4 5 6 7"),
    ("F8-C5", "cp", "chart_v08", f"experiments/runs/mini_a5_f8_chartv08_cp_step120_real_an29_{RUN_TS}",
     "data/fliptrack_chart_v08_calibration_v1_manifest.jsonl",
     "checkpoints/mini_a5/mini_a5_cp_seed1/global_step_120/actor/huggingface", 100, "0 1 2 3"),
    ("F8-C6", "member", "chart_v08", f"experiments/runs/mini_a5_f8_chartv08_member_step120_real_an29_{RUN_TS}",
     "data/fliptrack_chart_v08_calibration_v1_manifest.jsonl",
     "checkpoints/mini_a5/mini_a5_same_data_seed1/global_step_120/actor/huggingface", 100, "4 5 6 7"),
]

NUM_SHARDS = 4


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def acc_block(rows):
    n = len(rows)
    if n == 0:
        return {"n_pairs": 0}
    return {
        "n_pairs": n,
        "pair_accuracy_lenient": sum(bool(r["pair_correct"]) for r in rows) / n,
        "pair_accuracy_strict": sum(bool(r["strict_pair_correct"]) for r in rows) / n,
        "member_accuracy_lenient": sum(bool(r["correct_a"]) + bool(r["correct_b"]) for r in rows) / (2 * n),
        "member_accuracy_strict": sum(bool(r["strict_correct_a"]) + bool(r["strict_correct_b"]) for r in rows) / (2 * n),
        "contract_valid_rate": sum(bool(r["contract_valid_a"]) + bool(r["contract_valid_b"]) for r in rows) / (2 * n),
    }


report = {"run_ts": RUN_TS, "cells": []}
all_ok = True

for cell_id, arm, dataset, rd, man_rel, ckpt_rel, exp_rows, gpus in CELLS:
    c = {"cell_id": cell_id, "arm": arm, "set": dataset, "run_dir": rd,
         "expected_rows": exp_rows, "checks": {}, "problems": []}
    rdp = ROOT / rd
    mp = rdp / "run_manifest.json"
    if not mp.is_file():
        c["problems"].append("run_manifest.json absent")
        c["status"] = "MISSING"
        report["cells"].append(c)
        all_ok = False
        continue
    m = json.loads(mp.read_text(encoding="utf-8"))
    c["manifest_status"] = m.get("status")
    c["checks"]["status_complete"] = m.get("status") == "complete"
    c["checks"]["expected_shards_4"] = m.get("expected_shards") == NUM_SHARDS
    c["checks"]["node_is_an29"] = m.get("node") == "an29"
    c["checks"]["gpu_allocation_matches"] = m.get("gpu_allocation") == gpus
    c["checks"]["artifact_sha256_present"] = bool(m.get("artifact_sha256"))
    c["artifact_sha256"] = m.get("artifact_sha256")
    c["git_hash"] = m.get("git_hash")
    c["config_hash"] = m.get("config_hash")
    c["prompt_contract_sha256"] = m.get("prompt_contract_sha256")
    c["start_time_utc"] = m.get("start_time_utc")
    c["end_time_utc"] = m.get("end_time_utc")
    c["seed"] = m.get("seed")
    c["max_new_tokens"] = m.get("max_new_tokens")
    c["image_mode"] = m.get("image_mode")

    # --- data manifest sha256 recorded in run_manifest, and independently recomputed
    c["manifest_data_manifest"] = m.get("data_manifest")
    c["manifest_data_manifest_hash"] = m.get("data_manifest_hash")
    fresh_man = sha256_file(ROOT / man_rel)
    c["recomputed_data_manifest_sha256"] = fresh_man
    c["checks"]["data_manifest_path_matches"] = m.get("data_manifest") == man_rel
    c["checks"]["run_manifest_records_data_manifest_sha256"] = bool(m.get("data_manifest_hash"))
    c["checks"]["data_manifest_sha256_matches_recomputed"] = m.get("data_manifest_hash") == fresh_man

    # --- checkpoint index sha256
    c["manifest_checkpoint_index_sha256"] = m.get("checkpoint_index_sha256")
    fresh_ckpt = sha256_file(ROOT / ckpt_rel / "model.safetensors.index.json")
    c["recomputed_checkpoint_index_sha256"] = fresh_ckpt
    c["checks"]["run_manifest_records_checkpoint_index_sha256"] = m.get("checkpoint_index_sha256") is not None
    c["checks"]["model_path_matches"] = str(m.get("model_path", "")).rstrip("/") == str(ROOT / ckpt_rel)

    # --- shards
    man_rows = read_jsonl(ROOT / man_rel)
    c["checks"]["source_manifest_rows_expected"] = len(man_rows) == exp_rows
    man_ids_by_shard = defaultdict(list)
    for idx, r in enumerate(man_rows):
        man_ids_by_shard[idx % NUM_SHARDS].append(r["pair_id"])

    shard_counts = {}
    rows_all = []
    for si in range(NUM_SHARDS):
        sp = rdp / "shards" / f"shard_{si}.jsonl"
        if not sp.is_file():
            c["problems"].append(f"missing shard file shard_{si}.jsonl")
            continue
        rows = read_jsonl(sp)
        shard_counts[f"shard_{si}"] = len(rows)
        if len(rows) != len(man_ids_by_shard[si]):
            c["problems"].append(
                f"shard_{si} row count {len(rows)} != expected {len(man_ids_by_shard[si])}")
        if [r["pair_id"] for r in rows] != man_ids_by_shard[si]:
            c["problems"].append(f"shard_{si} pair_id sequence differs from manifest sharding")
        rows_all.extend(rows)
    c["shard_row_counts"] = shard_counts
    c["total_rows"] = len(rows_all)
    c["checks"]["total_rows_equals_expected"] = len(rows_all) == exp_rows

    ids = [r["pair_id"] for r in rows_all]
    dupes = [k for k, v in Counter(ids).items() if v > 1]
    c["checks"]["no_duplicate_pair_ids"] = not dupes
    c["checks"]["pair_id_set_equals_manifest"] = set(ids) == {r["pair_id"] for r in man_rows}
    if dupes:
        c["problems"].append(f"{len(dupes)} duplicate pair_ids")

    # --- leftover partials
    partials = sorted(p.name for p in rdp.rglob("*.partial"))
    c["checks"]["no_partial_files"] = not partials
    if partials:
        c["problems"].append(f"leftover partials: {partials}")

    # --- worker termination evidence (harness records no exit code; use log tail)
    logs = {}
    for si, gpu in enumerate(gpus.split()):
        lp = rdp / "logs" / f"an29_gpu{gpu}_shard{si}.log"
        entry = {"exists": lp.is_file()}
        if lp.is_file():
            txt = lp.read_text(encoding="utf-8", errors="replace")
            tail = [ln for ln in txt.strip().splitlines() if ln.strip()]
            entry["has_traceback"] = "Traceback (most recent call last)" in txt
            entry["last_line_is_metrics_json"] = False
            if tail:
                try:
                    obj = json.loads(tail[-1])
                    entry["last_line_is_metrics_json"] = isinstance(obj, dict) and "n_pairs" in obj
                    entry["log_reported_n_pairs"] = obj.get("n_pairs")
                except json.JSONDecodeError:
                    entry["last_line"] = tail[-1][:200]
        logs[f"shard_{si}_gpu{gpu}"] = entry
    c["worker_logs"] = logs
    c["checks"]["all_workers_clean_terminal_state"] = all(
        e.get("exists") and e.get("last_line_is_metrics_json") and not e.get("has_traceback")
        for e in logs.values())

    # --- per-shard metrics files agree with recomputation
    shard_metric_ok = True
    for si in range(NUM_SHARDS):
        mfp = rdp / "metrics" / f"shard_{si}.json"
        if not mfp.is_file():
            shard_metric_ok = False
            c["problems"].append(f"missing metrics/shard_{si}.json")
            continue
        sm = json.loads(mfp.read_text(encoding="utf-8"))
        srows = read_jsonl(rdp / "shards" / f"shard_{si}.jsonl")
        rec = acc_block(srows)
        if abs(sm.get("pair_accuracy", -1) - rec["pair_accuracy_lenient"]) > 1e-12:
            shard_metric_ok = False
            c["problems"].append(f"shard_{si} pair_accuracy disagrees with rows")
        if abs(sm.get("strict_pair_accuracy", -1) - rec["pair_accuracy_strict"]) > 1e-12:
            shard_metric_ok = False
            c["problems"].append(f"shard_{si} strict_pair_accuracy disagrees with rows")
        if int(sm.get("n_pairs", -1)) != len(srows):
            shard_metric_ok = False
            c["problems"].append(f"shard_{si} n_pairs disagrees with rows")
    c["checks"]["shard_metrics_agree_with_rows"] = shard_metric_ok

    # --- independent re-score from raw prediction text
    mismatch = 0
    for r in rows_all:
        rs = pair_score(r)
        if bool(rs["pair_correct"]) != bool(r["pair_correct"]) or \
           bool(rs["strict_pair_correct"]) != bool(r["strict_pair_correct"]):
            mismatch += 1
    c["rescore_mismatches"] = mismatch
    c["checks"]["rescore_reproduces_stored_scores"] = mismatch == 0

    # --- accuracies: pooled (non-endpoint diagnostic) and per template (I13)
    c["pooled_non_endpoint_diagnostic"] = acc_block(rows_all)
    by_t = defaultdict(list)
    for r in rows_all:
        by_t[str(r.get("template_id", "unknown"))].append(r)
    c["per_template"] = {t: acc_block(v) for t, v in sorted(by_t.items())}

    hard = ["status_complete", "expected_shards_4", "node_is_an29", "gpu_allocation_matches",
            "artifact_sha256_present", "data_manifest_path_matches",
            "run_manifest_records_data_manifest_sha256",
            "data_manifest_sha256_matches_recomputed", "model_path_matches",
            "source_manifest_rows_expected", "total_rows_equals_expected",
            "no_duplicate_pair_ids", "pair_id_set_equals_manifest", "no_partial_files",
            "all_workers_clean_terminal_state", "shard_metrics_agree_with_rows",
            "rescore_reproduces_stored_scores"]
    failed = [k for k in hard if not c["checks"].get(k)]
    c["failed_hard_checks"] = failed
    c["status"] = "ACCEPT" if not failed and not c["problems"] else "REJECT"
    if c["status"] != "ACCEPT":
        all_ok = False
    report["cells"].append(c)

report["all_cells_accepted"] = all_ok
out = ROOT / "reports" / "mini_a5_f8_cell_verification_v1.json"
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2, sort_keys=True))
