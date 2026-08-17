# Stale an12 GPU-claim removal — 2026-08-17

Removed before filling an12 4–7 per the PI utilization directive. All four
claim pids are dead; gpu4–6 claims are Aug-3 c5 leftovers, gpu7 is the
completed 2026-08-16 m7 seed-2 a2_gray eval whose launcher cleanup did not
run. Byte-exact contents:

## an12_gpu4.claim (mtime 2026-08-03 23:18:08.043181274 +0800)
```
{
  "schema_version": "blind-gains.gpu-claim.v1",
  "run_id": "c5_a2_gray_seed1_7b_an12_20260803T151727Z",
  "node": "an12",
  "gpu": 4,
  "pid": 3371976,
  "created_utc": "2026-08-03T15:18:07Z",
  "purpose": "c5_7b_access_arm",
  "registration": "docs/registered_c5_7b_access_pair_v1.md"
}
```
sha256: 1841ed0a89dfe7a476e6bb1ae1f3e498b789520edd1a1cfe2ee2a1547f418f9f

## an12_gpu5.claim (mtime 2026-08-03 23:18:08.047181304 +0800)
```
{
  "schema_version": "blind-gains.gpu-claim.v1",
  "run_id": "c5_a2_gray_seed1_7b_an12_20260803T151727Z",
  "node": "an12",
  "gpu": 5,
  "pid": 3371976,
  "created_utc": "2026-08-03T15:18:07Z",
  "purpose": "c5_7b_access_arm",
  "registration": "docs/registered_c5_7b_access_pair_v1.md"
}
```
sha256: 8e970c948369de6116e2fcf78d983b316818dcfbdcce25d6dec2d1e0a4cd8bfa

## an12_gpu6.claim (mtime 2026-08-03 23:18:08.051181333 +0800)
```
{
  "schema_version": "blind-gains.gpu-claim.v1",
  "run_id": "c5_a2_gray_seed1_7b_an12_20260803T151727Z",
  "node": "an12",
  "gpu": 6,
  "pid": 3371976,
  "created_utc": "2026-08-03T15:18:07Z",
  "purpose": "c5_7b_access_arm",
  "registration": "docs/registered_c5_7b_access_pair_v1.md"
}
```
sha256: 07536e2ca236548694546e545e3b0a653ded2c711f6766dbe0f5f03f87bbc709

## an12_gpu7.claim (mtime 2026-08-16 16:25:50.489891460 +0800)
```
{"gpu":7,"run_id":"m7_seed2_a2_gray_step100_eval","pid":749434,"eval_run_dir":"experiments/runs/m7_step100_heldout_seed2_a2_gray_seed2_gray_an12_20260816T082503Z","written_utc":"2026-08-16T08:25:49Z","written_by":"scripts/launch_m7_seed2_eval.sh"}
```
sha256: 581279a569f4ed414dcff8b82476c989e68f04bcd47423cd723ad275bc1cf365

