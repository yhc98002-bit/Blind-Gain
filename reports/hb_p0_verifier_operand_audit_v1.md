# Verifier-operand audit (08-12 dispatch P0.1 / EXPERIMENT_TODO P1.1b) — exceptions only

Executed 2026-08-16. Instrument: `scripts/audit_question_operands.py`
(question-named entity vs recorded operand; gold recompute from recorded
targets where the manifest carries them), plus the I21 patch to
`scripts/verify_track4_premise_v2_dev_batch.py`. Conventions were pinned
empirically before the audit shipped (R19 coordinate register: answer =
target's x under `semantic_side_assignment_swapped`, 600/600; chart-v08:
question "x = N" equals `verifier_results.target_x`, 100/100). Fixtures:
`tests/test_question_operand_audit.py` (10 tests — one adversarial
cue-ladder-class fixture per generator; every corruption case fails the
pre-fix state because the checks did not exist).

## Exceptions

1. **premise-v2 re-checker validated golds against
   `verifier_results.target_label`, never the question-named entity** (the
   I21 operand class; a renamed question with a stale `target_label` passed).
   **FIXED this round**: the re-checker now parses the question/premise
   question and refuses a name↔operand mismatch; end-to-end fixture
   (`test_patched_premise_v2_verifier_refuses_renamed_question`) corrupts one
   dev_v2 row and asserts refusal.
2. **B1 (`scripts/build_b1_geometry_track_prototype.py`)**: rows carry no
   scene serialization, so golds cannot be recomputed from the manifest
   post-hoc; `exact_by_construction` is a declared literal; the generator had
   **zero tests** before this round. Mitigations: the question-operand audit
   now covers the frozen batch from disk (100/100 + 20/20 clean); any future
   batch from this lineage must serialize scene truth (the premise-v2 lineage
   already does, via `scene_points_a/b`).
3. **v02 header-table family** (300 R19 + 300 R20 rows): no checkable
   operands are recorded (row/column codes absent from `verifier_results`),
   so the audit cannot cover it; its verifier fields are generation-time
   declarations. Frozen instrument (I11); recorded, not remediated.
4. **chart-v08 necessity manifest** (200 rows): rows carry no operand fields
   the checker can consume (0/200 checked). Its integrity rests on the
   builder's own guarantees (`build_chart_v08_necessity_eval_manifest.py`
   re-verifies every diagnostic image sha256 and asserts the random-star
   target implies a different answer) — adequate, but outside this audit's
   mechanical coverage.
5. **v02 `verifier_results` are predominantly declared literals** with
   computed exceptions (triangle angle sums, adjacent-crossing counts,
   palette CIE76). The coordinate-register family is now post-hoc
   recomputable from its recorded `target_a`/`target_b` and is clean
   (600 R19 + 600 R20 rows, gold recompute + question-name checks).
6. **Cue ladder**: retracted (invalid build; the class-defining operand bug —
   `gold_follows_question` checked the target, not the question). Retraction
   banners applied to `reports/cue_ladder_readout_v1.md` and RESULTS §16
   (P0.2); superseded by the L1/L2/L3 hierarchy.

## Sweep results (`tmp/operand_audit_sweep.json`, rc 0)

| manifest | rows | checked | unchecked | problems |
|---|---:|---:|---:|---:|
| `data/b1_geometry_track_v1/manifest.jsonl` | 100 | 100 | 0 | 0 |
| `data/b1_premise_probe_v1.jsonl` | 20 | 20 | 0 | 0 |
| `data/track4_premise_v2_dev_v1/manifest_causal_pairs.jsonl` | 160 | 160 | 0 | 0 |
| `data/track4_premise_v2_dev_v1/manifest_invariance_pairs.jsonl` | 160 | 160 | 0 | 0 |
| `data/track4_premise_v2_dev_v1/manifest_premise_probe.jsonl` | 140 | 140 | 0 | 0 |
| `data/track4_premise_v2_dev_v2/manifest_causal_pairs.jsonl` | 160 | 160 | 0 | 0 |
| `data/track4_premise_v2_dev_v2/manifest_invariance_pairs.jsonl` | 160 | 160 | 0 | 0 |
| `data/track4_premise_v2_dev_v2/manifest_premise_probe.jsonl` | 140 | 140 | 0 | 0 |
| `data/fliptrack_chart_v08_calibration_v1_manifest.jsonl` | 100 | 100 | 0 | 0 |
| `data/fliptrack_chart_v08_calibration_v1_necessity_eval_manifest_v1.jsonl` | 200 | 0 | 200 | 0 |
| `data/fliptrack_v02r19_artifact_expanded_source_manifest.jsonl` | 1200 | 900 | 300 | 0 |
| `data/fliptrack_r20_source_manifest.jsonl` | 1200 | 900 | 300 | 0 |

Unchecked rows are the exception-3/4 surfaces above — counted, never
silently passed. No problems anywhere; the frozen instruments and both
premise-v2 batches are operand-clean under every check the manifests support.
