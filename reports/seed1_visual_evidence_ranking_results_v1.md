# Seed-1 Visual-Evidence Ranking Results V1

Status:
- Complete as a post-seed-1 prospective diagnostic; it is not part of the original pilot preregistration.
- No automatic B1/B2/B3 assignment is made because no margin-scale SESOI was registered.

Evidence:
- Scorer: `visual-evidence-ranking-v1`; complete immutable cells: `9`.
- Primary statistic is paired mean-token-log-probability margin; candidate top-1 and MRR are secondary.

## Primary Geometry Effect

| checkpoint | blind comparator | mean image-dependent paired-margin effect | 95% paired bootstrap CI | pairs |
| --- | --- | ---: | ---: | ---: |
| a1_step100 | gray | 0.150142 | [0.144849, 0.155388] | 600 |
| a1_step100 | no_image | 0.150142 | [0.144849, 0.155388] | 600 |
| a1_step60 | gray | 0.089137 | [0.085755, 0.092493] | 600 |
| a1_step60 | no_image | 0.089137 | [0.085755, 0.092493] | 600 |

## Absolute Cell Summaries

| checkpoint | condition | construct | paired margin | 95% CI | pair success | candidate top-1 | candidate MRR |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| a1_step100 | gray | coordinate_register_twenty_point_x_v02 | 0.000000 | [0.000000, 0.000000] | 0.000000 | 0.000000 | 0.218644 |
| a1_step100 | gray | cued chart point-value reading | 0.000000 | [0.000000, 0.000000] | 0.000000 | 0.000000 | 0.305665 |
| a1_step100 | gray | header_cued_table_code_v02 | 0.000000 | [0.000000, 0.000000] | 0.000000 | 0.000000 | 0.217520 |
| a1_step100 | no_image | coordinate_register_twenty_point_x_v02 | 0.000000 | [0.000000, 0.000000] | 0.000000 | 0.000000 | 0.214219 |
| a1_step100 | no_image | cued chart point-value reading | 0.000000 | [0.000000, 0.000000] | 0.000000 | 0.000000 | 0.305310 |
| a1_step100 | no_image | header_cued_table_code_v02 | 0.000000 | [0.000000, 0.000000] | 0.000000 | 0.000000 | 0.210991 |
| a1_step100 | real | coordinate_register_twenty_point_x_v02 | 0.823452 | [0.797083, 0.849716] | 0.906667 | 0.476667 | 0.783897 |
| a1_step100 | real | cued chart point-value reading | 0.419201 | [0.400543, 0.437670] | 0.876667 | 0.566667 | 0.844813 |
| a1_step100 | real | header_cued_table_code_v02 | 2.176315 | [2.131098, 2.221760] | 1.000000 | 1.000000 | 1.000000 |
| a1_step60 | gray | coordinate_register_twenty_point_x_v02 | 0.000000 | [0.000000, 0.000000] | 0.000000 | 0.000000 | 0.218413 |
| a1_step60 | gray | cued chart point-value reading | 0.000000 | [0.000000, 0.000000] | 0.000000 | 0.000000 | 0.304909 |
| a1_step60 | gray | header_cued_table_code_v02 | 0.000000 | [0.000000, 0.000000] | 0.000000 | 0.000000 | 0.222737 |
| a1_step60 | no_image | coordinate_register_twenty_point_x_v02 | 0.000000 | [0.000000, 0.000000] | 0.000000 | 0.000000 | 0.216193 |
| a1_step60 | no_image | cued chart point-value reading | 0.000000 | [0.000000, 0.000000] | 0.000000 | 0.000000 | 0.305638 |
| a1_step60 | no_image | header_cued_table_code_v02 | 0.000000 | [0.000000, 0.000000] | 0.000000 | 0.000000 | 0.214315 |
| a1_step60 | real | coordinate_register_twenty_point_x_v02 | 0.762448 | [0.737831, 0.786774] | 0.906667 | 0.481667 | 0.781797 |
| a1_step60 | real | cued chart point-value reading | 0.389630 | [0.371958, 0.407081] | 0.860000 | 0.523333 | 0.829548 |
| a1_step60 | real | header_cued_table_code_v02 | 2.096582 | [2.053088, 2.140202] | 1.000000 | 1.000000 | 1.000000 |
| base | gray | coordinate_register_twenty_point_x_v02 | 0.000000 | [0.000000, 0.000000] | 0.000000 | 0.000000 | 0.218352 |
| base | gray | cued chart point-value reading | 0.000000 | [0.000000, 0.000000] | 0.000000 | 0.000000 | 0.306433 |
| base | gray | header_cued_table_code_v02 | 0.000000 | [0.000000, 0.000000] | 0.000000 | 0.000000 | 0.221265 |
| base | no_image | coordinate_register_twenty_point_x_v02 | 0.000000 | [0.000000, 0.000000] | 0.000000 | 0.000000 | 0.213061 |
| base | no_image | cued chart point-value reading | 0.000000 | [0.000000, 0.000000] | 0.000000 | 0.000000 | 0.305672 |
| base | no_image | header_cued_table_code_v02 | 0.000000 | [0.000000, 0.000000] | 0.000000 | 0.000000 | 0.208104 |
| base | real | coordinate_register_twenty_point_x_v02 | 0.673310 | [0.651021, 0.695718] | 0.906667 | 0.468333 | 0.775108 |
| base | real | cued chart point-value reading | 0.347039 | [0.331087, 0.363119] | 0.866667 | 0.506667 | 0.814008 |
| base | real | header_cued_table_code_v02 | 1.975614 | [1.933687, 2.017173] | 1.000000 | 1.000000 | 1.000000 |

