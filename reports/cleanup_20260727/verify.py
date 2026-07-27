#!/usr/bin/env python3
"""Post-cleanup verification for the 2026-07-27 cross-path storage cleanup."""
import glob
import json
import os
import subprocess
import sys

BG = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
os.chdir(BG)
fails = []


def check(label, ok, detail=""):
    print("  %-4s %s%s" % ("PASS" if ok else "FAIL", label, (" :: " + detail) if detail else ""))
    if not ok:
        fails.append(label)


print("=== [A] eval endpoint configs still resolve ===")
missing, checked = [], 0
for f in sorted(glob.glob("configs/eval/*.json")):
    try:
        d = json.load(open(f))
    except Exception as exc:
        missing.append((f, "unparseable: %s" % exc))
        continue
    p = d.get("checkpoint_path")
    if not p:
        continue
    checked += 1
    if not os.path.exists(p):
        missing.append((f, p))
check("%d configs with checkpoint_path, %d missing" % (checked, len(missing)), not missing)
for f, p in missing[:10]:
    print("       MISSING %s -> %s" % (f, p))

print("=== [B] per-lineage training telemetry intact ===")
need = ["experiment_log.jsonl", "experiment_config.json", "generations.log", "checkpoint_tracker.json"]
roots, gaps = [], []
for base in ("checkpoints/pilot", "checkpoints"):
    for d in sorted(glob.glob(base + "/*")):
        if not os.path.isdir(d):
            continue
        if not glob.glob(d + "/global_step_*"):
            continue
        # A *training* lineage produced real weights or a training log. Storage
        # dry-cycle probes contain only relocation-marker JSONs and never had
        # telemetry, so they are not lineages and must not be flagged.
        if not (os.path.exists(os.path.join(d, "experiment_log.jsonl"))
                or glob.glob(d + "/global_step_*/actor/huggingface")):
            print("       (skipped non-lineage probe: %s)" % d)
            continue
        roots.append(d)
        for n in need:
            if not os.path.exists(os.path.join(d, n)):
                gaps.append("%s/%s" % (d, n))
check("%d lineage roots scanned, %d missing telemetry files" % (len(roots), len(gaps)), not gaps)
for g in gaps[:15]:
    print("       MISSING %s" % g)

print("=== [C] the four seed-1 experiment_log.jsonl behind the published table ===")
pub = [
    "checkpoints/pilot/mech_a1_real_resume60/experiment_log.jsonl",
    "checkpoints/pilot/mech_a2_gray_resume60_retry2/experiment_log.jsonl",
    "checkpoints/pilot/mech_a2b_noimage_retry4/experiment_log.jsonl",
    "checkpoints/pilot/mech_a3_caption_resume20/experiment_log.jsonl",
]
for p in pub:
    check(p, os.path.exists(p), "%d bytes" % os.path.getsize(p) if os.path.exists(p) else "GONE")

print("=== [D] held-by-ruling raw blocks still present ===")
held = [
    "/XYFS02/HDD_POOL/paratera_xy/pxy1289/blindgain_archive/login_tmp_checkpoint_archive",
    "checkpoints/pilot/mech_a3_caption_seed3/global_step_100/actor",
    "checkpoints/m5_anchor_longhorizon_400/global_step_150/actor",
    "checkpoints/m5_anchor_longhorizon_400_resume150/global_step_300/actor",
]
for h in held:
    n = len(glob.glob(os.path.join(h, "*world_size_4*"))) if "actor" in h else -1
    check(h, os.path.exists(h), ("%d raw shards" % n) if n >= 0 else "present")

print("=== [E] live-job + kept caches intact ===")
for p in ["artifacts/hf_home/hub/datasets--hiyouga--geometry3k",
          "artifacts/hf_home/hub/datasets--TIGER-Lab--ViRL39K",
          "artifacts/hf_home/hub/models--facebook--dinov2-small",
          "data/modelscope/MathVerse/images.zip",
          "artifacts/datasets/hf_rayguan_HallusionBench_retry_no_xet",
          "artifacts/datasets/hf_MMVP_MMVP_retry_no_xet",
          "artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct",
          "data/mini_a5_train_v1/train.parquet",
          "data/virl39k/images"]:
    check(p, os.path.exists(p))

print("=== [F] git: no tracked file deleted ===")
out = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout
dels = [l for l in out.splitlines() if l[:2] in (" D", "D ", "DD")]
check("tracked deletions", not dels, "%d" % len(dels))
for d in dels[:10]:
    print("       %s" % d)

print("=== [G] live M5 run still writing ===")
mf = "experiments/runs/m5_anchor_longhorizon_segment300_350_an12_20260726T090446Z/run_manifest.json"
if os.path.exists(mf):
    m = json.load(open(mf))
    check("run_manifest status", m.get("status") == "running", str(m.get("status")))
tr = "checkpoints/m5_anchor_longhorizon_400_resume150/checkpoint_tracker.json"
if os.path.exists(tr):
    print("       tracker: %s" % json.load(open(tr)))
el = "checkpoints/m5_anchor_longhorizon_400_resume150/experiment_log.jsonl"
if os.path.exists(el):
    print("       experiment_log.jsonl: %d bytes, mtime %s" % (
        os.path.getsize(el), subprocess.run(["date", "-u", "-r", el, "+%FT%TZ"], capture_output=True, text=True).stdout.strip()))

print()
print("RESULT: %s (%d failures)" % ("ALL CHECKS PASS" if not fails else "FAILURES PRESENT", len(fails)))
sys.exit(1 if fails else 0)
