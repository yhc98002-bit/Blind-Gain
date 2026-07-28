# X3 — seed-3 replication of the A2-gray structured corrosion (v1)

Cached predictions only; uniform canonical re-scoring; scene features from exactly
replayed generator registers. The seed-1/2 method in
`scripts/x3_a2_degradation_forensics.py` is applied unchanged (helpers imported, not
transcribed) to the seed-3 A2-gray arm. All values below are recomputed from the cached
prediction rows. Facts only.

- Generated (UTC): 2026-07-28T12:40:20Z; git e3b4cf69f060400f28126b2d6592bbcb74e1deb4
- Template: `coordinate_register_twenty_point_x_v02`; n = 600 geometry pairs per run
- Seed-3 marker chain: `reports/pilot_4arm_seed3_results_v1.json`
  -> `experiments/runs/mech_a2_gray_seed3_an12_20260722T145916Z/step100_fliptrack_complete.json`
  -> eval run `pilot_fliptrack_a2_gray_seed3_step100_real_an29_20260725T092515Z`
- Base run: `fliptrack_v02r19_packaged_qwen25vl3b_real_an29_20260710T142716Z`
- Permutation / bootstrap seed for this report: 20260728 (10000 permutations, 10000 bootstrap resamples)
- Permutation p-values are computed as (hits + 1) / (permutations + 1) and are floored at 0.00010; a reported 0.00010 means 0 of 10000 draws reached the observed statistic, i.e. p is at the resolution limit, not measured below it.

## Method-agreement check against the frozen v1 report

Reference: `reports/x3_a2_degradation_forensics_v1.json` (sha256 `35746ccb5b16fb9bdf4cae96b755a52c32996451cc96e3f4cee3e9e1767aa800`)

- Seed-1/seed-2 fields recomputed and compared: 19/19 equal (all_equal = True)
- Seed1-vs-seed2 permutation null, frozen (seed 20260724) mean Jaccard 0.0978, p = 0.00010; recomputed here (seed 20260728) mean Jaccard 0.0972, p = 0.00010. Independent draws; not asserted equal.

## Lenient (acc_final / pair_correct)

Base geometry pair accuracy: 0.4717 (283/600), Wilson 95% CI [0.4320, 0.5117]

### A2-gray step-100 accuracy and delta vs base

| seed | A2 pair acc | n correct / n | Wilson 95% CI | net delta vs base | delta n items | paired bootstrap 95% CI | correct->wrong | wrong->correct |
|---|---|---|---|---|---|---|---|---|
| seed1 | 0.4267 | 256/600 | [0.3877, 0.4666] | -0.0450 | -27/600 | [-0.0733, -0.0167] | 51 | 24 |
| seed2 | 0.4267 | 256/600 | [0.3877, 0.4666] | -0.0450 | -27/600 | [-0.0717, -0.0183] | 49 | 22 |
| seed3 | 0.4350 | 261/600 | [0.3959, 0.4750] | -0.0367 | -22/600 | [-0.0633, -0.0100] | 45 | 23 |

### Correct-to-wrong set overlap (universe = base-correct items)

| comparison | size A | size B | intersection | union | Jaccard | null mean | null p95 | null max | p |
|---|---|---|---|---|---|---|---|---|---|
| seed3 vs seed1 | 45 | 51 | 43 | 53 | 0.8113 | 0.0932 | 0.1429 | 0.2468 | 0.00010 |
| seed3 vs seed2 | 45 | 49 | 40 | 54 | 0.7407 | 0.0913 | 0.1463 | 0.2368 | 0.00010 |
| seed1 vs seed2 | 51 | 49 | 42 | 58 | 0.7241 | 0.0972 | 0.1494 | 0.2500 | 0.00010 |
| all three (3-way) | sizes [51, 49, 45] | | 39 | 59 | 0.6610 | 0.0115 | 0.0263 | 0.0625 | 0.00010 |