## Per-Template Effects

| checkpoint | comparator | construct | paired-margin effect | 95% CI | pair-success effect | top-1 effect | MRR effect | raw-sum robustness |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| a1_step100 | gray | coordinate_register_twenty_point_x_v02 | 0.150142 | [0.144849, 0.155388] | 0.000000 | 0.008333 | 0.008497 | 1.050992 |
| a1_step100 | gray | cued chart point-value reading | 0.072163 | [0.068532, 0.075720] | 0.010000 | 0.060000 | 0.031573 | 0.577303 |
| a1_step100 | gray | header_cued_table_code_v02 | 0.200701 | [0.194617, 0.206893] | 0.000000 | 0.000000 | 0.003745 | 1.465728 |
| a1_step100 | no_image | coordinate_register_twenty_point_x_v02 | 0.150142 | [0.144849, 0.155388] | 0.000000 | 0.008333 | 0.007630 | 1.050992 |
| a1_step100 | no_image | cued chart point-value reading | 0.072163 | [0.068532, 0.075720] | 0.010000 | 0.060000 | 0.031168 | 0.577303 |
| a1_step100 | no_image | header_cued_table_code_v02 | 0.200701 | [0.194617, 0.206893] | 0.000000 | 0.000000 | -0.002887 | 1.465728 |
| a1_step60 | gray | coordinate_register_twenty_point_x_v02 | 0.089137 | [0.085755, 0.092493] | 0.000000 | 0.013333 | 0.006628 | 0.623961 |
| a1_step60 | gray | cued chart point-value reading | 0.042591 | [0.040262, 0.044847] | -0.006667 | 0.016667 | 0.017063 | 0.340730 |
| a1_step60 | gray | header_cued_table_code_v02 | 0.120968 | [0.116650, 0.125242] | 0.000000 | 0.000000 | -0.001471 | 0.883206 |
| a1_step60 | no_image | coordinate_register_twenty_point_x_v02 | 0.089137 | [0.085755, 0.092493] | 0.000000 | 0.013333 | 0.003557 | 0.623961 |
| a1_step60 | no_image | cued chart point-value reading | 0.042591 | [0.040262, 0.044847] | -0.006667 | 0.016667 | 0.015573 | 0.340730 |
| a1_step60 | no_image | header_cued_table_code_v02 | 0.120968 | [0.116650, 0.125242] | 0.000000 | 0.000000 | -0.006211 | 0.883206 |

Problems:
- Candidate-answer ranking is not a direct perception measure.
- Rejecting a zero effect would show improved visual-evidence ranking under this frozen score, not establish an internal perceptual mechanism.
- The R19 chart construct is `cued chart point-value reading` and remains secondary.

Decision:
- Publish estimates and intervals without automatic branch assignment or causal mechanism language.

Next actions:
- PIs compare the registered B1/B2/B3 descriptions to this diagnostic and the free-generation readout.
- Multi-seed pilot results remain the required confirmation for the original pilot estimands.
