# Registered LH2 Stage 1 V1 — Second Long-Horizon Seed of the Anchor Recipe

Status:
- Registration for the LH2 stage-1 training unit (`lh2_anchor_seed2_3b_geo3k`,
  optimizer steps 0 -> 200). Registration state: merged-at-HEAD; merge is
  sign-off (I9: this registration and every file in its immutable-inputs table
  merge before the first optimizer step; the launcher's merged-at-HEAD check is
  fail-closed).
- This document registers the design, the mandatory segmentation, the
  evaluation schedule, and the step-200 go/no-go. It does not launch anything.
  The orchestrator launches segment 1 when a genuinely free 4-GPU slot exists
  under the preconditions in section 6.
- Stage 2 (steps 200 -> 400) is pre-specified in section 5 and is reachable
  only through the registered GO branch. There is no other path to a step-400
  run under this registration.

## 1. Purpose

F6 Tier-3 upgrade condition, quoted from `docs/PAPER1_RESEARCH_DOC.md`:

> **Tier 3 — Upgrade condition.** If a second long-horizon seed reproduces the
> direction, prolonged proxy optimization is presented as a systematic source
> of visual grounding corrosion. Until then, Tier 2 stands as observed rather
> than systematic.

LH2 is that second long-horizon seed. Its only job is to test whether the
seed-1 grounding decline (`reports/m5b_trajectory_v1.md`: R19 geometry
pair accuracy 0.4800 / 0.4733 / 0.4633 / 0.4467 / 0.4133 at steps
100/150/200/300/400, monotone non-increasing, terminal delta vs step 100
-0.0667 [-0.0933, -0.0400], p = 2.40e-06) reproduces directionally in an
independent draw of the same recipe. It follows the staged LH2 row of
`docs/EXPERIMENT_TODO.md` (each stage a separate go/no-go; no full 400-step
commitment up front).

## 2. Design — what "second seed" means here

**LH2 stage 1 is a fresh 0 -> 200 training run of the anchor recipe from the
frozen base model with `data.seed: 2`. It does not warm-start from any
existing checkpoint (`trainer.load_checkpoint_path: null`).**

Why a fresh run is required and a warm start is disqualified:

- The archived step-100 anchor checkpoint
  (`checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_100`)
  **is the seed-1 trajectory**: its 0 -> 100 optimization was performed under
  `data.seed: 1`, and the M5 100 -> 400 extension that produced the Tier-2
  observation is the continuation of exactly that state.
- Warm-starting LH2 from it under any seed value would share seed 1's entire
  0 -> 100 optimization history and could vary only the 100 -> 200
  continuation. That is a second *continuation* of the same seed, not a second
  seed, and could not support the Tier-3 word "systematic". A genuine second
  seed must therefore pay the 0 -> 100 cost again.

What the seed controls (verified in the training code, not assumed):

- The anchor recipe exposes one experiment-level stochasticity control in its
  config, `data.seed`. EasyR1 consumes it in `verl/trainer/data_loader.py` as
  `torch.Generator().manual_seed(config.seed)` for the train-dataloader
  shuffle: the seed determines batch composition and order from step 0, and
  divergence propagates through rollouts, rewards, and updates.
- `worker.rollout.seed` (vLLM sampling seed) is not set in either the seed-1
  anchor config or the LH2 config; it stays at the package default (1) in
  both. This matches the project's established second-seed convention: every
  existing seed-2 config (`mech_*_seed2_*`, `m7_virl_*_seed2`) differs from
  its seed-1 counterpart in exactly `data.seed` plus experiment name and
  checkpoint path.
- There is no model-initialization randomness to reseed: both seeds start from
  the same frozen pretrained checkout
  (`artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct`, identical `model_path` in
  both configs).

Recipe identity: everything else mirrors the anchor / M5 configuration —
Qwen2.5-VL-3B, unfrozen vision tower, native r1v reward, unfiltered geo3k
train split (`hiyouga/geometry3k@train`), GRPO n=5, lr 1.0e-06, KL 0.01,
rollout_batch_size 512, global_batch_size 128, TP2 rollout, 4 GPUs, single
node. The machine-checked config diff in section 7 is the complete list of
differing leaves.

Cost (measured, not estimated from scratch):

