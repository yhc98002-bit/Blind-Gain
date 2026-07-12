# Four-Arm Mechanical Pilot Preregistration V1 Draft

Status:
- `draft only`; not approved, not merged as L12, and not authorization for a pilot optimizer step.
- Required external actions remain the frozen R19 human contact-sheet audit and approval by both PIs.

Frozen inputs:
- Filtered Geometry3K IDs: `data/geo3k_pilot_filtered_ids.json`, SHA256 `8631d015ee8593669b46cc707b9fe1fb3690391520bccf416b64bbb2306ff7d1`.
- L7 summary: `reports/blind_solvability_geo3k_v2.json`, SHA256 `44c21263c72279cfecf29eb7b154a939df7bbcd5099bc8d10a495d080f15a6a0`.
- L7 independent audit: `reports/blind_solvability_geo3k_v2_audited.json`, SHA256 `131e441f27e1099bcd87855591f6896773b3fcc079b44c3849fd7197bdb96ee7`, machine status `pass`.
- Pilot reward guard: `posix-itimer-v1` at `5.0` seconds.

| Arm | Image condition | Config | SHA256 |
| --- | --- | --- | --- |
| A1 real | `real` | `configs/train/mech_a1_real_3b_geo3k.yaml` | `abf9e9d9a48e35dd5f29e86a51dd674d1a666a088f9ced9f7acc86338a53560e` |
| A2 gray | `gray` | `configs/train/mech_a2_gray_3b_geo3k.yaml` | `c36f24f6bb4915b84722a262eb656332a6ebda1c0584be5f33f73d597ccaec64` |
| A2b no-image | `none` | `configs/train/mech_a2b_noimage_3b_geo3k.yaml` | `0ead558c117c69b752814287a1042614dc0027fc82c700e563b6c63478d981ac` |
| A3 caption | `caption` | `configs/train/mech_a3_caption_3b_geo3k.yaml` | `573b1ca7e26f8365ba140ecb40d76f75f23b8b2ff399c9b45d8200740e2d8826` |

The configs are structurally identical after removing only `data.image_condition`, `trainer.experiment_name`, and `trainer.save_checkpoint_path`.

Design:
- Four arms: A1 real, A2 gray, A2b no-image, and A3 fixed 3B question-blind captions.
- Qwen2.5-VL-3B, frozen vision tower, seed 1, G=5, 100 optimizer steps, and identical configs except registered arm identity.
- Synchronous EasyR1/GRPO stays on one node with four colocated GPUs; 3B rollout serving is TP1.
- Checkpoints: steps 0, 20, 40, 60, 80, and 100. Step 0 is the base model already on disk and is not duplicated.
- Greedy full Geometry3K-test validation every 10 steps under one locked prompt contract.
- Pilot checkpoints save to shared arm directories and are swept under the latest-raw-only retention rule; only step-100 merged remains on shared storage.

One-seed scope:
> These are pilot estimands and directional predictions, not definitive hypothesis tests of the training procedure; item-level paired intervals quantify evaluation uncertainty, not run-to-run RL variance.

Primary estimands:
- `D_gray = Delta_A1 - Delta_A2gray`.
- `D_none = Delta_A1 - Delta_A2b`.
- `D_caption = Delta_A1 - Delta_A3`.
- `Delta` is final minus step-0 greedy `Acc_final` on Geometry3K test; each estimand uses a paired item-bootstrap confidence interval.

Primary mechanistic prediction:
- Within each blind arm, per-item gains concentrate on items with high initial q_i under that arm's condition.
- Registered test: rank correlation between per-item gain and initial q_i is greater than zero, accompanied by a q_i-quartile gain table.
- The per-item q_i values are frozen by these guarded L7 output hashes:

| Condition | Per-item output SHA256 |
| --- | --- |
| gray | `55a215966904306e69fbbe1d2c5be8c7829873d0e653ec7738cd36df8f0b24a8` |
| none | `60db78c675680507f1c3bc28ae7294da4cf5811f5cea75306dfdb70318ea2a6d` |
| caption | `6c04277cca314dc22396c3a56175336e2ea0d81661ea2d52a96e5873d7746bd2` |

Computed filtered-train q_i anchors:
| Condition | Mean | CI low | CI high | Q25 | Median | Q75 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| gray | 0.212557 | 0.202497 | 0.223041 | 0.138659 | 0.138659 | 0.138659 |
| none | 0.211750 | 0.201292 | 0.222150 | 0.138659 | 0.138659 | 0.138659 |
| caption | 0.359185 | 0.343668 | 0.375652 | 0.138659 | 0.138659 | 0.548496 |

Directional predictions:
- `Delta_A3 >= Delta_A2gray` and `Delta_A3 >= Delta_A2b`.
- `Delta_A1` and `Delta_A3` are closer to each other than either is to the zero-visual-bit arms.

Secondary analyses:
- Recovery ratios are reported only if `Delta_A1 >= 2 x paired SE`, labeled conditional descriptive intervals.
- Equivalence of `Delta_A2gray - Delta_A2b` uses margin +/-0.05 and is supported only if the paired CI lies entirely inside the margin.
- Format prediction: `DeltaFormat_blind >= DeltaFormat_A1 - 0.05` using `contract_valid`, conditional on a nontrivial A1 format gain.

RQ2 FlipTrack R19 endpoints:
- Checkpoints: 0, 60, and 100. Step 60 is scored from the scratch-resident merged checkpoint before cleanup.
- PRIMARY: geometry-category pair accuracy.
- SECONDARY: overall R19 pair accuracy.
- Document category is calibration only because the 7B instrument is saturated.
- SESOI is +/-0.05; no material change is supported only if the paired CI is entirely within [-0.05, +0.05].

Falsification statement:
> If A1 improves geo3k strongly and produces a material geometry-FlipTrack gain while blind arms do not, the shortcut-only account is disfavored.

Deviations log:
| Time | Deviation | Reason | Effect on estimands | PI disposition |
| --- | --- | --- | --- | --- |

Approval state:
- R19 human contact-sheet audit: pending.
- PI 1 approval: pending.
- PI 2 approval: pending.
- Final L12 path `reports/preregistration_pilot_v1.md`: intentionally absent.
