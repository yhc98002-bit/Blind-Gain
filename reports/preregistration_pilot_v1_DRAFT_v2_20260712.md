# Four-Arm Mechanical Pilot Preregistration V1 Draft

Status:
- `draft only`; not approved, not merged as L12, and not authorization for a pilot optimizer step.
- Richard accepted the frozen R19 human audit at 60/60 pairs; approval and signatures from both PIs remain required.
- L13 remains fail-closed. No pilot optimizer step is authorized by this draft.

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

Prior observations (disclosed before launch):
- Engineering anchor Geometry3K test `Acc_final`: `0.1498 -> 0.4359`, paired delta `+0.2862`, 95% item-bootstrap CI `[+0.2446, +0.3278]`.
- Engineering anchor R19 overall pair accuracy: `0.5617 -> 0.5633`, paired delta `+0.0017`, 95% CI `[-0.0183, +0.0209]`.
- Engineering anchor R19 geometry pair accuracy: `0.4717 -> 0.4800`, paired delta `+0.0083`, 95% CI `[-0.0183, +0.0367]`.
- At step 100, R19 gray and noise pair accuracy were `0.0000` and `0.0000`; both Collapse Rates were `1.0`. These are evaluation-time ablations of the real-trained anchor, not matched blind-training arms.
- The A1/real branch of the falsification test is therefore partially informed by the anchor. Predictions for A2 gray, A2b no-image, and A3 caption remain genuine forecasts because none of those matched training arms has taken an optimizer step.
- Prior-observation source SHA256 values: Geometry3K `8ecc3a41f75bc335c73ac06a8762dce3c48c3e2d3c425bbcf9988dd142314435`, R19 real `618b8ffaaa527860f611bdbcb6961631557ea1d183558f237421f831d4b533d1`, R19 blind `bee3411413882d8d8acdff5dd23ebc9fe057d4079c0753564d6b1e70105ee32a`, resolved anchor config `fdbc29d475c23afce00f9cfa8ffd3a7a894e72a7be5027245ba9c161c61bbcaa`.

Anchor-to-pilot-A1 configuration deltas:
| Field | Engineering anchor as launched | Pilot A1 |
| --- | --- | --- |
| Training corpus | `hiyouga/geometry3k@train` (unfiltered Geometry3K train) | `data/geo3k_pilot_filtered.jsonl` (frozen 1,288-row filtered subset) |
| `freeze_vision_tower` | `false` | `true` |
| Optimized reward | native EasyR1 `r1v.py` extraction/grading | `pilot-reward-v1` canonical-v2 extraction with MathRuler precedence and shadow logging |
| Rollout TP width | `2` | `1` |
| Shared fields | Qwen2.5-VL-3B, real images, seed 1, G=5, 100 steps, matched batch/LR/KL settings | same |

Primary estimands:
- `D_gray = Delta_A1 - Delta_A2gray`.
- `D_none = Delta_A1 - Delta_A2b`.
- `D_caption = Delta_A1 - Delta_A3`.
- `Delta` is final minus step-0 greedy `Acc_final` on Geometry3K test; each estimand uses a paired item-bootstrap confidence interval.

Primary mechanistic prediction:
- Within each blind arm, per-item gains concentrate on items with high initial q_i under that arm's condition.
- Co-primary test 1: Spearman rank correlation between per-item gain and initial q_i is greater than zero. Spearman rho is computed as the Pearson correlation of average ranks, applying midranks to ties in both q_i and gain; report the point estimate and paired-item bootstrap CI.
- Co-primary test 2: `mean_gain(sample_correct_count >= 1) - mean_gain(sample_correct_count = 0)` is greater than zero, with a paired-item bootstrap CI. The at-floor group is exactly `0/16` sampled successes (`q_i=0.138659`), not every item numerically sharing that symmetric q_i.
- Descriptive gain table: report the at-floor group plus ten equal-count deciles of the above-floor tail. Sort above-floor items by `(q_i, row_index)`; `row_index` is the deterministic tie-breaker from the frozen per-item artifact. Report n and q_i range for every decile.
- Mechanistic support in this one-seed pilot requires both co-primary point estimates to be positive; intervals remain item-level and do not estimate RL run variance.
- The per-item q_i values are frozen by these guarded L7 output hashes:

| Condition | Per-item output SHA256 |
| --- | --- |
| gray | `55a215966904306e69fbbe1d2c5be8c7829873d0e653ec7738cd36df8f0b24a8` |
| none | `60db78c675680507f1c3bc28ae7294da4cf5811f5cea75306dfdb70318ea2a6d` |
| caption | `6c04277cca314dc22396c3a56175336e2ea0d81661ea2d52a96e5873d7746bd2` |

Computed filtered-train floor/above-floor anchors:
| Condition | n | At floor (0/16) | Floor fraction | Above floor | Above fraction | Mean q_i |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| gray | 1288 | 1092 | 0.8478 | 196 | 0.1522 | 0.212557 |
| none | 1288 | 1097 | 0.8517 | 191 | 0.1483 | 0.211750 |
| caption | 1288 | 732 | 0.5683 | 556 | 0.4317 | 0.359185 |

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
- The R19 v07 chart construct is labeled `cued point-value reading`: the circle marks the queried plot point and bypasses the first legend-to-series localization hop. This construct relabeling does not change any endpoint.
- SESOI is +/-0.05; no material change is supported only if the paired CI is entirely within [-0.05, +0.05].
- R20 caveat for the geometry primary: certification remains `R19-selected`. On fresh one-shot R20 seeds, geometry and chart missed only the 3B-real >=0.40 hardness band at `0.397` and `0.390`; all validity criteria passed, and no R21 was minted.

Falsification statement:
> If A1 improves geo3k strongly and produces a material geometry-FlipTrack gain while blind arms do not, the shortcut-only account is disfavored.
- Because the engineering anchor already informed the A1 branch, falsification is evaluated against the preregistered matched blind-arm contrasts; the blind-arm directions above remain forecasts.

No-peeking and launch enforcement:
- No one, including the implementing agent, may inspect pilot training or validation metrics before this preregistration is approved by both PIs, committed as `reports/preregistration_pilot_v1.md`, and present unchanged at Git `HEAD`.
- `scripts/launch_mech_pilot_arm.sh` invokes fail-closed authorization before creating a run directory or touching GPUs, then requires the final preregistration to be tracked and byte-clean against `HEAD`; it also requires critical pilot code and the selected config to be clean against `HEAD`.
- Any failed prerequisite exits before the first optimizer step. The draft filename is never sufficient.

Deviations log:
| Time | Deviation | Reason | Effect on estimands | PI disposition |
| --- | --- | --- | --- | --- |

Approval state:
- R19 human contact-sheet audit: approved. Richard accepted all three templates, 60/60 pairs across all six checks.
- PI 1 approval: pending.
- PI 2 approval: pending.
- Final L12 path `reports/preregistration_pilot_v1.md`: intentionally absent.
