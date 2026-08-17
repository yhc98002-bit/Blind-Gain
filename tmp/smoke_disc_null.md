# M5C Task B — expected-discordance null from sampled per-item rates at BOTH endpoints

- schema: `blind-gains.m5c-expected-discordance-null.v1`
- generated: 2026-07-30T12:42:02Z
- git: `357b4c60fe23f0f730cb98d6cdb2fdb83b6aa650`
- source JSON: `reports/smoke_disc_null.json`

## 0. What this closes and what it does not

Does the OBSERVED greedy discordance between geo3k step 100 and step 400 (137/601) exceed what independent per-item stochastic draws at each endpoint's own sampled success rate would produce?

Null: `E[disc] = mean_i [ p_i(100)(1-p_i(400)) + (1-p_i(100)) p_i(400) ], with p_i estimated separately at EACH endpoint from 16 temperature-1.0 samples.`

The prior figure recorded in `reports/m5c_turnover_v1.json` (`noise_reference_not_a_test`) estimated p_i from 16-sample temperature decoding at step 100 ONLY and then assumed the same per-item rates at step 400. That assumption is the thing under question, so p_i is estimated separately at each endpoint here.

Prior reference figure reproduced exactly before replacing it: recorded 0.21327735024958402, recomputed 0.21327735024958402.

## 1. Sampled protocol, verbatim

### step 100 — `blind_solvability_v2_anchor_step100_geo3k_guarded_real_an12_20260712T053344Z`

```json
{
  "greedy": {
    "n": 1,
    "temperature": 0,
    "top_p": 1
  },
  "max_tokens": 2048,
  "sampled": {
    "n": 16,
    "temperature": 1.0,
    "top_p": 1
  },
  "seed": 20260710
}
```

- `sample_count` = 16
- `sample_temperature` = 1.0
- `seed` = 20260710
- `max_tokens` = 2048
- `group_size` = 5, `format_weight` = 0.5
- `model_revision` = `checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_100/actor/huggingface`
- `prompt_contract_sha256` = `7ac39f53a2a824490fc5ee22671a888d2d79d55e1d8351919006d7d71c7a8f3f`
- `source_manifest_sha256` = `0ac91fb836f39776acd5137ccd5cca7259d4ad0a836347be60f96f535d00f639`
- `parser_version` = `canonical-v2`, `scoring_mode` = `pilot-reward-v1+canonical-v2`
- `per_item.jsonl` sha256 = `22d93ad3f5510c49d9755d82dd0cdb148ea0818f75db77e7363b757b8ed0d8c4`

Command:

```
TRANSFORMERS_OFFLINE=1 HF_HOME=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/artifacts/hf_home CUDA_VISIBLE_DEVICES=5 VLLM_WORKER_MULTIPROC_METHOD=spawn PYTHONHASHSEED=0 PYTHONPATH=. .venv/bin/python scripts/run_blind_solvability_v2.py --model-path checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_100/actor/huggingface --manifest data/geometry3k_caption_images_manifest.jsonl --train-filter-ids data/geo3k_pilot_filtered_ids.json --format-prompt artifacts/repos/EasyR1/examples/format_prompt/r1v.jinja --condition real --output experiments/runs/blind_solvability_v2_anchor_step100_geo3k_guarded_real_an12_20260712T053344Z/per_item.jsonl --cache-dir /dev/shm/blind-gains/blind_solvability_v2_anchor_step100_geo3k_guarded_real_an12_20260712T053344Z/condition_cache --run-manifest experiments/runs/blind_solvability_v2_anchor_step100_geo3k_guarded_real_an12_20260712T053344Z/run_manifest.json  --splits train test --batch-size 4 --max-model-len 8192 --max-tokens 2048 --sample-count 16 --sample-temperature 1.0 --group-size 5 --format-weight 0.5 --symbolic-grader-timeout-seconds 5.0 --seed 20260710
```

### step 400 — `blind_solvability_v2_anchor_step100_geo3k_guarded_real_an12_20260712T053344Z`

```json
{
  "greedy": {
    "n": 1,
    "temperature": 0,
    "top_p": 1
  },
  "max_tokens": 2048,
  "sampled": {
    "n": 16,
    "temperature": 1.0,
    "top_p": 1
  },
  "seed": 20260710
}
```

