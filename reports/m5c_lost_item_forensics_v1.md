# M5c — geo3k step-100 -> step-400 lost-item forensics (v1)

Generated 2026-07-29T17:59:01Z. CPU only; cached predictions only; no GPU job was started.
Facts, checks and provenance only.

## Provenance

- Dataset: Geometry3K test split (n=601), condition=real, arm=anchor_real, greedy temperature 0
- Scorer: `src.eval.blind_solvability.score_greedy_item_pilot under DEFAULT_PROMPT_CONTRACT (uniform re-score of cached predictions)`
- Answer canonicalization: normalize_answer -> numeric_value; numeric answers bucketed to 1e-6, non-numeric keep normalized text; contract-invalid rows carry no value and are counted separately
- Permutation convention: p = (hits + 1) / (n_perm + 1), n_perm = 10000, seed = 20260729, reported as max(p, 1e-04). p is reported as max((hits+1)/(n_perm+1), 1e-4); the smallest attainable value of the formula is 9.999e-5, so the floor binds only at zero hits
- Cached runs:
  - step 100: `experiments/runs/blind_solvability_v2_guarded_rescore_anchor_step100_geo3k_real_login_20260712T082107Z/per_item.jsonl`
  - step 150: `experiments/runs/m5_geo3k_step150_an12_gpu4_20260718T051839Z/per_item.jsonl`
  - step 200: `experiments/runs/m5_geo3k_step200_an29_gpu4_20260722T141052Z/per_item.jsonl`
  - step 300: `experiments/runs/m5_geo3k_step300_an12_gpu0_20260726T083303Z/per_item.jsonl`
  - step 400: `experiments/runs/m5_geo3k_step400_an12_gpu0_20260728T053115Z/per_item.jsonl`

## Verification (all checks run in code)

| check | result |
|---|---|
| test items per step (100/150/200/300/400) | 601/601/601/601/601 |
| item-key sets identical across all five steps | True |
| ground_truth identical across all five steps | True |
| problem sha256 identical across all five steps | True |
| step-100 file rows / non-test rows excluded (I13) | 1889 / 1288 |
| canonical re-score mismatches vs stored (per step) | 0/0/0/0/0 |
| substrate rows cross-checked / value mismatches | 601 / 0 |
| items where acc_final == acc_strict (per step) | 601/601/601/601/601 of 601 |

Level series reproduced from the cached runs (I7: both metrics):

| metric | 100 | 150 | 200 | 300 | 400 |
|---|---|---|---|---|---|
| acc_final | 0.4359 | 0.4692 | 0.4892 | 0.4742 | 0.4443 |
| acc_strict | 0.4359 | 0.4692 | 0.4892 | 0.4742 | 0.4443 |

acc_final == acc_strict on all 601 items at all five steps, so every table below is numerically identical under the lenient and the contract-strict metric. Both are reported and stored separately (I7); they are not collapsed.

## SCOPE LIMIT — the FlipTrack taxonomy is not transplanted

The gray-arm attractor taxonomy in scripts/x3_a2_degradation_forensics.py (nearest_gridline, nearest_neighbor_x, twin_member_gold, same_point_y, most_similar_label_x, other_scene_point_x) is defined over replayed coordinate_register_twenty_point_x_v02 scene registers on FlipTrack pairs. Geometry3K is a different task: real-image geometry word problems with no generator seed, no replayable scene register, no coordinate grid, no paired twin member. None of those taxa is computable here and none was transplanted.

Geo3k-native structure probes used instead:
- wrong-answer value repetition across items (attractor value concentration)
- same wrong value as an earlier checkpoint (temporal persistence)
- wrong value equals some other test item's gold answer
- numeric near-miss within 10% of own gold
- small-integer 1..20 occupancy

The three lost sets (100->200, 100->300, 100->400) come from three checkpoints of ONE training trajectory and share the same step-100 anchor evaluation. The FlipTrack 3-way Jaccard used independent seeds. The permutation null conditions on the step-100-correct pool, but serial dependence between checkpoints is not removed.

## 1. Set sizes (step 100 -> step 400)

