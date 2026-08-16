# E4 wording resolution — unfolded per-attacker AUC CIs (v1 criterion untouched)

v1 (folded, file of record): `reports/track4_premise_v2_attacker_gate_v1.json` · v2 re-run: `reports/track4_premise_v2_attacker_gate_v2_unfolded.json`

Reproduction check: PASS (CPU attackers exact; dinov2 tolerance 1e-9).

| attacker | scope | unfolded directed OOF AUC | unfolded 95% CI | CI includes 0.5 (literal) | folded stat (descriptive) | folded CI (descriptive) |
|---|---|---:|---|---|---:|---|
| dinov2 | pooled | 0.529141 | [0.507962, 0.552699] | **no** | 0.529141 | [0.507962, 0.552699] |
| dinov2 | t4v2_coordinate_register_n20_v1 | 0.506719 | [0.475613, 0.536563] | yes | 0.506719 | [0.500625, 0.537348] |
| dinov2 | t4v2_coordinate_register_n8_v1 | 0.508750 | [0.470625, 0.543285] | yes | 0.508750 | [0.500781, 0.544063] |
| frequency_stat | pooled | 0.545977 | [0.516365, 0.575511] | **no** | 0.545977 | [0.516365, 0.575511] |
| frequency_stat | t4v2_coordinate_register_n20_v1 | 0.533750 | [0.496559, 0.577973] | yes | 0.533750 | [0.502031, 0.577973] |
| frequency_stat | t4v2_coordinate_register_n8_v1 | 0.514219 | [0.482805, 0.546723] | yes | 0.514219 | [0.500781, 0.546723] |
| metadata | pooled | 0.501836 | [0.496718, 0.507385] | yes | 0.501836 | [0.500117, 0.507385] |
| metadata | t4v2_coordinate_register_n20_v1 | 0.499375 | [0.492184, 0.506406] | yes | 0.500625 | [0.500156, 0.508285] |
| metadata | t4v2_coordinate_register_n8_v1 | 0.497344 | [0.488125, 0.507188] | yes | 0.502656 | [0.500156, 0.511875] |

Per-attacker literal verdict: dinov2: FAIL; frequency_stat: FAIL; metadata: pass

The operative registered gate remains the folded one the instrument implements (point <= 0.55, folded CI upper <= 0.62); it is not modified here and its verdict is unchanged from v1.