- Universe (base-correct items) n = 283; nulls drawn with permutation seed 20260728, 10000 permutations, set sizes held at the observed sizes.
- Seed-3 recovers 39/42 of the seed1-and-seed2 shared degraded pairs = 0.9286, Wilson 95% CI [0.8099, 0.9754]

### Identical extracted wrong answer on shared wrong member slots

| comparison | same answer | shared wrong member slots | rate | Wilson 95% CI |
|---|---|---|---|---|
| seed3 vs seed1 | 44 | 44 | 1.0000 | [0.9197, 1.0000] |
| seed3 vs seed2 | 40 | 41 | 0.9756 | [0.8740, 0.9957] |
| seed1 vs seed2 | 41 | 42 | 0.9762 | [0.8768, 0.9958] |
| all three (3-way) | 39 | 40 | 0.9750 | [0.8712, 0.9956] |

### Transition taxonomy (per-seed counts of wrong member slots)

Counts are per-seed counts of wrong member slots, not a numerator/denominator pair.
The per-seed denominator (total wrong member slots for that seed) is the last row.

| taxon | seed1 | seed2 | seed3 |
|---|---|---|---|
| most_similar_label_x | 3 | 4 | 2 |
| nearest_gridline | 19 | 20 | 17 |
| nearest_neighbor_x | 6 | 12 | 7 |
| non_scene_value | 1 | 0 | 1 |
| other_scene_point_x | 14 | 13 | 14 |
| same_point_y | 8 | 3 | 4 |
| twin_member_gold | 1 | 1 | 1 |
| **total wrong member slots (denominator)** | 52 | 53 | 46 |

| nearest-gridline off-by-one | seed1 | seed2 | seed3 |
|---|---|---|---|
| count | 19 | 20 | 17 |
| denominator (wrong member slots) | 52 | 53 | 46 |
| share | 0.3654 | 0.3774 | 0.3696 |
| share Wilson 95% CI | [0.2480, 0.5013] | [0.2594, 0.5119] | [0.2452, 0.5140] |

### Member direction (counts of degraded pairs)

| direction | seed1 | seed2 | seed3 |
|---|---|---|---|
| both_members | 1 | 4 | 1 |
| member_a_only | 36 | 33 | 32 |
| member_b_only | 14 | 12 | 12 |
| **total degraded pairs** | 51 | 49 | 45 |

### Scene features (permutation test on mean difference)

| group | feature | group mean | group n | rest mean | rest n | perm p (two-sided) |
|---|---|---|---|---|---|---|
| seed3_degraded | crowding_within_3 | 2.6667 | 45 | 2.5672 | 238 | 0.68643 |
| seed3_degraded | distance_to_nearest_point | 2.5697 | 45 | 2.5377 | 238 | 0.75352 |
| seed3_degraded | min_label_levenshtein | 1.0000 | 45 | 1.0294 | 238 | 0.37586 |
| seed3_degraded | target_x_negative | 0.9333 | 45 | 0.7983 | 238 | 0.03040 |
| three_seed_union | crowding_within_3 | 2.6271 | 59 | 2.5714 | 224 | 0.79682 |
| three_seed_union | distance_to_nearest_point | 2.4906 | 59 | 2.5566 | 224 | 0.48245 |
| three_seed_union | min_label_levenshtein | 1.0000 | 59 | 1.0312 | 224 | 0.34577 |
| three_seed_union | target_x_negative | 0.8983 | 59 | 0.7991 | 224 | 0.08859 |

### Seed-3 shared degraded items under the other seed-3 arms

| arm | wrong on 3-seed shared | 3-seed shared n | wrong on seed3 degraded | seed3 degraded n | wrong on all base-correct | base-correct n |
|---|---|---|---|---|---|---|
| a1 | 20 | 39 | 22 | 45 | 26 | 283 |
| a2b | 34 | 39 | 38 | 45 | 46 | 283 |
| a3 | 21 | 39 | 22 | 45 | 24 | 283 |

### Degraded-set fingerprints (sha256 of sorted pair ids)

