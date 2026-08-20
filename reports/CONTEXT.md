# Blind Gains — context brief

*Snapshot **2026-08-20**, replacing the 2026-08-14 brief (which was already
partially superseded by the 08-16 consolidation round). `BlindGain_RESULTS.md`
remains the file of record — its §21 ledger is the reproduction backbone, and
sections N–T carry everything new since 08-16. Nothing in this brief is new
evidence; it is the catch-up layer.*

---

## 1. What this program is

**Blind Gains** asks what RL with verifiable rewards actually improves in a VLM
(Qwen2.5-VL-3B/7B, EasyR1/verl GRPO). **Paper 1** (*Learning Without Looking*)
shows most of the benchmark gain from image-conditioned RLVR is available
without the images — an access-matrix result built as claim ladder R1–R5 with a
mechanism story (readout sharpening, not content acquisition). **Paper 2** builds
the method + benchmark that could force genuine visual acquisition:
counterfactual intervention-group optimization over a hierarchical
Discover→Ground→Read benchmark, gated at every step by acceptance checks (blind
floor, caption stress, artifact attacker, difficulty band).

## 2. Status at a glance

| | |
|---|---|
| Brief current through | 2026-08-20T07:00Z |
| Git | HEAD `e0cab94` on `agent/gate2-recovery`; **7 commits committed but unpushed** — the cluster's mihomo proxy has been down since ~08-19T17:00Z (probe returns 000); a retry loop is armed and will land them |
| Paper-1 evidence | ladder R1–R5 closed; **corroborated on a new instrument** (D1 sweep, §O) |
| Paper-2 method | **ST3 both arms trained** — arm 1 complete, arm 2 complete-but-exit-1 (see §3); arm-1 readouts done, **arm-2 readouts running now** |
| Paper-2 benchmark | coordinate family **frozen** (r2 render); chart family **not accepted** — see §4.1 |
| Cluster | an29: arm-2 readout chain (merges → 6 evals, GPUs 0–5). an12: LH2 seg-4 on 0–3; 4–7 free after R19 finished |
| Storage | 1.66 TB used / 2.75 TB quota, 1.09 TB free. A 2 TB top-up was applied for on 08-19 |
| Decisions waiting on you | 4 live + 3 carry-overs — see §4 |

## 3. What happened since the 08-16 brief

**Four things landed; two blockers were caught before they cost anything; one
cost a run.**

**(a) The E2 lenient-class fork is resolved.** The matcher's tier-1 rule was
substring containment, so gold `1` scored correct against a predicted `-1`.
**721 of 785** lenient tier-1 credits across the hierarchy runs were exactly this
sign collision. Replaced with sign-aware parsed-numeric equality
(`match-tier-v3-sign-aware`). Effect: blind floors roughly **halve** (L3
0.120/0.113/0.137 → 0.067/0.040/0.067) — the benchmark gets *stronger* — and gate
outcomes are unchanged. Paper-1 exposure is bounded and small: FlipTrack member
accuracy moves ≤0.031, arm *differences* less, and M7/R3 is unaffected.

**(b) The hierarchical benchmark was cleaned and the coordinate family frozen.**
The in-image coordinate footer stated the L2 procedure inside L3/probe images —
re-rendered as r2, 0 verifier problems, 1500/1500 rows byte-identical outside
image/provenance fields. Chart-v2 failed its acceptance gates twice, so the
**pre-committed coord-only fallback fired** (Launch amendment 1).

**(c) Two pre-launch blockers caught by measurement, not by luck.**
- The registered ST3 arm-2 reward multiplied **k=4** member accuracies. Measured
  from data already on disk: only **2.41%** of groups could produce a GRPO
  gradient, against **42.2%** for the Mini-A5 k=2 arm the registration itself
  names as the reference implementation — 17× below a design known to train.
  Launching it would have produced "IGPO doesn't work" from a numerically dead
  reward. Regrouped to **k=2** (per-side premise gate) under Launch amendment 2.
  Vindicated in the live run: arm 2's observed joint accuracy at step 0 was
  **0.0933**, vs 0.005 predicted for k=4 — ~19× more signal.
