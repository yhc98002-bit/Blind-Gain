# X2 hard-negative ranking results (v1)

Registered ladder: `docs/registered_x2_ladder_v1.md`. Layer: candidate-evidence
ranking. 600 geometry pairs, frozen structured negative sets
(`data/fliptrack_r19_hard_negative_candidates_v2.jsonl`). The v2 against-set
number supersedes the corresponding v1 number in all downstream text.

- Ladder metric: against-set pair-success: both members rank their own gold first within the frozen structured negative set (candidate_pair_top1)
- The golds-only margin statistic is candidate-set-invariant by construction
  and is reported for continuity only.

## Old vs new pair-success (geometry template, 600 pairs)

| model | v1 margin pair-success | v2 margin pair-success | v1 against-set (14 candidates) | v2 against-set (structured, 4-8) |
|---|---|---|---|---|
| base | 0.9067 | 0.9067 | 0.4683 [0.4267, 0.5083] | 0.5167 [0.4750, 0.5567] |
| a1_step60 | 0.9067 | 0.9067 | 0.4817 [0.4417, 0.5217] | 0.5267 [0.4867, 0.5667] |
| a1_step100 | 0.9067 | 0.9067 | 0.4767 [0.4367, 0.5167] | 0.5133 [0.4733, 0.5533] |

## Registered ladder application (base model, v2 against-set pair-success)

- Measured: 0.5167 [0.4750, 0.5567]
- Ladder branch (mechanical): **candidate_set_structure_realization_gap_measurement_methods_finding**

Whichever branch obtains ships without renegotiation; branch text is defined
in the registration and is not restated here.
