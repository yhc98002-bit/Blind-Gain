# Registered: Track-4 premise-construct v2 — design registration (v1)

Registered 2026-08-06, **before any v2 item is generated and before any
acceptance eval runs**. This is the design response to two fired branches:

- **P0.1 branch (b)** (`docs/registered_b1_premise_probe_v1.md`,
  `reports/p01_premise_probe_v1.json`): the chained-premise floor is
  uninformative and the construct needs redesign before it can carry a
  Paper-2 claim. Base numbers on the 20 B1 `chained_premise` pairs: premise
  member accuracy **0.275**, final member accuracy 0.150, final pair accuracy
  0.000, reasoning-given-correct-premise 0.273 (denominator 11).
- **Gate-1 / Mini-A5 branch 2** (`PAPER2_RESEARCH_DOC.md` §6): the primary
  anchor stayed flat, so the premise-first redesign (C3 before C2) is the
  active Paper-2 branch. Track 4 (§4 Layer B) is the construct that carries it.

Scope locks: **no training configs are authorized by this registration**;
generation is capped at development scale per P1.4 (100–300 groups); GPU
acceptance evals are registered here (commands + pass criteria) but run
separately by the orchestrator. Registration precedes the batch build (I9
discipline; there is no optimizer step anywhere in this phase).

---

## 1. The two defects this design removes

**(D1) B1's `chained_premise` cannot express a premise transition.**
In `scripts/build_b1_geometry_track_prototype.py`, the candidate filter for the
moved nearest neighbour requires
`math.hypot(x - target.x, y_N - target.y) < d2 - 0.5` — the moved point is
*constrained to stay nearest*. Premise invariance is baked into the geometry;
the trailing `nn_label_b != nn_label` rejection is belt-and-braces, not the
mechanism. Consequently `premise_transition_accuracy` in
`scripts/build_p01_premise_readout.py` (which rescores the probe with **equal
golds** on both members, line ~76) *measures invariance* — it credits a model
for producing the **same** premise on both members. A genuine transition type
needs the **opposite geometric constraint**, not a flipped conditional.

**(D2) The construct sits below the learnable zone at 3B.** Base premise member
accuracy 0.275 (P0.1). A development batch must include an easier premise
variant with a registered target band before Phase-2 curriculum design can even
be discussed.

---

## 2. `premise_transition` item type — geometric construction

Scene: `n` labelled points on the frozen coordinate register (canvas 1400×1240,
grid −7..7, Chebyshev spacing ≥ 2). For a target `T`, rank the other points by
Euclidean distance: nearest `N` at `d1`, runner-up `M` at `d2`, third `P3` at
`d3`.

**The constraint inversion, stated precisely.**

| | B1 `chained_premise` (frozen) | v2 `premise_transition` |
|---|---|---|
| move | `N → N'` with `dist(T, N') < d2 − 0.5` | `N → N'` with `dist(T, N') ≥ d2 + 1.0` |
| effect | `N` **stays** nearest; premise fixed | `M` **becomes** nearest; premise changes `N → M` |
| final gold pair | `x(N)` vs `x(N')` (same point, moved) | `x(N)` vs `x(M)` (two different, unmoved-on-B points) |

The inversion is *geometric* — the moved point crosses to the far side of the
`d2` boundary with margin — never a flipped `if` on the invariance filter.

**Margins and guards (all enforced by construction, all recomputable from the
stored scene programs):**

- **G1 — A-side decidability:** `d2 − d1 ≥ 1.0` (`MARGIN_A`, retained from B1).
- **G2 — B-side ambiguity margin, mirroring G1:** after the move the B-side
  nearest is `M` at `d2` and the runner-up is `min(d3, dist(T, N'))`. Two
  constraints jointly guarantee `min(d3, dist(T, N')) − d2 ≥ 1.0`:
  `d3 − d2 ≥ 1.0` (`MARGIN_D3`) and `dist(T, N') ≥ d2 + 1.0` (`MARGIN_B`).
  A belt-and-braces recheck on the realized B-side ranking (nearest is `M`,
  margin ≥ `MARGIN_B`) rejects any residual case.