- `sample_count` = 16
- `sample_temperature` = 1.0
- `seed` = 20260710
- `max_tokens` = 2048
- `group_size` = 5, `format_weight` = 0.5
- `model_revision` = `checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_100/actor/huggingface`
- `prompt_contract_sha256` = `7ac39f53a2a824490fc5ee22671a888d2d79d55e1d8351919006d7d71c7a8f3f`
- `source_manifest_sha256` = `0ac91fb836f39776acd5137ccd5cca7259d4ad0a836347be60f96f535d00f639`
- `parser_version` = `canonical-v2`, `scoring_mode` = `pilot-reward-v1+canonical-v2`
- `per_item.jsonl` sha256 = `730cab92c78aa68d182b056c8c939bd40929572a3f0753e88d9d9a19b608e1d1`

Command:

```
TRANSFORMERS_OFFLINE=1 HF_HOME=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/artifacts/hf_home CUDA_VISIBLE_DEVICES=5 VLLM_WORKER_MULTIPROC_METHOD=spawn PYTHONHASHSEED=0 PYTHONPATH=. .venv/bin/python scripts/run_blind_solvability_v2.py --model-path checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_100/actor/huggingface --manifest data/geometry3k_caption_images_manifest.jsonl --train-filter-ids data/geo3k_pilot_filtered_ids.json --format-prompt artifacts/repos/EasyR1/examples/format_prompt/r1v.jinja --condition real --output experiments/runs/blind_solvability_v2_anchor_step100_geo3k_guarded_real_an12_20260712T053344Z/per_item.jsonl --cache-dir /dev/shm/blind-gains/blind_solvability_v2_anchor_step100_geo3k_guarded_real_an12_20260712T053344Z/condition_cache --run-manifest experiments/runs/blind_solvability_v2_anchor_step100_geo3k_guarded_real_an12_20260712T053344Z/run_manifest.json  --splits train test --batch-size 4 --max-model-len 8192 --max-tokens 2048 --sample-count 16 --sample-temperature 1.0 --group-size 5 --format-weight 0.5 --symbolic-grader-timeout-seconds 5.0 --seed 20260710
```

Greedy labels: temperature 0.0, top_p 1.0, n 1, seed 20260710, max_tokens 2048, from `reports/m5c_item_substrate_v1.jsonl` (sha256 `1fc5310785680afbf5420166c97d776ea77ab0b4081533097fd225648882a864`).

## 2. Results

### 2.1 Lenient — `acc_final (lenient, I7)`

Observed greedy discordance: **137/601 = 0.2280**

| quantity | plug-in `p=c/16` | Jeffreys `p=(c+0.5)/17` |
| --- | --- | --- |
| mean p_i step 100 | 0.3990 | 0.4050 |
| mean p_i step 400 | 0.3990 | 0.4050 |
| mean p_i (400 - 100) | 0.0000 | 0.0000 |
| Pearson r(p100, p400) | 1.0000 | 1.0000 |
| mean |p400 - p100| | 0.0000 | 0.0000 |
| **E[disc] fraction** | 0.2133 | 0.2460 |
| E[disc] count | 128.18 | 147.86 |
| observed - expected | 0.0147 | -0.0181 |
| observed - expected (count) | 8.82 | -10.86 |
| E[disc] bootstrap 95% CI | [0.1985, 0.2283] | [0.2329, 0.2593] |
| observed bootstrap 95% CI | [0.1947, 0.2629] | [0.1947, 0.2629] |
| (obs - exp) bootstrap 95% CI | [-0.0163, 0.0468] | [-0.0486, 0.0139] |
| bootstrap one-sided p (obs > exp) | 0.1782 | 0.8660 |
| MC null (plug-in p_i): null count mean +- sd | 128.13 +- 8.93 | 147.87 +- 9.76 |
| MC null (plug-in p_i): 95% range | [111.0, 146.0] | [129.0, 167.0] |
| MC null (plug-in p_i): one-sided p(null >= obs) | 0.1750 | 0.8782 |
| MC null (Jeffreys-posterior p_i): null count mean +- sd | 147.86 +- 9.71 | 147.86 +- 9.71 |
| MC null (Jeffreys-posterior p_i): 95% range | [129.0, 167.0] | [129.0, 167.0] |
| MC null (Jeffreys-posterior p_i): one-sided p(null >= obs) | 0.8788 | 0.8788 |

