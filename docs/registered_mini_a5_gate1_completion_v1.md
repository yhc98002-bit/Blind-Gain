# Registered: Mini-A5 Gate-1 completion — arm 1 (standard GRPO) and arm 3 (necessity sampling) (v1)

**Filed:** 2026-07-31, **before the first optimizer step of either arm** (I9).
**Serves:** `docs/PAPER2_RESEARCH_DOC.md` §5 Gate 1, `docs/registered_gate1_four_arm_v1.md`,
`docs/EXPERIMENT_TODO.md` §2E.
**Sign-off:** merge is sign-off under the M4 ruling, exactly as for
`docs/registered_mini_a5_main_v1.md`. `docs/EXPERIMENT_TODO.md` Part 3 lists the Gate-1
registration among the merge sign-offs; this document is that item for the two
completion arms. Launch additionally requires an immutable marker
(`reports/mini_a5_gate1_completion_registration_marker_v1.json`, to be built by the
existing marker pattern) binding this document's commit as an ancestor of `HEAD`.

## 1. Scope

Gate 1 is registered as four arms (PAPER2 §5): "(1) standard GRPO; (2) same paired
data + answer-only reward; (3) necessity sampling + answer-only reward; (4) IGPO."
Two are complete under `docs/registered_mini_a5_main_v1.md`:

| Gate-1 arm | executed as | status |
|---|---|---|
| 2 — paired data + answer-only | `mini_a5_same_data_seed1` (member mode) | complete, 120/120, F8 read |
| 4 — relational objective | `mini_a5_cp_seed1` (CP joint mode) | complete, 120/120, F8 read |

**Mapping note, recorded rather than smoothed.** The executed arm 4 is the registered
Mini-A5 CP instantiation — uniform sampling, exact product reward `acc(a_i)*acc(b_i)` —
not the full IGPO row of the four-arm table (which adds Δq sampling and the C3
premise reward). The four-arm table's arm 4 remains unexecuted at that full
specification; the CP arm stands as the Gate-1 test of the relational-reward factor.

**F8 outcome** (`reports/f8_mini_a5_endpoint_readout_v1.md`, sha256 `da7c7a74…`, §8):
**branch_2 fired.** On the primary anchor (R19 coordinate survey register, n=600):
lenient CP−member −0.0100, 95% CI [−0.0300, +0.0100], **NOT MOVED**; contract-strict
+0.0700, CI [+0.0417, +0.0983], **MOVED**, with the entire strict gap accounted for by
response-format contract validity by exact arithmetic (CP contract_valid 0.9683 vs
member 0.8133), and CP at +0.0000 lenient / +0.0100 strict against the frozen base.
The registered decision steps found branch 1's antecedent unsatisfied and fired
branch 2 (both flat on the primary anchor as measured).

**PI decision (2026-07-31, relayed in the round brief):** complete Gate 1 with the
two missing arms before choosing Paper 2's direction. Arms 1 and 3 decompose whether
the paired **data** or the necessity **selection** contribute anything, given that the
relational reward added nothing on the primary anchor. This supersedes the four-arm
registration's launch condition ("if F7 is positive, [the remaining arms] launch
without registration lag"): the branch that fired is the flat branch, and the
completion arms are authorized by the PI decision notwithstanding.

This document authorizes exactly two further 120-step arms after its marker binds.
It re-opens nothing about arms 2/4 or their readout; their numbers stand.

## 2. Design resolutions, each with its source

### R1 — Arm 1 trains on the unpaired rendering of the same frozen scenes

Sources: the four-arm registration's arms table (arm 1 data = "ordinary items",
arm 2 = "intervention-group data, flattened to single samples") **and** its Matching
clause ("Identical across all four arms: corpus, prompt template, prompt contract …").
Read together: arm 1 must come from the **same scene corpus** without the
counterfactual pairing — not from a different task corpus (geo3k/ViRL are excluded by
the Matching clause) and not from freshly generated scenes.

