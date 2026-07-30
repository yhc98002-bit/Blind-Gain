# M5C noise floor -- replicate evaluation of the same checkpoint (v1)

Generated 2026-07-30T12:33:30Z | git `ed4aa962f2bd945638b0183316be73137299cbcd`

## What was measured

McNemar on the step-100->400 substrate tests only whether the NET change departs from zero. It does not test whether the TOTAL turnover of 137/601 items exceeds evaluation/decoding noise. That test requires a replicate: the same checkpoint evaluated twice under an identical contract. Four replicate cells were run (step 400 x2, step 100 x2), 601 Geometry3K test items each.

## Runs

| label | run id | node/gpu | step | ckpt index sha256 | wall | per_item sha256 |
|---|---|---|---|---|---|---|
| `step400_r1` | `m5c_noisefloor_step400_r1_an29_gpu0_20260730T015228Z` | an29/0 | 400 | `4e6c95b75959c3bf` | 2026-07-30T01:52:38Z -> 2026-07-30T02:03:13Z | `60eac65a8b5bb9b3` |
| `step400_r2` | `m5c_noisefloor_step400_r2_an29_gpu1_20260730T015314Z` | an29/1 | 400 | `4e6c95b75959c3bf` | 2026-07-30T01:53:14Z -> 2026-07-30T02:03:13Z | `60eac65a8b5bb9b3` |
| `step100_r1` | `m5c_noisefloor_step100_r1_an29_gpu2_20260730T015523Z` | an29/2 | 100 | `ceaedcaab63781b5` | 2026-07-30T01:55:24Z -> 2026-07-30T02:09:56Z | `4a4a840f9a3edb1b` |
| `step100_r2` | `m5c_noisefloor_step100_r2_an29_gpu3_20260730T015600Z` | an29/3 | 100 | `ceaedcaab63781b5` | 2026-07-30T01:56:01Z -> 2026-07-30T02:10:08Z | `4a4a840f9a3edb1b` |
| `step400_cached` | `m5_geo3k_step400_an12_gpu0_20260728T053115Z` | an12/0 | 400 | `4e6c95b75959c3bf` | 2026-07-28T05:31:31Z -> 2026-07-28T05:38:54Z | `60eac65a8b5bb9b3` |
| `step100_cached` | `blind_solvability_v2_guarded_rescore_anchor_step100_geo3k_real_login_20260712T082107Z` | login/- | None | `null` | 2026-07-12T08:21:32Z -> 2026-07-12T08:22:21Z | `22d93ad3f5510c49` |

## THE DECISIVE NUMBER -- replicate discordance (R1 vs R2, same checkpoint)

| step | metric | discordant | fraction | agreement | R1 acc | R2 acc | acc diff |
|---|---|---|---|---|---|---|---|
| 400 | acc_final | 0/601 | 0.0000 | 1.000000 | 0.444260 | 0.444260 | +0.000000 |
| 400 | acc_strict | 0/601 | 0.0000 | 1.000000 | 0.444260 | 0.444260 | +0.000000 |
| 100 | acc_final | 0/601 | 0.0000 | 1.000000 | 0.435940 | 0.435940 | +0.000000 |
| 100 | acc_strict | 0/601 | 0.0000 | 1.000000 | 0.435940 | 0.435940 | +0.000000 |

## Response-text byte identity (stronger than the binary metric)

| step | pair | byte-identical | differing |
|---|---|---|---|
| 400 | r1_vs_r2 | 601/601 (1.0000) | 0 |
| 400 | r1_vs_cached | 601/601 (1.0000) | 0 |
| 400 | r2_vs_cached | 601/601 (1.0000) | 0 |
| 100 | r1_vs_r2 | 601/601 (1.0000) | 0 |
| 100 | r1_vs_cached | 601/601 (1.0000) | 0 |
| 100 | r2_vs_cached | 601/601 (1.0000) | 0 |

## Whole-artifact identity

- **step 400**: `step400_r1`=`60eac65a8b5bb9b3`, `step400_r2`=`60eac65a8b5bb9b3`, `step400_cached`=`60eac65a8b5bb9b3` -- all identical: **True**
  - matches the sha256 recorded as step-400 provenance in `reports/m5c_turnover_v1.json`: **True**