| quantity | acc_final (lenient) | acc_strict (contract-strict) |
|---|---|---|
| test items | 601 | 601 |
| correct at step 100 | 262 | 262 |
| correct at step 400 | 267 | 267 |
| LOST (correct@100, wrong@400) | 66 | 66 |
| GAINED (wrong@100, correct@400) | 71 | 71 |
| stable correct | 196 | 196 |
| stable wrong | 268 | 268 |
| net delta (items) | 5 | 5 |
| turnover (lost + gained) | 137 | 137 |
| LOST at 100->200 | 54 | 54 |
| LOST at 100->300 | 60 | 60 |
| net delta (accuracy) | +0.0083 | +0.0083 |

## 2. Step-400 wrong answers on the LOST set: concentrated or dispersed?

- LOST items: 66. Contract-valid step-400 answers: 63; contract-invalid (no extractable value): 3. The concentration statistics below are computed on the contract-valid answers only.
- Distinct wrong values: 55 over 63 answers (0.8730 distinct per item).
- Largest multiplicity of any single wrong value: 2 (8 values occur twice; none occurs three or more times).
- Shannon entropy 5.7233 bits (max possible 5.9773; normalized 0.9575); HHI 0.019904; top-1 share 0.0317; share of items sitting on a repeated value 0.2540.

Permutation nulls (equal-size draws of step-400 wrong answers, same seed and convention):

| null pool | pool n | draw n | null mean entropy (bits) | p(entropy <= obs) | p(HHI >= obs) | p(distinct <= obs) |
|---|---|---|---|---|---|---|
| stable_wrong_only | 268 | 66 | 5.7321 | 0.4486 | 0.5816 | 0.3815 |
| all_step400_errors | 334 | 66 | 5.7346 | 0.4417 | 0.5660 | 0.3835 |

`stable_wrong_only` is the role-clean null (items wrong at BOTH 100 and 400, disjoint from LOST); `all_step400_errors` includes the LOST items themselves in the pool and is reported for completeness.

Reference group, reported separately and NOT pooled with LOST (I13): the stable-wrong set (263 contract-valid step-400 answers, 5 contract-invalid) has 178 distinct values, entropy 7.1892 bits, normalized 0.8943, HHI 0.008805. Raw entropies are not comparable across different n; the matched-size permutation null above is the comparison.

Most frequent step-400 wrong values on the LOST set:

| canonical wrong value | count in LOST | items in the test split whose gold equals this value |
|---|---|---|
| `num::60.000000` | 2 | 11 |
| `num::0.380000` | 2 | 2 |
| `num::110.000000` | 2 | 3 |
| `num::6.000000` | 2 | 15 |
| `num::4.000000` | 2 | 12 |
| `num::120.000000` | 2 | 7 |
| `num::52.000000` | 2 | 1 |
| `num::45.000000` | 2 | 2 |
| `num::9.420000` | 1 | 0 |
| `num::152.500000` | 1 | 0 |
| `num::0.310000` | 1 | 0 |
| `num::42.000000` | 1 | 1 |

## 3. Is the LOST set more structured than a random equal-size subset of step-100-correct items?

Null pool: items correct at step 100 (n = 262). 10000 draws, seed 20260729, p = (hits+1)/(perms+1) floored at 1e-04.

- 3-way Jaccard of LOST(100->200) [n=54], LOST(100->300) [n=60] and LOST(100->400) [n=66]: **0.3118** vs permutation null mean 0.0221 (sd 0.0120), p <= 1e-04.
- Pairwise Jaccard j_200_300: 0.4074, p <= 1e-04.
- Pairwise Jaccard j_200_400: 0.4458, p <= 1e-04.
- Pairwise Jaccard j_300_400: 0.5750, p <= 1e-04.
- Share of LOST(100->400) items that were already lost at BOTH 100->200 and 100->300: 0.4394.
- Gold-answer concentration inside LOST: entropy 5.6996 bits over 56 distinct gold values in 66 items; null mean 5.5107 bits; p(entropy <= obs) 0.9468.
- Derived-bucket composition of LOST vs the step-100-correct pool: chi-square 11.7769 vs null mean 5.9581; p 0.0429 (uncorrected; see the multiplicity section).

