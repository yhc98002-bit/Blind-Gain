# X3 — A2 geometry degradation forensics (v1)

Cached predictions only; uniform canonical re-scoring; scene features from
exactly replayed generator registers. Facts only.

- Base geometry pair accuracy: 0.4717 (283/600)
- A2 step-100 pair accuracy: seed1 0.4267, seed2 0.4267 (net vs base: -0.0450 / -0.0450)
- Correct-to-wrong sets: seed1 51, seed2 49; intersection 42, union 58
- Jaccard 0.7241 vs permutation null mean 0.0978; p = 0.00010 (10000 permutations, seed 20260724)
- Same-wrong-answer rate on shared wrong member slots: 0.9762 (41/42)

## Transition taxonomy (wrong-member extracted answers)

| taxon | seed1 | seed2 |
|---|---|---|
| most_similar_label_x | 3 | 4 |
| nearest_gridline | 19 | 20 |
| nearest_neighbor_x | 6 | 12 |
| non_scene_value | 1 | 0 |
| other_scene_point_x | 14 | 13 |
| same_point_y | 8 | 3 |
| twin_member_gold | 1 | 1 |

## Member direction

| direction | seed1 | seed2 |
|---|---|---|
| both_members | 1 | 4 |
| member_a_only | 36 | 33 |
| member_b_only | 14 | 12 |

## Scene features: degraded union vs non-degraded base-correct

| feature | degraded mean | non-degraded mean | permutation p |
|---|---|---|---|
| target_x_negative | 0.8966 | 0.8000 | 0.12559 |
| crowding_within_3 | 2.6207 | 2.5733 | 0.83402 |
| min_label_levenshtein | 1.0000 | 1.0311 | 0.35166 |
| distance_to_nearest_point | 2.4950 | 2.5551 | 0.52025 |

## Same items under the other arms (shared degraded items)

| arm | seed | wrong on shared items | shared items | wrong on all base-correct | base-correct items |
|---|---|---|---|---|---|
| a1 | seed1 | 28 | 42 | 33 | 283 |
| a1 | seed2 | 26 | 42 | 28 | 283 |
| a2b | seed1 | 34 | 42 | 37 | 283 |
| a2b | seed2 | 38 | 42 | 43 | 283 |
| a3 | seed1 | 30 | 42 | 34 | 283 |
| a3 | seed2 | 32 | 42 | 36 | 283 |
