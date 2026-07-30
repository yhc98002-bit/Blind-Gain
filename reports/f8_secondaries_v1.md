# Mini-A5 F8 secondaries — readout (v1)

**Written:** 2026-07-30. **Repo HEAD at readout:** `ed4aa962f2bd945638b0183316be73137299cbcd`
(branch `agent/gate2-recovery`). **Git hash bound into both ranking run manifests:**
`b0b316d294a7f22f8812235f590499e65735b939` (verified ancestor of HEAD).
**Registration commit bound into every run manifest:** `a0ff9d5c44a754002b2b95d5e31da2fcb70b3158`
(verified ancestor of HEAD).

**Scope.** The three secondary endpoints listed in `docs/registered_mini_a5_main_v1.md`
line 92 and triaged in `docs/registered_mini_a5_endpoint_readout_v1.md` §6. One of the
three has an instrument and was run; two do not and are reported as such.

**What this document is not.** It carries no primary-endpoint verdict. The registered
Mini-A5 decision rule (addendum §4) is defined only on the primary generation endpoint
and is F8's deliverable, not this report's. Generation-layer numbers appear here **only**
as the second half of secondary 1's named contrast, on the pair set that contrast requires.
This report carries numbers, checks and provenance — not interpretation.

| endpoint | status | evidence |
|---|---|---|
| 1. Free-generation vs candidate-ranking | **RUN** | §1 |
| 2. Catch-trial stability | **INSTRUMENT-ABSENT** | §2 |
| 3. "The registered task benchmark" | **UNRESOLVABLE FROM THE REGISTRATION** | §3 |

---

## 1. Secondary 1 — free-generation vs candidate-ranking (RUN)

### 1.1 Instrument and invocation provenance

The candidate-ranking half was produced by the registered ranking instrument
`scripts/eval_qwen_vl_visual_evidence_ranking.py` (scorer `visual-evidence-ranking-v1`,
result schema `blind-gains.visual-evidence-ranking-result.v1`).

The invocation shape was copied from the completed prior run

```
experiments/runs/d1_visual_evidence_a1_seed2_step100_real_an29_gpu4_x5_ranking_matrix_queue_login_20260725T021220Z
```

— specifically its `worker.sh` and its `run_manifest.json.command`, which invoke
`scripts/launch_visual_evidence_ranking_cell.sh NODE GPU MODEL_KEY CONDITION RUN_DIR`.

Two changes were required, both scoped and committed as `b0b316d`
(`git show --stat`: 2 files, 74 insertions, 1 deletion):

1. **New config** `configs/eval/mini_a5_visual_evidence_ranking_v1.json`
   (sha256 `0baeb9f7b9263913c81961eaffcb1a1500a90ebcbf46d5e2342edf99d4f8c256`), passed via
   the launcher's existing `RANKING_CONFIG` hook. Its `candidate_registry`, `processor`,
   `prompt_contract` and `scoring` blocks are byte-identical to
   `configs/eval/x5_seed2_image_condition_matrix_v1.json`, so these cells are directly
   comparable to every prior registered ranking cell. Only the `models` map differs.
2. **Launcher allowlist**: the two Mini-A5 model keys were added to the `MODEL_KEY` regex
   in `scripts/launch_visual_evidence_ranking_cell.sh`. Verified from `git show b0b316d`
   that this is a one-line change (`1 insertion, 1 deletion`) adding only
   `|mini_a5_cp_step120|mini_a5_member_step120` to the alternation. No scoring, contract,
   gate or hash-check logic was touched.

The actual commands run:

```
RANKING_CONFIG=configs/eval/mini_a5_visual_evidence_ranking_v1.json \
  scripts/launch_visual_evidence_ranking_cell.sh an29 4 mini_a5_cp_step120     real <run_dir>
RANKING_CONFIG=configs/eval/mini_a5_visual_evidence_ranking_v1.json \
  scripts/launch_visual_evidence_ranking_cell.sh an29 5 mini_a5_member_step120 real <run_dir>
```

The launcher's own preflight gates all fired and passed: config/registration/registry
tracked and clean, `model.safetensors.index.json` sha256 matched the config for both arms,
registration commit an ancestor of HEAD, target GPU unoccupied.

### 1.2 Cells

| arm | model key | checkpoint | node:GPU | run dir |
|---|---|---|---|---|
| CP-GRPO | `mini_a5_cp_step120` | `checkpoints/mini_a5/mini_a5_cp_seed1/global_step_120/actor/huggingface` | an29:4 | `experiments/runs/mini_a5_s1_ranking_cp_step120_real_an29_gpu4_20260730T011842Z` |
| same-data GRPO (member) | `mini_a5_member_step120` | `checkpoints/mini_a5/mini_a5_same_data_seed1/global_step_120/actor/huggingface` | an29:5 | `experiments/runs/mini_a5_s1_ranking_member_step120_real_an29_gpu5_20260730T011842Z` |

