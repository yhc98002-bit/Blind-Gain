# M8 7B Preparation Status V2

Status:
- M8 remains `blocked`: four pilot-contract conditions have resumable prefixes,
  while noise, completion, aggregation, and the audited report remain outstanding.
- The four active jobs recorded in V1 were deliberately preempted for M2 A2-gray;
  this is scheduling, not a scientific failure.

Completed inputs:
- Qwen2.5-VL-7B-Instruct revision: `cc594898...`.
- Node-local model path on an12:
  `/dev/shm/blind-gains/models/Qwen2.5-VL-7B-Instruct`.
- Frozen 7B question-blind caption source:
  `virl39k_sample4096_qwen25vl7b_captionstore384_retry_20260710T163500Z`.
- Caption store coverage: 4,297/4,297 unique sample image hashes.
- Caption store SHA256:
  `426644dae442fcc4ee3d6e023928e179d3ac957ec3857486d37e7bb7a2f66b0c`.

Preserved batch-aligned prefixes:

| Condition | Original run | GPU | Preserved rows | Artifact |
| --- | --- | ---: | ---: | --- |
| real | `blind_solvability_virl39k_7b_v1_pilot_contract_owncaption_real_an12_20260713T025939Z` | 4 | 118 | `per_item.jsonl` |
| gray | `blind_solvability_virl39k_7b_v1_pilot_contract_owncaption_gray_an12_20260713T025944Z` | 5 | 126 | `per_item.jsonl` |
| no-image | `blind_solvability_virl39k_7b_v1_pilot_contract_owncaption_none_an12_20260713T025948Z` | 6 | 118 | `per_item.jsonl` |
| own-caption | `blind_solvability_virl39k_7b_v1_pilot_contract_owncaption_caption_an12_20260713T025953Z` | 7 | 126 | `per_item.jsonl` |

Preemption record:
- All four processes received graceful termination after writing complete batch
  records. Their manifests retain end times, exit `-15`, and deviation code
  `scheduled_preemption_for_m2_a2_gray` with `resume_required=true`.
- No prefix was overwritten or discarded.
- `scripts/launch_virl39k_7b_blind_v1_condition.sh` accepts the preserved JSONL as
  its fifth `RESUME_FROM` argument and rejects an invalid prefix.
- an12 GPUs 4-7 were released before M2 A2-gray started.

Next actions:
- Resume real, gray, no-image, and own-caption when a safe single-node slot opens.
- Launch the missing noise condition under the same 2,048-token, n=16 contract.
- Aggregate all five conditions and publish the M8 audited machine artifact before
  M9; no partial prefix is interpreted as a result.