Per-item rate extremes (plug-in):

- step 100: 135 items at p=0, 63 at p=1
- step 400: 135 items at p=0, 63 at p=1

Single-endpoint reference variants (both-ends-same-p_i, for contrast only):

- p_i(100) at both ends: 0.2133
- p_i(400) at both ends: 0.2133

**Direction: OBSERVED IS NOT DISTINGUISHABLE from the sampled-variability expectation.** observed 0.2280 vs expected 0.2133; difference 0.0147 (bootstrap 95% CI [-0.0163, 0.0468]); one-sided Monte-Carlo p(null count >= observed) = 0.1750 plug-in, 0.8788 posterior-propagated.

- Licensed by this measurement: The TOTAL turnover between step 100 and step 400 is NOT shown to exceed what independent per-item temperature-1.0 draws at each endpoint's own rate would produce. The turnover COUNT is therefore consistent with per-item stochastic instability at this null, and a claim of hidden churn cannot rest on the turnover magnitude. A claim about WHICH items move is a separate quantity, measured in reports/m5c_lost_item_forensics_v1.json, and is not affected by this result: per-item noise would REDUCE cross-checkpoint agreement of the LOST sets, not manufacture it.
- NOT licensed by this measurement: This does NOT measure the greedy harness's replicate determinism. Every geo3k greedy eval is single-pass temperature-0.0 decoding; a greedy replicate floor is a separate measurement (Task A).

### 2.2 Strict contract — `acc_strict (contract-strict, I7)`

Observed greedy discordance: **137/601 = 0.2280**

| quantity | plug-in `p=c/16` | Jeffreys `p=(c+0.5)/17` |
| --- | --- | --- |
| mean p_i step 100 | 0.3990 | 0.4050 |
| mean p_i step 400 | 0.3990 | 0.4050 |
| mean p_i (400 - 100) | 0.0000 | 0.0000 |
| Pearson r(p100, p400) | 1.0000 | 1.0000 |
| mean |p400 - p100| | 0.0000 | 0.0000 |
| **E[disc] fraction** | 0.2133 | 0.2460 |
| E[disc] count | 128.18 | 147.86 |
| observed - expected | 0.0147 | -0.0181 |
| observed - expected (count) | 8.82 | -10.86 |
| E[disc] bootstrap 95% CI | [0.1985, 0.2283] | [0.2329, 0.2593] |
| observed bootstrap 95% CI | [0.1947, 0.2629] | [0.1947, 0.2629] |
| (obs - exp) bootstrap 95% CI | [-0.0163, 0.0468] | [-0.0486, 0.0139] |
| bootstrap one-sided p (obs > exp) | 0.1782 | 0.8660 |
| MC null (plug-in p_i): null count mean +- sd | 128.13 +- 8.93 | 147.87 +- 9.76 |
| MC null (plug-in p_i): 95% range | [111.0, 146.0] | [129.0, 167.0] |
| MC null (plug-in p_i): one-sided p(null >= obs) | 0.1750 | 0.8782 |
| MC null (Jeffreys-posterior p_i): null count mean +- sd | 147.86 +- 9.71 | 147.86 +- 9.71 |
| MC null (Jeffreys-posterior p_i): 95% range | [129.0, 167.0] | [129.0, 167.0] |
| MC null (Jeffreys-posterior p_i): one-sided p(null >= obs) | 0.8788 | 0.8788 |

Per-item rate extremes (plug-in):

- step 100: 135 items at p=0, 63 at p=1
- step 400: 135 items at p=0, 63 at p=1

Single-endpoint reference variants (both-ends-same-p_i, for contrast only):

- p_i(100) at both ends: 0.2133
- p_i(400) at both ends: 0.2133

**Direction: OBSERVED IS NOT DISTINGUISHABLE from the sampled-variability expectation.** observed 0.2280 vs expected 0.2133; difference 0.0147 (bootstrap 95% CI [-0.0163, 0.0468]); one-sided Monte-Carlo p(null count >= observed) = 0.1750 plug-in, 0.8788 posterior-propagated.