| | CP | member |
|---|---|---|
| checkpoint index sha256 | `4bb3b752a9895596f57798116b660406110198669dcfefbc213594d540baed21` | `b4270b12dda440fdfdb345c4c074decd1dbbe8d40c751b67392ce6d96bd037f6` |
| rows written | 1,200 | 1,200 |
| manifest status / exit code | `complete` / `0` | `complete` / `0` |
| `scores.jsonl` sha256 (re-verified on disk) | `0491c25daf13c64803339d7bb92e10f802e1f90c67a797b8ff307ad6e7d7a14a` | `71e2d42f1179e2477241e5e0494ee98890c34e74e738595be8bb93fc653cf765` |
| wall clock (UTC) | 01:18:43 → 03:49:25 | 01:18:45 → 03:49:25 |

Candidate registry `data/fliptrack_r19_visual_evidence_candidates_v1.jsonl`
sha256 `fa9456941a730e174b1ed4bb4caefc151778e3f1adc0ca77db941955a4215f81`, 1,200 pairs,
built from the locked R19 manifest (`source_manifest_sha256` `e1dde984…`).
Condition `real`. Scoring: teacher-forced exact-candidate mean token log probability.
Every row carries `global_step: 120`, `condition: real` and its own arm's `model_key`
as a single distinct value.

**Placement.** an29 was fully idle at launch and again at readout (all 8 GPUs at 2 MiB,
zero compute apps); the F8 primary cells had already reached `status: complete`, so there
was no contention and no need to wait or to fall back to an12. **an12 GPUs 0-3 (M7 arm 1,
45-50 GiB resident throughout) were never touched, allocated or widened onto.** Each cell
is TP1 on one GPU; the launcher refuses any GPU with a compute app present (`exit 75`).

### 1.3 The free-generation half

The generation layer is not a new run. It is the already-scored output of the two
completed F8 primary R19 cells:

```
experiments/runs/mini_a5_f8_r19_cp_step120_real_an29_20260730T004031Z      (status complete)
experiments/runs/mini_a5_f8_r19_member_step120_real_an29_20260730T004031Z  (status complete)
```

1,200 predictions each across four shards of 300, `image_mode: real`, git `f2e37629`.

**Comparability checks (all pass, verified by running code):**

| check | result |
|---|---|
| prompt contract identical across both layers and both arms | `answer-tags-v1`, sha256 `7ac39f53…` in all four cells |
| image condition identical | `real` in all four cells |
| checkpoint paths identical across layers | CP and member paths match the ranking config exactly |
| `pair_id` sets identical across all four cells | 1,200 = 1,200; zero asymmetric difference |
| `pair_id` → `template_id` map identical across all four cells | pass |

Because the `pair_id` sets and template maps coincide exactly, the two layers are joined
per-pair with no coverage loss. (The `pair_id` rekeying hazard recorded in
`reports/f8_eval_plan_v1.json` applies to R20, not to this R19 registry.)

### 1.4 Scoring severities, and an honest note on I7

I7 requires both a lenient and a contract-strict reading of every metric. **The ranking
scorer implements no lenient/strict contract axis at all** — the scored completion is the
frozen string `<answer>{verbatim gold}</answer>`, so contract validity is 100 % by
construction and there is no format for a teacher-forced candidate to violate. The
lenient/contract-strict pair named in the addendum (`pair_correct` /
`strict_pair_correct`) belongs to the *generation* scorer `src/eval/fliptrack_metrics.py`.

So both layers are reported at two severities, but the two axes are not the same thing and
are not presented as such:

| layer | lenient reading | strict reading |
|---|---|---|
| candidate-ranking | `pair_success` — both gold-vs-twin margins strictly > 0 (2-way discrimination on both sides) | `candidate_pair_top1` — gold outranks **all** candidates on both sides, ties resolved against gold |
| free-generation | `pair_correct` (I7 lenient) | `strict_pair_correct` (I7 contract-strict) |

The ranking pair is a **severity** pair, both registered in
`docs/registered_seed1_visual_evidence_ranking_v1.md` ("pair success requires both margins
to be strictly greater than zero"; "Ties do not count as top-1"; pair success primary,
candidate-set top-1 and MRR secondary). It is **not** a scoring-contract pair. This is a
gap in the instrument, stated rather than papered over.

