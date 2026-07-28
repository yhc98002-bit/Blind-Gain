# Blind Gains — Experiment To-Do List (v2, launch-minded revision)
PI-final, 2026-07-24. Executor: Claude Code. In flight: X1 matrix (registered b9bd304) on an12 4–7 + an29 4–7; seed-3 A2b→A3 on an29 0–3; M5 segment 200→250 on an12 0–3. Trainer GPUs untouched, always.

## Track X — decisive diagnostics

**X1 — Grounding-Gap image-condition matrix (RUNNING).** Five models × {correct, mismatched-real, twin-counterfactual, gray, no-image} × both layers. Decides presence-gating vs content-specific evidence sharpening; the twin-counterfactual cell is the direct content-sensitivity test. ADDED — truncation guard: on a 50-item sample per open-form condition, measure emitted tokens vs the 32-token cap; if >0.5% of rows truncate before contract close, rerun all open-form cells at 128 tokens (version, never overwrite) and note it in the report.

**X2 — Hard-negative ranking v2: the stress test that upgrades our most memorable number.** Structured negatives per item (same-point y; neighbor's x; look-alike label's x; nearest gridline; twin's gold; symmetric sampling — composition never identifies gold). Purpose: convert 91% from a striking observation into an unassailable claim, at whatever level the data prints. **Pre-committed interpretation ladder (registered before scoring):** base-model geometry pair-success ≥ 0.75 → the latent-competence finding ships at FULL strength as a Paper-1 co-headline ("a large fraction of task-relevant visual answer information is present before RLVR and survives adversarial candidates; open-form generation realizes only ~47% of it"); 0.55–0.75 → mid-form ("substantial latent preference, partially candidate-sensitive"; realization gap remains a major finding at the measured number); < 0.55 → the 0.9067 is predominantly candidate-set structure; realization gap becomes a measurement-methods finding. Whichever branch obtains ships without renegotiation. **Language hierarchy:** "already perceived/understood" is permitted as hypothesis language everywhere, always; it becomes result language on the top branch plus premise-probe convergence (B1).

**X3 — A2 −0.045 item forensics (CPU, next wake-up).** Jaccard overlap across seeds with permutation null; transition directions; same-wrong-answer rate; visual-feature clustering; cross-arm behavior on the same items. Launch target: an interpretable degradation subset — "blind reward corrodes grounding, item-identifiably, across seeds" is a headline sub-finding if it prints.

**X4 — Visual-evidence calibration (CPU from X1 dumps, EXPLORATORY).** Reliability curves + ECE per model × condition; image-gated overconfidence quantified.

**X5 — Seed-2 replication of X1+X2** (blocked on X1 by registration).

**X6 — Related-work audit table (owner: PIs — Claude drafts, GPT cross-examines; not a cluster task).** Nine columns (peer-reviewed; code public; reproducible; studies RLVR dynamics; information-stripped train+test conditions; ranking+generation on the same pairs; trainability proof; access/grounding/realization separation; matched causal training arms) × {VisMin, TransBind, ViLMA, ViLP, Perception-R1, VPPO, + any found}. Output: the evidence-backed novelty paragraph — we claim the integrated framework, with the table attached.

## Track B — the benchmark's missing construct

**B1 — Renderable geometry track** (spec = this file's committed copy): six intervention types (fact-read; chained premise-to-reasoning with premise probes; binding swap; distractor-only; style twins; prior-conflict), per-item metadata (premise answer, final answer, hard negatives, intervention type, difficulty knobs, blind-solvability q̂), declared 100-pair calibration batch, one shot, standard gates. Human legibility pass: Richard.
**B2 — Release framing:** the six-layer FlipTrack profile as the artifact; two-layer names locked (candidate-evidence ranking / open-form realization); novelty positioned via X6's table; Mini-A5 as the published trainability validation.

## Track C — the critical chain (order unchanged)

C1 seed-3 → 16-endpoint eval → three-seed summary + pooled equivalence verdict. C2 Mini-A5: AUTHORIZED — launches on an29 0–7 the moment the seed-3 queue drains; X-work yields those GPUs. C3 M5 segments to step 400 (terminal rule merged). C4 M7 ViRL 3B stratified. C5 ≥1 7B A1-vs-A2b contrast; full 4×3 as budget allows.

## Track D — decided

Natural images → Paper 2 (one honest scope sentence in Paper 1). Crops → matrix v2 (token-count confound). Paper-2 repair = Selective Counterfactual RLVR (externally-verified premise/reasoning/counterfactual/invariance rewards; self-ranking-consistency rejected as a sharpening amplifier). Canonical working claim = the compressed thesis, scope-tagged. **Launch doctrine adopted as RESEARCH_DOC §11, binding for all paper text**: strengths-first structure, no chronology, no volunteered self-attack, comparisons only where we win and it matters — with the integrity anchor intact: every registered endpoint appears, cast as pivot, finding, or robustness evidence, never as confession.