**No unpaired rendering exists today.** `data/mini_a5_train_v1/` contains only the
paired corpus: 6,000 member rows of 3,000 counterfactual pairs (`train.parquet`,
`train.jsonl`, `pairs.jsonl`, `images/`, `masks/`, `decontamination.json`) — verified
by listing and by the corpus audit counts. The arm-1 corpus therefore **needs
generation** (CPU-only projection; §6 T1).

**Registered construction** (`data/mini_a5_std_train_v1/train.parquet`, 6,000 rows):
for every pair in the frozen corpus, keep **member a's rendering only**, and present
it **twice per epoch** as pseudo-members `a`/`b` of a synthetic uid
`std1_<original pair_group_uid>` (adjacent rows, same 7-column schema; image paths
keep pointing at the frozen `data/mini_a5_train_v1/images/` files — nothing is
re-rendered or copied). Under `pair_group_mode: member` each row normalizes over its
own 5 rollouts, which **is** standard GRPO grouping — machine-checked by the existing
advantage/config audit family — so the pseudo-pairing is loader/reward-compatibility
metadata only and never enters the objective. This makes arm 1 differ from arm 2 in
exactly one respect: the second per-epoch exposure of each scene is the **same
rendering** instead of the **counterfactual partner**. Steps, epochs (8 × 15),
rollout-batch composition (400 rows = 200 adjacent pseudo-pairs), scene exposure
frequency, and token budget are all matched to arm 2 by construction.

**Flagged, not chosen silently:**
- "Ordinary items"/"standard GRPO" does not by itself decide between (i) this
  projection, (ii) a 3,000-row corpus without duplication, and (iii) 6,000 freshly
  generated unpaired scenes. (iii) is rejected because the Matching clause fixes the
  corpus and fresh scenes would confound scene identity with pairing (and need new
  generation + decontamination + audit). (ii) is rejected because it halves
  steps-per-epoch (3,000/400 = 7.5, a non-integer epoch boundary whose dataloader
  behavior is unverified) and breaks the exact per-epoch scene-frequency match.
  The duplication in (i) is equivalent to doubling epochs over a 3,000-item corpus.
- Member **a** is kept for every pair. This is a random ~50/50 mix of semantic sides
  because the generator randomized `semantic_side_assignment` per pair (counts
  497–527 per template×side, recorded in the corpus audit), so no semantic side is
  systematically preferred.
- The pseudo-pair route reuses the exact member-mode code path that arm 2 ran and
  smoked (zero code change). The alternative `pair_group_mode: "none"` exists in the
  overlay patch but was never exercised by any smoke or main run, and
  `compute_member_score` hard-requires complete a/b pair metadata per batch
  (`validate_pair_rows`, `broadcast_joint_accuracy`), so "none" would also force a
  new reward function. Rejected in favor of the audited path.

### R2 — Arm 3 requires a per-item Δq measurement pass that does not exist

