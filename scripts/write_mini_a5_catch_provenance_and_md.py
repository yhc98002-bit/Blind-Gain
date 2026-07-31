#!/usr/bin/env python3
"""Post-run artifacts for the Mini-A5 catch-trial stability evaluation.

Registration (binding): docs/registered_mini_a5_catch_stability_v1.md.

Writes:
  reports/mini_a5_catch_run_provenance_v1.json  -- the out-of-band post-run
    checkpoint provenance record required by registration section 2.4 (the
    shard launcher has no m6_mini_a5_registered_main binding branch, so the
    two run_manifest.json files record null checkpoint provenance; this file
    carries it, exactly as reports/mini_a5_f8_run_provenance_v1.json did for
    the six F8 cells).
  reports/mini_a5_catch_stability_readout_v1.md -- registered readout in
    prose-free tabular form: numbers, checks, provenance. No interpretation.

Every number in the md is read from the scorer output JSON
(reports/mini_a5_catch_stability_readout_v1.json); nothing is retyped.
Checkpoint index sha256s and manifest sha256s are recomputed from disk here,
post-run, and asserted against the registered pins.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
TS = "20260731T162926Z"
NODE = "an29"
RUN_CP = f"experiments/runs/mini_a5_catch_cp_step120_real_{NODE}_{TS}"
RUN_MEMBER = f"experiments/runs/mini_a5_catch_member_step120_real_{NODE}_{TS}"
STATE_DIR = f"experiments/runs/mini_a5_catch_driver_state_{TS}"
READOUT_JSON = "reports/mini_a5_catch_stability_readout_v1.json"
PROVENANCE_OUT = "reports/mini_a5_catch_run_provenance_v1.json"
MD_OUT = "reports/mini_a5_catch_stability_readout_v1.md"
CLAIM_RUN_ID = f"mini_a5_catch_stability_v1_{TS}"

REGISTERED = {
    "manifest": "c4bb508f930ec47c9f3a2a4bc905693394f63bf6b4ebbd0f1332eef85afcbe4a",
    "manifest_provenance": "47f35dce7f76e3b43902951f7a0f24cdd147d9d3e576f6fb019fcfffddaa8ad8",
    "pairs": "fbd83d52fa01103bfb839fa2572eb9164c532f8c3a3431da6ca8f6033d6a9728",
    "cp_index": "4bb3b752a9895596f57798116b660406110198669dcfefbc213594d540baed21",
    "member_index": "b4270b12dda440fdfdb345c4c074decd1dbbe8d40c751b67392ce6d96bd037f6",
    "scorer": "d15eaa5d878cb757aa8dbae17d446c98cd6675cdc10fbd1a23bac1d7af1d8e91",
    "adapter": "b7b964f3c17f650d2355e36ab532e2893de8fb49aa51bb427a352e2fc995e93e",
    "prompt_contract": "7ac39f53a2a824490fc5ee22671a888d2d79d55e1d8351919006d7d71c7a8f3f",
}

CKPT = {
    "cp": "checkpoints/mini_a5/mini_a5_cp_seed1/global_step_120/actor/huggingface",
    "member": "checkpoints/mini_a5/mini_a5_same_data_seed1/global_step_120/actor/huggingface",
}
SOURCE_TRAINING = {
    "cp": "experiments/runs/mini_a5_cp_main_an29_20260727T064527Z",
    "member": "experiments/runs/mini_a5_member_main_an29_20260728T023715Z",
}
GPU = {"cp": 5, "member": 7}
RUN_DIR = {"cp": RUN_CP, "member": RUN_MEMBER}

TEMPLATES = (
    "mini_a5_catch_distractor_matrix_v1",
    "mini_a5_catch_distractor_scatter_v1",
    "mini_a5_catch_distractor_trajectory_v1",
)
INDICATORS = (
    "stable_lenient",
    "stable_strict",
    "pair_correct",
    "strict_pair_correct",
    "stable_and_correct_lenient",
    "stable_and_correct_strict",
)


def sha256(rel: str) -> str:
    h = hashlib.sha256()
    with (ROOT / rel).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def jload(rel: str):
    return json.loads((ROOT / rel).read_text())


def must(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"CHECK FAILED: {msg}")


def main() -> int:
    readout = jload(READOUT_JSON)
    checks: dict[str, dict] = {}

    def pin(name: str, rel: str, expected: str) -> str:
        got = sha256(rel)
        checks[name] = {"path": rel, "recomputed_sha256": got, "registered_sha256": expected,
                        "pass": got == expected}
        must(got == expected, f"{name}: {rel} sha {got} != registered {expected}")
        return got

    # --- recompute every pinned hash from disk, post-run ---
    pin("derived_eval_manifest", "data/derived/mini_a5_catch_eval_manifest_v1.jsonl", REGISTERED["manifest"])
    pin("derived_eval_manifest_provenance", "data/derived/mini_a5_catch_eval_manifest_v1.jsonl.provenance.json", REGISTERED["manifest_provenance"])
    pin("catch_source_pairs", "data/mini_a5_catch_v1/pairs.jsonl", REGISTERED["pairs"])
    pin("catch_decontamination", "data/mini_a5_catch_v1/decontamination.json",
        "19ed9a833665aead2aee1f4494279a26055c4f531fed68d3e3340af8a1a16bda")
    pin("catch_audit", "reports/mini_a5_catch_audit_v1.json",
        "37b9662c1f873c6b6cb7ee04a87a954dadef54ea974933c0e50e5ab8c60c2317")
    pin("checkpoint_index_cp", f"{CKPT['cp']}/model.safetensors.index.json", REGISTERED["cp_index"])
    pin("checkpoint_index_member", f"{CKPT['member']}/model.safetensors.index.json", REGISTERED["member_index"])
    pin("scorer", "src/eval/catch_stability.py", REGISTERED["scorer"])
    pin("adapter", "scripts/build_mini_a5_catch_eval_manifest.py", REGISTERED["adapter"])

    tracked = jload("experiments/manifests/mini_a5_catch_eval_manifest_v1.json")
    must(tracked["output_sha256"] == REGISTERED["manifest"], "tracked checksum record disagrees")
    checks["tracked_manifest_record"] = {
        "path": "experiments/manifests/mini_a5_catch_eval_manifest_v1.json",
        "output_sha256": tracked["output_sha256"], "pass": True,
    }

    # --- per-arm run facts, from the run manifests and shard outputs ---
    cells = []
    for arm in ("cp", "member"):
        rd = RUN_DIR[arm]
        rm = jload(f"{rd}/run_manifest.json")
        must(rm["status"] == "complete", f"{arm} run status {rm['status']}")
        must(rm["data_manifest_hash"] == REGISTERED["manifest"], f"{arm} run used a different manifest")
        must(rm["prompt_contract_sha256"] == REGISTERED["prompt_contract"], f"{arm} prompt contract drift")
        must(rm["seed"] == 0 and rm["max_new_tokens"] == 32 and rm["image_mode"] == "real",
             f"{arm} generation regime drift")
        shard = f"{rd}/shards/shard_0.jsonl"
        rows = [json.loads(line) for line in (ROOT / shard).read_text().splitlines()]
        must(len(rows) == 300, f"{arm} shard rows {len(rows)} != 300")
        n_a = sum(1 for r in rows if r.get("prediction_a"))
        n_b = sum(1 for r in rows if r.get("prediction_b"))
        must(n_a == 300 and n_b == 300, f"{arm} generations a={n_a} b={n_b}")
        src_manifest = jload(f"{SOURCE_TRAINING[arm]}/run_manifest.json")
        must(src_manifest["job_type"] == "m6_mini_a5_registered_main",
             f"{arm} source training job_type {src_manifest['job_type']}")
        pid = (ROOT / f"{rd}/pids/{NODE}_gpu{GPU[arm]}_shard0.pid").read_text().strip()
        cells.append({
            "cell_id": f"CATCH-C{1 if arm == 'cp' else 2}",
            "arm": arm,
            "set": "mini_a5_catch_v1",
            "checkpoint_path": str(ROOT / CKPT[arm]),
            "checkpoint_index_sha256_recomputed_post_run": checks[f"checkpoint_index_{arm}"]["recomputed_sha256"],
            "data_manifest": "data/derived/mini_a5_catch_eval_manifest_v1.jsonl",
            "data_manifest_sha256": REGISTERED["manifest"],
            "eval_seed": 0,
            "global_step": 120,
            "gpu_list": str(GPU[arm]),
            "image_mode": "real",
            "launcher_exit_code": 0,
            "max_new_tokens": 32,
            "node": NODE,
            "num_shards": 1,
            "pairs": 300,
            "generations": 600,
            "run_dir": rd,
            "worker_pid": int(pid),
            "run_manifest": {
                "artifact_sha256": sha256(f"{rd}/run_manifest.json"),
                "config_hash": rm["config_hash"],
                "git_hash": rm["git_hash"],
                "start_time_utc": rm["start_time_utc"],
                "end_time_utc": rm["end_time_utc"],
                "status": rm["status"],
                "data_manifest_hash": rm["data_manifest_hash"],
                "prompt_contract_sha256": rm["prompt_contract_sha256"],
                "checkpoint_index_sha256_field": rm["checkpoint_index_sha256"],
                "source_training_run_field": rm["source_training_run"],
                "global_step_field": rm["global_step"],
                "evaluation_scope_field": rm["evaluation_scope"],
            },
            "shard_output": shard,
            "shard_output_sha256": sha256(shard),
            "shard_metrics_sha256": sha256(f"{rd}/metrics/shard_0.json"),
            "per_row_scored_output": f"{rd}/catch_stability_rows_{arm}.jsonl",
            "per_row_scored_output_sha256": sha256(f"{rd}/catch_stability_rows_{arm}.jsonl"),
            "source_training_run": SOURCE_TRAINING[arm],
            "source_training_job_type": src_manifest["job_type"],
            "source_training_run_manifest_sha256": sha256(f"{SOURCE_TRAINING[arm]}/run_manifest.json"),
        })

    # scorer input binding: the readout consumed exactly the shards launched here
    for arm, cell in zip(("cp", "member"), cells):
        inp = readout["inputs"][f"{arm}_scores"]
        must(len(inp) == 1 and inp[0]["path"] == cell["shard_output"]
             and inp[0]["sha256"] == cell["shard_output_sha256"],
             f"readout consumed a different {arm} input than the launched run")
    checks["readout_inputs_are_these_runs"] = {
        "pass": True,
        "note": "readout JSON inputs.{cp,member}_scores paths+sha256 equal the shard outputs of the two runs launched by this driver",
    }

    git_head = (ROOT / STATE_DIR / "git_head_at_launch.txt").read_text().strip()
    git_status = (ROOT / STATE_DIR / "git_status_at_launch.txt").read_text()

    provenance = {
        "schema_version": "blind-gains.mini-a5-catch-run-provenance.v1",
        "title": "Mini-A5 catch-trial stability: out-of-band post-run checkpoint provenance (registered secondary 2)",
        "written_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "registration": "docs/registered_mini_a5_catch_stability_v1.md",
        "registration_sha256": sha256("docs/registered_mini_a5_catch_stability_v1.md"),
        "instrument_commit": "fc57cb8",
        "why_out_of_band": (
            "scripts/launch_fliptrack_eval_shards.sh has no m6_mini_a5_registered_main "
            "binding branch (reports/f8_eval_plan_v1.json blocking limitation "
            "'launcher_has_no_mini_a5_binding_branch'), so both run_manifest.json files "
            "record null for source_training_run/global_step/checkpoint_index_sha256/"
            "evaluation_scope. This record carries that provenance out-of-band, exactly "
            "as reports/mini_a5_f8_run_provenance_v1.json did for the six F8 cells; "
            "checkpoint index sha256s here are recomputed from disk post-run."
        ),
        "binding_env_vars_present_at_launch": [],
        "eval_seed_env": {"BLIND_GAINS_EVAL_SEED": "0"},
        "driver": "scripts/launch_mini_a5_catch_stability_eval.sh",
        "driver_state_dir": STATE_DIR,
        "git_head_at_launch": git_head,
        "git_status_at_launch_porcelain": git_status,
        "gpu_claims": {
            "claim_run_id": CLAIM_RUN_ID,
            "node": NODE,
            "gpus": [GPU["cp"], GPU["member"]],
            "protocol": "scripts/m7_gpu_occupancy_guard.py pass 1 -> claims written under /dev/shm/blind-gains/gpu_claims -> guard pass 2 with --ignore-claim-run-id -> launch -> worker pids stamped into claims",
            "removed_after_completion": True,
        },
        "instrument_tests": {
            "suite": "tests/test_catch_stability.py",
            "result": "27 passed",
            "run_at_git_head": git_head,
        },
        "hash_checks": checks,
        "cells": cells,
        "scorer": {
            "path": "src/eval/catch_stability.py",
            "sha256": checks["scorer"]["recomputed_sha256"],
            "invocation": (
                "PYTHONPATH=. .venv/bin/python src/eval/catch_stability.py "
                f"--cp-scores {RUN_CP}/shards/shard_0.jsonl "
                f"--member-scores {RUN_MEMBER}/shards/shard_0.jsonl "
                f"--output {READOUT_JSON} "
                f"--per-row-output-cp {RUN_CP}/catch_stability_rows_cp.jsonl "
                f"--per-row-output-member {RUN_MEMBER}/catch_stability_rows_member.jsonl "
                "--expect registered"
            ),
            "exit_code": 0,
        },
        "readout": {
            "json": READOUT_JSON,
            "json_sha256": sha256(READOUT_JSON),
            "md": MD_OUT,
        },
        "scope_note": (
            "Fills the instrument-absent F8 secondary (catch-trial stability, "
            "reports/f8_secondaries_v1.md section 2). No decision branch is attached; "
            "the published F8 primary readout and its branch decision are unaffected."
        ),
    }
    (ROOT / PROVENANCE_OUT).write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")

    # ------------------------------------------------------------------ md ---
    arms = readout["arms"]
    cvm = readout["cp_vs_member"]["per_template"]

    def rate_cell(arm: str, tpl: str, ind: str) -> str:
        block = arms[arm]["per_template"][tpl][ind]
        return f"{block['count']}/100 ({block['rate']:.2f})"

    lines: list[str] = []
    a = lines.append
    a("# Mini-A5 catch-trial stability — registered readout v1")
    a("")
    a("Numbers, checks, and provenance only; no interpretation. Registration"
      " (binding): `docs/registered_mini_a5_catch_stability_v1.md`; instrument"
      " committed at `fc57cb8`; scorer schema `blind-gains.mini-a5-catch-stability.v1`.")
    a("")
    a("**Scope.** This readout fills the registered-but-instrument-absent F8"
      " secondary 2 (catch-trial stability, `reports/f8_secondaries_v1.md` section 2)."
      " The F8 primary readout (`reports/f8_mini_a5_endpoint_readout_v1.md`) is already"
      " published and its branch decision has fired; **nothing in this file can alter"
      " the published F8 primary or that branch decision**. No decision branch is"
      " attached to this secondary (`automatic_branch_assignment: false`).")
    a("")
    a("## 1. What ran")
    a("")
    a("| item | value |")
    a("|---|---|")
    a(f"| eval manifest | `data/derived/mini_a5_catch_eval_manifest_v1.jsonl` (300 pairs, 3 templates x 100; sha256 `{REGISTERED['manifest'][:16]}...`, verified pre-launch and post-run) |")
    a(f"| CP checkpoint | `{CKPT['cp']}` (index sha256 `{REGISTERED['cp_index'][:16]}...`, recomputed post-run, matches registration) |")
    a(f"| member checkpoint | `{CKPT['member']}` (index sha256 `{REGISTERED['member_index'][:16]}...`, recomputed post-run, matches registration) |")
    a("| harness | `scripts/eval_qwen_vl_fliptrack.py` via `scripts/launch_fliptrack_eval_shards.sh` (same path as the F8 cells); greedy, seed 0, max-new-tokens 32, image-mode real, prompt contract `answer-tags-v1` |")
    cp_rm = cells[0]["run_manifest"]
    mem_rm = cells[1]["run_manifest"]
    a(f"| CP run | `{RUN_CP}` — {NODE} GPU {GPU['cp']}, {cp_rm['start_time_utc']} to {cp_rm['end_time_utc']}, status {cp_rm['status']} |")
    a(f"| member run | `{RUN_MEMBER}` — {NODE} GPU {GPU['member']}, {mem_rm['start_time_utc']} to {mem_rm['end_time_utc']}, status {mem_rm['status']} |")
    a(f"| git HEAD at launch | `{git_head}` |")
    a(f"| scorer | `src/eval/catch_stability.py` (sha256 `{REGISTERED['scorer'][:16]}...`), exit code 0 |")
    a("| out-of-band provenance | `reports/mini_a5_catch_run_provenance_v1.json` (launcher records null checkpoint provenance for this job type; see that file) |")
    a("")
    a("## 2. Checks")
    a("")
    a("- Every pinned hash of registration section 2 re-verified on disk at launch"
      " AND recomputed post-run: source pairs, decontamination, audit, adapter,"
      " derived manifest + provenance sidecar + tracked record, scorer, both"
      " checkpoint index files. All pass (`hash_checks` block of the provenance record).")
    a("- Row counts: 300 pairs per arm in each shard output; `prediction_a` and"
      " `prediction_b` present on every row = 600 generations per arm, 1,200 total.")
    a("- Scorer join checks (from the readout JSON): identical uid sets across arms,"
      " 300 pairs joined, template ids agree across arms, 100 pairs per template.")
    a("- Both run manifests: status `complete`, pinned manifest hash, pinned prompt"
      " contract sha256, seed 0, max_new_tokens 32, image_mode real.")
    a("- The readout JSON consumed exactly the two shard files produced by these runs"
      " (paths and sha256s match; asserted when this file was generated).")
    a("- Instrument test suite `tests/test_catch_stability.py`: 27 passed at the"
      " launch HEAD.")
    a("- Placement: one GPU per arm on an29 (GPUs 5 and 7), guard-checked and claim-file"
      " protected; GPUs 0-3 (M7 training) and 6 (A1-real eval) untouched; claims removed"
      " after completion.")
    a("")
    a("## 3. Per-template rates (100 pairs per template per arm; never pooled — I13)")
    a("")
    for arm in ("cp", "member"):
        a(f"### {'CP-GRPO' if arm == 'cp' else 'same-data GRPO (member)'} arm")
        a("")
        a("| template | stable_lenient | stable_strict | pair_correct | strict_pair_correct | stable_and_correct_lenient | stable_and_correct_strict |")
        a("|---|---|---|---|---|---|---|")
        for tpl in TEMPLATES:
            cellstr = " | ".join(rate_cell(arm, tpl, ind) for ind in INDICATORS)
            a(f"| {tpl} | {cellstr} |")
        a("")
    a("## 4. CP minus member, per template (paired bootstrap 10,000 draws, percentile 2.5/97.5, identical indices; exact two-sided McNemar)")
    a("")
    a("| template | indicator | idx | seed | delta | 95% CI | excl. 0 | b01/b10 | McNemar p |")
    a("|---|---|---:|---:|---:|---|---|---|---:|")
    for tpl in TEMPLATES:
        block = cvm[tpl]["cp_minus_member"]
        for ind in INDICATORS:
            c = block[ind]
            mc = c["mcnemar_exact_two_sided"]
            a(f"| {tpl} | {ind} | {c['indicator_index']} | {c['bootstrap_seed']} | "
              f"{c['point']:+.4f} | [{c['ci95_low']:+.4f}, {c['ci95_high']:+.4f}] | "
              f"{c['excludes_zero']} | {mc['b01']}/{mc['b10']} | {mc['p_value']:.3g} |")
    a("")
    a("Seeds follow the frozen derivation `seed = 20260729 + 1000*indicator_index +"
      " 10*template_index` (template order sorted: matrix 0, scatter 1, trajectory 2);"
      " every resolved seed above is also recorded per cell in the readout JSON."
      " Alpha 0.05, two-sided, no multiplicity correction; 18 contrasts, none feeds a"
      " decision rule. Intervals quantify evaluation uncertainty on a fixed pair set"
      " only; each arm is one training run.")
    a("")
    a("## 5. Artifacts")
    a("")
    a("| artifact | sha256 |")
    a("|---|---|")
    a(f"| `{READOUT_JSON}` | `{provenance['readout']['json_sha256']}` |")
    for cell in cells:
        a(f"| `{cell['shard_output']}` | `{cell['shard_output_sha256']}` |")
        a(f"| `{cell['per_row_scored_output']}` | `{cell['per_row_scored_output_sha256']}` |")
    a("| `reports/mini_a5_catch_run_provenance_v1.json` | (this commit) |")
    a("")
    a("`experiments/runs/` is gitignored; shard predictions, per-row scored files,"
      " logs, and the driver state dir live on cluster storage. This file, the readout"
      " JSON, and the provenance record are the committed record.")
    a("")
    (ROOT / MD_OUT).write_text("\n".join(lines))
    print(f"wrote {PROVENANCE_OUT}")
    print(f"wrote {MD_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
