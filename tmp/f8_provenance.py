#!/usr/bin/env python3
"""Build reports/mini_a5_f8_run_provenance_v1.json.

Required by reports/f8_eval_plan_v1.json -> post_run_provenance_artifact,
because the unbound launcher path leaves source_training_run / global_step /
checkpoint_index_sha256 / evaluation_scope null in every run_manifest.json.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
RUN_TS = sys.argv[1]
STATE = ROOT / "logs" / f"mini_a5_f8_driver_{RUN_TS}"

TRAIN = {
    "cp": "experiments/runs/mini_a5_cp_main_an29_20260727T064527Z",
    "member": "experiments/runs/mini_a5_member_main_an29_20260728T023715Z",
}
CKPT = {
    "cp": "checkpoints/mini_a5/mini_a5_cp_seed1/global_step_120/actor/huggingface",
    "member": "checkpoints/mini_a5/mini_a5_same_data_seed1/global_step_120/actor/huggingface",
}
CELLS = [
    ("F8-C1", "cp", "R19", f"experiments/runs/mini_a5_f8_r19_cp_step120_real_an29_{RUN_TS}",
     "experiments/runs/caption_qa_pair_build_fliptrack_v02r19_qwen25vl3b_384_20260710T140200Z/shards/captions_shard_0.jsonl", "0 1 2 3"),
    ("F8-C2", "member", "R19", f"experiments/runs/mini_a5_f8_r19_member_step120_real_an29_{RUN_TS}",
     "experiments/runs/caption_qa_pair_build_fliptrack_v02r19_qwen25vl3b_384_20260710T140200Z/shards/captions_shard_0.jsonl", "4 5 6 7"),
    ("F8-C3", "cp", "R20", f"experiments/runs/mini_a5_f8_r20_cp_step120_real_an29_{RUN_TS}",
     "data/fliptrack_r20_source_manifest.jsonl", "0 1 2 3"),
    ("F8-C4", "member", "R20", f"experiments/runs/mini_a5_f8_r20_member_step120_real_an29_{RUN_TS}",
     "data/fliptrack_r20_source_manifest.jsonl", "4 5 6 7"),
    ("F8-C5", "cp", "chart_v08", f"experiments/runs/mini_a5_f8_chartv08_cp_step120_real_an29_{RUN_TS}",
     "data/fliptrack_chart_v08_calibration_v1_manifest.jsonl", "0 1 2 3"),
    ("F8-C6", "member", "chart_v08", f"experiments/runs/mini_a5_f8_chartv08_member_step120_real_an29_{RUN_TS}",
     "data/fliptrack_chart_v08_calibration_v1_manifest.jsonl", "4 5 6 7"),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


payload = {
    "schema_version": "blind-gains.mini-a5-f8-run-provenance.v1",
    "title": "Mini-A5 F8 endpoint evaluation run provenance",
    "why_this_file_exists": (
        "scripts/launch_fliptrack_eval_shards.sh accepts a checkpoint provenance binding only for "
        "job_type l13_mechanical_pilot_arm / m3_mechanical_pilot_arm / m5_anchor_longhorizon_400. Both "
        "Mini-A5 training runs carry job_type m6_mini_a5_registered_main, so the six cells ran on the "
        "UNBOUND path and each run_manifest.json records source_training_run, source_training_job_type, "
        "global_step, checkpoint_index_sha256 and evaluation_scope as null. No contract file was modified. "
        "The bindings are recorded here instead, each value recomputed from disk by this script."
    ),
    "run_ts": RUN_TS,
    "plan": "reports/f8_eval_plan_v1.json",
    "driver_script": "tmp/f8_driver.sh",
    "driver_state_dir": str(STATE.relative_to(ROOT)),
    "global_step": 120,
    "node": "an29",
    "num_shards": 4,
    "image_mode": "real",
    "max_new_tokens": 32,
    "eval_seed": 0,
    "git_head_at_launch": (STATE / "git_head_at_launch.txt").read_text(encoding="utf-8").strip(),
    "git_status_porcelain_at_launch_verbatim":
        (STATE / "git_status_porcelain_at_launch.txt").read_text(encoding="utf-8"),
    "binding_env_vars_present_at_launch":
        [ln for ln in (STATE / "binding_env_check.txt").read_text(encoding="utf-8").splitlines() if ln.strip()],
    "cells": [],
}

for cell_id, arm, dataset, rd, man_rel, gpus in CELLS:
    m = json.loads((ROOT / rd / "run_manifest.json").read_text(encoding="utf-8"))
    tr = TRAIN[arm]
    tm = ROOT / tr / "run_manifest.json"
    ck = ROOT / CKPT[arm]
    rc_path = STATE / f"{cell_id}.launcher_exit_code"
    payload["cells"].append({
        "cell_id": cell_id,
        "arm": arm,
        "set": dataset,
        "run_dir": rd,
        "source_training_run": tr,
        "source_training_run_manifest_sha256": sha256_file(tm),
        "source_training_job_type": json.loads(tm.read_text(encoding="utf-8")).get("job_type"),
        "global_step": 120,
        "checkpoint_path": str(ck),
        "checkpoint_index_sha256": sha256_file(ck / "model.safetensors.index.json"),
        "data_manifest": man_rel,
        "data_manifest_sha256": sha256_file(ROOT / man_rel),
        "gpu_list": gpus,
        "num_shards": 4,
        "image_mode": m.get("image_mode"),
        "max_new_tokens": m.get("max_new_tokens"),
        "eval_seed": m.get("seed"),
        "launcher_exit_code": int(rc_path.read_text(encoding="utf-8").strip()) if rc_path.is_file() else None,
        "run_manifest": {
            "status": m.get("status"),
            "git_hash": m.get("git_hash"),
            "config_hash": m.get("config_hash"),
            "data_manifest_hash": m.get("data_manifest_hash"),
            "prompt_contract_sha256": m.get("prompt_contract_sha256"),
            "artifact_sha256": m.get("artifact_sha256"),
            "artifact_count": m.get("artifact_count"),
            "start_time_utc": m.get("start_time_utc"),
            "end_time_utc": m.get("end_time_utc"),
            "checkpoint_index_sha256_field": m.get("checkpoint_index_sha256"),
            "source_training_run_field": m.get("source_training_run"),
            "global_step_field": m.get("global_step"),
            "evaluation_scope_field": m.get("evaluation_scope"),
        },
    })

out = ROOT / "reports" / "mini_a5_f8_run_provenance_v1.json"
out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"wrote {out}")