- My own fixtures caught a duplicate-detection bug keyed by group instead of
  (group, rollout), which would have rejected **every** real batch at
  `rollout.n=5`.

**(d) The 7B×8 host-RAM ceiling — this one cost a run.** Two *distinct* failures:
a save-time OOM (fixed by `save_model_only: true`, verified) and, separately, a
generation-time leak of **~3.4 GB per worker per hour with no plateau**. Arm 1's
first attempt died at step 39/100 with 8 workers at ~110 GB (~886 GB of 1007).
100 steps would need ~1.6 TB — unreachable. Both arms were capped at **30 steps**
(Launch amendment 3). Crucially, the accumulation is **fully released on process
exit**, so recycling/segmenting the workers recovers it — the 100-step run is
deferred, not lost.

**(e) Arm 2 finished all 30 steps but exited 1.** The failure is *after*
training, in the terminal validation pass, and it was **my own member-contract
guard firing correctly**: the plumbing-val file still used the old `l3_a/l3_b`
member names after the k=2 regrouping. All three checkpoints are intact (8/8
shards, 31 GB each) and the training curve is complete, so the science is
unaffected. The builder bug is listed in §6.

## 4. Decisions waiting on you

**Live:**

1. **Paper-2's confirmatory instrument — the one blocking benchmark call.** No
   cell passes all three criteria: coord n12 fails caption stress, chart-v3
   s9_low fails the dinov2 attacker, chart high-density cells fail the L1
   readout band. The structural finding behind it: informativeness and
   attacker-resistance are anti-correlated along the crossing-density knob, and
   while pixel statistics are matchable, the *structural position* of a causal
   edit is not. This also blocks extending the D1 sweep to the chart family.
2. **Whether to run the k=4 warm-start third arm.** The only way to test the
   registered C2×C3 reward as written: a shared ~4-step warm start (~40 min)
   restores k=4 to ~0.75 usable and keeps §4 matching by construction, but it
   changes the base checkpoint, which §3 does not delegate to me. Heterogeneity
   makes it *more* attractive than first quoted — the true joint rate is 1.24×
   the homogeneous estimate.
3. **Whether to recover the 100-step budget.** Evidence now says yes: held-out
   L3 is **still rising at step 30** while training accuracy is flat, so the
   30-step result is a lower bound (§5). The fix is worker recycling, which §S
   shows releases the accumulation completely.
4. **m7/mini_a5 retention (~290 GB of superseded intermediate steps).** The
   ratified retention rule hard-aborts on `m7` and `lh2` and keeps mini_a5's
   step-20 as `best_global_step`; reclaiming needs a policy change. Likely moot
   once the 2 TB top-up lands.

**Carry-overs (PI-owned):** Richard's review of the four delivered human
packages; X6 related-work table; PAPER1 §3/§5 header-table wording.

**Resolved since the last brief** (no longer open): E2 lenient-class fork (→
matcher v3); E3 reading; E4 wording; the storage menu; GPT-plan adoption; ST3-7B
ratification.

## 5. Headline results (paper-facing)

### Paper 1 — the access matrix and its mechanism

The R1–R5 ladder, the C6 7B inversion, the SEED3γ grounding-corrosion
replication and the no-transfer results are unchanged from the 08-14 brief and
remain the paper's spine (see RESULTS §6–§13c). One addition and one caveat:

| claim | key numbers | where |
|---|---|---|
| **New, independent corroboration: no RLVR recipe buys target discovery** | 8 trained arms × 12 cells on the frozen r2 hierarchy instrument. All four M7 3B arms land within ~0.01 of each other on L3 — **including the blind ones** (n8/l3: real 0.383, gray 0.373, no-image 0.368, caption 0.370). The modest L3 lift over base is therefore **content-free**, on an instrument Paper 1 was not built from | RESULTS §O; `reports/hier_instrument_sweep_v2.*` |
| *Caveat to propagate* | all hierarchy numbers are now scored with `match-tier-v3-sign-aware`; FlipTrack cells move ≤0.031 and arm differences less | RESULTS §N; `reports/matcher_v3_rescore_v1.*` |

