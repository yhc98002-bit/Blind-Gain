# Four-Arm Mechanical Pilot Preregistration V1

Status:
- Registered after approval by both PIs; merge is sign-off.
- Richard accepted the frozen R19 human audit at 60/60 pairs. Under the
  main-phase rule, merge is sign-off; there are no signature or sealing rounds.
- No pilot optimizer step ran before this registration was merged.

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
> The existence and approximate magnitude of the A1 benchmark/FlipTrack dissociation were observed before registration. Therefore, hypotheses concerning A1's qualitative direction are partially informed. Blind-arm recovery, A3 behavior, q_i–gain associations, and cross-arm contrasts remain prospective.
- The anchor is an observed engineering calibration and is never presented as a preregistered confirmation.
- Prior-observation source SHA256 values: Geometry3K `8ecc3a41f75bc335c73ac06a8762dce3c48c3e2d3c425bbcf9988dd142314435`, R19 real `618b8ffaaa527860f611bdbcb6961631557ea1d183558f237421f831d4b533d1`, R19 blind `bee3411413882d8d8acdff5dd23ebc9fe057d4079c0753564d6b1e70105ee32a`, resolved anchor config `fdbc29d475c23afce00f9cfa8ffd3a7a894e72a7be5027245ba9c161c61bbcaa`.

Anchor-to-pilot-A1 comparison:
| Field | Engineering anchor as launched | Pilot A1 |
| --- | --- | --- |
| Corpus filtering | all 2,101 Geometry3K train rows | frozen 1,288-row subset after conservative-candidate removal |
| Reward implementation | native EasyR1 `r1v.py` extraction/grading | `pilot-reward-v1`: canonical-v2 extraction, MathRuler precedence, contract-valid format component, native shadow |
| Tower setting | `freeze_vision_tower=false` as resolved at launch | `freeze_vision_tower=true` |
| Prompt/parser | `r1v.jinja`; native non-DOTALL training extractor | same `r1v.jinja`; immutable canonical-v2 extraction for pilot reward/evaluation |
| Data | `hiyouga/geometry3k@train` + `hiyouga/geometry3k@test` | `data/geo3k_pilot_filtered.jsonl` + `hiyouga/geometry3k@test` |
| Checkpoint schedule | steps 20/40/60/80/100; validation every 10 steps | steps 20/40/60/80/100; validation every 10 steps |
| Eval set | 601-row Geometry3K test; post-hoc R19 at base/step 100 | same 601-row test; R19 at steps 0/60/100 |
| Decontamination | none applied before anchor training | Layer-1 plus train-vs-test conservative candidates removed under frozen V4 rule |
| Rollout placement | TP`2` | TP`1` |
| Shared optimization fields | Qwen2.5-VL-3B, real images, seed 1, G=5, 100 steps, batch/LR/KL settings | same |

Outcome tiers:
- Primary RQ1: cross-arm final-accuracy contrasts and recovery fractions on the Geometry3K test.
- Primary RQ2: change in R19 geometry pair accuracy.
- Key secondary: R19 overall pair-accuracy change; the q_i hurdle contrast; `D_caption^final = Acc_A3,100 - Acc_A1,100` with directional prediction `>= 0` on filtered Geometry3K; and `D_caption^gain = Delta_A3 - Delta_A1` reported separately.
- Secondary: all per-category FlipTrack endpoints, including the cued chart point-value reading category.
- Robustness: R20, chart v08, long horizon, and alternative parser fields.
- Overall R19 is always shown with every per-template result. No post-hoc R19-minus-chart composite is computed.

Primary RQ1 estimands:
- `D_gray = Delta_A1 - Delta_A2gray`.
- `D_none = Delta_A1 - Delta_A2b`.
- `D_caption = Delta_A1 - Delta_A3`.
- `Delta` is final minus step-0 greedy `Acc_final` on Geometry3K test; each estimand uses a paired item-bootstrap confidence interval.
- Recovery fractions are `Delta_arm / Delta_A1`, reported with paired item-bootstrap intervals and the registered denominator-stability condition.

Mechanism analysis:
- `q_i` is a Jeffreys-smoothed estimate of baseline reward-opportunity; it is never described as a directly observed latent.
- PRIMARY mechanism analysis: within each arm under its own baseline condition, the hurdle contrast `mean_gain(c_i > 0) - mean_gain(c_i = 0)` is greater than zero, with a paired-item bootstrap CI. Here `c_i` is the number correct among the 16 frozen baseline samples.
- Secondary: tie-corrected Spearman rank association between q_i and per-item gain over all items. Spearman rho is the Pearson correlation of average ranks, with midranks for ties in q_i and gain.
- Secondary: the same tie-corrected rank association restricted to `c_i > 0` items.
- The floor is exactly `c_i=0` (0/16 sampled successes, `q_i=0.138659`), not every item numerically sharing that symmetric q_i.
- Descriptive gain table: report the at-floor group plus ten equal-count deciles of the above-floor tail. Sort above-floor items by `(q_i, row_index)`; `row_index` is the deterministic tie-breaker from the frozen per-item artifact. Report n and q_i range for every decile.
- The per-item q_i values are frozen by these guarded L7 output hashes:

| Condition | Per-item output SHA256 |
| --- | --- |
| real | `021da42f00eab94bc431ed0e7924110c237f77454b23ded5a8f1064c48fd6aa3` |
| gray | `55a215966904306e69fbbe1d2c5be8c7829873d0e653ec7738cd36df8f0b24a8` |
| none | `60db78c675680507f1c3bc28ae7294da4cf5811f5cea75306dfdb70318ea2a6d` |
| caption | `6c04277cca314dc22396c3a56175336e2ea0d81661ea2d52a96e5873d7746bd2` |

