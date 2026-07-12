# Pilot Namespace Reclamation

Status:
- `listed before relocation`. Four small metadata files from the superseded historical TP2 smoke occupy the future A1 checkpoint namespace.
- The files are preserved as scientific/provenance evidence; they will be hash-verified into the historical smoke run before the source directory is removed.

Evidence:
- Source: `checkpoints/pilot/mech_a1_real`, allocated size 38,484 bytes.
- `checkpoint_tracker.json`: 227 bytes, SHA256 `9427d7b2abc7b05a778bc628721f069ad637c08ffac6a6e9cd6e44416c58b5e9`.
- `experiment_config.json`: 7,879 bytes, SHA256 `e7951f4896dc18191d32d5b5f249d7eb48fce4ef03dbd5beedd3a283ab89f3d9`.
- `experiment_log.jsonl`: 10,568 bytes, SHA256 `8098c842d4f67002c747b7b61161b38650fe3c23783696d550d6cfaa865f898c`.
- `generations.log`: 15,714 bytes, SHA256 `59a4b757e716239f5ddb433fa856b5e0033b0a08778c05e20dee9ab197baddd5`.
- The embedded config identifies `pilot_reward_smoke_an29_20260711T165700Z`, `max_steps=5`, and TP2.
- The tracker points to the already-deleted retention-expired `global_step_5` payload.

Problems:
- Leaving these files in place would make the resume-safe EasyR1 logger refuse a future non-resume A1 launch, as intended.
- Reusing them would contaminate the future A1 metric/config namespace with superseded smoke artifacts.

Decision:
- Classify the four files as `superseded`, not failed pilot output.
- Relocate them to `experiments/runs/pilot_reward_smoke_an29_20260711T165700Z/legacy_checkpoint_metadata` with source checksums and a relocation record.
- Remove only the empty `checkpoints/pilot/mech_a1_real` directory after destination hashes match.
- Append the relocation event to the historical smoke run manifest.

Next actions:
- Execute `scripts/relocate_legacy_smoke_metadata.py`, verify the destination, and append completion evidence below in a versioned report.