Candidate-set size differs by template and sets the strict-ranking denominator: 14 for the
coordinate register, 16 for the header table, 9 for the nine-series trace.

### 1.5 Aggregation rule (I13)

The registry's 1,200 pairs span three templates holding three distinct scientific roles
(addendum §3), so nothing is pooled across them:

| template | n pairs | role per addendum §3 |
|---|---:|---|
| `coordinate_register_twenty_point_x_v02` | 600 | primary visual anchor |
| `header_cued_table_code_v02` | 300 | saturated positive control / retention canary |
| `starred_series_value_nine_v07` | 300 | oracle-localized readout control |

Counts verified against the registry: 600 / 300 / 300.

### 1.6 Interval procedure

Paired item bootstrap on `pair_id`, 10,000 draws, percentile 2.5 / 97.5, both compared
quantities resampled on identical indices per replicate; exact two-sided McNemar alongside.
Seeds are derived deterministically from the addendum's pinned base seed 20260729 as
`seed = 20260729 + 1000*indicator_index + 10*template_index`, fixed before any value was
read and recorded per cell in the output JSON. The McNemar implementation was checked
against `scipy.stats.binomtest` exact two-sided p-values on all 13 discordant-count pairs
appearing below: max absolute difference **5.6e-17**.

**These intervals quantify evaluation uncertainty on a fixed pair set. They do not estimate
run-to-run RL variance. Each arm is one run.**

### 1.7 Numbers

#### 1.7.1 Arm rates, per template, both layers, both severities

Ranking layer:

| template (role) | n | arm | `pair_success` (lenient) | `candidate_pair_top1` (strict) | mean paired margin |
|---|---:|---|---:|---:|---:|
| coordinate register (**primary anchor**) | 600 | CP | 0.9450 (567/600) | 0.4833 (290/600) | 0.9163 |
| | 600 | member | 0.9500 (570/600) | 0.4867 (292/600) | 1.2188 |
| header-cued table (positive control) | 300 | CP | 1.0000 (300/300) | 1.0000 (300/300) | 2.0568 |
| | 300 | member | 1.0000 (300/300) | 1.0000 (300/300) | 2.4190 |
| nine-series trace (readout control) | 300 | CP | 0.9333 (280/300) | 0.7033 (211/300) | 0.5057 |
| | 300 | member | 0.9167 (275/300) | 0.6567 (197/300) | 0.6520 |

Generation layer (the completed F8 primary cells, re-read on the same `pair_id` set):

| template (role) | n | arm | `pair_correct` (lenient) | `strict_pair_correct` (contract-strict) |
|---|---:|---|---:|---:|
| coordinate register (**primary anchor**) | 600 | CP | 0.4717 (283/600) | 0.4533 (272/600) |
| | 600 | member | 0.4817 (289/600) | 0.3833 (230/600) |
| header-cued table (positive control) | 300 | CP | 0.9233 (277/300) | 0.2200 (66/300) |
| | 300 | member | 0.9233 (277/300) | 0.2600 (78/300) |
| nine-series trace (readout control) | 300 | CP | 0.6667 (200/300) | 0.6200 (186/300) |
| | 300 | member | 0.5900 (177/300) | 0.5233 (157/300) |

#### 1.7.2 CP minus member, within each layer and severity

| template | layer / severity | CP − member | 95 % CI | excludes 0 | McNemar p | discordant (member-only / CP-only) |
|---|---|---:|---|---|---:|---|
| coordinate register | ranking / lenient | −0.0050 | [−0.0150, +0.0050] | no | 0.5078 | 6 / 3 |
| coordinate register | ranking / strict | −0.0033 | [−0.0233, +0.0167] | no | 0.8714 | 20 / 18 |
| coordinate register | generation / lenient | −0.0100 | [−0.0300, +0.0100] | no | 0.4050 | 21 / 15 |
| coordinate register | generation / contract-strict | **+0.0700** | [+0.0433, +0.0983] | **yes** | 1.397e-06 | 17 / 59 |
| header table | ranking / lenient | 0.0000 | [0.0000, 0.0000] | no | 1.0 | 0 / 0 |
| header table | ranking / strict | 0.0000 | [0.0000, 0.0000] | no | 1.0 | 0 / 0 |
| header table | generation / lenient | 0.0000 | [−0.0167, +0.0167] | no | 1.0 | 3 / 3 |
| header table | generation / contract-strict | **−0.0400** | [−0.0700, −0.0133] | **yes** | 0.01182 | 16 / 4 |
| nine-series trace | ranking / lenient | +0.0167 | [−0.0067, +0.0433] | no | 0.3018 | 5 / 10 |
| nine-series trace | ranking / strict | **+0.0467** | [+0.0067, +0.0867] | **yes** | 0.03355 | 12 / 26 |
| nine-series trace | generation / lenient | **+0.0767** | [+0.0300, +0.1233] | **yes** | 0.002667 | 16 / 39 |
| nine-series trace | generation / contract-strict | **+0.0967** | [+0.0467, +0.1467] | **yes** | 0.0003367 | 17 / 46 |

