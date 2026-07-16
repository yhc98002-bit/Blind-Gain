# Registered Mechanical Pilot Seeds 2-3 V1

Registration state: merged-at-HEAD; merge is sign-off.

## Scope

- This document registers the M3 follow-up runs authorized in `docs/MAIN_PHASE_BRIEF.md`.
- Seed `1` remains governed by `reports/preregistration_pilot_v1.md` and is not reinterpreted here.
- Seed `2` and Seed `3` repeat the same four-arm mechanical pilot: A1 real, A2 gray, A2b no-image, and A3 fixed question-blind captions.
- Each seed is a training unit. This document and the selected config must be committed and byte-clean at `HEAD` before that unit's first optimizer step.
- The executing agent may inspect process health, storage, checkpoint completeness, and reward-log presence, but must not inspect training, validation, or evaluation performance values before all four arms in the same seed have completed and their immutable readout queue is bound.

## Locked Design

- Base model: `Qwen/Qwen2.5-VL-3B-Instruct@66285546d2b821cf421d4f5eb2576359d3770cd3`.
- Corpus: `data/geo3k_pilot_filtered.jsonl`, with frozen ID list `data/geo3k_pilot_filtered_ids.json`.
- Reward, prompt contract, parser, image transformations, caption store, frozen vision tower, G=5, optimizer settings, 100-step budget, validation cadence, and checkpoint cadence are identical to seed 1.
- Within a follow-up seed, every arm uses the same `data.seed`. The intervention seed remains fixed at `data.image_condition_seed=20260710` in all arms and all seeds so gray/noise construction is not an uncontrolled run-level variable.
- Checkpoints are `{0,20,40,60,80,100}`. Step 0 is the shared base model and is never duplicated.
- Placement is one synchronous EasyR1 trainer on four GPUs of one node, with TP1 rollout and four replicas. Two trainers are not colocated on one node because the seed-1 failure established inadequate host-memory headroom.
- Saves use unique shared namespaces under `checkpoints/pilot/`; latest-raw-only retention and independent evaluation queues remain mandatory.

## Immutable Configs

The only differences from the corresponding seed-1 arm config are `data.seed`, `trainer.experiment_name`, and `trainer.save_checkpoint_path`.

| Seed | Arm | Config | SHA256 |
| ---: | --- | --- | --- |
| 2 | A1 real | `configs/train/mech_a1_real_seed2_3b_geo3k.yaml` | `c357a636fd6596dbe2ca3eb1e9677f30396d6d256b806c27812f203da3d629a5` |
| 2 | A2 gray | `configs/train/mech_a2_gray_seed2_3b_geo3k.yaml` | `6fc6412f107d04e095ef9c0cff26c8635d3b8bc121719ac38cddf2a793d841fc` |
| 2 | A2b no-image | `configs/train/mech_a2b_noimage_seed2_3b_geo3k.yaml` | `4c882935db5b3a7ce9279b3f2a0c851a5efbfeee75b8f5e4dd81451cd8d63beb` |
| 2 | A3 caption | `configs/train/mech_a3_caption_seed2_3b_geo3k.yaml` | `c45fa70fd25a180dc4b723122c9efa47b70b6c8bc81804c1c188141099442098` |
| 3 | A1 real | `configs/train/mech_a1_real_seed3_3b_geo3k.yaml` | `f066d29bebb540fc63d1a4db6a62e6e6f5de59e9624c204d8917d741df7481b3` |
| 3 | A2 gray | `configs/train/mech_a2_gray_seed3_3b_geo3k.yaml` | `aa4c70eb3c4d82c9baf10f0c275b128f8f99833cc73e557f6b991436ef07d634` |
| 3 | A2b no-image | `configs/train/mech_a2b_noimage_seed3_3b_geo3k.yaml` | `f9bcaf4c5ee1368e183b5ddc80426e18aeeb1f2122491ae7f3296cb354845eb9` |
| 3 | A3 caption | `configs/train/mech_a3_caption_seed3_3b_geo3k.yaml` | `8e0758ddce0a1366325e34c737487395d7e61d08b424256717d72492bb3f23ac` |

## Registered Readout

- `reports/pilot_3seed_summary_v1.md` reports every seed-1 estimand for each seed, pooled item-paired estimands, and descriptive seed dispersion.
- The pooled gray-versus-no-image equivalence check retains the registered margin and confidence-interval rule. R4 has independently retained A2 gray in the 7B flagship from the precommitted M8 fork; M3 still reports the equivalence result but does not reverse that fired rule.
- M10 support sharpening is folded into each seed readout. Required language is “mass sharpening within observed support” and “not observed in the base K-sample set”; no result may claim that RL created or taught a capability.
- Registered analyses only. Process-health observations cannot select checkpoints, stop runs, alter arm order, or change the terminal step.

## Deviations

- Initially empty. Any operational or scientific irregularity is appended once to `reports/main_deviations.md` and bound into the affected run manifest.
