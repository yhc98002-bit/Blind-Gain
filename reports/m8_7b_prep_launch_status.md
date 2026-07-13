# M8 7B Preparation Launch Status

Status:
- M8 is running and incomplete.
- The frozen 7B own-caption store has exact image-hash coverage of the
  4,096-item ViRL39K sample.
- Four of five pilot-contract conditions are active; noise remains queued.

Caption store:
- Run:
  `experiments/runs/virl39k_sample4096_qwen25vl7b_captionstore384_retry_20260710T163500Z`.
- Store rows / unique image hashes: 4,297 / 4,297.
- Frozen sample unique image hashes: 4,297.
- Missing or extra hashes: 0.
- Store SHA256:
  `426644dae442fcc4ee3d6e023928e179d3ac957ec3857486d37e7bb7a2f66b0c`.
- One fixed caption-prompt SHA256 across all rows; generation is greedy,
  question-blind, and capped at 384 tokens.

Model staging:
- Model: Qwen2.5-VL-7B-Instruct revision
  `cc594898137f460bfe9f0759e9844b3ce807cfb5`.
- Source remains the registered ModelScope artifact.
- Runtime path:
  `an12:/dev/shm/blind-gains/models/Qwen2.5-VL-7B-Instruct`.
- Config and safetensors-index hashes match the persistent source.

Active runs:
| Condition | Run suffix | GPU | TP | Max tokens | Samples/item |
| --- | --- | ---: | ---: | ---: | ---: |
| real | `pilot_contract_owncaption_real_an12_20260713T025939Z` | 4 | 1 | 2048 | 16 |
| gray | `pilot_contract_owncaption_gray_an12_20260713T025944Z` | 5 | 1 | 2048 | 16 |
| no-image | `pilot_contract_owncaption_none_an12_20260713T025948Z` | 6 | 1 | 2048 | 16 |
| own-caption | `pilot_contract_owncaption_caption_an12_20260713T025953Z` | 7 | 1 | 2048 | 16 |

Contract:
- Greedy pass plus n=16 at temperature 1.0.
- top_p 1.0, G=5, seed 20260710.
- pilot-reward-v1 plus canonical-v2 scoring.
- fixed prompt-contract hash and symbolic-grader guard.
- one node, one TP1 replica per condition.

Next actions:
- Launch noise when one M8 replica completes.
- Aggregate all five conditions and publish the independently audited final M8
  reports without reusing the superseded 512-token 7B rows.
