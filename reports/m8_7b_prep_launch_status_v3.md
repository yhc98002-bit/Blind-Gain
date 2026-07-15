# M8 7B Preparation Launch Status V3

Status:
- M8 remains `blocked`: all five registered conditions are now running, but full
  completion, aggregation, and the audited report are outstanding.
- V3 supersedes the operational snapshot in V2 without modifying the preserved
  V1/V2 reports or any prior run.

Evidence:
- A hash-verified 7B snapshot was staged to
  `an29:/dev/shm/blind-gains/models/Qwen2.5-VL-7B-Instruct` by
  `experiments/runs/shared_model_stage_Qwen2.5-VL-7B-Instruct_an29_20260715T202013Z`.
- Source revision:
  `Qwen/Qwen2.5-VL-7B-Instruct@cc594898137f460bfe9f0759e9844b3ce807cfb5`.
- Source bytes: `16,595,985,455`; source-manifest SHA256:
  `7497ecc32ed34db83b7d2a8f79fd5bf45ef755195a2306805688af5c8a4cb4db`.
- Staging run-manifest SHA256:
  `022130a8c031245db6c17eefb585166dfefdd6bd0afe5e71b74ed3fcf78f845c`.
- The staging run completed with exit code 0 after every copied file passed
  SHA256 verification and the partial directory was atomically renamed.

| Condition | GPU | Resume prefix | Active run |
| --- | ---: | ---: | --- |
| real | 0 | 118 rows | `experiments/runs/blind_solvability_virl39k_7b_v1_pilot_contract_owncaption_resume1_real_an29_20260715T202424Z` |
| gray | 1 | 126 rows | `experiments/runs/blind_solvability_virl39k_7b_v1_pilot_contract_owncaption_resume1_gray_an29_20260715T202424Z` |
| no-image | 2 | 118 rows | `experiments/runs/blind_solvability_virl39k_7b_v1_pilot_contract_owncaption_resume1_none_an29_20260715T202424Z` |
| own-caption | 3 | 126 rows | `experiments/runs/blind_solvability_virl39k_7b_v1_pilot_contract_owncaption_resume1_caption_an29_20260715T202425Z` |
| noise | 4 | none; fresh condition | `experiments/runs/blind_solvability_virl39k_7b_v1_pilot_contract_owncaption_initial_noise_an29_20260715T202424Z` |

- Placement is five independent TP1 jobs on one node. The fixed 7B caption store,
  pilot prompt/reward/parser contract, 2,048-token limit, n=16 sampling, seed, and
  sample manifest remain unchanged.
- At the first health check (`2026-07-15T20:26:34Z`), GPUs 0-4 showed 89-100%
  utilization and 60-62 GiB allocated. All five run manifests remained `running`.
- Resumed outputs began with their exact validated prefixes; noise had no resume
  source and began at zero rows.

Problems:
- None of the five conditions is complete yet.
- Aggregation, confidence intervals, row-identity checks, recomputation audit, and
  the final M8 report do not exist yet.
- GPUs 5-7 are intentionally unassigned because no higher-priority registered job
  currently fits that three-GPU fragment.

Decision:
- Run all five conditions concurrently because M8 is higher priority than M11/M12
  gap-fillers and each 7B model fits one GPU.
- Preserve and validate prior batch-aligned work rather than restart four conditions.
- Keep M8 blocked until the complete five-condition artifact passes the consistency
  auditor; partial rows are not interpreted as results.

Next actions:
- Monitor row advancement, GPU memory, process liveness, and manifest status.
- Aggregate only after all five conditions complete.
- Build the audited machine artifact and publish
  `reports/blind_solvability_virl39k_7b_sample_v1.md`.
- Fill the M8-dependent flagship fields only from the audited complete artifact.

Machine-readable companion:
- `reports/m8_7b_prep_launch_status_v3.json`.