On the primary visual anchor the ranking layer separates the arms under neither severity;
the generation layer separates them under contract-strict scoring only. On the header table
the two generation severities disagree in sign (0.0000 lenient, −0.0400 strict). Per the
addendum, a disagreement between contracts is itself the result and is not resolved here.

#### 1.7.3 The endpoint contrast: ranking minus generation, within arm

Positive = the ranking layer scores higher than the generation layer on the same pairs.

| template | arm | severity | ranking − generation | 95 % CI | McNemar p | discordant (gen-only / rank-only) |
|---|---|---|---:|---|---:|---|
| coordinate register | CP | lenient | +0.4733 | [+0.4333, +0.5133] | 6.43e-86 | 0 / 284 |
| coordinate register | CP | strict | +0.0300 | [+0.0150, +0.0467] | 1.211e-04 | 2 / 20 |
| coordinate register | member | lenient | +0.4683 | [+0.4283, +0.5083] | 3.65e-83 | 1 / 282 |
| coordinate register | member | strict | +0.1033 | [+0.0783, +0.1283] | 3.56e-16 | 3 / 65 |
| header table | CP | lenient | +0.0767 | [+0.0500, +0.1067] | 2.384e-07 | 0 / 23 |
| header table | CP | strict | +0.7800 | [+0.7333, +0.8233] | 7.24e-71 | 0 / 234 |
| header table | member | lenient | +0.0767 | [+0.0467, +0.1067] | 2.384e-07 | 0 / 23 |
| header table | member | strict | +0.7400 | [+0.6900, +0.7867] | 2.97e-67 | 0 / 222 |
| nine-series trace | CP | lenient | +0.2667 | [+0.2167, +0.3167] | 3.43e-23 | 1 / 81 |
| nine-series trace | CP | strict | +0.0833 | [+0.0433, +0.1233] | 7.025e-05 | 7 / 32 |
| nine-series trace | member | lenient | +0.3267 | [+0.2733, +0.3800] | 6.31e-30 | 0 / 98 |
| nine-series trace | member | strict | +0.1333 | [+0.0900, +0.1800] | 2.29e-08 | 7 / 47 |

All twelve ranking−generation intervals exclude zero in the positive direction. The
comparison is between two different instruments on one pair set (teacher-forced scoring of
a frozen gold string vs sampled free generation through the prompt contract); the strict
readings on the two sides are not the same criterion, as §1.4 states.

**No decision branch fires from this endpoint.** The Mini-A5 decision rule is defined only
on the primary generation endpoint (addendum §4); this secondary carries no pre-committed
branch of its own, and the config records `automatic_branch_assignment: false`.

---

## 2. Secondary 2 — catch-trial stability (INSTRUMENT-ABSENT)

### 2.1 Confirmation that the existing script never loads a model

`scripts/audit_mini_a5_catch.py` (302 lines) was read in full. It is a data-integrity
audit. Verified by grep over the file **and over all four of its project-module imports**:
no `torch`, no `transformers`, no `Qwen`, no `from_pretrained`, no `vllm`, no `cuda`, no
checkpoint path. Its only matches for the substring `model` are the provenance-flag keys
`selection_on_model_performance` / `no_model_performance_selection`, which assert the
*negative*, plus one report line. Its imports are `argparse`, `json`, `os`,
`collections.Counter`, `pathlib`, `typing`, `PIL.Image`/`ImageChops`, plus
`scripts.audit_mini_a5_corpus`, `src.fliptrack.build_mini_a5_catch`,
`src.fliptrack.build_mini_a5_train`, `src.fliptrack.schema` — each grep-checked clean.

What it actually checks: 300 pairs and 100 per template; `answer_a` nonempty and
`answer_a == answer_b`; `target_fact_a/b` equal to the preserved answers; five verifier
booleans true (`answer_preserved`, `target_fact_preserved`, `target_region_pixel_invariant`,
`exact_by_construction`, `changed_mask_is_exact_pixel_diff`); `answer_pointing_cue` and
`selection_on_model_performance` explicitly false; registered template id and schema
version; target-region bounds inside 720×520; and — via `PIL.ImageChops.difference` on the
cropped target region — that the nuisance edit changes **no pixel** in the queried region.
Plus training/evaluation decontamination overlaps and artifact hashes.