- seed1: `85d5e8d6d00ecfcab123205b25b7c2c9b3b747b5f2c2da49bcde076fb105e146`
- seed2: `b428834e024924ce8cc871cf562223d9e5261cb95b2f841bbde3a415d36eaf50`
- seed3: `2b4d9af5bd18ad9d615cdea285736ba15eed5c0d31754dc7187f14f3fa25711a`

## Contract-strict (acc_strict / strict_pair_correct)

Base geometry pair accuracy: 0.4433 (266/600), Wilson 95% CI [0.4041, 0.4833]

### A2-gray step-100 accuracy and delta vs base

| seed | A2 pair acc | n correct / n | Wilson 95% CI | net delta vs base | delta n items | paired bootstrap 95% CI | correct->wrong | wrong->correct |
|---|---|---|---|---|---|---|---|---|
| seed1 | 0.2417 | 145/600 | [0.2091, 0.2775] | -0.2017 | -121/600 | [-0.2383, -0.1650] | 138 | 17 |
| seed2 | 0.3217 | 193/600 | [0.2855, 0.3601] | -0.1217 | -73/600 | [-0.1550, -0.0900] | 92 | 19 |
| seed3 | 0.1867 | 112/600 | [0.1575, 0.2198] | -0.2567 | -154/600 | [-0.2950, -0.2183] | 166 | 12 |

### Correct-to-wrong set overlap (universe = base-correct items)

| comparison | size A | size B | intersection | union | Jaccard | null mean | null p95 | null max | p |
|---|---|---|---|---|---|---|---|---|---|
| seed3 vs seed1 | 166 | 138 | 135 | 169 | 0.7988 | 0.3957 | 0.4408 | 0.4975 | 0.00010 |
| seed3 vs seed2 | 166 | 92 | 91 | 167 | 0.5449 | 0.2865 | 0.3299 | 0.3871 | 0.00010 |
| seed1 vs seed2 | 138 | 92 | 89 | 141 | 0.6312 | 0.2623 | 0.3068 | 0.3690 | 0.00010 |
| all three (3-way) | sizes [138, 92, 166] | | 89 | 170 | 0.5235 | 0.1272 | 0.1563 | 0.1991 | 0.00010 |

- Universe (base-correct items) n = 266; nulls drawn with permutation seed 20260728, 10000 permutations, set sizes held at the observed sizes.
- Seed-3 recovers 89/89 of the seed1-and-seed2 shared degraded pairs = 1.0000, Wilson 95% CI [0.9586, 1.0000]

### Identical extracted wrong answer on shared wrong member slots

| comparison | same answer | shared wrong member slots | rate | Wilson 95% CI |
|---|---|---|---|---|
| seed3 vs seed1 | 146 | 149 | 0.9799 | [0.9425, 0.9931] |
| seed3 vs seed2 | 88 | 93 | 0.9462 | [0.8803, 0.9768] |
| seed1 vs seed2 | 88 | 91 | 0.9670 | [0.9075, 0.9887] |
| all three (3-way) | 86 | 90 | 0.9556 | [0.8912, 0.9826] |

### Transition taxonomy (per-seed counts of wrong member slots)

Counts are per-seed counts of wrong member slots, not a numerator/denominator pair.
The per-seed denominator (total wrong member slots for that seed) is the last row.

| taxon | seed1 | seed2 | seed3 |
|---|---|---|---|
| gold_value_contract_invalid | 104 | 50 | 146 |
| most_similar_label_x | 3 | 4 | 2 |
| nearest_gridline | 18 | 19 | 16 |
| nearest_neighbor_x | 6 | 12 | 7 |
| non_scene_value | 1 | 0 | 1 |
| other_scene_point_x | 14 | 13 | 14 |
| same_point_y | 7 | 2 | 3 |
| twin_member_gold | 1 | 1 | 1 |
| **total wrong member slots (denominator)** | 154 | 101 | 190 |