- Basis: the two clean, uncontended 50-step M5 segments on 4 A800s —
  `m5_anchor_longhorizon_segment250_300_an12_20260725T100517Z` (22.34 h) and
  `m5_anchor_longhorizon_segment350_400_an12_20260727T073429Z` (21.73 h),
  start/end times from their run manifests. Mean 22.03 h per 50 steps =
  **44.1 h per 100 steps at 4 GPUs**.
- Stage 1 (0 -> 200): about **88 h of training wall-clock, roughly 3.7 days**
  on one 4-GPU half-node, plus boundary audits/relaunches and the three
  evaluation points.
- If the GO branch fires, stage 2 (200 -> 400) adds another ~88 h; a completed
  LH2 is ~176 h (~7.3 days) of 4-GPU training end to end.

## 3. Mandatory process segmentation (host-memory mandate)

`reports/m5_host_memory_incident_v1.md`: the unsegmented M5 long-horizon
process died at `2026-07-18T00:41:18Z` when node host memory reached
`957.22 / 1007.52 GB` (0.950071, above Ray's 0.95 kill threshold), with the
four trainer workers at ~146 GB host RSS each; the seed-1 anchor 0 -> 100 run
itself also needed an unplanned mid-run resume at step 80. Every completed
long-horizon segment in this family since has run as a bounded 50-step
process. Segmentation is therefore **mandatory, not optional** for LH2:

- Four segments in stage 1: 0 -> 50, 50 -> 100, 100 -> 150, 150 -> 200. Each
  segment is a separate OS process launched fresh; no process performs more
  than 50 optimizer steps.
- All segments share one immutable checkpoint root
  `checkpoints/lh2_anchor_seed2_3b_geo3k/<STAGE_RUN_ID>/`; segment k resumes
  via `trainer.load_checkpoint_path=<root>/global_step_<50(k-1)>` and clamps
  `trainer.max_steps=<50k>` (`save_freq: 50` aligns saves to boundaries).
- **Hash-verified checkpoint boundaries**: before segment k+1 launches, the
  segment-k boundary checkpoint must pass a raw-state audit recorded as a JSON
  artifact in the segment run directory, with at minimum: expected step;
  `world_size == 4`; model, optimizer, and extra-state shard counts == 4 each;
  a per-file sha256 checksum manifest; and a stable-during-hash check (two
  hash passes agree) — the same evidence contract the M5 recovery launcher
  enforces fail-closed (`scripts/launch_m5_anchor_segment.sh`,
  `restored_checkpoint_audit.json` fields). A failed or absent audit blocks
  the next segment and is a deviations-log line.
- Duplicated wall-clock from any mid-segment failure is operational overhead;
  it never adds optimizer budget. A crashed segment resumes from the last
  hash-verified boundary in a new immutable run directory, and the crash is a
  deviations-log line, never a stopping decision.

## 4. Evaluation schedule — steps 100, 150, 200

Mirrors the M5 registered checkpoint schedule and instruments
(`docs/registered_extensions_v1.md` Extension 1; `reports/m5b_trajectory_v1.md`
sections 6-7), applied at stage-1's steps:

| step | benchmark axis | grounding axis |
| ---: | :--- | :--- |
| 100 | geo3k test, full split (n=601), greedy | R19 geometry, real images (600 pairs) |
| 150 | same | same |
| 200 | same | same |

Locked contracts, identical to the seed-1 readouts:

- Prompt contract `answer-tags-v1`, sha256
  `7ac39f53a2a824490fc5ee22671a888d2d79d55e1d8351919006d7d71c7a8f3f`.
- Benchmark axis: `src.eval.blind_solvability.score_greedy_item_pilot`
  (`pilot-reward-v1 + canonical-v2`, `posix-itimer-v1` guard, 5.0 s), greedy
  sub-contract `n=1, temperature=0.0, top_p=1.0, max_tokens=2048,
  seed=20260710`.
- Grounding axis: `src.eval.fliptrack_metrics.pair_score` on the packaged R19
  set with `data_manifest_hash`
  `e1dde98451e1c7473906637c029713ab4f95ab4f7c915bd035f697953bf2ffb2`,
  `max_new_tokens=32`, greedy; primary slice
  `category == geometry_coordinate_indexing` (600 pairs).
- Intervals: 2,000-draw paired item bootstrap, 95%, seed `20260728`, via
  `src.eval.fliptrack_metrics.bootstrap_ci`; McNemar exact p on the same
  paired indicators.
- **Lenient and strict are both computed and both reported at every step**
  (I7). The gate in section 5 reads the lenient value; a lenient/strict sign
  disagreement at the gate does not move the gate but is a mandatory
  deviations-log line and is reported prominently.
- No cross-seed pooling (I13): every paired analysis stays within seed 2;
  seed-1 numbers appear only as the fixed reference series; cross-seed
  statements are directional/descriptive only. Gray/noise blind-floor
  conditions are registered at the stage-2 terminal (step 400) only,
  mirroring M5.
- In-run `val_freq: 10` validation is operational monitoring only; it is not a
  registered readout and cannot gate anything.

## 5. Registered go/no-go at step 200

Let `g(s)` = R19 `geometry_coordinate_indexing` lenient pair accuracy
(`pair_correct`) of the LH2 seed-2 checkpoint at optimizer step `s`, real
images, the 600-pair packaged set above. Both `g(100)` and `g(200)` come from
this registration's own evaluations of this run's checkpoints — the
comparison is within seed 2, never against seed-1 values.

- **GO** iff `g(200) - g(100) < 0` (strictly negative point estimate).
- **NO-GO** iff `g(200) - g(100) >= 0`.

The comparison is **directional only. There is no magnitude threshold and no
confidence-interval requirement**: the seed-1 direction to be reproduced is
"declining from its own step-100 value" (seed 1: 0.4633 - 0.4800 = -0.0167 at
the same 200-vs-100 contrast). The bootstrap CI and McNemar p are reported but
do not gate. Step 150 is descriptive and cannot gate. The benchmark axis is
descriptive and cannot gate. **The decision fires on the stated rule, not
discretion** — no analyst, orchestrator, or PI judgment enters the branch.

On GO:
- Continue 200 -> 400 under the identical segmentation contract (segments
  200 -> 250, 250 -> 300, 300 -> 350, 350 -> 400, mirroring the M5 segment
  grid), resuming from the hash-verified step-200 boundary. The stage-2
  continuation config is built from the stage-1 config with exactly
  `trainer.max_steps: 400` and the load path changed, machine-checked by the
  same diff discipline before launch.
- Evaluations at steps 300 and 400 under section-4 contracts, plus the
  step-400 gray/noise blind-floor cells, mirroring M5.
- Step 400 is terminal. No extension or rerun under any outcome.
- The Tier-3 upgrade claim itself is then made iff the seed-2 terminal
  contrast `g(400) - g(100) < 0` (direction reproduced at the terminal
  endpoint, same directional standard). If GO fired at 200 but the terminal
  contrast is non-negative, there is no upgrade; the result is reported as-is.

On NO-GO:
- Stop at step 200. Report the full stage-1 trajectory as-is (all steps, both
  axes, both strictness levels). **F6 Tier 2 stands as observed rather than
  systematic.** No rerun, no extension, and no third seed under this
  registration; any further long-horizon proposal is a new registration.

## 6. Launch specification (for the orchestrator)

Preconditions, all fail-closed, checked at every segment launch:

- This registration and all immutable inputs merged at HEAD; working tree
  clean for every registered file (I9).
- `python scripts/check_lh2_config_diff.py` exits 0 at the current HEAD.
- Single node, four genuinely free GPUs claimed under the project's guard
  discipline; never split across nodes; never colocated with a 7B offload
  trainer or a 72B captioner/server; no other project RL trainer on the node
  (`reports/m5_host_memory_incident_v1.md` decision list); node host memory
  headroom sufficient for four ~146 GB workers (M5 recovery precedent:
  >= 650 GiB free host memory at launch).
- Detached execution on the compute node (`setsid` + `nohup`), logs and
  `run_manifest.json` (node, command, git hash, config hash, seed, artifact
  paths) in an immutable `experiments/runs/<RUN_ID>/` directory, following
  `scripts/launch_anchor_a0_recipe_3b_geo3k.sh` /
  `scripts/launch_m5_anchor_segment.sh`.

Canonical per-segment command (segment 1 shown; `ROOT` is the repo root):

```
env PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1 HYDRA_FULL_ERROR=1 \
    RAY_TMPDIR=<short-ray-tmp> RAY_DEDUP_LOGS=0 \
    CUDA_VISIBLE_DEVICES=<g0,g1,g2,g3> EASYR1_ATTN_IMPLEMENTATION=sdpa \
    HF_HOME=${ROOT}/artifacts/hf_home \
    HF_DATASETS_CACHE=${ROOT}/artifacts/hf_home/datasets \
    TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 \
    PYTHONPATH=${ROOT}/artifacts/repos/EasyR1 \
  python -u -m verl.trainer.main \
    config=${ROOT}/configs/train/lh2_anchor_seed2_3b_geo3k.yaml \
    trainer.max_steps=50 \
    trainer.experiment_name=<RUN_ID> \
    trainer.save_checkpoint_path=${ROOT}/checkpoints/lh2_anchor_seed2_3b_geo3k/<STAGE_RUN_ID>
```

Registered allowed command-line overrides — exactly these four keys and
nothing else; every other value must come byte-identically from the config
file:

| key | allowed values |
| :--- | :--- |
| `trainer.max_steps` | segment end: 50, 100, 150, 200 (stage 2: 250, 300, 350, 400) |
| `trainer.load_checkpoint_path` | absent (segment 1) or `<checkpoint root>/global_step_<segment start>`, hash-verified per section 3 |
| `trainer.experiment_name` | the immutable `<RUN_ID>` of the segment |
| `trainer.save_checkpoint_path` | `${ROOT}/checkpoints/lh2_anchor_seed2_3b_geo3k/<STAGE_RUN_ID>` (constant across all segments of a stage) |

## 7. Immutable inputs and machine-checked config diff

Config diff, machine-checked by `scripts/check_lh2_config_diff.py`
(flattened-leaf comparison, fail-closed on any unregistered differing leaf or
value; artifact `reports/lh2_config_diff_check_v1.json`, status **pass**):

- LH2 vs the seed-1 anchor recipe template
  (`configs/train/anchor_a0_recipe_3b_geo3k.yaml`) — exactly 5 leaves:
  `data.seed` 1 -> 2; `trainer.max_steps` 100 -> 200; `trainer.save_freq`
  20 -> 50 (boundary-aligned saves, matching M5; plumbing, not scientific);
  `trainer.experiment_name` and `trainer.save_checkpoint_path` renames.
- LH2 vs the M5 long-horizon config
  (`configs/train/m5_anchor_longhorizon_400.yaml`) — exactly 5 leaves:
  `data.seed` 1 -> 2; `trainer.max_steps` 400 -> 200;
  `trainer.load_checkpoint_path` anchor-step-100 -> null (fresh start — the
  second-seed decision of section 2); `trainer.experiment_name` and
  `trainer.save_checkpoint_path` renames.
- All other leaves are byte-equal across all three configs.

Adversarial fixture (I10 discipline for the new checker,
`scripts/lh2_adversarial_fixture.py`, artifact
`reports/lh2_adversarial_fixture_v1.json`, status **pass**): the clean config
exits 0; an unregistered-leaf tamper (`worker.actor.optim.lr` 1.0e-06 ->
2.0e-06) exits 1; a registered-leaf wrong-value tamper (`data.seed` 2 -> 3)
exits 1.

| artifact | path | sha256 |
| :--- | :--- | :--- |
| LH2 stage-1 config | `configs/train/lh2_anchor_seed2_3b_geo3k.yaml` | `fdb59c57219514c3c4054f53e2064751ba23581119cf488db2dad2abff80c3bc` |
| Seed-1 anchor recipe template | `configs/train/anchor_a0_recipe_3b_geo3k.yaml` | `fdd39cead00fa6932d03c3040d90e76b71599983623b7478d67a309ce4dc3862` |
| M5 long-horizon reference config | `configs/train/m5_anchor_longhorizon_400.yaml` | `73ff58bd3b6a5a9a190f6f379a927bc6405c88001bd524f61846ffb22996f48c` |
| Config diff checker | `scripts/check_lh2_config_diff.py` | `c4ece6d83f7643915951fe75a16745c04c776491ebdda0312982d064fb927185` |
| Diff-check artifact (pass) | `reports/lh2_config_diff_check_v1.json` | `e7edd641cae77ef947fd99d6d8e1fc14dcf4f9970062653949089927eb88d6fa` |
| Adversarial fixture script | `scripts/lh2_adversarial_fixture.py` | `eabff67cf3c5c66b7d430fe1fb39af865bc79f2f8d3de01c56ac2dc4a40af896` |
| Adversarial fixture result (pass) | `reports/lh2_adversarial_fixture_v1.json` | `d6b07f5fb7419f09ac54b5979d58a8de3bbaa108c6d0115933365d60798ed83c` |
| Format prompt (native r1v) | `artifacts/repos/EasyR1/examples/format_prompt/r1v.jinja` | `f1b62cb8332bdbec38efc8689aff6e9ce65174c0db8967937307880f95f58fca` |
| Reward function (native r1v) | `artifacts/repos/EasyR1/examples/reward_function/r1v.py` | `694c4197e8dd5088732b702dc4796f80a10319a9abfc125d2bc3c024aa097c5b` |
| Base model identity anchor | `artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct/model.safetensors.index.json` | `c7dd78a4c6bea60b51332f1baf37b8f8124ecab2c35395a29a29825bf2619768` |
| Seed-1 trajectory readout (reference series) | `reports/m5b_trajectory_v1.json` | `ec42a7ff613c19bfbe140729480fc539ef7851686b01c2287c37da53160cf36a` |
| Host-memory incident (segmentation mandate) | `reports/m5_host_memory_incident_v1.md` | `62f6c5e9219e8aee961e13509793233666a2dbfe9284af7eb99961ec70dc7f6f` |
| Prompt contract `answer-tags-v1` | (contract hash) | `7ac39f53a2a824490fc5ee22671a888d2d79d55e1d8351919006d7d71c7a8f3f` |
| R19 packaged pair set | (`data_manifest_hash`) | `e1dde98451e1c7473906637c029713ab4f95ab4f7c915bd035f697953bf2ffb2` |
| Training data identity | `hiyouga/geometry3k@train` / `@test` (unfiltered) | — |

## 8. Attribution and scope

Attribution clause (I19), verbatim from `docs/PAPER1_RESEARCH_DOC.md` F6
Tier 2, required in every mention of LH2 results:

> *Attribution, required in every mention:* this extends the **anchor**
> configuration — unfrozen vision tower, native r1v reward, unfiltered corpus
> — never pilot A1. The unfrozen tower is what makes it consequential:
> corrosion occurs with gradients reaching the visual encoder. The unfiltered
> corpus is named as part of the configuration because abundant cheap reward
> is mechanistically relevant, not incidental. *Scope:* one trajectory;
> intervals quantify evaluation uncertainty, not run-to-run RL variance.

One-trajectory-per-seed scope: **LH2 contributes exactly one trajectory per
seed.** Every interval reported under this registration is a paired item
bootstrap and quantifies evaluation-item uncertainty only, never run-to-run RL
variance. Two seeds sharing a direction support exactly the registered Tier-3
sentence — prolonged proxy optimization presented as a *systematic* source of
visual grounding corrosion — and license no magnitude claim, no rate claim,
and no claim about the distribution over seeds. Seed dispersion is
descriptive. No cross-seed pooled statistic is computed (I13).

## 9. Deviations log

| Time UTC | Training unit | Deviation | Reason | Effect on estimands | PI disposition |
| --- | --- | --- | --- | --- | --- |
| 2026-08-08T17:36Z (logged 08-09) | seg1 attempt 1 (`lh2_seed2_seg1_an12_20260808T173144Z`) | Trainer died ~5 min in: `OSError: AF_UNIX path length cannot exceed 107 bytes` — the run-id-derived `RAY_TMPDIR` made Ray's plasma-store socket path exceed the kernel limit. | Chain-script defect (tmpdir naming), not a recipe defect; zero optimizer steps taken. | **None** — no steps, no values. Fixed in `scripts/lh2_segment_chain.sh` (`/dev/shm/bgray/<timestamp>`, ≤31 chars), committed. | Logged. |
| 2026-08-10T14:40Z (logged) | seg1 attempt 2 (`lh2_seed2_seg1_an12_20260809T143807Z`) | Killed at ~17.3 h (tracker=0, before the step-50 boundary) by Ray's host-memory monitor (07:57:37Z), same node-level RAM exhaustion that killed the colocated M7 a2_gray seed-2 trainer (both logs end the same second). | Orchestrator placement error: two ramping Ray trainers on one node (see the M7 amendment's generalized rule of this date). | **None on any estimand** — no boundary banked, nothing read; chain stopped itself without auto-retry as designed. Seg1 restarts from step 0, **solo on an12 0-3**, auto-relaunched by `scripts/seed2_an12_chain.sh` after the a2_gray arm completes (~08-12); stage-1 go/no-go date shifts ~2 days, criteria unchanged. | Logged. |