Its own rendered markdown says so in as many words: *"This result establishes catch-set data
readiness only."*

**Conclusion: the audit certifies that the catch data is fit to be scored. It produces no
model behaviour, and therefore no stability measurement.**

### 2.2 A second, independent reason the instrument is absent

Even granting a generation harness, **no existing metric field equals the invariance
criterion.** `src/eval/fliptrack_metrics.pair_score` already handles equal-gold items
correctly for *correctness* — the P0.2 fix; `golds_equivalent` returns `True` on catch rows
and `acc_final` becomes "matches the single gold" instead of the structurally unsatisfiable
discriminative criterion. But its `collapsed` field, the only agreement indicator, is
**hard-suppressed to `False` on every equal-gold row** by construction:

```python
"collapsed": collapsed and normalize_text(row["answer_a"]) != normalize_text(row["answer_b"]),
```

Confirmed by running `pair_score` on catch-shaped rows (`answer_a = answer_b = "B9U"`)
under the registered contract:

| predictions | invariance criterion | `pair_correct` | `strict_pair_correct` | `collapsed` |
|---|---|---|---|---|
| `B9U` / `B9U` (agree, both right) | satisfied | True | True | **False** |
| `C1X` / `C1X` (agree, both wrong) | **satisfied** | False | False | **False** |
| `B9U` / `C1X` (disagree) | violated | False | False | **False** |

Row 2 is decisive: the invariance criterion is satisfied while every existing field reads
negative, and no existing field distinguishes row 2 from row 3. `collapsed` carries zero
information on catch pairs and must not be used as the stability indicator. Reusing
`pair_correct` as a proxy would silently measure accuracy, not stability.

### 2.3 The data that does exist

`data/mini_a5_catch_v1/` — audit `pass`, zero errors (`reports/mini_a5_catch_audit_v1.json`,
sha256 `37b9662c1f873c6b6cb7ee04a87a954dadef54ea974933c0e50e5ab8c60c2317`, which **matches
the hash pinned at `docs/registered_mini_a5_main_v1.md` line 31 exactly**).

| item | value |
|---|---|
| `pairs.jsonl` | 300 rows, sha256 `fbd83d52fa01103bfb839fa2572eb9164c532f8c3a3431da6ca8f6033d6a9728` |
| `decontamination.json` | `status: pass`, sha256 `19ed9a833665aead2aee1f4494279a26055c4f531fed68d3e3340af8a1a16bda` |
| images / masks | 600 / 600 |
| templates | `mini_a5_catch_distractor_matrix_v1` 100, `..._scatter_v1` 100, `..._trajectory_v1` 100 |
| nuisance side assignment | swapped on 153, unswapped on 147 |
| equal-gold rows | **300 of 300** — verified `answer_a == answer_b` on every row |
| decontamination overlap vs training and all 3 evaluation manifests | 0 template ids, 0 pair ids, 0 image hashes |

Per-row fields available: `pair_group_uid`, `question`, `image_a_path`, `image_b_path`,
`image_a_sha256`, `image_b_sha256`, `answer_a`, `answer_b`, `template_id`, `category`,
`changed_region_mask_a/b`, `mask_sha256`, `catch_twin_id`, `parent_group_uid`, `provenance`,
`verifier_results` (including `target_region_xyxy` and `changed_distractor_cells`).

### 2.4 What a scorer would need — specification only (NOT BUILT)

**Inputs**

1. `data/mini_a5_catch_v1/pairs.jsonl` (300 rows) and its `images/`, pinned by the two
   hashes above. Read-only.
2. Both arms at step 120 — the same two checkpoints and index hashes used in §1.2.
3. The generation harness `scripts/eval_qwen_vl_fliptrack.py`, which reads exactly
   `pair_id`, `question`, `image_a_path`, `image_b_path` per row (and `answer_a`/`answer_b`
   for its inline scoring). **One adapter step is required: the catch set keys its rows
   `pair_group_uid`, and the harness reads `pair_id`.** Every other required field is
   already present under the name the harness expects.
4. Prompt contract `answer-tags-v1` (sha256 `7ac39f53…`), the frozen processor artifact
   `bb6a1bfd…c81544`, and `image_mode: real`, to match §1.3 and every other Mini-A5 cell.
5. Decoding settings recorded verbatim from the F8 generation cells, so catch numbers sit
   on the same generation regime.