- **G3 — final-answer distinguishability:** the golds are `x(N)` and `x(M)`,
  read from two *different* points, so B1's moved-point delta guard
  (`|Δx| ≥ 3`) does not apply to the gold pair. The guard is
  `_answers_distinguishable(gold_a, gold_b)` under the frozen lenient matcher
  (`match_tier == 0` in both directions) — the scorer-aligned criterion.
- **G4 — premise-gold distinguishability:**
  `_answers_distinguishable(label(N), label(M))`.
- **G5 — degeneracy guards:** `N'` must satisfy `x ≠ 0` (off-axis),
  `|x − x_N| ≥ 3` (visible move), spacing ≥ 2 from all other points; the scene
  needs ≥ 3 non-target points; distance ties at `d1/d2/d3` are rejected by
  G1/G2; the rendered pair must have a non-empty exact pixel-change mask.
- **G6 — the runner-up `M` never moves:** `x(M)` is readable at the same
  location on both members. The final-answer change is carried *entirely* by
  the premise change — which is the construct's point: answering B correctly
  requires re-deriving the premise, not tracking a moved patch.

## 3. Per-member premise golds

`premise_answer` was a single scalar shared by both members in B1 (equal-gold
by construction). v2 replaces it:

- **pair rows** carry `premise_answer_a` / `premise_answer_b`, assigned to
  *physical* sides — when the 50% side swap fires, premise golds, final golds
  and the serialized scene programs (`scene_points_a/b`) all swap together, so
  every gold on every row is recomputable from the scene points stored beside
  it (fixture-enforced).
- **group records** (schema v2, §6) carry semantic sides: the original's
  `premise_answer`, and per-member `premise_answer` plus a boolean
  `premise_transition` flag on the causal member that the loader checks against
  the golds.
- `chained_premise` items keep equal premise golds (`transition = false`);
  `fact_read` items carry no premise fields at all. Half-specified premise
  metadata fails closed in the loader.

## 4. The redefined premise-transition metric

For a transition item with premise golds `(g_A, g_B)`, `g_A ≠ g_B` by
construction:

```
transition_correct = [extract(premise response on A) ≍ g_A]
                 AND [extract(premise response on B) ≍ g_B]
```

with `≍` the frozen lenient matcher; the strict variant uses contract-strict
extraction. **Both are reported (I7).** Cell-level premise-transition accuracy
is the mean over transition items. The correct premise must be produced **on
each member**, and the premise **changes as constructed** — a premise-frozen
policy (same premise on both members) scores exactly zero.

Operationally: `transition_correct` equals `pair_correct` of the derived
premise-probe row under the P0.2-fixed scorer, because the probe row carries
*differing* golds and therefore takes the discriminative two-gold branch. No
new scorer is introduced.

The old P0.1 quantity (same premise on both members, scored equal-gold) remains
defined **only for chained items** and is renamed **`premise_stability`**. It
is an invariance reading. `premise_stability` and `premise_transition_accuracy`
are never aggregated with each other or across item types (I13), and the
Track-4 five-number profile (premise accuracy, reasoning|correct-premise,
final member accuracy, final pair accuracy, transition/stability) continues to
be reported as separate numbers.

**Adversarial fixture (I10)** — `tests/test_track4_premise_v2_generator.py`:
a premise-frozen prediction earns credit under the old definition and zero
under the new one; a genuinely tracking prediction earns zero under the old
and credit under the new; and the planted transition pair *violates* B1's
stay-nearest filter, proving the frozen builder could never emit it.

## 5. Easier premise variant — the difficulty lever

