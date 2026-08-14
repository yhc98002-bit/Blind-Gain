# Blind Gains — context brief

*Snapshot 2026-08-14. This file is a one-sitting orientation brief; `BlindGain_RESULTS.md` remains the file of record (its §21 ledger is the reproduction backbone). Nothing here is new evidence.*

---

## 1. What this program is

**Blind Gains** asks what RL with verifiable rewards actually improves in a VLM (Qwen2.5-VL-3B/7B, EasyR1/verl GRPO). **Paper 1** (*Learning Without Looking*) shows that most of the benchmark gain from image-conditioned RLVR is available without the images — an access-matrix result built as a claim ladder R1–R5 with a mechanism story (readout sharpening, not content acquisition). **Paper 2** builds the method + benchmark that could force genuine visual acquisition: counterfactual intervention-group optimization over a FlipTrack-style benchmark, gated at every step by acceptance checks (blind floor, caption stress, artifact attacker, difficulty band).

## 2. Status at a glance

| | |
|---|---|
| Docs current through | 2026-08-11T16:32Z (this round refreshes them to 08-14) |
| Git | all three refs (`agent/gate2-recovery`, `master`, `main`) at `da0751d`; this round adds one docs+cleanup commit |
| Paper-1 evidence | **claim ladder R1–R5 closed**; C6 mechanism-at-scale landed 08-11 |
| Paper-2 gates | Gate 0, Phase 0, Gate 1 complete; **all four premise-v2 acceptance gates run** |
| Cluster (08-12 → 08-14) | **deadlocked on storage quota; unblocked this round** — see §3 |
| In flight after unblock | M7 seed-2 a2_gray + a3_caption training → evals → two-seed R3 readout; LH2 stage 1 re-armed behind a2_gray |
| Decisions waiting on you | 5 live + 3 carry-overs — see §4 |

## 3. What happened while you were away

**Nothing scientific landed after 08-11T16:32Z — the cluster silently deadlocked.** Cause → chain → consequence:

- **Cause.** `checkpoints/` grew to 2.4 T; the storage guard saw 63.5 GB free against the 2.5 TiB project capacity and refused every 55 GB checkpoint save (floor 21.5 GB), retrying every 300 s forever (`MAX_ATTEMPTS=0`). The storage snapshot kept self-reporting `"status": "pass"` while free space was effectively negative against the soft quota — quota exhaustion was never treated as a failure by anything watching.
- **Chain.** M7 seed-2 **a2_gray** wedged at the step-80 save (banked through step 60, best_val 0.6476); **a3_caption** wedged at the step-60 save (banked through 40, best_val 0.6690). Both trainers stayed alive-but-idle with unsaved progress in memory; all 16 GPUs sat at 0 % util. Both chain waiters hit their hard 60-h deadlines on 08-13 and aborted (149-byte logs: "deadline; abort").
- **Consequence.** Neither seed-2 eval launched; the LH2 stage-1 relaunch trigger never fired; the two-seed R3 readout was impossible (2 of 4 arms). R3 remains a **single-seed claim** until this completes.
- **Process lesson (one line).** The 60-h waiter deadline converted a storage stall into silent abandonment — waiters need a wedged-vs-dead distinction, and `"status": "pass"` on the storage snapshot is not a health check.

**What I did about it (2026-08-14, PI-approved policy: clearly-redundant deletions only):**