**The invariance criterion — the field that must be added.** The criterion is
*self-consistency under a non-queried visual change*: the model's own answer on member A
equals its own answer on member B, i.e.

```
normalize_text(extracted_answer_a) == normalize_text(extracted_answer_b)
```

evaluated **regardless of whether either matches the gold**, and **not** gated on
`answer_a != answer_b`. This is the field that does not exist today (§2.2). It is
derivable post-hoc from the `extracted_answer_a` / `extracted_answer_b` fields the harness
already emits per row, so no change to `pair_score` itself is strictly required.

Both severities must be reported (I7):

- **lenient (stability):** the equality above.
- **contract-strict (stability):** the same equality **and**
  `contract_valid_a and contract_valid_b`, so a pair whose members agree only because both
  fell out of contract does not count as stable.

Stability and correctness must stay separable, because the two members share one gold:

| model behaviour | stability | correctness |
|---|---|---|
| same answer, matches gold | holds | holds |
| same answer, wrong | **holds** | fails |
| different answers | **fails** | fails (at least one side) |

**Outputs a scorer should write**

- Per row: `pair_group_uid`, `template_id`, `prediction_a/b`, `extracted_answer_a/b`,
  `stable_lenient`, `stable_strict`, `correct_a`, `correct_b`, `pair_correct`,
  `strict_pair_correct`, `contract_valid_a/b`, `parser_version`.
- Per template (100 pairs each; **never pooled — three templates, and their roles within
  the catch design are not established anywhere, so pooling is unjustified under I13**):
  stability rate, correctness rate, and the joint "stable and correct" rate, each at both
  severities.
- CP minus member per template per indicator: paired item bootstrap on `pair_group_uid`,
  10,000 draws, percentile 2.5/97.5, both arms on identical indices, plus exact two-sided
  McNemar — the §1.6 procedure with the seed derivation extended to the new indicators.
- A run manifest matching the schema the other cells use, carrying both checkpoint index
  hashes and both catch artifact hashes.

**Missing pieces, exhaustively:** (i) the `pair_group_uid` → `pair_id` manifest adapter;
(ii) an aggregation/readout script computing the stability indicators and the per-template
tables; (iii) a registration fixing the seed, the alpha and the per-template reporting
before any value is read. Nothing else — the generation harness, the equal-gold correctness
metric and the data are all in place and verified.

**Cost estimate.** 300 pairs × 2 members = 600 generations per arm, 1,200 total — roughly
half the load of one F8 R19 arm pair, one GPU per arm.

**This scorer was not built.** The endpoint is reported as **instrument-absent** per
addendum §6.2, is not silently dropped, and **no number for it appears in this report.**

---

## 3. Secondary 3 — "the registered task benchmark" (UNRESOLVABLE)

### 3.1 The phrase is bound to nothing

`git grep` over all tracked files for `registered task benchmark` returns five hits, of
which exactly **one** is a binding use:

| file:line | nature |
|---|---|
| `docs/registered_mini_a5_main_v1.md:92` | **the only binding use** — the registration sentence itself |
| `docs/registered_mini_a5_endpoint_readout_v1.md:107` | self-referential: the addendum discussing the phrase |
| `reports/f8_eval_plan_v1.json:127` | self-referential: the F8 plan echoing the addendum |
| `reports/f8_mini_a5_endpoint_readout_v1.json:1215` | self-referential: the F8 readout echoing the addendum |
| `reports/f8_mini_a5_endpoint_readout_v1.md:217` | self-referential: same, rendered |

The registration sentence reads: *"Secondary: catch-trial stability; **the registered task
benchmark**; free-generation versus candidate-ranking diagnostics under the existing
registered ranking instrument."*

(The addendum's literal wording "occurs exactly once in the repo" was true of binding uses
when written; the raw count is now five because the addendum, the plan and the F8 readout
quote it. The substance is unchanged: one binding use, zero referents.)

The phrase names **no dataset file, no manifest, no config key, no script, and no benchmark
id.** There is no "Immutable inputs" row for it in the registration — that table pins
training-side artifacts only. The word "benchmark" appears **zero times** in
`PAPER1_RESEARCH_DOC.md` and `PAPER2_RESEARCH_DOC.md`, so no upstream registration binds it
either.

### 3.2 The training configs evaluate no benchmark

Verified in both registered main configs, at the exact sha256 the registration pins
(`8d7736f5…c325e8` and `358e6d7c…a0fcd9b`, both matching):

```
val_freq: 0
val_before_train: false
val_only: false
val_generations_to_log: 0
val_files: data/mini_a5_plumbing_val_v1.jsonl
```