- **step 100**: `step100_r1`=`4a4a840f9a3edb1b`, `step100_r2`=`4a4a840f9a3edb1b` -- all identical: **True**
  - cached excluded: The cached step-100 column lives in a different row schema (guarded rescore, 1889 rows incl. train, greedy_* field names), so whole-file sha comparison is not meaningful there; the per-item and per-response comparisons above cover it.

Checkpoint identity (replicate vs cached):

| step | same resolved checkpoint path | replicate ckpt index sha256 | cached |
|---|---|---|---|
| 400 | True | `4e6c95b75959c3bf7ad9895beb6ce9f77074973f3287f225cb49726a584c0fb1` | `4e6c95b75959c3bf7ad9895beb6ce9f77074973f3287f225cb49726a584c0fb1` |
| 100 | True | `ceaedcaab63781b5ed051d465f8e652c5436db035be6da0d98dd2fe404fefadb` | not recorded by the rescore manifest |

## Does each replicate reproduce the CACHED substrate column?

| step | pair | metric | agreement | discordant | cached acc | replicate acc |
|---|---|---|---|---|---|---|
| 400 | r1_vs_cached | acc_final | 601/601 (1.000000) | 0 | 0.444260 | 0.444260 |
| 400 | r1_vs_cached | acc_strict | 601/601 (1.000000) | 0 | 0.444260 | 0.444260 |
| 400 | r2_vs_cached | acc_final | 601/601 (1.000000) | 0 | 0.444260 | 0.444260 |
| 400 | r2_vs_cached | acc_strict | 601/601 (1.000000) | 0 | 0.444260 | 0.444260 |
| 100 | r1_vs_cached | acc_final | 601/601 (1.000000) | 0 | 0.435940 | 0.435940 |
| 100 | r1_vs_cached | acc_strict | 601/601 (1.000000) | 0 | 0.435940 | 0.435940 |
| 100 | r2_vs_cached | acc_final | 601/601 (1.000000) | 0 | 0.435940 | 0.435940 |
| 100 | r2_vs_cached | acc_strict | 601/601 (1.000000) | 0 | 0.435940 | 0.435940 |

## Floor vs observed turnover -- arithmetic only

Observed step-100->400 turnover: 137/601 = 0.2280.

| step | metric | floor count | floor fraction | turnover/floor | turnover-floor |
|---|---|---|---|---|---|
| 400 | acc_final | 0 | 0.0000 | undefined (floor = 0) | 137 |
| 400 | acc_strict | 0 | 0.0000 | undefined (floor = 0) | 137 |
| 100 | acc_final | 0 | 0.0000 | undefined (floor = 0) | 137 |
| 100 | acc_strict | 0 | 0.0000 | undefined (floor = 0) | 137 |

## Readout

MEASURED FLOOR IS ZERO. Re-evaluating the same checkpoint twice under the cached decoding contract produced 0/601 discordant items on acc_final and 0/601 on acc_strict, at BOTH step 400 and step 100, and both replicate accuracies equal the cached accuracy exactly (step 400: 267/601 = 0.4442595674; step 100: 262/601 = 0.4359400998). The turnover/floor ratio is undefined because the denominator is zero; the floor-subtracted turnover is 137 - 0 = 137 items. Measurement noise in this harness is therefore 0 items, and all 137 step-100-to-400 flips are policy differences between the two checkpoints, not evaluation or decoding noise.

Beyond the binary metric, all 601 greedy response STRINGS are byte-identical across every compared pair (R1 vs R2, R1 vs cached, R2 vs cached, at both steps). Greedy decoding in this harness is bitwise reproducible across replicate, across node (an12 vs an29), across GPU index, across date, and -- at step 100 -- across generation harness.

### Superseded reference figure

`reports/m5c_turnover_v1.json :: noise_reference_not_a_test` recorded an expected discordance of 0.2133 from 16-sample temperature-1.0 dispersion, explicitly labelled not-a-test. That figure describes temperature-1.0 sampling dispersion, not the greedy evaluation harness. It is NOT the replicate noise floor and is superseded by the directly measured floor in this report.

### Scope

This report addresses only the TURNOVER-MAGNITUDE soft spot. The separate reproducible-LOST-items result (3-way Jaccard 0.3118 vs permutation null 0.0221, p<=1e-4) is unaffected either way: per-item noise would reduce cross-checkpoint agreement, not manufacture it. The two results are not conflated here.

## Contract provenance -- what is and is not an exact replicate

