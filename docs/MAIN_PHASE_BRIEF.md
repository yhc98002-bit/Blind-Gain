Main-phase assignment; supersedes the prelaunch task list (its operating rules carry over).
Commit as docs/MAIN_PHASE_BRIEF.md, derive MAIN_TASKS.md, open reports/main_progress.md, start M0+M1.

# Blind Gains — Main Phase (M0–M14)

You are the implementing researcher. PIs audit; you never declare a gate passed. Ambiguity → `blocked` line, continue with unblocked work. Commit this file verbatim as `docs/MAIN_PHASE_BRIEF.md`; derive the `MAIN_TASKS.md` registry (M0–M14 → named reports); ledger `reports/main_progress.md`, one line per task: `<id> | pass|fail|blocked | note`.

**Rules.** All prelaunch operating rules remain in force (ModelScope-first, run-manifest hashes, greedy eval lock + fixed prompt contract, adversarial fixture with every fix, storage guards + retention, single-node placement, minimal TP, researcher's jobs are normal neighbors). New this phase:

- **Registration before training:** each training unit's registered document merges BEFORE its first optimizer step; launchers enforce merged-at-HEAD. The merge is the sign-off — no signature rounds, no sealing. Irregularities → one deviations-log line.
- Maintain `docs/RESEARCH_DOC.md` per its §8: update §4–6 with each ledger pass; never edit §1–3 or §7.
- Answer-pointing cues (circle/highlight/arrow on the queried element) are banned as difficulty tools for any construct claiming localization/search/correspondence; permitted only for explicitly named cued constructs, always labeled secondary/calibration.

## M0 — Finalize preregistration (first; blocks M2/M3)

Apply to the draft (earlier interim overlaps = verify):

1. Prior-observations section: anchor-vs-pilot-A1 comparison table (corpus filtering; reward implementation; tower setting — report the anchor's resolved `freeze_vision_tower` as launched and enter it here; prompt/parser; data; checkpoint schedule; eval set; decontamination). Include the geometry-category anchor delta (compute if absent). Verbatim: "The existence and approximate magnitude of the A1 benchmark/FlipTrack dissociation were observed before registration. Therefore, hypotheses concerning A1's qualitative direction are partially informed. Blind-arm recovery, A3 behavior, q_i–gain associations, and cross-arm contrasts remain prospective." Never present the anchor as a preregistered confirmation.
2. Mechanism analysis: PRIMARY = hurdle contrast, per-item gain on c_i>0 vs c_i=0 floor items, per arm under its own condition. Secondary = tie-corrected Spearman(q_i, gain); secondary = rank association within c_i>0. q_i is a Jeffreys-smoothed estimate of baseline reward-opportunity, never a directly observed latent.
3. R20 caveat, verbatim: "The primary FlipTrack endpoint was selected during R19 calibration. R20 independently satisfies all registered validity and anti-shortcut criteria but narrowly misses the preregistered 3B-real sensitivity floor for geometry and chart; it is therefore reported as robustness evidence, not a confirmatory pass." No R19/R20 pooling.
4. Provenance block: registration commit hash; exact launch command; "no pilot optimizer step has run"; one sentence: "the executing agent had continuous log access; PIs reviewed the anchor and audit artifacts before registration."
5. ViRL39K fork table (mandatory), five rows: caption q≈real AND zero-bit q substantial → geo3k mechanism likely generalizes | caption well below real AND zero-bit near floor → shortcut susceptibility is corpus-dependent; geo3k cannot support a broad claim | strong source/category heterogeneity → H-mixed becomes the headline; stratify | captions exceed real → caption-mediated accessibility; A3 indispensable | gray materially ≠ no-image → image-token presence is itself causal; retain both.
6. Outcome tiers: Primary RQ1 = cross-arm final-accuracy contrasts + recovery fractions. Primary RQ2 = R19 geometry pair-accuracy change. Key secondary = R19 overall; q_i floor contrast; D_caption^final = Acc_A3,100 − Acc_A1,100 (directional ≥ 0 on filtered geo3k, secondary prospective) and D_caption^gain = ΔA3 − ΔA1 reported separately. Secondary = per-category endpoints. Robustness = R20, chart-v08, long horizon, alternative parser fields. Overall R19 always shown with per-template results; no post-hoc R19-minus-chart composite.
7. Chart construct, verbatim: "In the R19 chart template, a circle indicates the queried plot point in both pair members. The task therefore certifies fine-grained value reading at a visually cued location; it does not certify the intended legend-to-series localization hop. An accompanying in-image sentence inaccurately describes the star as marking the queried point, although the star appears in the legend and the circle marks the plot point. Human audit found no resulting answer ambiguity, but the wording and cue narrow the construct. Chart results are secondary and are reported separately from the geometry-primary endpoint." Label: "cued chart point-value reading."
8. Parser acceptance conditions (replace retired 0.95 threshold): disagreements preserved row-by-row; fixed residual taxonomy; no native-correct/canonical-wrong residual after blinded adjudication; canonical-v2 passes the adversarial negative set; parser/reward versions immutable before launch; native reward logged as shadow. Report 0.9156 as context, not criterion.
9. Weighting evidence: quote the native r1v.py weight lines in `reports/pilot_reward_spec_v3.md`; if native ≠ 0.5/0.5 → `blocked` for PI disposition.
10. Human-audit record: `reports/fliptrack_v02r19_human_audit.md` = accepted, 60/60, with the three chart notes (circle → cued reading; wrong in-image star sentence; marginal nine-series color discriminability); item 7 references it. Done: ledger states list applied → Richard merges as `reports/preregistration_pilot_v1.md` → mark pass.

## M1 — L10 + fork ruling (parallel with M0)

Finish the ViRL39K 4,096-item audit → report + audited JSON, no sealing. After M0 merges: record which fork row obtains in `reports/virl_fork_ruling.md`; PIs confirm via Richard.

## M2 — Pilot seed 1 (needs merged M0)

Four arms via the existing launch machinery; every registered estimand incl. the restructured mechanism analysis; StrictGain identity check; FlipTrack at {0, 60, 100}. → `reports/pilot_4arm_seed1_results_v1.md`. Registered analyses only.

## M3 — Pilot seeds 2–3 (launch arms as GPUs free)

→ `reports/pilot_3seed_summary_v1.md`: per-seed + pooled estimands; seed dispersion descriptive; pooled gray≡no-image equivalence check (decides A2-gray at 7B).

## M4 — Registered extensions doc (blocks M5–M7, M9)

`docs/registered_extensions_v1.md` = transcription of decided designs; invention needed → `blocked`. Richard merges on your confirmation. Contents:

- **Long-horizon:** extend the anchor from archived step-100 state to FIXED step 400; benchmark + FlipTrack evals at 150/200/300/400; "Do not stop because the desired curve appears early." Precondition: restore-and-resume integrity check (1-step resume; hash/loss continuity); registered fallback = fresh 400-step run at anchor config, disclosed.
- **Mini-A5, two arms:** CP (shared group uid; broadcast r_i = acc(a_i)×acc(b_i)) vs same-data standard GRPO (member-level reward) on one generated pair corpus from training-only templates disjoint from all eval templates; matched 3B model, prompts, G, 100–150 steps, token budget. Primary: Δ_CP − Δ_same-data on held-out-template FlipTrack. Required: advantage-tensor equivalence test; catch-trial stability; step-0 reward-hit/variance stats for both rewards; no silent shaped-reward switch (fallback predeclared, PI-approved before use); template-disjointness in the decon manifest.
- **ViRL 3B template:** 4 arms × 2 seeds on the decontaminated subset; {computed} fields filled after the fork ruling.
- **7B flagship template:** A1/A2b/A3 (+A2-gray reinstated if M3's equivalence check fails its margin); 3 seeds per arm, seed 1 first; A3 = frozen 7B own-caption store, plus a fixed-3B-caption sensitivity condition at inference/small scale; item-paired analyses; one node per arm.

## M5 — Long-horizon (after M4; 4 GPUs)

Execute → `reports/anchor_longhorizon_400_results_v1.md`: four checkpoint evals + registered flat/rising verdict.

## M6 — Mini-A5 (after M4; 8 GPUs, one node)

Execute → `reports/mini_a5_control_results_v1.md`: primary contrast with paired CIs; catch-trial table; reward stats; equivalence-test result.

## M7 — ViRL 3B decomposition (after M4 + fork ruling)

Prep: ViRL×Layer-1 decon manifest; frozen subset ID list + hash; 3B caption store (100% coverage or enumerated gaps). Run 4 arms × 2 seeds → `reports/virl_3b_decomposition_results_v1.md`.

## M8 — 7B prep (parallel with M7)

7B own-caption store over the ViRL subset; 7B blind-solvability on the 4,096 sample incl. own-captions (pilot contract); flagship configs hashed into M4's fields.

## M9 — 7B flagship (after M4 + M8; one node per arm)

Seed 1 → `reports/flagship_7b_results_v1.md` → seeds 2–3 trailing (may interleave with M14) → `reports/flagship_7b_3seed_v1.md`. Registered analyses only.

## M10 — Support-sharpening resampling (fold into every readout)

Newly-solved items with base 0/16 under that arm's condition: draw 64 extra base samples; recompute posterior support; "high-confidence support-expansion candidate" only if still absent. Language: "mass sharpening within observed support" / "not observed in the base K-sample set" — never "RL created/taught a capability."

## M11 — Non-Qwen audits (inference-only; gap-filler)

InternVL3-9B (ModelScope) and Gemma-3-12B-IT (gated: ModelScope-first; if blocked, report the obstacle and propose one alternative for PI pick; never substitute silently; never Molmo-7B-D — Qwen2 backbone). Conditions real / no-image / fixed question-blind caption, on FlipTrack R19+R20 and the blind-solvability sample. → `reports/generalization_audits_v1.md`.

## M12 — Chart v08 (gap-filler; new family, R19 untouched)

Two subfamilies, reported separately: **legend-target flip** (curves identical; the star moves between legend entries; answer changes; mask = star region) and **point-value flip** (starred entry fixed; one value on its series changes; mask = marker + affected segments). Plus: two-hop necessity diagnostic (removing/randomizing the star-legend association must materially cut performance, else an unintended cue exists); human-legibility gate (preregistered sample answerable by a human without zoom; series identity unambiguous; colorblind-safe palette; distinct linestyles + markers); one-shot confirmatory after freeze (retain every mechanically valid pair; no replacement; no renderer edits after seeing scores; a failed confirmation is preserved as evidence). → `reports/chart_v08_calibration.md`, then `reports/chart_v08_confirmatory.md`.

## M13 — Paper pipeline (continuous)

`docs/paper1/`: section skeleton with empty result slots; figure scripts from ledger outputs (decomposition bars per corpus/scale; floor-contrast mechanism plot; benchmark-vs-FlipTrack dissociation scatter; audit tables); master result table; shared methods appendix; data card; Paper-1/2 contribution-nonoverlap table. Text rule: "caption-mediated accessibility" — never "captions contain more information than images," "vision hurts," or "caption training is blind training."

## M14 — Merge-back readouts (after M6 + M9 seed 1)

7B CP-GRPO pilot arm (registered addendum to M4 first; ~200 steps, mini-A5 recipe scaled up) + external-transfer eval of that checkpoint vs its A1 counterpart. → `reports/mergeback_gate_readouts_v1.md` with the three gate inputs (mini-A5, 7B CP, transfer). PIs apply the pre-committed split/merge/cancel rule.

## Order

M0/M1 now → M2 on merge → M3 + M4 → M5/M6 as GPUs free → fork ruling → M7/M8 → M9 → M14. M11/M12/M13 fill idle capacity; M10 folds into each readout. Single-node always; scheduling judgment is yours within dependencies.