`val_freq: 0` with `val_before_train: false` means **no validation pass ever ran** during
either arm. And `val_files` does not point at a benchmark: it is
`data/mini_a5_plumbing_val_v1.jsonl`, 48 rows with fields
`answer, category, images, pair_group_uid, pair_member, problem, template_id` — a plumbing
smoke fixture from the Mini-A5 corpus itself, never consumed, and not named by the
registration. It does not bind the phrase.

There is therefore no training-side benchmark reading to recover, and no evaluation-side
artifact the phrase points at.

### 3.3 Nearest convention referent, named but NOT adopted

By project convention the nearest referent is **Geometry3K** — 443 tracked files mention
`geo3k`/`geometry3k`, including 15 training configs (`anchor_a0_recipe_3b_geo3k.yaml`, the
`mech_a{1,2,2b,3}_*_3b_geo3k.yaml` family and its seed-2/seed-3 twins) and a large family
of evaluation queue configs (`configs/eval/m2_a2_geo3k_step100_queue_v*.json`,
`configs/eval/m3_seed{2,3}_*_geo3k_queue_v1.json`).

**It is not adopted here, and two verified facts argue against adopting it silently:**

1. The addendum (§6.3) explicitly declines to make that choice, and this report has no
   standing to make it either — doing so after the arms are trained and the primary values
   read would be exactly the post-hoc latitude the addendum was filed to remove.
2. Geometry3K is not neutral for Mini-A5. Verified from the configs: the arms that
   establish the convention **train on** Geometry3K (`anchor_a0_recipe_3b_geo3k.yaml` →
   `train_files: hiyouga/geometry3k@train`; `mech_a1_real_3b_geo3k.yaml` →
   `train_files: data/geo3k_pilot_filtered.jsonl`), whereas the Mini-A5 arms train on
   `data/mini_a5_train_v1/train.parquet` and never on Geometry3K. Reading Geometry3K on
   them would be an out-of-domain transfer measurement, not the in-domain "task benchmark"
   the phrase appears to intend. That is a substantive scientific choice, not a default.

**Reported as unresolvable from the registration.** Resolving it requires an amendment that
names a dataset file, a scoring contract and an interval procedure — a registration act,
not an analysis step.

---

## 4. Checks

| # | check | result |
|---|---|---|
| C1 | an29 idle before launch and at readout; F8 primary complete; no contention | PASS — 8/8 GPUs at 2 MiB, 0 compute apps |
| C2 | an12 GPUs 0-3 (M7 arm 1) untouched | PASS — an12 never allocated; only an29:4 and an29:5 |
| C3 | launcher preflight: config + registration + registry tracked and clean | PASS |
| C4 | checkpoint `model.safetensors.index.json` sha256 matches config, both arms | PASS |
| C5 | candidate registry sha256 matches config | PASS `fa945694…` |
| C6 | registry `source_manifest_sha256` == locked R19 manifest | PASS `e1dde984…` |
| C7 | processor artifact + prompt contract sha256 match config | PASS `bb6a1bfd…` / `7ac39f53…` |
| C8 | registration commit and run git hash are ancestors of HEAD | PASS `a0ff9d5`, `b0b316d` |
| C9 | both ranking manifests `status=complete`, `exit_code=0`, 1,200 rows | PASS |
| C10 | `scores.jsonl` sha256 on disk == value each run printed | PASS, both arms |
| C11 | `pair_success` recomputed from raw `margin_a`/`margin_b` | PASS — matches stored field on all 1,200 rows, both arms |
| C12 | `global_step` / `condition` / `model_key` single-valued per cell | PASS — 120 / `real` / own arm |
| C13 | all four cells share one `pair_id` set; template map agrees | PASS 1,200 = 1,200, zero asymmetric difference |
| C14 | template counts match addendum §3 roles | PASS 600 / 300 / 300 |
| C15 | generation-layer rates match published `reports/f8_mini_a5_endpoint_readout_v1.md` | PASS — 0.4817/0.4717 lenient, 0.3833/0.4533 strict on the anchor |
| C16 | `audit_mini_a5_catch.py` never instantiates a model, incl. all 4 transitive imports | PASS |
| C17 | catch audit report hash matches the registration pin | PASS `37b9662c…` |
| C18 | catch set is equal-gold on all rows | PASS 300/300 |
| C19 | `collapsed` is uninformative on equal-gold rows | CONFIRMED by running the metric — `False` in all three cases, including the agreeing-but-wrong one |
| C20 | "registered task benchmark" bound to no artifact | PASS — 1 binding occurrence, 4 self-references, 0 referents |
| C21 | Mini-A5 training ran no validation | PASS `val_freq: 0`, `val_before_train: false`, config hashes match registration |
| C22 | "benchmark" absent from PAPER1/PAPER2 research docs | PASS — 0 occurrences |
| C23 | McNemar implementation correct | PASS — matches `scipy.stats.binomtest` exact two-sided p on all 13 cells, max diff 5.6e-17 |
| C24 | R19/R20 never modified or regenerated (I11) | PASS — read-only throughout |