Sources: PAPER2 §2 C1 ("Δq_i = q_i^real − q_i^blind … Apply as **sampling
probability**, not reward scaling", I1) and the four-arm registration's I1 clause.

**Per-item blind-solvability metadata does NOT exist for the Mini-A5 corpus.**
Established, not assumed:
- `reports/mini_a5_corpus_audit_v1.json` (sha256 `3f02f8e9…`) carries integrity,
  disjointness, adjacency, and template-count checks only — no per-item model
  metric of any kind. The nearest field, `answer_pointing_cues` in
  `decontamination.json`, is a text-cue audit, not blind solvability.
- No `blind_solvability*` run over this corpus exists under `experiments/runs/`
  (all existing runs are geo3k, geo3k_filtered_v2, anchor-step100, ViRL, or C5-7B).
- Per-item Δq exists only for geo3k (`reports/gate0_stratification_v1.json`,
  fields `delta_q`, `q_blind_mean`) — a different corpus; unusable here.
- `reports/mini_a5_step0_reward_audit_v1.json` is step-0 reward hit rates under the
  **training (real)** condition; it contains no blind condition and no Δq.

**Registered measurement pass** (§6 T2–T3, GPU, before the arm-3 corpus can exist):
blind-solvability inference over all 6,000 training member rows with the frozen base
model (`Qwen/Qwen2.5-VL-3B-Instruct`, registered tree digest `84c656fb…`), under
conditions `real` and `none`, via the registered harness family
(`scripts/launch_manifest_blind_solvability.sh` → `scripts/run_blind_solvability.py`,
which the launcher invokes with its self-created run manifest; family defaults
hard-coded in the launcher: group_size 5, sample_count 16, temperature 1.0,
max-tokens 512, seed 20260710). The harness consumes the geometry-manifest schema
(`split`/`row_index`/`qid`/`problem`/`answer`/`images[{path,sha256}]`), which
`train.jsonl` is not in, so a **manifest converter is prework** (T2) with a
byte-correspondence audit.

Per item: `q_real_i` and `q_blind_i` := `p_sample` (mean correctness of the 16
temperature-1 samples — the reward-opportunity estimand C1 names), and
`Δq_i = q_real_i − q_blind_i`.

**Registered sampling law (I1 — probability, never reward scaling):** draw weight
`w_i = max(Δq_i, 0) + 1/16`, sampling probability `p_i = w_i / Σ w`. Implemented
**as data**, not as a trainer change: `data/mini_a5_necessity_train_v1/train.parquet`
is 6,000 row-slots drawn i.i.d. **with replacement** from the 6,000 frozen member
rows with probability `p_i` (build seed 20260731), arranged as 3,000 adjacent
synthetic pseudo-pairs (`nec1_%06d`, drawn rows relabeled alternately `a`/`b`),
same 7-column schema, source mapping recorded in a sidecar. The training loop,
reward, and config geometry stay byte-identical to arm 2's member path, so the arm
differs from arm 2 **only** in which items it samples — which is exactly C1.

**Flagged, not chosen silently** (none of these is fixed by any prior document;
merge of this file ratifies them):
- Blind condition = `none` (no image), not `gray`/`noise`/`caption`. `none` is the
  literal "blind" of C1's `q_blind`; the others are Paper-1 access-matrix controls.
- `q` field = `p_sample` (16-sample mean), not `pass_at_k16`/`p_greedy`:
  reward opportunity under the training decode (T=1 sampling) is what GRPO sees.
- `f(Δq) = max(Δq,0) + 1/16`: the floor equals the measurement resolution of 16
  samples, keeps every item reachable (no support collapse), and bounds the max/min
  draw ratio at 17:1. Negative Δq is clipped to the floor rather than excluded.
- Pre-materialized resampling (fixed for all 8 epochs, `shuffle: false`) rather than
  a per-epoch weighted sampler: zero trainer-code change, exactly auditable, and the
  registered configs already run fixed-order corpora. The cost — epochs replay the
  same draw — is recorded as a known property, not discovered later.

### R3 — Geometry mirrors the completed arms exactly

Source: the two registered Mini-A5 configs and the main registration's
matched-difference discipline. Verified this round: the member and CP configs differ
**only** in `pair_group_mode`, `reward_function`, `experiment_name`,
`save_checkpoint_path`. The two new configs are byte-identical to the **member**
config except `train_files`, `experiment_name`, `save_checkpoint_path` (three
fields; machine-checkable, and re-verified at launch). Both new arms therefore run:
120 steps, seed 20260716, rollout_batch_size 400, global_batch_size 80, n=5,
temperature 1, top-p 1, lr 1e-6, KL-as-loss 0.01, frozen vision tower, val_freq 0,
save_freq 20, one node × 8 GPUs, member-mode grouping, answer-only reward
`compute_member_score` — identical to arm 2. Single seed per arm, matching the
completed arms (`*_seed1`).

## 3. Locked design — arm 1 (`mini_a5_std_seed1`)

- Config: `configs/train/mini_a5_std_3b_v1.yaml`
  (sha256 `9c267b3058adc08ad5abcf0b740b67f1fb83c58f5a1964fbef2249e569f91ca8`).
- Corpus: `data/mini_a5_std_train_v1/train.parquet` per R1 — **to be built** (T1),
  hash pinned in the launch marker.
- Reward: `src/rewards/cp_grpo_reward.py:compute_member_score` (answer-only);
  `pair_group_mode: member`; the run must never enter the joint branch.

## 4. Locked design — arm 3 (`mini_a5_necessity_seed1`)

- Config: `configs/train/mini_a5_necessity_3b_v1.yaml`
  (sha256 `4cc41233732eb5f71a2023d61cd06a4ceed629a2070021ba0a88360654e92b9e`).
- Corpus: `data/mini_a5_necessity_train_v1/train.parquet` per R2 — **cannot exist
  until the Δq measurement pass completes** (T2–T4), hash pinned in the launch marker.
- Reward and mode: identical to arm 1.
- Necessity enters **only** through the draw probabilities (I1). No reward term, no
  loss weight, no advantage transform anywhere touches Δq.

## 5. Immutable inputs that exist today

| Input | Path | SHA256 |
|---|---|---|
| Arm-1 config | `configs/train/mini_a5_std_3b_v1.yaml` | `9c267b3058adc08ad5abcf0b740b67f1fb83c58f5a1964fbef2249e569f91ca8` |
| Arm-3 config | `configs/train/mini_a5_necessity_3b_v1.yaml` | `4cc41233732eb5f71a2023d61cd06a4ceed629a2070021ba0a88360654e92b9e` |
| Member template config | `configs/train/mini_a5_same_data_3b_v1.yaml` | `358e6d7cd40c3748e9e5dbae6715310611fcb295bab107e1138b4071ea0fcd9b` |
| CP config (matched-diff check) | `configs/train/mini_a5_cp_3b_v1.yaml` | `8d7736f5364bd8bfd5595584aa05917a71306888282eeb2a37682ebf02c325e8` |
| Frozen paired corpus | `data/mini_a5_train_v1/train.parquet` | `0b0f0965987d1c340c3ebd78da742c9d99b319b61524b5cb42960519fd9c9b28` |
| Frozen paired corpus (jsonl) | `data/mini_a5_train_v1/train.jsonl` | `07d785ee6ae4a3b5325e12595f7830c5924e31c49565554f1e88b2abffc5fa5c` |
| Pair records | `data/mini_a5_train_v1/pairs.jsonl` | `c592d8560cf3f5544fea36a12b3b52642d0faf0056c4ef9fddc0dde1f75f34bd` |
| Decontamination record | `data/mini_a5_train_v1/decontamination.json` | `6060439b0b2b4b3253fbbc62843ba4307578af36806b3c577a1bb736c290851d` |
| Monitoring val set | `data/mini_a5_plumbing_val_v1.jsonl` | `1ed1413f6ca92d67fdd9ea2f8bf9072d9126c97403ffcd9fef0f97d9cbb74475` |
| Pair grouping impl | `src/train/cp_grouping.py` | `6cb21c0a199d049780aa427aad1f51cd995db553433c1d2627431f0c1c1076e0` |
| Reward impl | `src/rewards/cp_grpo_reward.py` | `e8dea3e49c03c44a050881fba6e9bec5c8120977659f5a786f2bf4526b6213f0` |
| EasyR1 overlay | `docs/easyr1_mini_a5_pair_grouping_patch.diff` | `03a46cd00626b58d5a4e56c0c7d450330801ef5b05cb3e11e7243bff15614b86` |
| Corpus audit | `reports/mini_a5_corpus_audit_v1.json` | `3f02f8e995c33018c9ccbb2e72cfb97bdf3c99ed6fde5b97fb84fbf94baa4131` |
| F8 readout (cited outcome) | `reports/f8_mini_a5_endpoint_readout_v1.md` | `da7c7a742893fcfdfe56ba4b7305ea7e0c7c26d1d399a3b79196496ae900d2eb` |
| Launcher (pre-extension) | `scripts/launch_mini_a5_main.sh` | `15e1cfc719d21cfacc9832e31e518d772b770ac7e1debd77a8d6c820e61c1824` |
| R19 eval manifest | `data/fliptrack_v02r19_artifact_expanded_source_manifest.jsonl` | `23dd24452670392d6355c06b6b167a1c868660c11d21b20e0bae393dc82126f0` |
| R20 eval manifest | `data/fliptrack_r20_source_manifest.jsonl` | `20222e60201b4e116b4520f1aad8bd749bf49185a0a414087c1a8fe22dbf2ef3` |
| chart-v08 eval manifest | `data/fliptrack_chart_v08_calibration_v1_manifest.jsonl` | `d90f3f13c1f3304669c8ca6c717ae58eaa7cfe4e785fab3bae8520e15065c292` |

Model: ModelScope `Qwen/Qwen2.5-VL-3B-Instruct`, registered tree digest
`84c656fb6d6a5f4ef3ccbf47c3880c3a3d22c63eb8736a88fa7a0ddb542e3568`; EasyR1 base
revision `dd71bbd252694f5f850213eec15795b6b88d9fea` with the patch inventory applied
only in `artifacts/repos/EasyR1-mini-a5` — all unchanged from the main registration
and re-verified at launch.

## 6. What does NOT exist yet — prework ledger (all blocking, in dependency order)

| # | Item | Harness / pattern | Cost | GPU |
|---|---|---|---|---|
| T1 | Arm-1 corpus `data/mini_a5_std_train_v1/` + build report | new `scripts/build_mini_a5_std_corpus.py` (deterministic projection per R1) + audit extension + **adversarial fixture (I10)** | CPU, minutes | none |
| T2 | Harness manifest for the training corpus | new `scripts/build_mini_a5_blind_solvability_manifest.py` (train.jsonl → geometry-manifest schema with per-image sha256) + fixture | CPU, minutes | none |
| T3 | **Δq measurement pass** | `scripts/launch_manifest_blind_solvability.sh <node> <gpu> {real,none} <base model> <T2 manifest> …` — the launcher creates the run manifest itself; never invoke the runner bare | 6,000 items × (greedy + 16 samples) × 2 conditions; reference: geo3k `none` = 2,702 items in 70 min ⇒ **≈ 2.5–3.5 h per condition, ≤ ~7 GPU·h total** | **1 GPU** (single free GPU suffices; two conditions may run on two GPUs in parallel) |
| T4 | Δq table + arm-3 corpus `data/mini_a5_necessity_train_v1/` | new `scripts/build_mini_a5_necessity_corpus.py` (reads both per_item.jsonl, emits `data/mini_a5_necessity_metadata_v1/delta_q.jsonl` + resampled parquet per R2) + **empirical draw-frequency audit** + fixture | CPU, minutes | none |
| T5 | Launcher extension (`std`/`necessity` cases with per-mode TRAIN_DATA and expected reward suffix) + refusal re-checks | edit `scripts/launch_mini_a5_main.sh`; new hash pinned in the marker | CPU | none |
| T6 | Registration marker binding this doc | `build_mini_a5_main_registration_marker.py` pattern → `reports/mini_a5_gate1_completion_registration_marker_v1.json` | CPU | none |
| T7 | Plumbing smokes, one per arm, + step-0 reward audit on each new corpus | 1-step smoke mirroring `mini_a5_member_plumbing_smoke_v1.yaml` on a 48-row builder-produced subset; step-0 audit per the existing pattern | ~15–30 min per smoke | 8 GPUs briefly (smoke), 1 GPU (step-0) |

Main arms after prework: 120 steps each ≈ 20–40 h wall on a fully free 8-GPU node
(observed: CP ≈ 20 h, member ≈ 39 h including checkpoint merges), sequential on one
node or concurrent on two distinct nodes, storage watcher mandatory as in the main
registration. **No GPU work, including T3, is launched in the round that files this
document.** No training/reward/grouping code change is authorized by this
registration; T1–T7 touch only data builders, the launcher, and audits.

## 7. Execution and placement

Exact launch commands (after T1–T7 complete and this document's marker binds):

```bash
bash scripts/launch_mini_a5_main.sh std <node> 0,1,2,3,4,5,6,7
bash scripts/launch_mini_a5_main.sh necessity <node> 0,1,2,3,4,5,6,7
```

The launcher refuses everything the main registration lists (dirty inputs, marker
commit not an ancestor of `HEAD`, hash drift, EasyR1 revision/patch drift, occupied
GPUs, competing trainer, checkpoint overwrite, storage-guard failure), with the new
corpora and the two new configs added to its hash-verified input set.

## 8. Sealed endpoints — the four-arm readout

Same instruments, harness, and procedure as `docs/registered_mini_a5_endpoint_readout_v1.md`,
extended to four arms; nothing else changes:

- **Item sets:** the three pinned manifests of §5; R19 evaluated through the locked
  R19 manifest (`R19_MANIFEST_SHA256` in `scripts/launch_fliptrack_eval_shards.sh`).
- **Decoding:** greedy, max_new_tokens 32, image_mode real, eval seed 0 — identical
  to the six F8 cells.
- **Primary endpoint:** R19 **coordinate survey register** pair accuracy
  (`src.eval.fliptrack_metrics.pair_score`), per task role, **never aggregated
  across roles (I13)**; header-cued table stays the retention canary and the
  nine-series trace the oracle-localized control, each reported separately.
- **Both contracts reported for every cell (I7):** lenient `pair_correct` and
  contract-strict `strict_pair_correct`; if they disagree, the disagreement is the
  result (as it was in F8).
- **Pre-specified contrasts**, paired item bootstrap 10,000 draws, seed 20260729,
  percentile 2.5/97.5, unit `pair_id`, both sides resampled on the same pair
  indices, exact McNemar alongside; "moves" = CI excluding zero, a contained-zero
  positive point estimate is NOT MOVED:
  1. arm 2 − arm 1 (is the paired data enough?),
  2. arm 3 − arm 2 (is item selection enough?),
  3. arm 1 − base and arm 3 − base (absolute levels against the frozen base cells
     already cited in F8 §6).
  The arm 4 − arm 2 contrast was read in F8 and is not re-decided.
- **Branch reading:** the four-arm registration's pre-committed branches apply with
  the F8 outcome fixed (arm 4 ≈ arm 2 on the primary lenient contract; the
  contract-strict disagreement recorded, fully format-attributed). Margins are not a
  success criterion; chained premise carries no weight; the VAG attribution
  constraint stands and remains **instrument-absent** here (no blind control arm is
  part of this completion — any success wording is bounded accordingly, I8).
- **Sealing:** no prediction, metric, or accuracy file from arm 1 or arm 3 is opened
  before **both** arms complete and the acceptance audit below passes; partial
  readouts are prohibited. R19/R20 are never modified, regenerated, or trained on
  (I11); the new corpora reuse only frozen training-side scenes, so the corpus
  audit's train/eval disjointness carries over and is re-verified per T1/T4 (I6).

## 9. Acceptance conditions (mirror the main registration)

1. Both run manifests finish with exit code 0 and exactly 120 optimizer steps.
2. Effective configs, data, model, registration, placement, and EasyR1 hashes match
   this registration and its marker.
3. Neither run ever enters the joint branch (member-mode discipline; the structured
   advantage-audit events show per-source-prompt grouping only).
4. No NaN, traceback, OOM, or fatal NCCL signature in either log.
5. Every saved checkpoint is hash-inventoried before any retention action.
6. An independent versioned report records every check before any endpoint value is
   read.
7. **Corpus audits pass before launch:** T1's projection audit (row-for-row identity
   with the frozen corpus member-a rows; synthetic-uid disjointness from real uids;
   adjacency; 7-column schema) and T4's resample audit (every slot byte-identical to
   a source row; empirical draw frequencies consistent with the registered `p_i`
   vector; build-seed reproducibility; adjacency; schema).
8. **Matched-difference audit:** each new config differs from
   `mini_a5_same_data_3b_v1.yaml` in exactly `train_files`, `experiment_name`,
   `save_checkpoint_path` — machine-checked at launch.
9. Every new builder/audit ships an adversarial fixture its predecessor fails (I10);
   `*_audited` artifacts are never byte-identical to their source.

A failed arm does not authorize an ad-hoc retry; a fix requires a new registered
version with an adversarial fixture.

## 10. Deviations log

(empty at filing)