| derived bucket | observed in LOST | expected from step-100-correct pool |
|---|---|---|
| angle_measure | 18 | 10.08 |
| arc_measure | 3 | 2.52 |
| area | 9 | 7.31 |
| circumference | 1 | 1.01 |
| length_measure | 0 | 2.02 |
| other | 10 | 15.37 |
| perimeter | 3 | 2.77 |
| ratio | 3 | 2.02 |
| solve_for_variable | 19 | 22.92 |

## 4. Template / category / source metadata

**No template, category or source field exists for geo3k in this repository.** Checked in code:
- The dataset manifest `data/geometry3k_caption_images_manifest.jsonl` has exactly one field set across all 2702 rows: `answer`, `images`, `problem`, `row_index`, `split`. There is no template id, no category, no sub-source, no generator seed.
- `qid` is null in all 601 test rows at every one of the five steps (non-null counts — step 100: 0, step 150: 0, step 200: 0, step 300: 0, step 400: 0).
- `source_metadata` is null in all 601 test rows at every one of the five steps (non-null counts — step 100: 0, step 150: 0, step 200: 0, step 300: 0, step 400: 0).

Because no such field exists, the buckets below are **derived by this analysis** from the problem string by a fixed ordered regex cascade. They are not dataset metadata and must not be cited as such. Rules, in order of application:

| order | bucket | regex (applied to lowercased problem with `<image>` stripped) |
|---|---|---|
| 1 | area | `\barea\b` |
| 2 | perimeter | `\bperimeter\b` |
| 3 | circumference | `\bcircumference\b` |
| 4 | volume | `\bvolume\b` |
| 5 | arc_measure | `\\widehat|\barc\b` |
| 6 | angle_measure | `\\angle|∠|\bm\s*\\angle` |
| 7 | ratio | `\bratio\b` |
| 8 | length_measure | `\blength\b|\bmeasure\b|\bperimeter\b` |
| 9 | solve_for_variable | `\bfind\s+\$?\\?[xyz]\$?\b|\bfind\s+the\s+value\b` |
| fallback | other | (no rule matched) |

LOST and GAINED by derived stem bucket:

| derived bucket | all test items | correct@100 | wrong@100 | LOST | lost rate within correct@100 | GAINED | gained rate within wrong@100 |
|---|---|---|---|---|---|---|---|
| angle_measure | 143 | 40 | 103 | 18 | 0.4500 | 19 | 0.1845 |
| arc_measure | 38 | 10 | 28 | 3 | 0.3000 | 5 | 0.1786 |
| area | 60 | 29 | 31 | 9 | 0.3103 | 4 | 0.1290 |
| circumference | 4 | 4 | 0 | 1 | 0.2500 | 0 | n/a |
| length_measure | 14 | 8 | 6 | 0 | 0.0000 | 1 | 0.1667 |
| other | 124 | 61 | 63 | 10 | 0.1639 | 14 | 0.2222 |
| perimeter | 19 | 11 | 8 | 3 | 0.2727 | 3 | 0.3750 |
| ratio | 10 | 8 | 2 | 3 | 0.3750 | 2 | 1.0000 |
| solve_for_variable | 189 | 91 | 98 | 19 | 0.2088 | 23 | 0.2347 |

Concentration test for GAINED against its own reference pool (items wrong at step 100, n = 339; draw n = 71): chi-square 8.8062, p 0.1334. LOST and GAINED are tested against different pools and are never pooled with each other (I13).

LOST and GAINED by derived gold-answer type:

| gold type | all test items | correct@100 | wrong@100 | LOST | GAINED |
|---|---|---|---|---|---|
| decimal | 132 | 50 | 82 | 19 | 11 |
| integer | 420 | 187 | 233 | 42 | 52 |
| non_numeric | 49 | 25 | 24 | 5 | 8 |

## 5. Geo3k-native structure probes (LOST vs stable-wrong reference)

LOST n = 66 (63 contract-valid at step 400); stable-wrong reference n = 268 (263 contract-valid). The two groups hold different scientific roles and are reported side by side, never pooled.