## 5. Artifacts

| path | content |
|---|---|
| `reports/f8_secondaries_v1.md` | this document |
| `reports/mini_a5_s1_ranking_vs_generation_v1.json` | machine-readable §1.7 with every resolved seed (schema `blind-gains.mini-a5-secondary1-ranking-vs-generation.v1`) |
| `configs/eval/mini_a5_visual_evidence_ranking_v1.json` | ranking config for the two arms (committed `b0b316d`) |
| `scripts/analyze_mini_a5_s1.py` | the §1.7 analysis |
| `experiments/runs/mini_a5_s1_ranking_cp_step120_real_an29_gpu4_20260730T011842Z/` | CP ranking cell: `scores.jsonl`, `run_manifest.json`, `worker.sh`, `logs/` |
| `experiments/runs/mini_a5_s1_ranking_member_step120_real_an29_gpu5_20260730T011842Z/` | member ranking cell, same layout |

## 6. Deviations and limits

1. **Launcher allowlist widened.** One regex line in
   `scripts/launch_visual_evidence_ranking_cell.sh` now admits the two Mini-A5 model keys
   (`git show b0b316d`: 1 insertion, 1 deletion). No gate, hash check, scoring rule or
   contract was altered. Unlike `scripts/launch_fliptrack_eval_shards.sh`, this launcher is
   not a named M5 contract file and is not git-diff-gated.
2. **Bootstrap seeds are derived, not individually pinned.** The addendum pins base seed
   20260729 for the primary and enumerates no seeds for this secondary. The §1.6 derivation
   was fixed before any value was read and every resolved seed is recorded in the output
   JSON. The primary anchor's lenient ranking cell uses exactly `20260729`.
3. **One consequence of (2), disclosed rather than reconciled away.** The generation
   contract-strict CP−member interval on the anchor is `[+0.0433, +0.0983]` here against
   `[+0.0417, +0.0983]` in `reports/mini_a5_f8_r19_paired_comparison_v1.json`, which used
   seed `20260729` directly. Point estimate (+0.0700), McNemar p (1.3969e-06) and
   discordant counts (17 / 59) are identical. The lower bound differs by 0.001667 = exactly
   one pair out of 600, i.e. one percentile step of bootstrap granularity. No conclusion
   changes.
4. **The within-arm ranking-vs-generation contrast shares one seed between the two arms**
   at a given template and severity, so both arms are resampled on the same indices. This
   is deliberate, for comparability.
5. **One condition only.** Only `real` was run. The instrument supports five image
   conditions; the registered secondary names none, and the other four (`gray`, `no_image`,
   `mismatched_real`, `twin_counterfactual`) answer a different question than
   free-generation-vs-ranking. They remain available and unrun.
6. **Single seed per arm.** Each arm is one training run. No interval here estimates
   run-to-run RL variance.
7. **A frozen base-model ranking cell exists** on this exact registry under
   `experiments/runs/d1_visual_evidence_*base*`. It was **not** adopted: the registered
   secondary contrasts CP against member and ranking against generation, and introducing an
   untrained third arm is not part of it.
8. **The generation-layer cells carry weaker provenance than the ranking cells.** Their
   `run_manifest.json` records `global_step: null`, `model_key: null`, `condition: null` and
   `exit_code: null` (a different manifest schema; `status: complete`), because the Mini-A5
   job type has no binding branch in the FlipTrack launcher (documented in
   `reports/f8_eval_plan_v1.json` → `launcher_has_no_mini_a5_binding_branch`). The
   checkpoint identity of those cells rests on `model_path`, verified here to equal the
   paths in §1.2. The ranking cells record `global_step` and `model_index_sha256` directly.
9. **I7 is satisfied for the generation layer and only partially for the ranking layer**,
   because the ranking scorer implements no scoring-contract axis (§1.4). Two severities are
   reported for it; they are not a lenient/contract-strict pair and are not labelled as one.
10. **Two of the three registered secondaries produced no number.** §2 is instrument-absent
    and §3 is unresolvable. Neither was replaced by a proxy.
