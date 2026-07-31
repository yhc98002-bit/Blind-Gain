# Registered: Mini-A5 catch-trial stability (secondary 2) — instrument + readout (v1)

**Written:** 2026-07-31. **Branch:** `agent/gate2-recovery`.
**Status:** registration of an instrument for an already-registered endpoint.
**Sealed (I9):** the catch-stability eval launches only AFTER this document and
the instrument files it pins are merged. No value from either arm is read
before then.

## 0. What this registration is, and is not

The endpoint "catch-trial stability" was registered in the MAIN Mini-A5
registration (`docs/registered_mini_a5_main_v1.md` line 92: *"Secondary:
catch-trial stability; …"*) and was reported **instrument-absent** in the F8
secondaries readout (`reports/f8_secondaries_v1.md` §2, per the addendum
`docs/registered_mini_a5_endpoint_readout_v1.md` §6.2: no scorer that loads a
model existed, and no existing metric field equals the invariance criterion).
This registration supplies the missing instrument, exactly as §2.4 of that
report specifies, and fixes every analysis choice before any value is read.

**The F8 primary readout is already published**
(`reports/f8_mini_a5_endpoint_readout_v1.md`; branch decision fired). **This
secondary cannot alter it.** It fills the registered-but-uninstrumented gap; it
does not reopen the branch decision, and no decision branch of any kind is
attached to it (`automatic_branch_assignment: false`). Output is numbers and
provenance per template at both severities — never interpretation.

## 1. The endpoint

Self-consistency under a non-queried visual change, on the 300-pair Mini-A5
catch set (all pairs equal-gold by construction). The invariance criterion —
the field that did not exist before this instrument (f8_secondaries §2.2) — is

```
stable_lenient := normalize_text(extracted_answer_a) == normalize_text(extracted_answer_b)
```

evaluated **regardless of gold** and **not** gated on `answer_a != answer_b`
(the gate that hard-suppresses the pre-existing `collapsed` field to `False` on
every equal-gold row). Both severities are reported (I7):

- **lenient**: the equality above;
- **contract-strict**: the equality AND `contract_valid_a` AND
  `contract_valid_b` — a pair whose members agree only because both fell out of
  contract is not strict-stable.

Correctness stays separable from stability (both members share one gold):
`correct_a`/`correct_b` use the P0.2-fixed equal-gold path in
`src/eval/fliptrack_metrics.pair_score` (`golds_equivalent` short-circuits the
structurally-unsatisfiable discriminative criterion; success = matching the
single gold).

## 2. Pinned inputs

### 2.1 Data (read-only; `data/mini_a5_catch_v1/` is never modified)

| artifact | sha256 |
|---|---|
| `data/mini_a5_catch_v1/pairs.jsonl` (300 rows, 3 templates x 100) | `fbd83d52fa01103bfb839fa2572eb9164c532f8c3a3431da6ca8f6033d6a9728` |
| `data/mini_a5_catch_v1/decontamination.json` (`status: pass`) | `19ed9a833665aead2aee1f4494279a26055c4f531fed68d3e3340af8a1a16bda` |
| `reports/mini_a5_catch_audit_v1.json` (audit `pass`, matches main registration line 31) | `37b9662c1f873c6b6cb7ee04a87a954dadef54ea974933c0e50e5ab8c60c2317` |

### 2.2 Derived eval manifest (the pair_group_uid → pair_id adapter output)

The generation harness `scripts/eval_qwen_vl_fliptrack.py` reads `pair_id`; the
catch set keys rows `pair_group_uid`. The adapter
`scripts/build_mini_a5_catch_eval_manifest.py` (sha256
`b7b964f3c17f650d2355e36ab532e2893de8fb49aa51bb427a352e2fc995e93e`) verifies
the source against the pinned hash above before reading a row, copies every
source field unchanged, adds `pair_id := pair_group_uid`, validates the catch
invariants (300 rows, 3 registered templates x 100, equal nonempty golds,
unique uids, images on disk), and writes deterministically:

| artifact | sha256 |
|---|---|
| `data/derived/mini_a5_catch_eval_manifest_v1.jsonl` | `c4bb508f930ec47c9f3a2a4bc905693394f63bf6b4ebbd0f1332eef85afcbe4a` |
| `data/derived/mini_a5_catch_eval_manifest_v1.jsonl.provenance.json` | `47f35dce7f76e3b43902951f7a0f24cdd147d9d3e576f6fb019fcfffddaa8ad8` |

Both arms are evaluated on this one manifest. Per repo convention `/data/` is
gitignored (generated datasets stay local; checksums are tracked under
`experiments/manifests/`), so the derived manifest is pinned by the **tracked**
checksum record `experiments/manifests/mini_a5_catch_eval_manifest_v1.json`
(a copy of the provenance sidecar) and is rebuilt deterministically
(byte-identical, source-hash-verified) by the adapter wherever it is absent.
The launch preflight must verify the on-disk manifest against the
`output_sha256` above before generation starts.

### 2.3 Checkpoints (the same two step-120 arms as every F8 cell)

| arm | checkpoint | `model.safetensors.index.json` sha256 |
|---|---|---|
| CP-GRPO | `checkpoints/mini_a5/mini_a5_cp_seed1/global_step_120/actor/huggingface` | `4bb3b752a9895596f57798116b660406110198669dcfefbc213594d540baed21` |
| same-data GRPO (member) | `checkpoints/mini_a5/mini_a5_same_data_seed1/global_step_120/actor/huggingface` | `b4270b12dda440fdfdb345c4c074decd1dbbe8d40c751b67392ce6d96bd037f6` |

(Source: `reports/f8_eval_plan_v1.json` checkpoint block; identical to the
hashes in `reports/f8_secondaries_v1.md` §1.2. The index hash of each arm must
be re-verified on disk at launch and recorded in the run provenance.)

### 2.4 Generation regime (verbatim from the completed F8 generation cells)

| setting | value |
|---|---|
| harness | `scripts/eval_qwen_vl_fliptrack.py` (greedy, `do_sample=False`) |
| prompt contract | `answer-tags-v1`, sha256 `7ac39f53a2a824490fc5ee22671a888d2d79d55e1d8351919006d7d71c7a8f3f` |
| frozen processor artifact | sha256 `bb6a1bfd88cb88a749ff1f86affa84907a70bfdf98c10e303368db5685c81544` |
| `--image-mode` | `real` |
| `--seed` | `0` |
| `--max-new-tokens` | `32` |

These match the `run_manifest.json` of
`experiments/runs/mini_a5_f8_r19_{cp,member}_step120_real_an29_20260730T004031Z`,
so catch numbers sit on the same generation regime as the F8 primary cells.
As with the F8 cells, the shard launcher has no `m6_mini_a5_registered_main`
binding branch; checkpoint provenance is carried out-of-band by a post-run
provenance record (per `reports/f8_eval_plan_v1.json` blocking-limitations
mitigation), which must include both index hashes and both manifest hashes.

## 3. The scorer

`src/eval/catch_stability.py` (sha256
`d15eaa5d878cb757aa8dbae17d446c98cd6675cdc10fbd1a23bac1d7af1d8e91`), schema
`blind-gains.mini-a5-catch-stability.v1`. It re-scores every row from the raw
`prediction_a`/`prediction_b` fields of the harness output (it never trusts
stability-adjacent fields already present), refuses non-equal-gold rows, and
emits:

**Per row:** `pair_group_uid`, `template_id`, `prediction_a/b`,
`extracted_answer_a/b`, `stable_lenient`, `stable_strict`, `correct_a`,
`correct_b`, `pair_correct`, `strict_pair_correct`,
`stable_and_correct_lenient`, `stable_and_correct_strict`,
`contract_valid_a/b`, `parser_version` (`canonical-v2`), prompt-contract id +
sha256.

**Per template ONLY** (3 templates, 100 pairs each; roles within the catch
design are established nowhere, so pooling is unjustified — I13; the output
schema has **no slot** for a pooled number and the test suite enforces this
structurally): count and rate for each of the six registered indicators below,
i.e. stability, correctness, and joint stable-and-correct, each at both
severities (I7).

## 4. Registered indicators and CP-vs-member procedure

| indicator_index | row field | family | severity |
|---:|---|---|---|
| 0 | `stable_lenient` | stability | lenient |
| 1 | `stable_strict` | stability | contract-strict |
| 2 | `pair_correct` | correctness | lenient |
| 3 | `strict_pair_correct` | correctness | contract-strict |
| 4 | `stable_and_correct_lenient` | joint | lenient |
| 5 | `stable_and_correct_strict` | joint | contract-strict |

The two named endpoint indicators are **stability** and **correctness**, each
read at both severities (indices 0–3); the joint rates (indices 4–5) are
reported alongside as the registered separability check. This table's order is
frozen (a fixture pins it): reordering would silently remap bootstrap seeds.

**CP minus member, per template, per indicator:** paired item bootstrap on
`pair_group_uid`, **10,000 draws**, percentile **2.5/97.5**, both arms
resampled on **identical indices** per replicate; **exact two-sided McNemar**
alongside (implementation verified against `scipy.stats.binomtest` in the test
suite). Alpha 0.05, two-sided, no multiplicity correction — 18 per-template
CP-vs-member contrasts are reported, none feeds a decision rule.

**Seed derivation** (the f8_secondaries §1.6 procedure, indicator enumeration
fixed by the table above; fixed here before any value is read):

```
base seed 20260729
seed = 20260729 + 1000*indicator_index + 10*template_index
template_index: sorted template-id order —
  0 mini_a5_catch_distractor_matrix_v1
  1 mini_a5_catch_distractor_scatter_v1
  2 mini_a5_catch_distractor_trajectory_v1
```

Every resolved seed is recorded per cell in the output JSON. Intervals
quantify evaluation uncertainty on a fixed pair set only; they do not estimate
run-to-run RL variance; each arm is one training run.

## 5. Adversarial fixtures (I10)

`tests/test_catch_stability.py` (sha256
`c809be291181eaabeffea770e85ee04945c562fdcb1993df31f6315b41e49209`), 27 tests,
all passing at registration time. The decisive ones:

1. **The f8_secondaries §2.2 decisive row**: members agree, both wrong →
   `stable_lenient=True`, `pair_correct=False`; and the pre-existing fields
   (`pair_correct`, `strict_pair_correct`, `collapsed`) are asserted
   **identical** between this pair and a disagreeing pair while
   `stable_lenient` separates them — the proof the old schema could not carry
   this endpoint.
2. Agreement reached only out of contract (`Answer: B9U` twice, no tags; also
   two empty generations; also a one-sided contract break) →
   `stable_lenient=True`, `stable_strict=False`.
3. Template pooling structurally impossible: aggregation output has exactly
   one key (`per_template`); a recursive schema walk asserts every indicator
   rate lives under a concrete template id and no pooled/overall/combined slot
   exists anywhere in the readout; rows without `template_id` are refused.
4. Determinism: two full CLI runs (readout JSON + both per-row files) are
   byte-identical.
5. Domain guards: non-equal-gold rows refused; mismatched uid sets and
   cross-arm template disagreement refused; adapter refuses source-hash
   mismatch, pre-existing `pair_id`, unequal golds, and silent overwrite.
6. Registered-parameter pins: indicator order, seed formula values, 10,000
   resamples, identical-index bootstrap (degenerate [0,0] interval on
   identical arms), McNemar vs `scipy.stats.binomtest` (< 1e-12).

## 6. Cost and placement (NOT launched here)

300 pairs x 2 members = 600 greedy generations per arm; 1,200 across the two
arms. Reference throughput: the F8 R19 cells processed 1,200 rows in ~14 min
on 4-GPU quads; at one GPU per arm this cell is expected to take roughly
**30–60 min per arm**. Placement: any single free GPU per arm on one node
(single-node placement; e.g. an29 GPUs 6–7, idle at registration time). The
launch is a separate step that happens only after this registration merges
(I9); nothing in this task started a GPU process.

## 7. Sealed

- The eval over `data/derived/mini_a5_catch_eval_manifest_v1.jsonl` launches
  only after this document merges; registrations merge before the first
  optimizer/eval step they govern (I9).
- `data/mini_a5_catch_v1/` is read-only; R19/R20 and the two checkpoints are
  never modified (I11).
- Numbers are reported per template at both severities, never pooled (I13,
  I7), with provenance; no interpretation, no decision branch.
- The published F8 primary readout is unaffected by any value this instrument
  produces.
