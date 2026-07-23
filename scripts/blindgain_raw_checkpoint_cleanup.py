#!/usr/bin/env python3
"""BlindGain-only raw-checkpoint cleanup with dry-run inventory and hash manifests.

Targets ONLY an explicit allowlist of raw FSDP shard files inside completed or
superseded BlindGain lineages whose merged HuggingFace checkpoints are verified
present. Never touches merged weights (actor/huggingface), trackers, configs,
logs, seed-3 lineages, the M5 long-horizon chain's fallback raw state, or any
path outside the BlindGain checkpoints tree.

Modes:
  --mode dry-run   write the inventory JSON, delete nothing
  --mode execute   re-verify, hash every file, write the manifest, then delete
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import datetime
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")

# (candidate_dir, reason, merged_proof_path or None)
CANDIDATES = [
    (
        "checkpoints/pilot/mech_a2_gray/global_step_60",
        "seed-1 A2 stub superseded by mech_a2_gray_resume60_retry2 (complete, merged, evaluated)",
        "checkpoints/pilot/mech_a2_gray_resume60_retry2/global_step_100/actor/huggingface/model.safetensors.index.json",
    ),
    (
        "checkpoints/pilot/mech_a1_real/global_step_60",
        "seed-1 A1 stub superseded by mech_a1_real_resume60 (complete, merged, evaluated); merged step-60 HF inside this dir is preserved for the registered ranking config",
        "checkpoints/pilot/mech_a1_real_resume60/global_step_100/actor/huggingface/model.safetensors.index.json",
    ),
    (
        "checkpoints/pilot/mech_a3_caption/global_step_20",
        "seed-1 A3 stub superseded by mech_a3_caption_resume20 (complete, merged, evaluated)",
        "checkpoints/pilot/mech_a3_caption_resume20/global_step_100/actor/huggingface/model.safetensors.index.json",
    ),
    (
        "checkpoints/pilot/mech_a2_gray_seed2/global_step_20",
        "seed-2 A2 stub superseded by mech_a2_gray_seed2_resume20 (complete, merged, evaluated)",
        "checkpoints/pilot/mech_a2_gray_seed2_resume20/global_step_100/actor/huggingface/model.safetensors.index.json",
    ),
    (
        "checkpoints/pilot/mech_a2b_noimage_seed2/global_step_20",
        "seed-2 A2b stub superseded by mech_a2b_noimage_seed2_resume20 (complete, merged, evaluated)",
        "checkpoints/pilot/mech_a2b_noimage_seed2_resume20/global_step_100/actor/huggingface/model.safetensors.index.json",
    ),
    (
        "checkpoints/pilot/mech_a2_gray_resume60_retry2/global_step_80",
        "seed-1 A2 final lineage complete; step-80 raw superseded by verified step-100",
        "checkpoints/pilot/mech_a2_gray_resume60_retry2/global_step_100/actor/huggingface/model.safetensors.index.json",
    ),
    (
        "checkpoints/pilot/mech_a2_gray_resume60_retry2/global_step_100",
        "seed-1 A2 final lineage complete, merged and evaluated; raw optimizer state has no registered resume future",
        "checkpoints/pilot/mech_a2_gray_resume60_retry2/global_step_100/actor/huggingface/model.safetensors.index.json",
    ),
    (
        "checkpoints/smoke/mini_a5_cp_plumbing_smoke_v1/global_step_1",
        "registered smoke checkpoint; docs/registered_mini_a5_smoke_v1.md declares retention-expired after the passed independent audit plus pre-deletion inventory",
        None,
    ),
    (
        "checkpoints/smoke/mini_a5_member_plumbing_smoke_v1/global_step_1",
        "registered smoke checkpoint; same retention rule as CP smoke",
        None,
    ),
    (
        "checkpoints/m5_anchor_resume_integrity_step101/global_step_101",
        "M5 restore-integrity test artifact; test passed and is recorded in the M4 authorization; not a resume source for the 200-400 continuation",
        None,
    ),
    (
        "checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_100",
        "anchor A0 raw resume source superseded by the M5 long-horizon chain (durable verified step-200); merged step-100 HF endpoint preserved in place",
        "checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_100/actor/huggingface/model.safetensors.index.json",
    ),
]

RAW_PATTERNS = ("model_world_size_", "optim_world_size_", "extra_state_world_size_")


def candidate_files(step_dir: Path) -> list[Path]:
    files: list[Path] = []
    actor = step_dir / "actor"
    if actor.is_dir():
        for entry in sorted(actor.iterdir()):
            if entry.is_file() and entry.name.startswith(RAW_PATTERNS):
                files.append(entry)
    loader = step_dir / "dataloader.pt"
    if loader.is_file():
        files.append(loader)
    # smoke checkpoints are model-only saves: model shards live directly in actor/
    return files


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 22), b""):
            digest.update(chunk)
    return digest.hexdigest()


def quota_snapshot() -> dict:
    out = subprocess.run(
        ["lfs", "quota", "-p", "2228473301", "/XYFS02"],
        capture_output=True,
        text=True,
    ).stdout
    return {"raw": out.strip().splitlines()[-2:] if out else []}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("dry-run", "execute"), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    os.chdir(ROOT)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    inventory = []
    total_bytes = 0
    for rel_dir, reason, merged_proof in CANDIDATES:
        step_dir = ROOT / rel_dir
        entry = {
            "candidate_dir": rel_dir,
            "reason": reason,
            "project_ownership": "BlindGain repository checkpoints tree; run manifests and trackers in-repo",
            "merged_proof": merged_proof,
            "merged_proof_present": bool(merged_proof and (ROOT / merged_proof).is_file()),
            "exists": step_dir.is_dir(),
            "files": [],
            "bytes": 0,
        }
        if step_dir.is_dir():
            files = candidate_files(step_dir)
            for f in files:
                size = f.stat().st_size
                entry["files"].append({"path": str(f.relative_to(ROOT)), "bytes": size})
                entry["bytes"] += size
            mtimes = [f.stat().st_mtime for f in files] or [0]
            entry["newest_mtime_utc"] = datetime.datetime.utcfromtimestamp(
                max(mtimes)
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
            preserved = []
            hf = step_dir / "actor" / "huggingface"
            if hf.is_dir():
                preserved.append(str(hf.relative_to(ROOT)))
            entry["preserved_in_place"] = preserved
        if merged_proof and not entry["merged_proof_present"]:
            entry["blocked"] = "merged proof missing; excluded from deletion"
        total_bytes += entry["bytes"]
        inventory.append(entry)

    report = {
        "schema_version": "blind-gains.raw-checkpoint-cleanup.v1",
        "mode": args.mode,
        "generated_utc": stamp,
        "git_hash": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "quota_before": quota_snapshot(),
        "total_candidate_bytes": total_bytes,
        "total_candidate_gib": round(total_bytes / (1 << 30), 2),
        "candidates": inventory,
        "protected_invariants": [
            "no path outside the BlindGain checkpoints tree is read or modified",
            "actor/huggingface merged weights preserved for every lineage",
            "checkpoint_tracker.json, experiment logs, and configs untouched",
            "no seed-3 lineage is a candidate",
            "m5_anchor_longhorizon_400/global_step_150 raw retained as M5 fallback resume state",
            "the /tmp checkpoint archive tier is not touched",
        ],
    }
    inv_path = args.output_dir / f"cleanup_inventory_{args.mode}_{stamp}.json"
    inv_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"inventory": str(inv_path), "total_gib": report["total_candidate_gib"]}))

    if args.mode == "dry-run":
        return

    deleted = []
    for entry in inventory:
        if not entry["exists"] or entry.get("blocked"):
            continue
        manifest_rows = []
        for frec in entry["files"]:
            path = ROOT / frec["path"]
            manifest_rows.append(
                {"path": frec["path"], "bytes": frec["bytes"], "sha256": sha256_file(path)}
            )
        cm_path = args.output_dir / (
            "checksums_" + entry["candidate_dir"].replace("/", "__") + ".json"
        )
        cm_path.write_text(json.dumps(manifest_rows, indent=1, sort_keys=True) + "\n")
        os.fsync(os.open(cm_path, os.O_RDONLY))
        for frec in entry["files"]:
            (ROOT / frec["path"]).unlink()
        deleted.append(
            {
                "candidate_dir": entry["candidate_dir"],
                "bytes_removed": entry["bytes"],
                "checksum_manifest": str(cm_path),
                "checksum_manifest_sha256": sha256_file(cm_path),
            }
        )
        print(json.dumps({"deleted": entry["candidate_dir"], "gib": round(entry["bytes"] / (1 << 30), 2)}), flush=True)

    exec_report = {
        "schema_version": "blind-gains.raw-checkpoint-cleanup-execution.v1",
        "generated_utc": datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"),
        "dry_run_inventory": str(inv_path),
        "deleted": deleted,
        "quota_after": quota_snapshot(),
    }
    exec_path = args.output_dir / f"cleanup_execution_{stamp}.json"
    exec_path.write_text(json.dumps(exec_report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"execution_report": str(exec_path)}))


if __name__ == "__main__":
    main()