| nearest-gridline off-by-one | seed1 | seed2 | seed3 |
|---|---|---|---|
| count | 18 | 19 | 16 |
| denominator (wrong member slots) | 154 | 101 | 190 |
| share | 0.1169 | 0.1881 | 0.0842 |
| share Wilson 95% CI | [0.0752, 0.1772] | [0.1239, 0.2752] | [0.0525, 0.1324] |

### Member direction (counts of degraded pairs)

| direction | seed1 | seed2 | seed3 |
|---|---|---|---|
| both_members | 16 | 9 | 24 |
| member_a_only | 76 | 58 | 90 |
| member_b_only | 46 | 25 | 52 |
| **total degraded pairs** | 138 | 92 | 166 |

### Scene features (permutation test on mean difference)

| group | feature | group mean | group n | rest mean | rest n | perm p (two-sided) |
|---|---|---|---|---|---|---|
| seed3_degraded | crowding_within_3 | 2.7169 | 166 | 2.3200 | 100 | 0.02840 |
| seed3_degraded | distance_to_nearest_point | 2.4695 | 166 | 2.6956 | 100 | 0.00600 |
| seed3_degraded | min_label_levenshtein | 1.0181 | 166 | 1.0200 | 100 | 1.00000 |
| seed3_degraded | target_x_negative | 0.9518 | 166 | 0.5700 | 100 | 0.00010 |
| three_seed_union | crowding_within_3 | 2.7059 | 170 | 2.3229 | 96 | 0.03450 |
| three_seed_union | distance_to_nearest_point | 2.4647 | 170 | 2.7135 | 96 | 0.00230 |
| three_seed_union | min_label_levenshtein | 1.0176 | 170 | 1.0208 | 96 | 1.00000 |
| three_seed_union | target_x_negative | 0.9471 | 170 | 0.5625 | 96 | 0.00010 |

### Seed-3 shared degraded items under the other seed-3 arms

| arm | wrong on 3-seed shared | 3-seed shared n | wrong on seed3 degraded | seed3 degraded n | wrong on all base-correct | base-correct n |
|---|---|---|---|---|---|---|
| a1 | 40 | 89 | 43 | 166 | 46 | 266 |
| a2b | 87 | 89 | 156 | 166 | 167 | 266 |
| a3 | 43 | 89 | 46 | 166 | 47 | 266 |

### Degraded-set fingerprints (sha256 of sorted pair ids)

- seed1: `9de4411f6bad70c853a95a0f65292031151c87078d6dfb82c51bc0f667b6f7a0`
- seed2: `b6248c90715461346d92d50976f899b28eb6cb3dde0a56bfe39fa5cbbe1eb36c`
- seed3: `cfb9ee8c6d4c8ed24df8e19fae53f93addac66cf3ee75c9f027d75c8bb9c5329`

## Notes on the contract-strict track

In the contract-strict track a member slot can be wrong solely because the response violates the answer-tag contract while still carrying the gold value. Those slots are labelled gold_value_contract_invalid; the frozen classifier is applied unchanged to all other strict-wrong slots.

## Runs re-scored

| arm | seed | run |
|---|---|---|
| a1 | seed3 | `pilot_fliptrack_a1_real_seed3_step100_real_an29_20260725T092506Z` |
| a2b | seed3 | `pilot_fliptrack_a2b_noimage_seed3_step100_real_an29_20260725T092523Z` |
| a2 | seed1 | `pilot_fliptrack_a2_gray_seed1_step100_real_an12_20260716T152519Z` |
| a2 | seed2 | `pilot_fliptrack_a2_gray_seed2_step100_real_an29_20260721T163431Z` |
| a2 | seed3 | `pilot_fliptrack_a2_gray_seed3_step100_real_an29_20260725T092515Z` |
| a3 | seed3 | `pilot_fliptrack_a3_caption_seed3_step100_real_an29_20260725T092532Z` |
| base | shared | `fliptrack_v02r19_packaged_qwen25vl3b_real_an29_20260710T142716Z` |

