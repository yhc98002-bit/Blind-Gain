#!/usr/bin/env python3
"""Correct the false status:"running" on the OOM-killed arm-4 run manifest.

Honest-provenance notes:
 - exit_code is NOT recorded: the process is gone and its wait status was never
   captured, so any number would be fabricated.
 - end_time_utc is DERIVED from the last write to the stdout/stderr log and is
   labelled as such, not observed at exit.
"""
import datetime as dt, json, os, sys
from pathlib import Path

RUN = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/"
           "experiments/runs/m7_virl_a3_caption_seed1_an29_20260730T121906Z")
man = RUN / "run_manifest.json"
log = RUN / "logs" / "an29.log"
p = json.loads(man.read_text())
if p.get("status") != "running":
    print("status already %r; no change" % p.get("status")); sys.exit(0)
mt = dt.datetime.fromtimestamp(log.stat().st_mtime, dt.timezone.utc)
oom = [l.strip() for l in log.read_text(errors="replace").splitlines()
       if "torch.OutOfMemoryError" in l]
p.update({
    "status": "fail",
    "end_time_utc_source": "last write to stdout_stderr_log (process exit was not observed live)",
    "end_time_utc": mt.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "failure_reason": {
        "class": "cuda_oom_during_vllm_kv_cache_allocation",
        "verbatim": oom[-1] if oom else "(no torch.OutOfMemoryError line found)",
        "contending_pids_on_requested_gpus": [1475268, 1476867],
        "contending_jobs": [
            "experiments/runs/m5c_sampled_m5c-taskb-step400_an29_gpu4_20260730T122620Z",
            "experiments/runs/m5c_sampled_m5c-taskb-step100-repro_an29_gpu5_20260730T122701Z"],
        "note": ("This arm claimed an29 GPUs 4-7 at 12:19:06Z and was still in vLLM "
                 "startup when two m5c_sampled endpoint evals were started onto physical "
                 "GPUs 4 and 5 at 12:26:20Z/12:27:01Z by a separate session. Those evals "
                 "are launched by scripts/launch_m5c_sampled_endpoint_eval.sh, which "
                 "carries no GPU-occupancy guard, so nothing refused the overlap. The M7 "
                 "GPU-scope guard protects an M7 launch from existing occupants; it cannot "
                 "protect an already-running M7 arm from a later non-M7 job."),
        "corrected_by": "verification session 2026-07-30T13:0XZ; status was falsely 'running'",
    },
})
tmp = man.with_name(".%s.partial.%d" % (man.name, os.getpid()))
with tmp.open("x") as fh:
    fh.write(json.dumps(p, indent=2, sort_keys=True) + "\n")
    fh.flush(); os.fsync(fh.fileno())
os.replace(tmp, man)
print("status -> fail; end_time_utc(derived) =", p["end_time_utc"])
print("OOM verbatim:", p["failure_reason"]["verbatim"][:160])
