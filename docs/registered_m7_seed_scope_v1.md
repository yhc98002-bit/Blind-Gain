# Registered: M7 seed scope and checkpoint-format amendment (v1)

**Filed:** 2026-07-29, **before the first optimizer step of M7 arm 2** (I9).
Amends `docs/registered_extensions_v1.md` Extension 3 and
`docs/registered_m7_amendment_v1.md`. Every other M7 registration document —
`registered_m7_heldout_split_v2.md`, `registered_m7_single_image_v2.md` — is
unchanged and remains in force.

## 1. What changes

### (a) Seed scope: seed 1 only, for all four arms

Extension 3 registers:

> "Four arms: A1 real, A2 gray, A2b no-image, and A3 fixed question-blind captions."
> "Two seeds per arm."

and `registered_m7_amendment_v1.md:52` defines the primary quantity as

> "`gain[b,s]` is the mean across the two fixed M7 seeds of
> `Acc_final(step_final) − Acc_final(step_0)` on paired held-out items."

**This amendment runs seed 1 only for all four arms and reports every estimand
per-seed rather than as the registered two-seed mean.** Seed 2 is **deferred, not
abandoned**: the launcher's `SEED ∈ {1,2}` guard is untouched, and completing seed 2
later requires no further amendment.

**Reason.** Measured, not estimated: arm 1 has run 40 of 100 steps in 29.6 h, i.e.
~44 min/step and ~74 h per arm. Eight arms is ~2–3 weeks of exclusive GPU occupancy.
Disk is the harder bound — at the inherited save policy each arm writes five
checkpoints of 38.5 GB (measured: 77 GB for arm 1's first two), so eight arms need
~1.5 TB against a 1.5 TB total quota.

**What this costs, stated plainly.** The registered estimator averaged two seeds;
per-seed reporting has no seed replication, so between-seed variance on the second
corpus is unmeasured and no claim may be made about it. **The R3 prediction itself
remains testable**: it is a within-run correlation across strata —
`rho_gain[b]` and `rho_recovery[b]`, stratum recovery tracking stratum
blind-opportunity — not a between-seed contrast. Every M7 readout must carry the
scope tag "one seed" wherever a gain, recovery or correlation is reported.

### (b) Checkpoint format for arms 2–4: `save_model_only: true`

Extension 3 registers checkpoint cadence as **unspecified**:

> line 122: "Matched model, prompts, G, optimizer steps, token budget, batch size,
> reward, parser, **checkpoint cadence**, and evaluation protocol."
> line 136: "| **Checkpoint cadence** | `{computed-pending}` |"

The values in force (`save_freq: 20`, `save_model_only: false`, `save_limit: -1`)
were inherited silently from the geo3k pilot template by `scripts/build_m7_configs.py`,
whose matched-recipe assertion covers only the `algorithm` and `worker` blocks — the
`trainer` block holding every save field is deliberately outside it and already varies
by arm.

**Arms 2–4 set `save_model_only: true`. `save_freq: 20` is unchanged, so the
registered "matched checkpoint cadence" requirement is satisfied — cadence is
identical across all four arms; only the on-disk format differs** (7.6 GB of HF
weights per checkpoint instead of 38.5 GB including FSDP optimizer shards).

**Why this is a storage choice and not a scientific one.** Every registered M7
estimand is a two-point contrast, `Acc_final(step_final) − Acc_final(step_0)`.
`step_0` is the shared base model and is never checkpointed
(`registered_pilot_seed23_v1.md:19`). **No registered quantity reads an intermediate
checkpoint**, and Extension 3 contains no intermediate evaluation schedule — in
pointed contrast to Extension 1 (M5), which explicitly registers "Evaluate the
registered benchmark and FlipTrack suites at steps 150, 200, 300, and 400." The
silence is structural, not accidental.

**What it costs.** Model-only checkpoints carry no optimizer state, so arms 2–4
cannot be resumed mid-run; a crash means restarting that arm. Accepted deliberately:
the alternative is 157 GB per arm of resume insurance that the quota cannot fund, and
arm 1 has run 30 h without incident on a launcher hardened after six earlier defects.

Recorded in `SANCTIONED_DEVIATIONS` in `scripts/build_m7_configs.py` and in each run
manifest, so the difference is discoverable from the artifacts alone.

## 2. What does not change

Four arms; the strata; the single-image v3 splits and their sha256s; the held-out
split; `max_steps: 100`; the 4-GPU width; the reward, parser, prompt contract and
evaluation protocol; the `algorithm` and `worker` blocks byte-identical across arms;
the registered prediction that stratum recovery tracks stratum blind-opportunity.

**Arm 1 is not restarted or altered.** It continues at `save_model_only: false` on
an12 GPUs 0–3. Arms 1 and 2–4 therefore differ in checkpoint *format* but not in
cadence, recipe, or any reported quantity.

## 3. Verification before arm 2's first optimizer step

- This document merged at HEAD (the launcher fails closed on merged-at-HEAD, I9).
- Arms 2–4 configs byte-identical to arm 1 in `algorithm` and `worker`.
- Diff against arm 1 confined to `trainer` fields: `experiment_name`,
  `save_checkpoint_path`, `project_name`, `load_checkpoint_path`, `save_model_only`.
- `n_gpus_per_node: 4` and the launcher's GPU-count guard agree.
- Arm 2 placed on an12 GPUs 4–7; M7 arm 1 untouched on 0–3.