**Lever: `n_points` (label count), 20 → 8.** Verified against
`src/fliptrack/build_v02.py`: `_sample_high_entropy_points(rng, count)`
parameterizes the point count, and `_render_high_entropy_coordinate_register`
draws exactly the dict it is given; font size (19 px bold labels), marker
radius, canvas, grid and the Chebyshev spacing floor (2) are all hardcoded.
Label count is therefore the **only** difficulty lever the frozen renderer
already parameterizes — the easy variant changes nothing else. (Font scale and
point spacing would require new renderer code and are rejected for that
reason.)

Why this lever should move premise accuracy: the premise failure is a
search/binding failure over 20 labels (P0.1; F2d's layer selectivity), and
`n_points` directly scales the search set (19 → 7 distractors) without touching
the premise semantics, the question text, or the metric target.

**Target band: base premise member accuracy ∈ [0.40, 0.60] on
`chained_premise_easy`** (primary carrier; anchor point 0.275 at n=20).
`premise_transition_easy` is read against the same band as a secondary,
reported number. The n=20 types are reported descriptively with no band.

**How it is measured before any training config exists:** the registered
difficulty-band eval E1 (§7) — base Qwen2.5-VL-3B, greedy, `answer-tags-v1`
contract, `max_new_tokens 32`, real images, over the derived premise-probe
manifest. Identical decoding lock to every FlipTrack eval (I7). No training
config may cite this batch until E1–E4 have run and pass.

**Registered branches and pre-committed responses:**

- **(a) band hit** (0.40 ≤ acc ≤ 0.60): `n=8` is frozen as the Phase-2
  curriculum entry difficulty. No further lever moves.
- **(b) too easy** (acc > 0.60): one pre-committed step to `n=12`; one fresh
  40-group easy tranche built under identical registered constraints from
  unused development-bucket scenes; **one** re-measure. No other knob moves.
- **(c) still too hard** (acc < 0.40): one pre-committed step to `n=5` (the
  minimum at which the premise remains a genuine 4-distractor search); same
  single re-measure discipline.
- **(d) the single re-measure also misses:** the label-count lever is declared
  insufficient for this construct. Escalate to the PAPER2 §6 premise-first
  redesign (simpler premise curriculum or a small verified warm start, which
  mandates the SFT+standard-GRPO comparator, I16). The miss is reported as a
  result; there is no further iteration on this batch.

## 6. Schema v2 — `blind-gains.intervention-group.v2`

`src/train/intervention_group_schema.py` gains an **additive** v2 validator;
the v1 validator is the frozen P0.3 artifact and is byte-untouched. Field spec
on top of v1:

| field | rule |
|---|---|
| `schema_version` | must equal `blind-gains.intervention-group.v2`; the v2 loader refuses any other version, and the v1 loader (unchanged) refuses v2 — mutual, total refusal (I15) |
| `intervention_type` | **required** non-empty string at group level |
| `premise` | optional `{question}`; when present the premise rules below become mandatory |
| `original.premise_answer` | required non-empty in premise groups |
| causal member `premise_answer` | required non-empty in premise groups |
| causal member `premise_transition` | required **boolean**; must agree with `premise_answer != original.premise_answer` (normalized) — a lying flag fails closed |
| invariance member `premise_answer` | required; must **equal** the original's — a premise-moving twin is a causal intervention mislabelled as a control |
| negative controls | must **not** carry premise fields; `no_image` must not carry an image; `mismatched_real` must carry one; `gray`/`caption` carry path+sha together or neither |
| `blind_solvability.measurement_state` | required, `pending` \| `measured`. `pending` ⇒ `q_real`/`q_blind`/`delta_q` all null (I14 makes blind solvability an acceptance *measurement*, never a build-time guess). `measured` ⇒ probabilities + `delta_q` consistency. The training path calls `validate_*_v2(..., require_measured=True)` and **refuses pending groups**, so an unmeasured group can never reach an optimizer step |
| non-premise groups | any stray `premise_answer`/`premise_transition` on the original or a member fails closed |

Loader fixture: `tests/test_intervention_group_schema_v2.py` (28 cases,
including cross-version refusal in both directions and every premise rule
above). The generator fixture additionally proves the v1 loader refuses a
*real* generated v2 group.

## 7. Acceptance gates (I14) — registered commands and pass criteria

The track is unusable for training or release reporting until all four gates
run and pass. All four need GPU inference (~hours on 1 GPU); **they are not run
in this round**. The orchestrator should run, per the project's guarded
free-GPU discipline (never colocated with a 7B offload trainer):

Let `ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain`,
`BASE=artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct`,
`DATA=data/track4_premise_v2_dev_v1`, run dirs under `experiments/runs/` with
logs, node, git hash and command recorded per operational defaults.

**E1 — difficulty band** (1 GPU; drives §5 branches):

```
python scripts/eval_qwen_vl_fliptrack.py --model-path $BASE \
  --manifest $DATA/manifest_premise_probe.jsonl \
  --output experiments/runs/<RUN>/premise_probe/predictions.jsonl \
  --metrics-output experiments/runs/<RUN>/premise_probe/metrics.json \
  --image-mode real --seed 0 --noise-seed 0 --max-new-tokens 32
python scripts/eval_qwen_vl_fliptrack.py --model-path $BASE \
  --manifest $DATA/manifest_causal_pairs.jsonl \
  --output experiments/runs/<RUN>/final/predictions.jsonl \
  --metrics-output experiments/runs/<RUN>/final/metrics.json \
  --image-mode real --seed 0 --noise-seed 0 --max-new-tokens 32
```

Readout: per-intervention-type premise member accuracy (probe run) and final
member/pair accuracy (causal run), lenient + strict (I7), no aggregation
across types (I13). Pass: `chained_premise_easy` premise member accuracy in
[0.40, 0.60] (else §5 branches fire).

**E2 — blind floor** (1 GPU): repeat both E1 commands with
`--image-mode no_image` and `--image-mode gray` (four runs). Pass, per type:
blind (no_image and gray) **final** member accuracy ≤ 0.133 (2× the 1/15
uniform-x chance) and blind **premise** member accuracy ≤ 2×`1/(n_points−1)`
(n=20: ≤ 0.105; n=8: ≤ 0.286), on lenient scoring. Fail ⇒ the failing type is
excluded from any training use; the blind-solvable `pair_id`s are reported; no
silent regeneration. E1+E2 predictions also fill per-group
`q_real`/`q_blind` and flip `measurement_state` to `measured` via a rescore
script — until then the training loader refuses every group by schema.

**E3 — caption stress** (1 GPU): caption the dev-batch images with the
project's standard captioner via
`scripts/launch_caption_store_shards.sh <node> 0 <shards> artifacts/models/Qwen/Qwen2.5-VL-7B-Instruct $DATA/images <run_dir>`,
merge, build QA rows (`scripts/build_caption_qa_pairs.py`), then
`scripts/eval_caption_qa_fliptrack.py --model-path $BASE --input <qa.jsonl> --output ... --max-new-tokens 32`.
Pass, per type: caption member accuracy ≤ blind-floor threshold + 0.10
absolute. Fail ⇒ the track is caption-leaky: eval-only until revised.

**E4 — attacker check** (1 GPU):
`bash scripts/launch_artifact_gate_v02.sh <node> <gpu> $DATA/attacker_release $DATA/attacker_key.jsonl reports/track4_premise_v2_attacker_gate_v1.json`
(DINOv2 + pixel-statistic attackers over the packaged causal-pair release).
Pass: every attacker's side-prediction accuracy 95% bootstrap CI includes 0.5.
Fail ⇒ batch quarantined to eval-only; artifact source diagnosed before any
regeneration.

## 8. Development batch composition (P1.4: one declared batch, 160 groups)

| intervention type | groups | n_points | template_id | role |
|---|---|---|---|---|
| `premise_transition` | 40 | 20 | `t4v2_coordinate_register_n20_v1` | the new construct, reference difficulty |
| `premise_transition_easy` | 40 | 8 | `t4v2_coordinate_register_n8_v1` | new construct × easier lever |
| `chained_premise_easy` | 40 | 8 | `t4v2_coordinate_register_n8_v1` | easier variant carrying the §5 band |
| `chained_premise` | 20 | 20 | `t4v2_coordinate_register_n20_v1` | frozen-construction control (anchors against P0.1's 0.275) |
| `fact_read` | 20 | 20 | `t4v2_coordinate_register_n20_v1` | reading control (no premise) |

Every group: original + causal member + one invariance member (style twin or
answer-and-premise-preserving distractor move, alternating) + `no_image` +
`gray` + `mismatched_real` controls (donor: the next group's original within
the same type, cyclic). Builder:
`scripts/build_track4_premise_v2_dev_batch.py`, `BATCH_SEED = 20260806`,
attempt-indexed per-item seeds, one-shot, refuses to overwrite. Outputs under
`data/track4_premise_v2_dev_v1/`: `manifest_causal_pairs.jsonl`,
`manifest_invariance_pairs.jsonl`, `manifest_premise_probe.jsonl` (140 rows —
every type except `fact_read`), `groups_v2.jsonl` (160 validated v2 groups,
`measurement_state: pending`), `attacker_release/` + `attacker_key.jsonl`, and
the shared gray-control image. Build report with per-file SHA-256, node, git
hash, command and attempt counts: `reports/track4_premise_v2_dev_build_v1.json`.
The build fails closed on any image-SHA collision with the frozen B1 corpus.

**One-shot discipline:** no acceptance iteration. If a type exhausts its
declared attempt cap (3000× its count), that is a reportable build failure;
the single pre-committed mechanical response is a rebuild with the cap doubled
(attempt-indexed seeding keeps all surviving items identical). Nothing else
about the constraints may change without a new registration.

## 9. Three-way program-level split (I6 / P1.7)

Rule, registered now for **all** future Track-4 v2 builders (training,
development, confirmatory):

```
bucket(spid) = int(sha256(spid + "|split-v1").hexdigest()[:8], 16) % 100
training      : bucket in [0, 60)
development   : bucket in [60, 80)
confirmatory  : bucket in [80, 100)
```

where `spid = "t4v2_" + sha256("t4v2|" + canonical_points_json)[:16]` is the
scene-program id. Enforcement is structural, not procedural: **this builder
rejects every scene outside the development bucket**, so no program generated
here can ever collide with a training or confirmatory program; the future
training/confirmatory builders must use the identical hash string and their
own bucket. The split is by scene program and template family
(`t4v2_coordinate_register`), never a random item split. R19, R20 and the
frozen B1 batch are outside the `t4v2_` namespace and are additionally
protected by the build-time image-SHA disjointness check; none of the three is
ever trained on.

## 10. Explicitly not authorized by this registration

Training configs of any kind; generation beyond the 160 declared groups;
running E1–E4 (GPU) in the build round; any edit to the frozen B1 builder,
its corpus, R19, R20, or the v1 schema validator; aggregation across item
types or across the stability/transition metrics.

## 11. Provenance

- Design + this registration: `docs/registered_track4_premise_v2_design_v1.md`
- Schema v2: `src/train/intervention_group_schema.py`
  (`SCHEMA_VERSION_V2`, `validate_group_v2`, `validate_batch_v2`);
  fixtures `tests/test_intervention_group_schema_v2.py`
- Generator: `scripts/build_track4_premise_v2_dev_batch.py`;
  fixtures `tests/test_track4_premise_v2_generator.py`
- Invariants exercised: I5, I6, I7, I10, I13, I14, I15 (I9 vacuously — no
  optimizer step exists in this phase)
- Anchoring evidence: `reports/p01_premise_probe_v1.json` (cells.base),
  `reports/f8_mini_a5_endpoint_readout_v1.*` (branch 2),
  `scripts/build_b1_geometry_track_prototype.py` (frozen constraint, D1)
