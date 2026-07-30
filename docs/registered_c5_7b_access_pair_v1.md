# Registered C5 7B Access Pair V1 (Ladder Rung R4)

Registration state:
- Merged-at-HEAD; merge is sign-off. No C5 optimizer step has run.
- Authored 2026-07-30. Launch is deferred until M7 frees GPUs (~2026-08-02)
  and MUST go through `scripts/launch_c5_7b_arm.sh`, whose gates are
  fail-closed on this exact tracked document at `HEAD`.
- This document amends Extension 4 of `docs/registered_extensions_v1.md`; the
  amendment scope is stated precisely below so nothing is silently dropped.

## Scope

- C5 implements ladder rung R4: a PURE SCALE manipulation of the headline
  Geometry3K access matrix. The recipe is the registered seed-1 3B geo3k
  pilot recipe; only the model changes to 7B, plus the two mechanics
  deviations declared below. The test side of the access matrix is inference
  on frozen endpoints, so the headline matrix replicates from two training
  runs (`docs/EXPERIMENT_TODO.md` row C5).
- Two arms, one seed: A1 real and A2 gray, both at `data.seed: 1`. A2b and A3
  are NOT run at 7B.
- A2-gray is retained by the FIRED precommitted M8 fork rule, quoted from
  Extension 4:

  > A2 is retained because the precommitted M8 fork rule fired: audited 7B
  > greedy accuracy is 0.2456 for gray and 0.1824 for no-image, with
  > non-overlapping 95% intervals. This is a rule-citation, not a
  > discretionary arm-selection decision.

  The rule's evidence corpus is ViRL39K
  (`reports/blind_solvability_virl39k_7b_sample_v1.md`), while C5 trains on
  geo3k; the rule is cited for which blind arm accompanies A1 at 7B, not as a
  geo3k measurement. The gray arm is also the sharper geo3k contrast: pooled
  crossed TrainShare 0.487 [0.383, 0.588] from zero visual information
  (`reports/d3_trainshare_v1.md`), the "49% crossed recovery" cited in the C5
  row.
- Relation to Extension 4 ("7B Flagship"): Extension 4 registers a four-arm x
  three-seed 7B run on a frozen ViRL39K subset with a 7B own-caption store,
  all `{computed-pending}`. C5 does NOT discharge it. C5 executes the scale
  rung on the Geometry3K pilot recipe; the ViRL39K flagship is DEFERRED with
  every one of its pending fields intact. Running the deferred flagship later
  requires no amendment to this document.
- Discipline: the executing agent may inspect process health, storage,
  checkpoint completeness, and reward-log presence, but must not inspect
  training, validation, or evaluation performance values before both arms
  have completed and the readout queue is bound (same rule as
  `docs/registered_pilot_seed23_v1.md`).

## Locked Design

- Base model: `artifacts/models/Qwen/Qwen2.5-VL-7B-Instruct` (16 GB, five
  safetensors shards, `Qwen2_5_VLForConditionalGeneration`,
  `index_total_size` 16,584,333,312). The directory carries NO upstream
  revision marker, so model identity is pinned by computed on-disk hashes
  (table below, full set in `reports/c5_arm_configs_v1.json`). Equality with
  `Qwen/Qwen2.5-VL-7B-Instruct@cc594898137f460bfe9f0759e9844b3ce807cfb5` (the
  M8 audit revision named in Extension 4) is NOT asserted.

  | File | SHA256 |
  | --- | --- |
  | `model.safetensors.index.json` | `73b333b0b16e5286ddba615d2caebcd495cf7e616f52eb217a81781393d79de9` |
  | `config.json` | `77d9ec7321cc572e3579e2c84799c9cadaded63c49ce93b101733349fc330c43` |
  | `model-00001-of-00005.safetensors` (3,900,233,256 B) | `e97b877e47fde53a6c6e77aafb36e58e91ee9d95c4a3eeac6f1b5c0e6a1c986e` |
  | `model-00002-of-00005.safetensors` (3,864,726,320 B) | `a9a300a43b4724eee2abe7c18ceb26768d0ab011eb0cad19d9bfd2476a24d024` |
  | `model-00003-of-00005.safetensors` (3,864,726,424 B) | `111223d173e00bbee81cba1216fad28668df3476706b7fd26f4d5b50f8b3a507` |
  | `model-00004-of-00005.safetensors` (3,864,733,680 B) | `ef47f634fa57d46ee134edcc09f34085a47da1e16c12a2abe0d67118be6d72ed` |
  | `model-00005-of-00005.safetensors` (1,089,994,880 B) | `0c859795ad3a627a9b95bcb762e059d5b768a4a36fdd4affeff269d93fdecc67` |

