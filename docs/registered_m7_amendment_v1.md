# Registered M7 Mechanism Amendment V1

Status:
- Registration state: merged-at-HEAD; merge is sign-off.
- This amendment governs M7 together with Extension 3 of
  `docs/registered_extensions_v1.md`.
- No M7 optimizer step has run.
- The future M7 launcher must require this exact tracked document at `HEAD`
  before any arm takes its first optimizer step.

## Informed-Prediction Disclosure

This prediction was written after the completed Geometry3K seed-1 readout.
The observed Geometry3K recovery anchors are `0.0789` for A2 gray and `0.1184`
for A2b no-image. The direction registered below is therefore informed rather
than a fully prospective cross-corpus hypothesis. No ViRL39K training outcome
has been observed.

The 3B ViRL39K blind-solvability audit is the primary basis for the M7
prediction. Its source/category heterogeneity and arm-specific base
reward-opportunity estimates are frozen in
`reports/blind_solvability_virl39k_sample_v1.json`. The audited 7B ViRL39K
result is corroborating evidence only and does not replace the 3B basis.

## Primary Within-Corpus Mechanism Prediction

Within ViRL39K, strata with higher baseline blind reward-opportunity `q_bar`
are expected to show larger blind-arm gains and recovery fractions.

Arms and conditions:
- A2 uses its own gray-condition base `q_i` values.
- A2b uses its own no-image-condition base `q_i` values.
- A3 uses its own fixed-caption-condition base `q_i` values.
- A1 is the real-image reference and is not called a blind arm.

Frozen stratification:
- The primary strata are the joint `(source, category)` labels already present
  in the frozen ViRL39K metadata.
- A stratum enters a rank statistic only when the frozen held-out evaluation
  set contains at least 30 items in that stratum. The threshold depends only on
  sample count, never on a model outcome.
- Every smaller mechanically valid stratum remains in the published per-stratum
  table and is labeled `descriptive-small-n`; it is not merged, discarded, or
  used in the rank statistic.
- Source-only and category-only tables are descriptive robustness views. They
  do not replace the registered joint-stratum analysis.

Quantities, separately for each blind arm `b` and eligible stratum `s`:
- `q_bar[b,s]` is the item mean of the frozen Jeffreys-smoothed base `q_i`
  estimates under arm `b`'s own information condition. It is an estimate of
  reward opportunity, not a directly observed latent.
- `gain[b,s]` is the mean across the two fixed M7 seeds of
  `Acc_final(step_final) - Acc_final(step_0)` on paired held-out items.
- `gain[A1,s]` is computed identically for the real-image reference.
- `recovery[b,s] = gain[b,s] / gain[A1,s]` only when `gain[A1,s] > 0` and is
  at least two paired standard errors above zero. Otherwise recovery is
  reported `undefined-unstable-denominator`; the stratum stays in the gain
  analysis but is omitted from the recovery rank statistic.

Registered association statistics:
- `rho_gain[b]`: tie-corrected Spearman association across eligible strata
  between `q_bar[b,s]` and `gain[b,s]`.
- `rho_recovery[b]`: tie-corrected Spearman association across strata with a
  stable A1 denominator between `q_bar[b,s]` and `recovery[b,s]`.
- The directional prediction is `rho_gain[b] > 0` and
  `rho_recovery[b] > 0`; a nonpositive estimate is reported as a failed
  direction. No minimum effect magnitude is implied.

Uncertainty:
- Use 5,000 item-bootstrap draws.
- In each draw, resample held-out items with replacement within every frozen
  joint stratum, preserving item identity across step 0, all arms, and both
  seeds.
- Recompute stratum `q_bar`, seed-averaged gains, A1 denominator stability,
  recoveries, and both tie-corrected Spearman statistics in every draw.
- Report percentile 95% intervals, the number of eligible strata, the number
  of recovery strata, and the count of draws where a rank statistic is
  undefined. Undefined draws are not replaced with zero; if more than 5% are
  undefined, the corresponding interval is labeled unstable.
- Bootstrap RNG seed is `20260716`, with deterministic statistic/arm labels
  hashed into independent streams. Seed-to-seed dispersion is also reported
  descriptively and is not replaced by item-bootstrap uncertainty.

## Secondary Cross-Corpus Directional Prediction

