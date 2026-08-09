# Mini-A5 Gate-1 completion — acceptance audit

- schema_version: `blind-gains.mini-a5-gate1-acceptance-audit.v1`
- registration: `docs/registered_mini_a5_gate1_completion_v1.md`
- marker: `reports/mini_a5_gate1_completion_registration_marker_v1.json`
- generated_at_utc: 2026-08-09T14:57:06Z
- **verdict: PASS**

## Conditions

| condition | status |
|---|---|
| 1_exit0_and_120_steps | ok |
| 2_hashes_match_registration | ok |
| 3_member_mode_discipline | ok |
| 4_no_fatal_log_signatures | ok |
| 5_checkpoint_hash_inventory | ok |
| 6_report_precedes_readout | ok |
| 7_prelaunch_corpus_audits | ok |
| 8_matched_difference | ok |
| 9_fixtures_and_nonidentity | ok |

## Arms

- **necessity**: run `experiments/runs/mini_a5_necessity_main_an29_20260807T222122Z`, checkpoint `checkpoints/mini_a5/mini_a5_necessity_seed1`
  - checkpoint inventory: 6 saved steps, 219 files, 253975192879 bytes (per-file sha256 in the JSON twin)
- **std**: run `experiments/runs/mini_a5_std_main_an29_20260807T013033Z`, checkpoint `checkpoints/mini_a5/mini_a5_std_seed1`
  - checkpoint inventory: 6 saved steps, 219 files, 253975192895 bytes (per-file sha256 in the JSON twin)

## Failures

(none)

## Sealing

No endpoint prediction/metric/accuracy value is read or reported by this audit; sealed basenames (experiment_log.jsonl, generations.log, predictions/metrics/accuracy files) are refused by a guard on every content read. Step counts come from run_manifest.json, checkpoint_tracker.json, and the global_step_* inventory.
