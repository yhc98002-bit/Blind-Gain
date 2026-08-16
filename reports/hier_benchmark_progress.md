# Hierarchical benchmark build — progress ledger (08-12 dispatch, P0–P2)

One line per dispatch task ID: `pass | fail | blocked | running` + note.
Honest `blocked` beats a thin `pass`. NOTE on IDs: the dispatch's P0.x/P1.x
IDs are scoped to THIS ledger only — they collide with differently-defined
IDs in `docs/EXPERIMENT_TODO.md` (its P0.1–P0.4 are the completed Phase-0
tasks; its P1.1 is the superseded cue-ladder rebuild). Mapping: dispatch
P0.1 ≈ TODO P1.1b; P1.0 ≈ HB.0; P1.1 ≈ HB.1+HB.3+HB.5; P1.2+P2.x ≈ HB.7.
Registration of record: `docs/registered_hier_benchmark_v1.md` (merged
2026-08-16, commit `2248c7f`).

| ID | Task | Status | Note |
|---|---|---|---|
| P0.1 | Verifier-operand audit, every generator with a verifier | pass | `reports/hb_p0_verifier_operand_audit_v1.md` — 6 exceptions recorded; the I21 gap in the premise-v2 re-checker FIXED (+ end-to-end fixture); sweep over 12 manifests / 3,740 rows: 0 problems; one cue-ladder-class fixture per generator (`tests/test_question_operand_audit.py`, 10 tests). |
| P0.2 | Retraction headers on `reports/cue_ladder_readout_v1.md` + RESULTS §16 | pass | Both headers applied 2026-08-16 (supersede, not delete); `.json` siblings covered by the md banner. Neither carried a retraction marker before (verified by grep). |
| P0.3 | premise-v2 branch-(c) n=5 + E2-failing types excluded | pass | Executed in the 2026-08-16 consolidation round: dev_v2 one-shot, E1 PASS (0.5125 in band, n=5 frozen); exclusions stand (E2 FAIL persists via the lenient-class collision — PI fork). `reports/track4_premise_v2_gate_readout_v2.*`. |
| P0.4 | Census exporter: standing, inventory-driven review artifact | pass | `scripts/build_generator_census.py` (+4 fixtures): every template-carrying `data/**.jsonl` appears automatically; first census `reports/generator_census_v2.{json,md}` — 50 families, 168 variants, 92 files scanned, 84 variants loudly stage-unmapped; arms-joining deferred to the P2.4 package builder by design. |
| P1.0 | `docs/registered_hier_benchmark_v1.md` before any item exists | pass | Authored + merged 2026-08-16 (`2248c7f`), before any HB item existed. Chart crossing-density bands + pair-role split to be pinned by amendment BEFORE chart/coord generation (P1.2 gate). |
| P1.1 | Mother-item derivation in both generators; verifiers (a)–(e), each with an adversarial fixture | pass | `scripts/hier_v1_lib.py` + `scripts/build_hier_dev_batch.py` + `scripts/verify_hier_dev_batch.py`; offset-cue engine under the registered allowed-color ink rule; Amendments A1 (concrete grids/cue/probes) + A2 (layer × role matrix: target-switch is L3-only — a switch pair admits no single truthful identity question); 8 fixtures incl. cue-occlusion + unrendered-variant detection (`tests/test_hier_v1_builder.py`). |
| P1.2 | Dev batches: 150 mother-items per family per knob cell, one shot | pass | 7 cells × (150 L3 + 100 L2 + 100 L1 + 150 probe) rows, seed 20260817; coord balance ≤ 0.10 every cell; 9-series palette CIE76 minima 26.4 normal / 16.2–20.7 CVD (above the chart-v08 floors); candidate registries per causal L2/L3 manifest. From-disk verification **0 problems** (4,900 images rehashed, 1,400 cue pairs pixel-checked; `logs/verify_hier_dev_20260816.log`). Deviation: attempt 1 died at s9_low (random-values proposal cannot reach the registered low-crossing band at 9 series); partial tree removed pre-declaration; banded PROPOSAL added, registered band filter unchanged (`reports/hier_v1_dev_build_v1.json` deviations). |
| P2.1 | Base 3B/7B + `mini_a5_std_seed1`/`mini_a5_cp_seed1` step-120 on all layers/roles + discovery probe; open-form + candidate-ranking | pending | Both mini-A5 merged HF checkpoints verified on disk (pin 8131575808 / 825). 12 GPUs idle (an12 4–7 + an29 0–7); LH2 owns an12 0–3. |
| P2.2 | HB.7 informativeness gates on base 3B, per knob cell | pending | Gates quoted in the registration §7; pass/fail only, no knob iteration. |
| P2.3 | Blind-floor + 72B caption-stress cells + attacker checks | pending | 72B not on disk (ephemeral-/dev/shm design, ~137 GiB via ModelScope through the 127.0.0.1:7890 proxy, TP4 — an12 4–7 is the documented block); attacker pipeline = `src/fliptrack/artifact_attackers.py` per the chart-v08 gate launcher precedent. |
| P2.4 | Census review package v3 (new families) → human gates queue | pending | Never self-certified; queue includes the chart-v08 no-zoom audit, which EXPERIMENT_TODO Part 3 says blocks chart-side P2. |