Aggregate blind-arm recovery on ViRL39K is expected to be greater than the
completed Geometry3K seed-1 anchors:

| Arm | Geometry3K seed-1 recovery anchor |
| --- | ---: |
| A2 gray | 0.0789 |
| A2b no-image | 0.1184 |

For each arm, compute the ViRL39K aggregate recovery from the two-seed mean
blind gain divided by the two-seed mean A1 gain, conditional on the same stable
A1-denominator rule. Use 5,000 item-paired bootstrap draws across the frozen
held-out corpus, preserving item identity across arms and seeds. Report the
ViRL recovery, its 95% interval, and the difference from the fixed Geometry3K
anchor. The registered direction is simply greater than the anchor; no
numeric minimum difference and no use of `substantially` are authorized. A
failed direction is reported as such.

## Readout Discipline

- Corpus aggregate, every joint stratum, and source-only/category-only
  descriptive tables are all published; a pooled-only readout is prohibited.
- A2/A2b/A3 results are never pooled into one generic blind arm.
- The informed Geometry3K comparison is labeled as such in every report and
  paper table.
- M10 support-sharpening language remains non-causal.
- Any irregularity is appended to the M7 deviations log before values are
  interpreted.

## Deviations Log

Time UTC is the time of the event where the event has one, otherwise the time
the entry was logged, marked `logged`. Every row was verified against the
artifacts named in it, not against a report.