- **step 400**: EXACT replicate. The cached step-400 run and both replicates invoke the same script scripts/run_pilot_geo3k_step100_eval.py with the same --batch-size 4, --max-model-len 8192, --max-tokens 2048, --seed 20260710, temperature 0, top_p 1, and the same checkpoint index sha256 4e6c95b75959c3bf7ad9895beb6ce9f77074973f3287f225cb49726a584c0fb1; only output paths, node and GPU differ (cached an12 gpu0 2026-07-28; replicates an29 gpu0/gpu1 2026-07-30).
- **step 100**: R1-vs-R2 is an exact within-harness replicate. R-vs-CACHED is additionally a CROSS-HARNESS comparison: the cached step-100 substrate column came from scripts/run_blind_solvability_v2.py (greedy n=1 PLUS 16 samples at temperature 1.0 in the same vLLM session, an12 gpu5, 2026-07-12), rescored on the login node by scripts/rescore_blind_solvability_v2_guarded.py, whereas the replicates used the greedy-only pilot harness. Any R-vs-cached step-100 difference could therefore reflect harness difference rather than nondeterminism; agreement across that gap is correspondingly stronger evidence than a same-harness match.

## Determinism audit -- the replicates decoded fresh

A zero floor would be an artifact if a replicate had reused cached generations, so each cell is audited for that.

| label | manifest resume_from | `--resume-from` in cmd | resumed rows in log | shard loads | weight load | run-scoped node-local cache dir |
|---|---|---|---|---|---|---|
| `step400_r1` | None | False | 0 | 2 | True | True |
| `step400_r2` | None | False | 0 | 2 | True | True |
| `step100_r1` | None | False | 0 | 2 | True | True |
| `step100_r2` | None | False | 0 | 2 | True | True |

Eval harness byte-identical between the cached step-400 commit `4dc541b3814f` and the replicate commit `ed4aa962f2bd` over `scripts/run_pilot_geo3k_step100_eval.py`, `src/eval/`, `src/rewards/`: **True**.

## Verification

| label | stored vs recomputed acc_final | acc_strict | n |
|---|---|---|---|
| `step400_r1` | 601 | 601 | 601 |
| `step400_r2` | 601 | 601 | 601 |
| `step100_r1` | 601 | 601 | 601 |
| `step100_r2` | 601 | 601 | 601 |
| `step400_cached` | 601 | 601 | 601 |
| `step100_cached` | 601 | 601 | 601 |

Recomputed cached column vs `reports/m5c_item_substrate_v1.jsonl`:

- step 100 acc_final: 601/601 match (1.000000)
- step 100 acc_strict: 601/601 match (1.000000)
- step 400 acc_final: 601/601 match (1.000000)
- step 400 acc_strict: 601/601 match (1.000000)

## Verbatim replicate command (step 400 R1)

```
TRANSFORMERS_OFFLINE=1 HF_HOME=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/artifacts/hf_home CUDA_VISIBLE_DEVICES=0 VLLM_WORKER_MULTIPROC_METHOD=spawn PYTHONHASHSEED=0 PYTHONPATH=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain:/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/artifacts/repos/EasyR1 .venv/bin/python scripts/run_pilot_geo3k_step100_eval.py --arm anchor_real --condition real --model-path /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/checkpoints/m5_anchor_longhorizon_400_resume150/global_step_400/actor/huggingface --manifest data/geometry3k_caption_images_manifest.jsonl --format-prompt artifacts/repos/EasyR1/examples/format_prompt/r1v.jinja --output experiments/runs/m5c_noisefloor_step400_r1_an29_gpu0_20260730T015228Z/per_item.jsonl --cache-dir /dev/shm/blind-gains/m5c_noisefloor_step400_r1_an29_gpu0_20260730T015228Z/condition_cache --run-manifest experiments/runs/m5c_noisefloor_step400_r1_an29_gpu0_20260730T015228Z/run_manifest.json --source-training-manifest experiments/runs/m5c_noisefloor_step400_r1_an29_gpu0_20260730T015228Z/source_training_manifest_snapshot.json --checkpoint-index-sha256 4e6c95b75959c3bf7ad9895beb6ce9f77074973f3287f225cb49726a584c0fb1 --batch-size 4 --max-model-len 8192 --max-tokens 2048 --seed 20260710 --global-step 400 --row-schema-version blind-gains.m5-geo3k-checkpoint-eval.v1
```