| probe | LOST | stable-wrong reference | permutation p vs stable-wrong null |
|---|---|---|---|
| step-400 wrong value equals some other test item's gold | 40/63 = 0.6349 | 160/263 = 0.6084 | 0.3192 |
| numeric near-miss: within 10% of own gold | 11/54 = 0.2037 | 20/230 = 0.0870 | 0.0005 |
| small integer 1..20 | 10/63 = 0.1587 | 54/263 = 0.2053 | not tested |

Temporal persistence of the step-400 wrong value (same canonical value at an earlier step):

| earlier step | LOST: same value / comparable | rate | stable-wrong: same value / comparable | rate |
|---|---|---|---|---|
| 150 | 8/61 | 0.1311 | 75/251 | 0.2988 |
| 200 | 13/63 | 0.2063 | 73/253 | 0.2885 |
| 300 | 14/61 | 0.2295 | 110/256 | 0.4297 |

## Multiplicity

15 permutation tests form the pre-listed family. Bonferroni threshold at alpha 0.05 is 0.00333. All permutation tests reported here form one pre-listed family; the family is reported with Holm-Bonferroni at alpha 0.05 alongside the raw p values. The acc_strict family is numerically identical to the acc_final family because acc_final == acc_strict on all 601 items at all five steps.

| test | raw p | Holm-Bonferroni reject at alpha 0.05 |
|---|---|---|
| lost_set_three_way_jaccard | <= 1e-04 | True |
| lost_set_pairwise_jaccard::j_200_300 | <= 1e-04 | True |
| lost_set_pairwise_jaccard::j_200_400 | <= 1e-04 | True |
| lost_set_pairwise_jaccard::j_300_400 | <= 1e-04 | True |
| native_near_miss_rate | 0.0005 | True |
| lost_derived_bucket_chi2 | 0.0429 | False |
| gained_derived_bucket_chi2 | 0.1334 | False |
| native_other_gold_rate | 0.3192 | False |
| wrong_answer_concentration::stable_wrong_only::p_n_distinct_le_observed | 0.3815 | False |
| wrong_answer_concentration::all_step400_errors::p_n_distinct_le_observed | 0.3835 | False |
| wrong_answer_concentration::all_step400_errors::p_entropy_le_observed | 0.4417 | False |
| wrong_answer_concentration::stable_wrong_only::p_entropy_le_observed | 0.4486 | False |
| wrong_answer_concentration::all_step400_errors::p_hhi_ge_observed | 0.5660 | False |
| wrong_answer_concentration::stable_wrong_only::p_hhi_ge_observed | 0.5816 | False |
| lost_gold_answer_entropy | 0.9468 | False |

## What could not be computed

- Wrong-answer concentration cannot be compared against a null drawn from step-100-correct items in general, because items that are correct at step 400 emit no wrong value. The matched-size null for that statistic is therefore drawn from the step-400 error pool (section 2), and the step-100-correct null in section 3 is applied to set-membership and item-attribute statistics only. No proxy was silently substituted.
- The near-miss contrast in section 5 is NOT difficulty-controlled. LOST items were correct at step 100 and the stable-wrong reference items were not, so the two groups differ in step-100 solvability by construction. The permutation null resamples inside the stable-wrong group only and therefore does not remove that difference. A difficulty-matched null would need a step-100 solvability score per item (for example p_i from the guarded rescore run) carried into a matched-resampling design; that was not built here.
- GAINED items are correct at step 400 by construction, so they emit no wrong value and no wrong-answer distribution is computable for them. Section 2 covers LOST only; GAINED appears in the set-size and derived-bucket tables.
- Independent-seed replication of the geo3k step-400 checkpoint does not exist in the cache, so the FlipTrack cross-seed Jaccard cannot be reproduced on geo3k. The 3-way Jaccard here uses three checkpoints of one trajectory and is a different quantity.
- The reference run emits two `macro '\frac' failed its substitution` warnings from the symbolic grader on latex-shaped answers. They come from the canonical scorer, are present in the original cached runs' scoring path as well, and did not change any score: re-scoring reproduced the stored acc_final and acc_strict on 601/601 items at all five steps.