Computed filtered-train floor/above-floor anchors:
| Condition | n | At floor (0/16) | Floor fraction | Above floor | Above fraction | Mean q_i |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| real | 1288 | 668 | 0.5186 | 620 | 0.4814 | 0.354453 |
| gray | 1288 | 1092 | 0.8478 | 196 | 0.1522 | 0.212557 |
| none | 1288 | 1097 | 0.8517 | 191 | 0.1483 | 0.211750 |
| caption | 1288 | 732 | 0.5683 | 556 | 0.4317 | 0.359185 |

Directional predictions:
- `Delta_A3 >= Delta_A2gray` and `Delta_A3 >= Delta_A2b`.
- `Delta_A1` and `Delta_A3` are closer to each other than either is to the zero-visual-bit arms.
- `D_caption^final = Acc_A3,100 - Acc_A1,100 >= 0` is secondary and prospective; `D_caption^gain = Delta_A3 - Delta_A1` is reported separately.

Secondary analyses:
- Recovery fractions are interpreted only if `Delta_A1 >= 2 x paired SE`; otherwise the registered primary values are shown with an unstable-denominator warning.
- Equivalence of `Delta_A2gray - Delta_A2b` uses margin +/-0.05 and is supported only if the paired CI lies entirely inside the margin.
- Format prediction: `DeltaFormat_blind >= DeltaFormat_A1 - 0.05` using `contract_valid`, conditional on a nontrivial A1 format gain.

RQ2 FlipTrack R19 endpoints:
- Checkpoints: 0, 60, and 100. Step 60 is scored from the scratch-resident merged checkpoint before cleanup.
- PRIMARY: geometry-category pair accuracy.
- SECONDARY: overall R19 pair accuracy.
- Document category is calibration only because the 7B instrument is saturated.
- Label: `cued chart point-value reading`.
> In the R19 chart template, a circle indicates the queried plot point in both pair members. The task therefore certifies fine-grained value reading at a visually cued location; it does not certify the intended legend-to-series localization hop. An accompanying in-image sentence inaccurately describes the star as marking the queried point, although the star appears in the legend and the circle marks the plot point. Human audit found no resulting answer ambiguity, but the wording and cue narrow the construct. Chart results are secondary and are reported separately from the geometry-primary endpoint.
- SESOI is +/-0.05; no material change is supported only if the paired CI is entirely within [-0.05, +0.05].
> The primary FlipTrack endpoint was selected during R19 calibration. R20 independently satisfies all registered validity and anti-shortcut criteria but narrowly misses the preregistered 3B-real sensitivity floor for geometry and chart; it is therefore reported as robustness evidence, not a confirmatory pass.
- R19 and R20 are never pooled.

Falsification statement:
> If A1 improves geo3k strongly and produces a material geometry-FlipTrack gain while blind arms do not, the shortcut-only account is disfavored.
- Because the engineering anchor already informed the A1 branch, falsification is evaluated against the preregistered matched blind-arm contrasts; the blind-arm directions above remain forecasts.

Parser acceptance conditions:
- The 0.9156 canonical-v2/native agreement rate is context, not an acceptance criterion; the retired 0.95 threshold is not used.
- All disagreements remain preserved row-by-row under a fixed residual taxonomy.
- Blinded adjudication contains no native-correct/canonical-wrong residual.
- Canonical-v2 passes the adversarial negative set, including unit-conflict and malformed-answer cases.
- Parser and reward versions become immutable before launch; native r1v reward is logged as a shadow for every rollout.

ViRL39K interpretation fork:
| Observed M1 pattern | Registered ruling |
| --- | --- |
| caption q≈real AND zero-bit q substantial | Geo3K mechanism likely generalizes. |
| caption well below real AND zero-bit near floor | Shortcut susceptibility is corpus-dependent; Geo3K cannot support a broad claim. |
| strong source/category heterogeneity | H-mixed becomes the headline; stratify. |
| captions exceed real | Caption-mediated accessibility; A3 indispensable. |
| gray materially differs from no-image | Image-token presence is itself causal; retain both. |
- M1 records the obtaining row after this registration merges; PIs confirm through Richard.

Registration provenance and no-peeking:
- Registration commit hash: `2782815cc057d85a302af8bac232cac2b0e1ec75`, the first commit introducing this approved final path.
- Exact planned launch commands:
  - `scripts/launch_mech_pilot_arm.sh a1_real an12 0,1,2,3`
  - `scripts/launch_mech_pilot_arm.sh a2_gray an12 4,5,6,7`
  - `scripts/launch_mech_pilot_arm.sh a2b_noimage an29 0,1,2,3`
  - `scripts/launch_mech_pilot_arm.sh a3_caption an29 4,5,6,7`
- no pilot optimizer step has run
- the executing agent had continuous log access; PIs reviewed the anchor and audit artifacts before registration.
- No one, including the implementing agent, may inspect pilot training or validation metrics before this preregistration is merged as `reports/preregistration_pilot_v1.md` and present unchanged at Git `HEAD`.
- `scripts/launch_mech_pilot_arm.sh` invokes fail-closed authorization before creating a run directory or touching GPUs, then requires the final preregistration to be tracked and byte-clean against `HEAD`; it also requires critical pilot code and the selected config to be clean against `HEAD`.
- Any failed prerequisite exits before the first optimizer step. The draft filename is never sufficient.

Deviations log:
| Time | Deviation | Reason | Effect on estimands | PI disposition |
| --- | --- | --- | --- | --- |

Registration state:
- R19 human contact-sheet audit: approved. Richard accepted all three templates, 60/60 pairs across all six checks.
- Registration state: merged-at-HEAD; merge is sign-off.
- Final M0 path: `reports/preregistration_pilot_v1.md`.
