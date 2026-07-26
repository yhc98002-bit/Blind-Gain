# B1 trained-checkpoint scoring (v1)

Registered: `docs/registered_b1_trained_v1.md`. Declared 100-pair batch
unchanged; base rates pinned from the base calibration, not re-measured;
consistency pairs scored single-gold as in that calibration.

**Registered reading: no_registered_branch_fact_read_not_improved_in_both_seeds**
Chained construct: c_chained_construct_not_discriminative_at_3b

## Pair-correct by intervention type (delta vs base in parentheses)

| intervention | pairs | base | A1 s1 | A1 s2 | A2b s1 | A3 s1 |
|---|---|---|---|---|---|---|
| fact_read | 20 | 0.600 | 0.550 (-0.050) | 0.500 (-0.100) | 0.500 (-0.100) | 0.500 (-0.100) |
| chained_premise | 20 | 0.000 | 0.000 (+0.000) | 0.000 (+0.000) | 0.000 (+0.000) | 0.000 (+0.000) |
| binding_swap | 16 | 0.188 | 0.188 (+0.000) | 0.188 (+0.000) | 0.188 (+0.000) | 0.188 (+0.000) |
| distractor_only | 16 | 0.438 | 0.375 (-0.062) | 0.438 (+0.000) | 0.438 (+0.000) | 0.375 (-0.062) |
| style_twin | 14 | 0.643 | 0.643 (+0.000) | 0.714 (+0.071) | 0.571 (-0.071) | 0.643 (+0.000) |
| prior_conflict | 14 | 0.143 | 0.357 (+0.214) | 0.286 (+0.143) | 0.429 (+0.286) | 0.429 (+0.286) |

## Member-correct by intervention type

| intervention | base | A1 s1 | A1 s2 | A2b s1 | A3 s1 |
|---|---|---|---|---|---|
| fact_read | 0.700 | 0.725 | 0.700 | 0.675 | 0.700 |
| chained_premise | 0.150 | 0.100 | 0.075 | 0.125 | 0.075 |
| binding_swap | 0.375 | 0.406 | 0.438 | 0.438 | 0.406 |
| distractor_only | 0.438 | 0.406 | 0.438 | 0.438 | 0.375 |
| style_twin | 0.750 | 0.786 | 0.821 | 0.750 | 0.786 |
| prior_conflict | 0.429 | 0.536 | 0.571 | 0.571 | 0.571 |

No interpretation beyond the registered readings.
