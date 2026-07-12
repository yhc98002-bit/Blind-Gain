# Pilot Namespace Reclamation V2

Status:
- `complete`. Superseded TP2-smoke metadata is preserved under its historical run, and `checkpoints/pilot/mech_a1_real` is absent.
- No checkpoint, generated dataset, evaluation output, or future pilot artifact was deleted.

Evidence:
- Source classification and pre-relocation inventory: `reports/pilot_namespace_reclamation.md`.
- Destination: `experiments/runs/pilot_reward_smoke_an29_20260711T165700Z/legacy_checkpoint_metadata`.
- Four source files, 34,388 payload bytes; all destination hashes revalidated with `sha256sum -c` before source removal.
- Source checksum manifest SHA256: `4a833dec7348807cd3e11b98ef4fffed7670a4db1b48086c542c2da3125efc55`.
- Relocation record SHA256: `22d0baee24ace8e44722940440474a8668f195a326973976ca148e60290c17ea`.
- Updated historical run-manifest SHA256: `35506fcc0458c67e9a0ed6718bbc4fc36109bb13e40e95d4ae4f9181c6f9060d`.
- The run manifest now records `superseded-metadata-relocated` with source, destination, size, and relocation-record path.
- Adversarial fixture rejects an unrelated experiment name without removing the source; four focused relocation/logger tests pass.

Problems:
- The relocation cleans the future A1 namespace but does not authorize L13.
- A future arm launcher must still refuse any nonempty checkpoint namespace and bind the final L12 hash.

Decision:
- Preserve the metadata permanently with the historical smoke evidence.
- Treat `checkpoints/pilot/mech_a1_real` as clean only while it remains absent; never reuse stale logger/tracker files.

Next actions:
- Include an empty-namespace check in the L13 launch preflight for every arm.
