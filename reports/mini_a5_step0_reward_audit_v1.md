# Mini-A5 Step-0 Reward Audit V1

Status:
- Audit status: `pass`.
- Base-model diagnostic only; no optimizer step is taken and no PI gate is declared.

Evidence:
- Machine summary: `reports/mini_a5_step0_reward_audit_v1.json`.
- Predictions: `experiments/runs/mini_a5_step0_qwen25vl3b_an12_20260716T183755Z/predictions.jsonl`; SHA256 `5a796f7ea69cb7a1d40dcd8ec318cb3f872a0cfa5ee5e63d660e59297cd3e126`.
- Overall reward statistics: `{"cp_unique_pair_outcomes": {"hit_rate": 0.146875, "n": 960, "population_variance": 0.125302734375, "sample_variance": 0.12543339416058394}, "member_outcomes": {"hit_rate": 0.2526041666666667, "n": 1920, "population_variance": 0.18879530164930555, "sample_variance": 0.18889368377627236}}`.
- Pair-order check: `{"side_a": {"hit_rate": 0.2520833333333333, "n": 960, "population_variance": 0.1885373263888889, "sample_variance": 0.18873392422662497}, "side_a_minus_b_hit_rate": -0.001041666666666663, "side_b": {"hit_rate": 0.253125, "n": 960, "population_variance": 0.189052734375, "sample_variance": 0.18924986965589155}}`.

Per-template statistics:
```json
{
  "mini_a5_train_code_matrix_v1": {
    "cp_unique_pair_outcomes": {
      "hit_rate": 0.375,
      "n": 320,
      "population_variance": 0.234375,
      "sample_variance": 0.23510971786833856
    },
    "member_outcomes": {
      "hit_rate": 0.4953125,
      "n": 640,
      "population_variance": 0.24997802734375,
      "sample_variance": 0.25036922926447575
    }
  },
  "mini_a5_train_labeled_scatter_v1": {
    "cp_unique_pair_outcomes": {
      "hit_rate": 0.053125,
      "n": 320,
      "population_variance": 0.050302734375,
      "sample_variance": 0.050460423197492166
    },
    "member_outcomes": {
      "hit_rate": 0.184375,
      "n": 640,
      "population_variance": 0.150380859375,
      "sample_variance": 0.1506161971830986
    }
  },
  "mini_a5_train_named_trajectory_v1": {
    "cp_unique_pair_outcomes": {
      "hit_rate": 0.0125,
      "n": 320,
      "population_variance": 0.01234375,
      "sample_variance": 0.012382445141065831
    },
    "member_outcomes": {
      "hit_rate": 0.078125,
      "n": 640,
      "population_variance": 0.072021484375,
      "sample_variance": 0.07213419405320813
    }
  }
}
```

Checks:
| Check | Result |
| --- | --- |
| `exact_row_count_1920` | `pass` |
| `exact_pair_count_192` | `pass` |
| `all_pairs_complete` | `pass` |
| `reward_recomputation_exact` | `pass` |
| `one_contract_value_per_field` | `pass` |
| `unique_cp_outcomes_exact_960` | `pass` |
| `member_outcomes_exact_1920` | `pass` |

Problems:
- Audit errors: `[]`.
- A merged registration marker and EasyR1 GPU plumbing smoke remain separate prerequisites.