- Corpus: `data/geo3k_pilot_filtered.jsonl`, SHA256
  `f3d88dd1e52ccef833f266880e487eef252193f774c1076f7dfbccd180b450e6`, with
  frozen ID list `data/geo3k_pilot_filtered_ids.json`, SHA256
  `8631d015ee8593669b46cc707b9fe1fb3690391520bccf416b64bbb2306ff7d1` — the
  pilot corpus unchanged.
- Reward, prompt contract, parser: identical to the pilot.
  `src/rewards/pilot_reward.py:compute_score` (SHA256
  `706de156da12ecbcfa2d52591b7477baf322fe488b98d3a52fac4ec2d628d97d`), format
  prompt `artifacts/repos/EasyR1/examples/format_prompt/r1v.jinja` (SHA256
  `f1b62cb8332bdbec38efc8689aff6e9ce65174c0db8967937307880f95f58fca`).
- Recipe inheritance: G=5, rollout_batch_size 512, global_batch_size 128,
  lr 1e-6, low_var_kl at 0.01, frozen vision tower, 100-step budget,
  val_freq 10, save_freq 20, `data.image_condition_seed: 20260710`, and every
  other algorithm/worker/data field are inherited byte-identically from the
  seed-1 3B pilot configs. `scripts/build_c5_configs.py` asserts this
  programmatically: algorithm and worker blocks equal to the pilot baseline
  after stripping exactly the sanctioned deviation paths, data blocks equal
  to each arm's own template, and the two C5 arms differing only in
  `data.image_condition` and run identity. The verified byte diff against the
  3B template is exactly: `model_path`, `gpu_memory_utilization`,
  `project_name`, `experiment_name`, `save_model_only`,
  `save_checkpoint_path`.
- Placement: one synchronous EasyR1 trainer on four GPUs of one node
  (`n_gpus_per_node: 4`), TP1 rollout with four independent replicas.
  TP1 is required for models at or below 7B by the PI GPU Placement Addendum
  `pi-2026-07-11` (`docs/PRELAUNCH_BRIEF.md`) and the Global Contract of
  `docs/registered_extensions_v1.md`. The upstream EasyR1 default is TP2, so
  the explicit `tensor_parallel_size: 1` override is retained in both
  configs. The two C5 arms are not colocated on one node (the seed-1 pilot
  failure established inadequate host-memory headroom for two colocated
  trainers; `docs/registered_pilot_seed23_v1.md`); they run sequentially on
  one node or in parallel on separate nodes as GPUs free.
- Mechanics deviations (registered here before any launch; neither touches an
  estimand):
  1. `worker.rollout.gpu_memory_utilization` 0.6 -> 0.45. Measured 3B peak is
     63.58 GB of 79.33 (transient FSDP all-gather alongside the vLLM
     reservation; live arms show ~68 GB). 7B at the inherited 0.6 projects to
     75-78 GB — not safe; 0.45 projects to ~65 GB. Serving memory reservation
     only. Identical in both arms, so the pair stays matched. Registered
     secondary lever if OOM still occurs:
     `micro_batch_size_per_device_for_experience` 2 -> 1, to be applied only
     as a further logged deviation, identically in both arms.
  2. `trainer.save_model_only: true` for BOTH arms. No registered C5 estimand
     reads intermediate optimizer state; `save_freq` stays 20, so the
     registered checkpoint CADENCE is unchanged and only the on-disk format
     differs (~17 GB of HF weights per save, ~85 GB/arm, instead of ~600 GB
     of full FSDP state per arm). Cost: neither arm can be resumed mid-run.
     Symmetric across arms, so no arm-to-arm asymmetry is introduced.
- Cost disclosure: measured 3B M7 rate is 30.31 min/step; 7B on 4 GPUs
  projects to 67-91 min/step, i.e. 4.6-6.3 days per arm for the 100-step
  budget.
- Checkpoints land under `checkpoints/c5/<experiment_name>`; the launcher
  refuses an existing namespace.

## Immutable Configs

Generated and hash-inventoried by `scripts/build_c5_configs.py` into
`reports/c5_arm_configs_v1.json`; the launcher refuses any config whose bytes
do not match the inventory.