- Licensed by this measurement: The TOTAL turnover between step 100 and step 400 is NOT shown to exceed what independent per-item temperature-1.0 draws at each endpoint's own rate would produce. The turnover COUNT is therefore consistent with per-item stochastic instability at this null, and a claim of hidden churn cannot rest on the turnover magnitude. A claim about WHICH items move is a separate quantity, measured in reports/m5c_lost_item_forensics_v1.json, and is not affected by this result: per-item noise would REDUCE cross-checkpoint agreement of the LOST sets, not manufacture it.
- NOT licensed by this measurement: This does NOT measure the greedy harness's replicate determinism. Every geo3k greedy eval is single-pass temperature-0.0 decoding; a greedy replicate floor is a separate measurement (Task A).

### 2.3 Relation to the greedy replicate floor (Task A)

- source: `reports/m5c_noise_floor_replicate_v1.json` (sha256 `54e5e8c3f5d07deb8f2ed093ba9c1cb6fb73fd37753c0da7fac5bf29a408c7e5`)
- `measured_floor_is_zero` = True
- max replicate discordance across cells = 0
- greedy responses byte-identical across all replicate pairs = True

These are two different bars. The greedy replicate floor measured in Task A is the HARNESS floor: re-running the same checkpoint gives 0/601 discordance and byte-identical responses, so none of the observed 137 is measurement noise. The null computed HERE is a strictly more permissive bar: it asks whether 137 exceeds the per-item FRAGILITY implied by each checkpoint's own temperature-1.0 output distribution. A result that clears the Task A floor but not this null means the turnover is fully reproducible yet no larger than each endpoint's own decoding-level answer instability.

## 3. Checks

| check | value |
| --- | --- |
| `substrate_rows` | 601 |
| `item_key_sets_identical` | True |
| `samples_per_item_step100` | [16] |
| `samples_per_item_step400` | [16] |
| `step100_greedy_label_matches_substrate_acc_final` | 601 |
| `step100_greedy_label_matches_substrate_acc_strict` | 601 |
| `step400_sampledrun_greedy_matches_substrate_acc_final` | 464 |
| `step400_sampledrun_greedy_matches_substrate_acc_strict` | 464 |
| `step100_rescore_vs_guarded_sample_correct_identical` | 601 |
| `sampled_rows_correct_but_not_contract_valid_step100` | 0 |
| `sampled_rows_correct_but_not_contract_valid_step400` | 0 |
| `strict_equals_lenient_sampled_counts_step100` | True |
| `strict_equals_lenient_sampled_counts_step400` | True |
| `strict_equals_lenient_observed_greedy_discordance` | True |
| `decoding_settings_match_between_endpoints` | True |
| `prompt_contract_sha256_match` | True |
| `source_manifest_sha256_match` | True |
| `format_prompt_sha256_match` | True |
| `parser_version_match` | True |
| `scoring_mode_match` | True |
| `step400_run_status` | complete |
| `step400_run_exit_code` | 0 |
| `turnover_report_observed_discordance` | 137 |

### 3.1 Step-100 reproduction cell

- not available: step-100 reproduction cell not supplied or not complete

## 4. Caveats

- Sampled variability at temperature 1.0 is NOT identical to greedy replicate variability. This null bounds STOCHASTIC INSTABILITY of each checkpoint under temperature decoding; it does not measure the greedy harness's determinism.
- Temperature 1.0 is strictly noisier than temperature 0.0, so this null is an UPPER bound on the per-item stochastic churn a greedy comparison could inherit from decoding randomness. A comparison that fails to clear it does not clear a greedy-replicate noise floor either.
- p_i is estimated from only 16 samples per item per endpoint; the posterior-propagated Monte-Carlo null carries that estimation error, the plug-in null does not.
- The null treats the two endpoints as independent draws. Any true shared item difficulty structure is already inside p_i(100) and p_i(400); the independence assumption concerns only the residual draw, which is exactly the null being tested.
- The step-400 sampled cell was run with --splits test instead of the registered --splits train test. Test rows begin at global row index 1288 in the registered run and 1288 % batch_size(4) == 0, so per-item 4-row batch grouping is unchanged; the step-100 reproduction cell tests this empirically.