### Paper 2 — the first positive result, and what is still missing

| item | outcome | where |
|---|---|---|
| **ST3 arm 1 (`st3_std`) moves L3 — and the gain is content-dependent** | L3 composition at step 30: **0.890 / 0.800 / 0.965** (n12/n20/n8) vs 7B base 0.575 / 0.470 / 0.660. The matched **gray control is 0.000 on every L3 and probe cell** (0.025–0.045 on L1/L2). First recipe in the program to move target discovery, and unlike the M7/C5 arms its lift cannot be blind | RESULTS §R, §T |
| **Trajectory: held-out L3 still climbing when training saturates** | n12/l3 0.575 → 0.760 (@10) → 0.815 (@20) → **0.890** (@30) while training accuracy is flat at 0.97+ from step 19. Training reward is a poor proxy for the transfer we measure; the 30-step cap truncated the curve | RESULTS §T; `reports/st3_arm1_trajectory_v1.*` |
| **ST3 arm 2 (`st3_igpo`) trained successfully at k=2** | joint accuracy 0.093 → **0.968** over 30 steps; member accuracy 0.295 → 0.984. The premise-gated objective is learnable — the amendment-2 regrouping was necessary and sufficient | run `st3_igpo_seed1_7b_an29_20260819T165105Z` |
| **The decisive comparison — NOT YET AVAILABLE** | arm-2 checkpoints are merging/evaluating now on an29. Until those land, *no claim about IGPO vs standard GRPO is supported* | chain `st3_readout_chain.sh st3_igpo_seed1_7b an29` |
| Registered primary endpoint 1 (R19 held-out content) | first ST3 measurement completed for arm-1 step-30 (4 shards × 300 rows); arm-2 counterpart still to run | `experiments/runs/st3_r19_std_step30_an12_20260819T235456Z` |
| Scope limits to state in the paper | training used coord n8/n12 of the same family as the instrument, so this is **program-level held-out transfer within family**; n20 is the one genuinely unseen density cell (and it moved, 0.470 → 0.800) | RESULTS §R |

## 6. Where everything lives

- **File of record:** `BlindGain_RESULTS.md` (here) = cluster `reports/RESULTS.md`,
  hash-verified mirror. §21 ledger: one row per claim → registration → artifacts
  → repro command blocks. New since 08-16: **§N–§T**.
- **Cluster repo:** `/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain`;
  refs `agent/gate2-recovery` = `master` = `main`. Registrations in `docs/`
  (ST3 = `registered_stage3_7b_v1.md`, now carrying **three launch amendments**);
  runs in `experiments/runs/`; reports in `reports/`.
- **Authority docs** (`/home/claude/blind_gain/`): `EXPERIMENT_TODO.md`,
  `PAPER1_RESEARCH_DOC.md`, `PAPER2_RESEARCH_DOC.md`.
- **Known issues, not yet fixed:**
  - `build_st3_train_corpus.py` emits plumbing-val rows with mother4 member
    names (`l3_a`/`l3_b`) even under `--group-mode side2`, which trips the
    member-contract guard in a terminal validation pass. Harmless to training;
    fix before any corpus rebuild.
  - **144 launcher scripts** call `jq` without putting `~/.local/bin` on PATH.
    They work from an interactive shell and fail from a non-interactive ssh
    command list. Deliberately not mass-patched (large unreviewable diff);
    export PATH at the call site. `launch_easyr1_checkpoint_merge.sh` is fixed.
  - Four LH2 manifests from earlier segments still read `"status": "running"`
    though only seg-4 is live; the GPU guard reads trainer-manifest occupancy,
    so close them when LH2 wraps.
  - Cluster exec requires `ssh -tt paracloud-node` (plain exec hangs); `/tmp` is
    node-local and login sessions land on ln206 *or* ln207 at random.