- Deleted **712.6 GB** (712,585,804,824 bytes, 26 items): the three archived failed-attempt checkpoint dirs (c5 attempt-1 host-OOM 132.7 GB, m7 seed-2 attempt-1 ×2) and the **non-terminal** `global_step` dirs of the six complete, eval-banked, §21-ledgered M7 runs — every evaluated/best step kept (each run's step 100; also step 80 for a1_real_seed2 where best=80). Byte-exact record: `reports/storage_cleanup_20260814.md`.
- Found the guard doesn't measure disk directly — it reads `reports/storage_usage_snapshot.json`, refreshed by a 3-h login-node loop — so I refreshed the snapshot manually (`scripts/measure_storage_usage.py`) instead of losing another 2.5 h. Used fell 2.685 TB → **1.97 TB**, free **776 GB**.
- The wedged trainers were left untouched: both guards flipped to `pass` on their next 300-s retry (15:28/15:29Z) and the step-80/step-60 saves + training resumed unaided.
- Re-armed both aborted chains at 15:31:02Z under fresh 60-h windows (`seed2_an12_chain` → a2_gray eval on an12 gpu 7 + LH2 relaunch on an12 0–3; `a3_eval_chain` → a3 eval on an29 gpu 1).
- Expected landing order (estimates at ~0.6 h/step): a2_gray completes ~08-15 04Z → its eval (~9.5 h) + LH2 stage-1 launch; a3_caption completes ~08-15 16Z → its eval; **two-seed R3 readout ready ~08-16**.

## 4. Decisions waiting on you

**Live:**

1. **E3 reading (a) vs (b) — the one open measurement call.** Four of five intervention types pass caption-stress under both readings. `chained_premise_easy` measures caption member accuracy **0.2625**: it **fails** reading (a) (registered literal blind floor 0.133 + 0.10 = 0.233) and **passes** reading (b) (its own measured blind floor + 0.10 = 0.325). The failure under (a) is inherited from E2's answer-balance defect, not from captions. The instrument deliberately refuses to choose. → `reports/track4_premise_v2_e3_readout_v1.md`.
2. **Gate-1 §6 branch reading (Paper-2 direction).** The four-arm result (no axis buys content at 3B; the lever is reward *resolvability*, not reward shape) is on file; PAPER2 §6's branch menu is explicitly yours to fire. C6's 7B inversion (below) bears on it: Stage 3 is no longer a scale-up formality.
3. **GPT Benchmark Revision Plan adoption** (`GPT Benchmark Revision Plan for Paper 2.md`, Aug 13 — unintegrated). Digest: keep R19/R20 frozen; build a deliberately small hierarchical extension — **Discover → Ground → Read** (L3/L2/L1), two families (coordinate plots from the premise-v2 generator; line charts from the chart-v08 renderer), all three layers derived from the **same mother-item** with oracle information as the only difference; three counterfactual pair roles (target-switch / target-stable / invariance); a one-time **verifier-operand audit**; P0 integrity → P1 build → P2 dev validation (no new training) → P3 freeze → P4 method eval. **Conflicts with EXPERIMENT_TODO:** P1.1 currently rebuilds cue-ladder v2 as a full component — the plan demotes it to a calibration diagnostic; the plan's verification section overlaps P1.1b (verifier-operand audit), already in the TODO. Keeps everything already paid for (premise-v2, chart-v08, acceptance gates).
4. **E4 registration wording.** The prose criterion ("every attacker's CI includes 0.5") is unsatisfiable for the folded statistic `max(AUC, 1−AUC)` the instrument computes; reconcile wording, no numbers change.
5. **Remaining storage menu** (only clearly-redundant items were deleted; these need your call): mini_a5 steps 20–80 (keeping step 100 + terminal 120) ~500 G — kept pending confirmation that no ranking-cell analysis referenced them, c5 completed-run non-terminal steps ~248 G, `pilot/` 206 G, `smoke/` 31 G, `m5_anchor_longhorizon_400/global_step_150` 51 G (resume-source only; terminal step 400 kept).

**Already decided by you, propagated into the docs this round** (were still listed "open" in RESULTS §19): E1 branch-(c) step to `n=5` **approved**; E2-failing intervention types **excluded from training use** until final-answer distributions are balanced (per EXPERIMENT_TODO 2B-status).

**Carry-overs:** Richard's review of the four delivered human packages; X6 related-work table; PAPER1 §3/§5 header-table wording (all PI-owned).

## 5. Headline results (paper-facing)

### Paper 1 — the access matrix and its mechanism

| claim | key numbers | where |
|---|---|---|
| **R1–R5 ladder closed**: the blind gain is real, grows with scale, generalizes across corpus and family | R3 (ViRL39K): matched recovery **0.72–0.88** vs 0.08–0.12 on geo3k (seed 1). R4 (7B): A1 matched gain **+0.2479** vs +0.2435 at 3B; crossed TrainShare **0.487 [0.383, 0.588] @3B → 0.7785 [0.6418, 0.9214] / 0.8402 strict @7B**, intervals disjoint | RESULTS §12d, §12e; ledger rows R3/R4 |
| **Mechanism: readout sharpening, not content** (3B) | Mini-A5/F8 branch 2: primary anchor flat on content; CP moves only the oracle-localized readout. M5 long-horizon: R2 **FALLING**; M5c turnover 137/601 flips against a measured **zero** noise floor | §8, §12–12c |
| **Blind reward corrodes grounding, item-identifiably** | SEED3γ replication: 3-way Jaccard **0.661** vs null 0.012 | §6, §6a |
| **No out-of-domain transfer of the blind gain** | E1b 48/48 external cells: P1, S1, S2 all miss; E1c blind columns across 7 benchmarks (MMVP exactly 0.000) | §13c, §13b-bis |
| **C6: at 7B the dissociation inverts — real-image arm only** | A1-real moves the **primary anchor** +0.0250 [0.0033, 0.0467] (R19) / +0.0233 [0.0017, 0.0433] (R20), both contracts, both instruments — branch (d); readout flat. A2-gray moves **neither** — branch (c). First arm in the program to move the primary anchor. One seed; descriptive; re-decides neither Gate 1 nor R4 | § "2026-08-11 — C6"; ledger row C6; `reports/c6_mechanism_at_scale_v1.*` + independent replicate (24/24 numbers exact) |

### Paper 2 — gates run, method direction open

| item | outcome | where |
|---|---|---|
| Gate 0 + Phase 0 | complete (stratification; premise-probe P0.1 → branch (b); invariance scorer fixed) | §10, §11 |
| **Gate 1 — four arms (std · paired · necessity · CP)** | **No arm moves held-out content on the primary anchor**; every registered difference is strict/format. Pairing = strict-contract tax (**−0.32** canary, p=4e−27); necessity refunds **+0.043 [0.018, 0.070]**; **all four recipes move the oracle readout +0.15–0.23**. Lever = reward resolvability, not reward shape | § "2026-08-09 — GATE 1"; ledger row Gate 1 |
| Track-4 premise-v2 **E4** (attacker) | **PASS** — no transferable artifact signal: DINOv2 memorises train folds (AUC 1.0) yet lands at OOF 0.529; max folded gate statistic 0.546, max CI upper 0.576 | ledger row E4; `reports/track4_premise_v2_attacker_gate_v1.json` |
| Track-4 **E1** (difficulty) | **FAIL, branch (c)** — n=20→n=8 moved premise solvability only 0.275→**0.2875**; difficulty is not candidate-set size; pre-committed step to n=5 approved | ledger row E1/E2; `reports/track4_premise_v2_gate_readout_v1.md` |
| Track-4 **E2** (blind floor) | Premise clause **PASS at exactly 0.000** blind for every type; final clause **FAIL all five** (0.1375–0.250 vs 0.133) via a degenerate constant answer (collapse 1.000) meeting a non-uniform gold distribution — **answer-balance defect, not a visual leak**; construct not regenerated | same |
| Track-4 **E3** (caption stress) | **Not caption-leaky** — caption−blind ≤ 0 for 4/5 types, +0.0375 for the fifth; reading (a)/(b) split on one type → your call (§4.1) | ledger row E3; `reports/track4_premise_v2_e3_readout_v1.*` |

## 6. Where everything lives

- **File of record:** `BlindGain_RESULTS.md` (here) = cluster `reports/RESULTS.md`, hash-verified mirror. §21 evidence ledger: one row per claim → registration → artifacts → inline repro command blocks A–I.
- **Cluster repo:** `/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain`; refs `agent/gate2-recovery` = `master` = `main` on GitHub. Registrations under `docs/`; run dirs under `experiments/runs/`; reports under `reports/`.
- **Authority docs (authoritative copies in `/home/claude/blind_gain/`):** `EXPERIMENT_TODO.md` (the VM-Transfer copy is a duplicate), `PAPER1_RESEARCH_DOC.md`, `PAPER2_RESEARCH_DOC.md`.
- **Housekeeping:** three stale `BlindGain_RESULTS.md.tmp.4777.*` editor temps (July) sit in this folder — deletable at your leisure. Cluster exec sessions now require `ssh -tt paracloud-node` (plain exec hangs). Queued small fixes, not yet applied: the storage snapshot's `"status": "pass"`-while-over-quota bug; the E3 runner's STAGE-B argument-order bug (E3 itself completed via the banked-captions recovery); waiter wedged-vs-dead handling.