| Arm | Seed | Config | SHA256 |
| --- | ---: | --- | --- |
| A1 real | 1 | `configs/train/c5_a1_real_seed1_7b.yaml` | `e600ef59347f3d5cb1748651023456e4817177d3df7e8a180d28f53569327857` |
| A2 gray | 1 | `configs/train/c5_a2_gray_seed1_7b.yaml` | `52e5a1dbe9b0f732b4ab774b07706ad43bccaeddd5825bbe57a3e8dd1bafe971` |

Templates (parity baseline): `configs/train/mech_a1_real_3b_geo3k.yaml`
`abf9e9d9a48e35dd5f29e86a51dd674d1a666a088f9ced9f7acc86338a53560e`,
`configs/train/mech_a2_gray_3b_geo3k.yaml`
`c36f24f6bb4915b84722a262eb656332a6ebda1c0584be5f33f73d597ccaec64`.

## Launch Preconditions (enforced by `scripts/launch_c5_7b_arm.sh`)

- This document, `docs/registered_extensions_v1.md`, both configs, the
  inventory, the builder, the launcher, the occupancy guard,
  `scripts/run_manifest_job.py`, `scripts/finalize_run_manifest.py` and the
  reward file tracked and byte-clean at `HEAD` (I9; merge is sign-off).
- Config SHA256 equal to the inventory entry; `data.image_condition` equal to
  the arm; corpus and frozen-ID hashes equal to the inventory; model path,
  index hash and per-shard byte sizes equal to the registered identity (full
  shard hashes re-verified with `C5_VERIFY_SHARD_HASHES=1`).
- Exported GPU count equal to `trainer.n_gpus_per_node`.
- GPU-scope occupancy guard (`scripts/m7_gpu_occupancy_guard.py`) passes;
  after it passes, per-GPU reservation claim files are written on the node
  BEFORE launch and the guard is re-run excluding only this run's claims.
  Fresh claims (age < 30 min or recorded pid alive) read as occupied to every
  later guard invocation, closing the vLLM-init TOCTOU window that killed M7
  arm 4's first attempt.
- The trainer is routed through `scripts/run_manifest_job.py` so the run
  manifest finalizes itself; deviations in the manifest are DERIVED from the
  effective config against the pilot template, never hardcoded.

## Registered Readout

- Endpoints: the step-100 final weights of each arm, and the 7B BASE model
  (step 0). Step 0 is the shared base model and is never duplicated.
- Evaluation: the locked pilot prompt contract, greedy decoding
  (temperature 0), on the geo3k evaluation split fixed in the configs'
  `val_files` (`hiyouga/geometry3k@test`).
- Cells: {7B base, A1-real, A2-gray} x test condition {real, gray}. Six
  cells; all six are reported.
- Estimands, mirroring the pilot access-matrix readout:
  - Matched gain per arm: `Acc(arm, test = its training condition) −
    Acc(7B base, same test condition)`.
  - Crossed gain for A2-gray: `Acc(A2, test real) − Acc(base, test real)`.
  - Crossed recovery (TrainShare, as in `reports/d3_trainshare_v1.md`):
    `[Acc(A2, test real) − Acc(base, real)] / [Acc(A1, test real) −
    Acc(base, real)]`, defined only when the denominator is positive and at
    least two paired standard errors above zero (the M7 stability rule);
    otherwise reported `undefined-unstable-denominator`.
  - A1 crossed cell (`A1 tested gray`) is reported descriptively.
- Uncertainty: 5,000 item-paired bootstrap draws over the evaluation items,
  preserving item identity across all six cells; percentile 95% intervals;
  bootstrap RNG seed 20260730. Same discipline as the pilot and M7 readouts.
- 7B base requirement: verified 2026-07-30 — NO geo3k evaluation of the 7B
  base exists anywhere in `experiments/runs` (the only run matching 7B+geo3k
  is `geometry3k_qwen25vl7b_captionstore384_20260710T011700Z`, a caption-
  store build, not an accuracy evaluation). The two 7B base cells (test real,
  test gray) MUST be evaluated under the locked contract before any C5
  estimand is interpreted; they are inference-only and may run before the
  training arms or after, but no gain is read without them.
- Registered analyses only. Process-health observations cannot select
  checkpoints, stop runs, alter arm order, or change the terminal step.
  M10 support-sharpening language remains non-causal; scale comparisons
  against the 3B pilot are descriptive and labeled cross-scale.

## Deviations Log

Every irregularity is one immutable line here, appended before values are
interpreted, and bound into the affected run manifest.

| Time UTC | Training unit | Deviation | Reason | Effect on estimands | PI disposition |
| --- | --- | --- | --- | --- | --- |