| Time UTC | Deviation | Reason | Effect on estimands | PI disposition |
| --- | --- | --- | --- | --- |
| 2026-07-30T15:52Z (logged) | Frozen per-item base `q_i` covers only 448 of the 4,239 registered held-out items (10.57%). | `q_i` was measured on the separate 4,096-item frozen ViRL39K stratified sample (`reports/blind_solvability_virl39k_sample_v1.json`, `n_items` 4096). The intersection of that sample's `qid` set with `data/virl39k_m7_heldout_v3.jsonl` is exactly 448 under every condition (`real`, `gray`, `none`, `noise`, `caption`), from the five `per_item.jsonl` files under `experiments/runs/blind_solvability_virl39k_v1_pilot_contract_guarded_*_an12_20260712T05*`. | `q_bar[b,s]` cannot be formed for the registered joint `(source, category)` strata from the frozen sample alone: on 448 items almost no stratum reaches the registered `n >= 30` eligibility threshold, so neither `rho_gain[b]` nor `rho_recovery[b]` is computable. | Held. The step-0 held-out runs `experiments/runs/m7_step0_heldout_base_{real,gray,none,caption}_an29_20260730T1544*Z` re-measure `q_i` (sample-count 16) over all 4,239 held-out rows and supply the remaining 3,791. No `q_bar`-dependent value is interpreted until they land and are audited. |
| 2026-07-30T15:52Z (logged) | The registered held-out set is 4,239 rows, but in-training validation scored 4,095. | `data.filter_overlong_prompts: true` with `data.max_prompt_length: 2048` in `configs/train/m7_virl_a1_real_seed1_3b.yaml` drops 144 rows before validation (4,239 − 4,095 = 144). The 4,095 denominator is recovered exactly by rational reconstruction of the `val` block of `checkpoints/m7/m7_virl_a1_real_seed1/experiment_log.jsonl`: the LCM of the exact fractions is 4,095 at both step 0 and step 100 (`format_reward` = 1208/4095 at step 0 and 802/819 at step 100; `accuracy_reward` = 2092/4095 at step 100). | Two denominators are in play and are not interchangeable. In-training `val` curves are means over 4,095 filtered rows; every registered estimand (`q_bar`, `gain`, `recovery`, both tie-corrected Spearman statistics) is defined over the frozen 4,239-row held-out set. The `n >= 30` stratum eligibility rule is also denominator-sensitive. | Reconciliation is mandatory before interpretation: every reported quantity states its denominator, the registered estimands are computed on the 4,239-row set from the step-0/step-final held-out evaluations, and no in-training `val` number is compared with a 4,239-row number until the 144 dropped rows are enumerated and their stratum membership published. |
| 2026-07-30T12:39:29Z | Arm 4 seed 1 run `m7_virl_a3_caption_seed1_an29_20260730T121906Z` failed with CUDA OOM; manifest `status: fail`. | `torch.OutOfMemoryError` during vLLM KV-cache allocation, recorded verbatim in that run's `run_manifest.json` `failure_reason`. The arm claimed an29 GPUs 4-7 at 12:19:06Z and was still in vLLM startup when two `m5c_sampled` endpoint evals (pids 1475268, 1476867) were started onto physical GPUs 4 and 5 at 12:26:20Z/12:27:01Z by a separate session. `scripts/launch_m5c_sampled_endpoint_eval.sh` carries no GPU-occupancy guard, so nothing refused the overlap; the M7 guard protects an M7 launch from existing occupants but cannot protect a running M7 arm from a later non-M7 job. | None directly: the run took no optimizer step and wrote no checkpoint, so it contributes no value to any estimand. It must not be counted as an arm-4 attempt in any seed or run tally. | Relaunched as `m7_virl_a3_caption_seed1_an12_20260730T131311Z` on an12 GPUs 0-3 at 13:13:11Z with an identical config hash (`7c9f32bd5159…`); git HEAD differs between the two launches (`ed4aa96` → `8aeb720`). The failed run is excluded from all analysis. The unguarded-neighbour hole in the non-M7 eval launcher is tracked as open work. |
| 2026-07-30T15:45:49Z | Arm 1 run `m7_virl_a1_real_seed1_an12_20260728T102036Z` completed at 2026-07-30T12:57:54Z but its manifest read `"status": "running"`, `"end_time_utc": null` until it was closed post-hoc 2 h 47 min 55 s later. | The pre-fix `scripts/launch_m7_virl_arm.sh` exec'd `verl.trainer.main` directly instead of routing through `scripts/run_manifest_job.py`, so no process outlived the trainer to call `finalize_manifest`. | Estimand values are unaffected. Timing metadata is: `end_time_utc` = 2026-07-30T15:45:49Z is the close-time stamp, not the completion time, so any duration or throughput derived from it overstates the run by 2 h 47 min 55 s. `exit_code: 0` is inferred from artifacts (`last_global_step` 100, all five checkpoints, 101 log lines, no traceback in the final 40 MB of `logs/an12.log`, pid 687841 gone from an12), never observed. | Closed with `scripts/close_orphaned_run_manifest.py`, which stamps `end_time_utc_source`, `observed_completion_utc` (2026-07-30T12:57:54Z), `observed_completion_evidence` and `exit_code_provenance` into the manifest. The launcher now routes through `run_manifest_job.py` for future launches. Arms 2-4 were launched on the old path and hold their own pids, so they must be closed by the same post-hoc tool before the R3 readout; nothing was applied to them in flight. |
| 2026-07-28T09:43:10Z | `experiments/runs/m7_virl_a1_real_seed1_an12_20260728T094310Z` holds an `effective_config.yaml` but no `run_manifest.json`, and empty `logs/` and `pids/`. | The launch aborted after the effective config was installed and before the manifest was written; no trainer started and no checkpoint exists. | None: the directory carries no values. Its risk is misreading it as a second arm-1 seed-1 run. | Recorded as a false start. Arm 1 seed 1 is `m7_virl_a1_real_seed1_an12_20260728T102036Z` and no other run. |
| 2026-07-30T15:17:24Z | The four step-0 held-out evaluation runs write no `run_manifest.json`, and their launcher `scripts/run_m7_step0_heldout_evals.sh` is untracked at HEAD. | Verified: `experiments/runs/m7_step0_heldout_base_{real,gray,none,caption}_an29_20260730T1544*Z` each contain only a `logs/` directory, and `git ls-files --error-unmatch scripts/run_m7_step0_heldout_evals.sh` fails. | These runs are the sole source of `q_i` at full held-out coverage and of `Acc_final(step_0)` for every arm, so on current provenance the primary stratified analysis would rest on unregistered, unmanifested runs. | The launcher must be committed and each run given a manifest recording node, GPU, git hash, config/contract hashes and input hashes — post-hoc if necessary — before any step-0 value enters an estimand. |
| 2026-07-28T10:20:36Z | The Status block above still asserts "No M7 optimizer step has run", which became false when arm 1 launched and is now false by 100 optimizer steps. | The Status block was written before any M7 launch and no mechanism updates it. The registration text is left byte-identical on purpose: this log is the sanctioned place to record the discrepancy, and amending a merged registration is a PI decision, not a bookkeeping one. | None on values; a reader of the registration alone would misjudge how much of M7 has already run. | Flagged for PI. Until the Status block is amended by sign-off, treat this row as the authoritative statement of M7 execution state. |
| 2026-07-30T15:52Z | The arm-1 closure, the launcher routing fix and the first eight rows of this log were committed inside `2d12d4f`, whose message ("G0.2 addendum: record prose-target drift in the wording proposal") describes unrelated work. | Several sessions share one git index on the shared filesystem. A concurrent session ran `git commit` between this session's `git add` and `git commit`, sweeping the staged files into its own commit; `2d12d4f` carries six M7 bookkeeping files and three G0.2 files. | None on values. Provenance only: `git log` for `scripts/launch_m7_virl_arm.sh`, `scripts/close_orphaned_run_manifest.py` and this file points at a commit message that does not describe the change. | Recorded here rather than rewriting history that other sessions have already built on. This row plus the commit that carries it is the accurate description. Multi-session commits should use `git commit --only <paths>` so the shared index cannot be captured. |
| 2026-07-30T12:18Z / 12:18Z / 13:13Z | Arms 2, 3 and 4 (`a2_gray`, `a2b_noimage`, `a3_caption`) checkpoint with `trainer.save_model_only: true`; arm 1 ran `false`. Cross-reference row, not a new irregularity. | Sanctioned by `docs/registered_m7_seed_scope_v1.md` 1(b) and already recorded in `scripts/build_m7_configs.py:SANCTIONED_DEVIATIONS` and in each arm's own run manifest. Verified in `configs/train/m7_virl_{a1_real,a2_gray,a2b_noimage,a3_caption}_seed1_3b.yaml`. | None on the registered estimands: `save_freq` is unchanged at 20, so the matched checkpoint cadence holds and only the on-disk format differs. The cost is that arms 2-4 cannot be resumed mid-run. | No action; logged here so the deviations log is a complete index of the arm-to-arm asymmetries. |
| 2026-07-30T17:20Z (logged) | Two rows above originally cited step-0 run ids `m7_step0_heldout_*_20260730T151724Z`. That was a first launch attempt that failed before any decoding — the harness requires a pre-existing run manifest carrying the prompt contract — and its four dirs were removed after producing 0 rows. | The live runs were relaunched through the extended `launch_virl39k_blind_v1_condition.sh` (commit `ca00b91`), which writes the manifest correctly; the citations above now name the live `m7_step0_heldout_base_*` runs. | None — no value was read from either attempt; the failed attempt decoded nothing. | Logged. |
| 2026-07-31T00:30Z (logged) | Measured `save_model_only: true` checkpoint size is ~16 GB per save (4 fp32 FSDP model shards of 3.8 GiB; verified identical across all three arms at step 20), not the "~7.6 GB of HF weights" stated in `registered_m7_seed_scope_v1.md` 1(b) and echoed in each run manifest's deviation record. The mechanism differs too: the flag skips optimizer shards (absent, as intended) but still writes fp32 model shards, and `actor/huggingface/` remains a config+tokenizer stub. | The 7.6 GB figure was the bf16 HF-export size, taken from the merged Mini-A5 checkpoints; no model-only M7 checkpoint existed to measure at filing. | None on any estimand — cadence (`save_freq: 20`) is unchanged and no registered quantity reads a checkpoint's on-disk format. Operationally: arms 2-4 total ~240 GB not ~114 GB (headroom ample), resume remains impossible as stated, and each arm's step-100 checkpoint requires the standard HF merge before evaluation — the same `launch_easyr1_checkpoint_merge.sh` path arm 1 used (~3 min, verified). | Logged. |
| 2026-08-04T00:45Z (logged) | M7 `a1_real` seed 2 attempt 1 (`m7_virl_a1_real_seed2_an29_20260803T155232Z`) died at ~step 0 (43 min in, before the first optimizer step completed) in the same an29 host-memory cascade that killed C5 arm 1 attempt 1 — see the C5 deviations log. Its manifest self-recorded `fail` (the re-routed launcher's finalization working as designed). | Colocated with a 7B host-offload trainer; placement error. | None — seed 2 is the deferred upgrade path, seed-1 R3 is complete and read; seed 2 will be relaunched on a node with no 7B arm once the C5 pair completes (~2026-08-08). | Logged. |
