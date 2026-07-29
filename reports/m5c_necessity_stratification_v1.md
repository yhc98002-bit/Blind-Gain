# M5c — geo3k step-100 → step-400 change stratified by visual necessity (PI item 5)

Artifact: `reports/m5c_necessity_stratification_v1.json` · built by `scripts/build_m5c_necessity_stratification.py` · git `1b17b3b598f807c67256ea831a05022ba6b9bfb7` · generated 2026-07-29T17:53:47Z · login node, CPU only, no GPU job started.

Scope: the 601 Geometry3K **test** items in `reports/m5c_item_substrate_v1.jsonl` (sha256 `1fc5310785680afbf5420166c97d776ea77ab0b4081533097fd225648882a864`, 601 rows), item key `(split, row_index) on the Geometry3K test split`.

## 1. Stratification definition adopted (reused from Gate 0, not invented here)

**Primary — delta_q terciles (Gate 0 G0.1).** Quoted from `reports/gate0_stratification_v1.md`:

> Δq = q_real − q_blind per item, taken from the registered blind reward-opportunity audit's own `q_i`. Terciles of Δq, mean per-item image-present gain in each

and from the Gate 0 builder docstring (scripts/build_gate0_stratification.py (function `concentration`, n_bins=3)):

> Delta-q uses the audit's own per-item q_i, real minus none, on the identical rows.

Operational rule as executed here: q_real = q_i from the guarded-rescore `real` per_item.jsonl; q_blind = q_i from the guarded-rescore `none` per_item.jsonl (base model, Jeffreys-smoothed). delta_q = q_real - q_blind. Bin edges = np.quantile(delta_q, [0,1/3,2/3,1]) with the outer edges opened to +/-inf; bin 0 is delta_q <= e1, bin i>0 is e_i < delta_q <= e_{i+1}. Identical code path to Gate 0.

Label map applied to the three Gate 0 terciles: `bin0_low_delta_q` → **blind_solvable**, `bin1_mid_delta_q` → **intermediate**, `bin2_high_delta_q` → **image_necessary**.

**Label caveat (measured, see §3).** Gate 0 never attached the words blind-solvable / image-necessary to these terciles; it called them low/mid/high Δq. The low-Δq bin means 'the image bought no measured reward opportunity', which is satisfied both by items the base model solves blind and by items it solves under no condition. q_blind and q_real are reported per bin so this is visible.

**Secondary — blind-answerable split (Gate 0 G0.2 headroom control).** Quoted from `reports/gate0_stratification_v1.md`:

> `q_blind` is Jeffreys-smoothed, so items with no observed blind success sit at the floor 0.1387. The split is therefore **blind-answerable** (≥1 observed blind success, n=117) versus **not** (n=484).

Operational rule: FLOOR = min(q_blind) over the 601 eval items; blind_answerable = q_blind > FLOOR + 1e-9. (`scripts/build_g02_headroom_control.py lines 39-42`). This is Gate 0's only literal 'blind-solvable' definition. It is binary, so it cannot produce an 'intermediate' bin; it is reported alongside, not merged (I13).

Necessity source runs (base model `Qwen2.5-VL-3B-Instruct`, the same two files Gate 0 used):

| arm | run | per_item sha256 | rows total | rows test |
| :-- | :-- | :-- | ---: | ---: |
| q_real (`real`) | `experiments/runs/blind_solvability_v2_guarded_rescore_geo3k_filtered_v2_retry_real_login_20260712T050905Z` | `021da42f00eab94b…` | 1889 | 601 |
| q_blind (`none`) | `experiments/runs/blind_solvability_v2_guarded_rescore_geo3k_filtered_v2_retry_none_login_20260712T055030Z` | `60db78c675680507…` | 1889 | 601 |

Δq is a **base-model dataset property**, not a training-arm outcome, per `reports/blind_solvability_geo3k_v3_audited.md` ("These are base-model dataset-property measurements, not training-arm outcomes.").

### Which necessity artifact is canonical

| candidate | what it actually contains | used here |
| :-- | :-- | :-- |
| `reports/blind_solvability_geo3k_v3_audited.json` | aggregate-only (no per-item rows); 2702 items, canonical-v1 512-token Gate-2 audit family | no — wrong item universe (2702, not the 601-item filtered-v2 eval split) and carries no per-item field |
| `reports/blind_solvability_geo3k_v2_audited.json` | machine measurement-integrity audit of the 1889-row filtered-v2 condition runs; checks only, no per-item scores | no — it is the audit that certifies the runs below, not a source of per-item values |
| `reports/gate0_stratification_v1.json` | holds the Δq **summary** (`delta_q`) and the binned results, but not per-item Δq | consulted as the reproduction target, not as input |
| `experiments/runs/blind_solvability_v2_guarded_rescore_geo3k_filtered_v2_retry_{real,none}_login_*/per_item.jsonl` | the per-item `q_i` Gate 0 itself reads | **yes — canonical per-item source** |

Neither audited JSON is superseded by the other; they are different measurement families (2702-item canonical-v1 vs 1889-row filtered-v2). Only the filtered-v2 family contains the 601 test items this substrate is built on, so it is the only one that can be joined.

## 2. Join to the substrate

- Join key: `(split, row_index)`, restricted to `split == "test"`.
- Substrate rows: **601**. Necessity `real` test rows: **601**. Necessity `none` test rows: **601**.
- Joined: **601 / 601** → join rate **1.0000 (100.00%)**. Items failing to join: **0** in either direction.
- Non-test rows excluded, not aggregated (I13): 1288 `split=train` rows per arm.

Cross-field identity checks on the 601 joined rows (0 = pass):

| check | mismatches |
| :-- | ---: |
| `ground_truth_sub_vs_none` | 0 |
| `ground_truth_sub_vs_real` | 0 |
| `image_sha256_real_vs_none` | 0 |
| `image_sha256_sub_vs_none` | 0 |
| `image_sha256_sub_vs_real` | 0 |
| `problem_real_vs_none` | 0 |

- qid is null on every substrate row and on every necessity row, so a qid arm of the identity check is vacuous and is not claimed as a check. (`qid` null on 601/601 substrate rows, 601/601 and 601/601 necessity rows.)
- The real and none guarded-rescore arms carry different data_manifest_hash values. This is inherited from Gate 0's inputs, which are used unchanged. Item identity across the two arms is therefore asserted from the row fields directly: problem and image_sha256 are equal on 601/601 joined test rows (see cross_field_mismatch_counts).

## 3. Bin sizes and what the bins contain

| bin | Gate 0 name | Δq range | n | mean Δq | mean q_real | mean q_blind | blind-answerable in bin |
| :-- | :-- | :-- | ---: | ---: | ---: | ---: | ---: |
| **blind_solvable** | low delta_q tercile | [-0.7988, 0.0000] | 329 | -0.0513 | 0.2065 | 0.2578 | 77 |
| **intermediate** | mid delta_q tercile | (0.0000, 0.2312] | 121 | +0.2089 | 0.4509 | 0.2420 | 26 |
| **image_necessary** | high delta_q tercile | (0.2312, 0.7988] | 151 | +0.5382 | 0.7084 | 0.1702 | 14 |
| all | — | [-0.7988, 0.7988] | 601 | +0.1492 | 0.3818 | 0.2326 | 117 |

- The terciles are unequal because Δq is heavily tied: **271 of 601** items have Δq exactly 0, so the 33rd-percentile edge lands exactly on 0 and the low bin absorbs every Δq ≤ 0 item (n=329).
- Secondary split: blind-answerable **117** vs not **484**, Jeffreys floor 0.1387.

Cross-tab of the two Gate 0 stratifications (reported side by side, never merged — I13):

| Δq bin | blind-answerable | not blind-answerable |
| :-- | ---: | ---: |
| blind_solvable | 77 | 252 |
| intermediate | 26 | 95 |
| image_necessary | 14 | 137 |

**Two measured facts that constrain how the `blind_solvable` label can be read.** (a) Only 77 of the 329 low-Δq items are blind-answerable; 252 of them have zero observed blind successes. The low-Δq bin is therefore dominated by items the base model solves under **no** condition, not by items it solves blind. (b) Mean q_real rises across the bins 0.2065 → 0.4509 → 0.7084, so the high-Δq bin is also the bin the base model scores highest on **with** the image.

### Reproduction check against Gate 0

| quantity | here | `reports/gate0_stratification_v1.json` | match |
| :-- | :-- | :-- | :-- |
| tercile sizes | [329, 121, 151] | [329, 121, 151] | PASS |
| tercile edges | [[-0.798841, 0.0], [0.0, 0.231229], [0.231229, 0.798841]] | [[-0.798841, 0.0], [0.0, 0.231229], [0.231229, 0.798841]] | PASS |
| Δq mean / min / max | 0.149188 / -0.798841 / 0.798841 | 0.149188 / -0.798841 / 0.798841 | PASS |
| Jeffreys floor | 0.1386589900 | 0.1386589900 | PASS |
| blind-answerable n | [117, 484] | [117, 484] | PASS |

The binning code path is Gate 0's own; these five checks confirm the reproduction is exact, so any difference from Gate 0's published stratum results is attributable to the outcome variable, not to the strata.

## 4. Step 100 → step 400 per bin (I7: lenient and contract-strict, both reported)

Paired **item** bootstrap, 10,000 draws, seed `20260729`. Resampling is within-bin and paired (the same item contributes its step-100 and step-400 outcome to every draw). `mcnemar_exact_p` is the two-sided exact binomial test on the discordant pairs at p=0.5.

### 4.1 lenient `acc_final`

| stratum | n | acc @100 | acc @400 | Δ (400−100) | 95% CI | gained | lost | stable ✓ | stable ✗ | turnover | McNemar exact p |
| :-- | ---: | ---: | ---: | ---: | :---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **blind_solvable** (low Δq) | 329 | 0.2523 (83) | 0.2462 (81) | -0.0061 | [-0.0547, +0.0426] | 32 | 34 | 49 | 214 | 0.2006 | 0.9022 |
| **intermediate** (mid Δq) | 121 | 0.5372 (65) | 0.6198 (75) | +0.0826 | [-0.0083, +0.1736] | 22 | 12 | 53 | 34 | 0.2810 | 0.1214 |
| **image_necessary** (high Δq) | 151 | 0.7550 (114) | 0.7351 (111) | -0.0199 | [-0.0993, +0.0596] | 17 | 20 | 94 | 20 | 0.2450 | 0.7428 |
| _all 601 items_ | 601 | 0.4359 (262) | 0.4443 (267) | +0.0083 | [-0.0300, +0.0466] | 71 | 66 | 196 | 268 | 0.2280 | 0.7327 |
| blind-answerable (2ary) | 117 | 0.5470 (64) | 0.5128 (60) | -0.0342 | [-0.1282, +0.0598] | 13 | 17 | 47 | 40 | 0.2564 | 0.5847 |
| not blind-answerable (2ary) | 484 | 0.4091 (198) | 0.4277 (207) | +0.0186 | [-0.0248, +0.0599] | 58 | 49 | 149 | 228 | 0.2211 | 0.4394 |

### 4.2 contract-strict `acc_strict`

| stratum | n | acc @100 | acc @400 | Δ (400−100) | 95% CI | gained | lost | stable ✓ | stable ✗ | turnover | McNemar exact p |
| :-- | ---: | ---: | ---: | ---: | :---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **blind_solvable** (low Δq) | 329 | 0.2523 (83) | 0.2462 (81) | -0.0061 | [-0.0547, +0.0426] | 32 | 34 | 49 | 214 | 0.2006 | 0.9022 |
| **intermediate** (mid Δq) | 121 | 0.5372 (65) | 0.6198 (75) | +0.0826 | [-0.0083, +0.1736] | 22 | 12 | 53 | 34 | 0.2810 | 0.1214 |
| **image_necessary** (high Δq) | 151 | 0.7550 (114) | 0.7351 (111) | -0.0199 | [-0.0993, +0.0596] | 17 | 20 | 94 | 20 | 0.2450 | 0.7428 |
| _all 601 items_ | 601 | 0.4359 (262) | 0.4443 (267) | +0.0083 | [-0.0300, +0.0466] | 71 | 66 | 196 | 268 | 0.2280 | 0.7327 |
| blind-answerable (2ary) | 117 | 0.5470 (64) | 0.5128 (60) | -0.0342 | [-0.1282, +0.0598] | 13 | 17 | 47 | 40 | 0.2564 | 0.5847 |
| not blind-answerable (2ary) | 484 | 0.4091 (198) | 0.4277 (207) | +0.0186 | [-0.0228, +0.0599] | 58 | 49 | 149 | 228 | 0.2211 | 0.4394 |

**I7 note.** `acc_final == acc_strict` on 601/601 items at step 100 and 601/601 at step 400. Both metrics are computed, stored and reported separately and are never collapsed. Where the two tables carry identical point estimates it is because the underlying per-item vectors are identical, not because one was substituted for the other. Small differences between the lenient and strict bootstrap CIs are Monte-Carlo only: identical data, different draws consumed from the single seeded stream.

**Continuity with `reports/m5b_trajectory_v1.md`.** The all-items row reproduces m5b exactly: acc_final 0.4359 → 0.4443, Δ +0.0083, McNemar exact p 0.7327 (m5b: +0.0083, p=0.73). The CI here is [-0.0300, +0.0466] against m5b's [-0.0283, +0.0449]; the two differ only by bootstrap Monte-Carlo (different seed and draw count). Bin gained/lost sum to 71 / 66, matching the substrate's 71 / 66.

## 5. The PI's hypothesis, tested

Hypothesis as stated: *"blind-solvable items improve or hold while image-necessary items decline, cancelling to a flat overall"*.

Three independent readings of the same question:

**(a) Direction and size of each bin's move** (from §4, `acc_final`; `acc_strict` identical):

| bin | Δ (400−100) | 95% CI | CI excludes 0? | direction vs hypothesis |
| :-- | ---: | :---: | :-- | :-- |
| blind_solvable | -0.0061 | [-0.0547, +0.0426] | no | predicted: improve or hold; observed: declines |
| intermediate | +0.0826 | [-0.0083, +0.1736] | no | predicted: (unspecified); observed: rises |
| image_necessary | -0.0199 | [-0.0993, +0.0596] | no | predicted: decline; observed: declines |

**(b) Direct between-bin contrast** (image_necessary Δ minus blind_solvable Δ). Bins are disjoint item sets, so the bootstrap resamples each bin independently; the permutation reshuffles bin membership within the union of the two bins.

| metric | contrast | 95% CI | permutation p (two-sided) |
| :-- | ---: | :---: | ---: |
| `acc_final` | -0.0138 | [-0.1036, +0.0773] | 0.8374 |
| `acc_strict` | -0.0138 | [-0.1043, +0.0778] | 0.8373 |

**(c) Is the turnover itself systematic in Δq?** Mean Δq of the items that gained vs the items that lost, plus a tie-aware Spearman of per-item change against Δq over all 601 items. Permutations: 10,000.

| metric | n gained | n lost | mean Δq gained | mean Δq lost | difference | perm p | Spearman ρ (change vs Δq) | perm p |
| :-- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `acc_final` | 71 | 66 | 0.1540 | 0.1238 | +0.0301 | 0.5432 | +0.0212 | 0.6053 |
| `acc_strict` | 71 | 66 | 0.1540 | 0.1238 | +0.0301 | 0.5547 | +0.0212 | 0.6026 |

(Mean Δq of the 464 items that did not change: 0.1521.)

### Verdict against the hypothesis

**The data do not support the hypothesis as stated, on any of the three readings.**

1. The predicted split does not appear. `blind_solvable` moves -0.0061 — down, not up or flat — and `image_necessary` moves -0.0199. The two bins move in the **same** direction, and the only bin that rises is `intermediate` (+0.0826), which the hypothesis makes no prediction about.
2. Every one of the three bin CIs contains 0 ([-0.0547, +0.0426], [-0.0083, +0.1736], [-0.0993, +0.0596]), and every per-bin McNemar exact p is ≥ 0.1214. No bin's move is distinguishable from zero.
3. The direct contrast is -0.0138 with CI [-0.1036, +0.0773] and permutation p 0.8374; the Spearman of per-item change against Δq is +0.0212, p 0.6053; gained and lost items differ in mean Δq by +0.0301, p 0.5432.

**Stated plainly: the bins move together, not against each other.** The flat aggregate is not measured here to be a cancellation of opposing bin-level trends. Turnover is large in every bin (20.1% / 28.1% / 24.5%) and is not measurably sorted by Δq. Note this is a non-rejection at n=601 with per-bin n as low as 121, not a demonstration that no necessity-linked effect exists; the contrast CI [-0.1036, +0.0773] is wide enough to admit bin differences of about ±0.10.

## 6. Per-bin real-vs-blind accuracy gap

### 6.1 Step 100 — computable

All five step-100 arms evaluate the same checkpoint (`checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_100/actor/huggingface`): verified identical. The real arm is a guarded RESCORE; the four blind arms are raw run outputs. To remove that asymmetry every greedy response in all five arms was re-scored here through src.eval.blind_solvability.score_greedy_item_pilot under DEFAULT_PROMPT_CONTRACT, and the gap is computed from those recomputed values. Stored == recomputed on 601/601 rows for both metrics in all five arms, so the rescore asymmetry has no effect on these numbers.

**Lenient `acc_final`** — accuracy at step 100 by condition, and the paired real-minus-blind gap (95% CI, 10,000 draws, seed `20260729`). Conditions are never pooled (I13).

| stratum | n | real | none | gap (real−none) | 95% CI | gray | gap | noise | gap | caption | gap |
| :-- | ---: | ---: | ---: | ---: | :---: | ---: | ---: | ---: | ---: | ---: | ---: |
| blind_solvable | 329 | 0.2523 | 0.1155 | +0.1368 | [+0.0912, +0.1854] | 0.1125 | +0.1398 | 0.1277 | +0.1246 | 0.1793 | +0.0729 |
| intermediate | 121 | 0.5372 | 0.1240 | +0.4132 | [+0.3140, +0.5041] | 0.1405 | +0.3967 | 0.1322 | +0.4050 | 0.3967 | +0.1405 |
| image_necessary | 151 | 0.7550 | 0.0861 | +0.6689 | [+0.5894, +0.7417] | 0.0728 | +0.6821 | 0.0861 | +0.6689 | 0.6159 | +0.1391 |
| blind-answerable (2ary) | 117 | 0.5470 | 0.4701 | +0.0769 | [-0.0171, +0.1709] | 0.4530 | +0.0940 | 0.4786 | +0.0684 | 0.4957 | +0.0513 |
| not blind-answerable (2ary) | 484 | 0.4091 | 0.0227 | +0.3864 | [+0.3409, +0.4318] | 0.0248 | +0.3843 | 0.0310 | +0.3781 | 0.2934 | +0.1157 |
| _all 601 items_ | 601 | 0.4359 | 0.1098 | +0.3261 | [+0.2845, +0.3677] | 0.1082 | +0.3278 | 0.1181 | +0.3178 | 0.3328 | +0.1032 |

**Contract-strict `acc_strict`** — accuracy at step 100 by condition, and the paired real-minus-blind gap (95% CI, 10,000 draws, seed `20260729`). Conditions are never pooled (I13).

| stratum | n | real | none | gap (real−none) | 95% CI | gray | gap | noise | gap | caption | gap |
| :-- | ---: | ---: | ---: | ---: | :---: | ---: | ---: | ---: | ---: | ---: | ---: |
| blind_solvable | 329 | 0.2523 | 0.1155 | +0.1368 | [+0.0912, +0.1824] | 0.1125 | +0.1398 | 0.1277 | +0.1246 | 0.1793 | +0.0729 |
| intermediate | 121 | 0.5372 | 0.1240 | +0.4132 | [+0.3140, +0.5124] | 0.1405 | +0.3967 | 0.1322 | +0.4050 | 0.3967 | +0.1405 |
| image_necessary | 151 | 0.7550 | 0.0861 | +0.6689 | [+0.5894, +0.7417] | 0.0728 | +0.6821 | 0.0861 | +0.6689 | 0.6159 | +0.1391 |
| blind-answerable (2ary) | 117 | 0.5470 | 0.4701 | +0.0769 | [-0.0171, +0.1709] | 0.4530 | +0.0940 | 0.4786 | +0.0684 | 0.4957 | +0.0513 |
| not blind-answerable (2ary) | 484 | 0.4091 | 0.0227 | +0.3864 | [+0.3409, +0.4318] | 0.0248 | +0.3843 | 0.0310 | +0.3781 | 0.2934 | +0.1157 |
| _all 601 items_ | 601 | 0.4359 | 0.1098 | +0.3261 | [+0.2829, +0.3661] | 0.1082 | +0.3278 | 0.1181 | +0.3178 | 0.3328 | +0.1032 |

Step-100 blind runs used:

| condition | run | per_item sha256 | status |
| :-- | :-- | :-- | :-- |
| `real` | `experiments/runs/blind_solvability_v2_guarded_rescore_anchor_step100_geo3k_real_login_20260712T082107Z` | `22d93ad3f5510c49…` | complete |
| `none` | `experiments/runs/blind_solvability_v2_anchor_step100_geo3k_guarded_none_an29_20260712T102011Z` | `3a89d287cbf6387b…` | complete |
| `gray` | `experiments/runs/blind_solvability_v2_anchor_step100_geo3k_guarded_gray_an12_20260712T101335Z` | `bdec5b17b7ca8bf1…` | complete |
| `noise` | `experiments/runs/blind_solvability_v2_anchor_step100_geo3k_guarded_noise_an12_20260712T101335Z` | `15a71936f2b31590…` | complete |
| `caption` | `experiments/runs/blind_solvability_v2_anchor_step100_geo3k_guarded_caption_an29_20260712T102011Z` | `c4131d45fbd8fa25…` | complete |

### 6.2 Step 400 — NOT COMPUTED, no artifact exists

No Geometry3K evaluation of any M5 step-400 checkpoint under a blind condition exists. A scan of every experiments/runs/*/run_manifest.json whose manifest mentions 'geo' and whose condition field is not 'real' returns 100 runs; all of them evaluate either the frozen base model or a step-60/step-100 pilot checkpoint. The only step-400 blind evaluations in the repo are m5_r19_step400_gray_an12_20260728T054005Z and m5_r19_step400_noise_an12_20260728T054005Z, which are R19 grounding probes, not geo3k, and are not substitutable. The step-400 real-vs-blind column is therefore not reported.

**The step-400 real-vs-blind column is therefore absent from every table above and is not fabricated, estimated, or back-filled from a step-100 or base-model proxy.** Consequently the *change* in the real-vs-blind gap between step 100 and step 400 — the quantity that would connect this section to §4 — cannot be computed at all.

## 7. Verification ledger

| check | result |
| :-- | :-- |
| substrate sha256 matches the one recorded in `reports/m5c_turnover_v1.json` | PASS (`1fc5310785680afb…`) |
| join rate substrate ↔ necessity | 601/601 = 100.00% |
| cross-field mismatches (image_sha256, ground_truth, problem) | 0 |
| tercile sizes / edges reproduce Gate 0 | PASS |
| Jeffreys floor and blind-answerable n reproduce Gate 0 | PASS |
| step-100 real arm reproduces the substrate's step-100 column | acc_final 601/601, acc_strict 601/601 |
| stored == recomputed under `score_greedy_item_pilot` (all 5 step-100 arms) | real 601/601, none 601/601, gray 601/601, noise 601/601, caption 601/601 |
| all-items Δ and McNemar p reproduce m5b | Δ +0.0083, p 0.7327 |
| bin gained/lost sum to the substrate's 71/66 | PASS |
| step-400 blind geo3k artifact search | 0 found; column withheld |

**Field-mapping caveat.** The step-100 per_item rows carry greedy_correct / greedy_acc_strict; the m5_geo3k step-150..400 rows carry acc_final / acc_strict. greedy_correct is the field that equals score_greedy_item_pilot(...)['acc_final'] (601/601). The separate field greedy_canonical_correct agrees with greedy_correct on only 598/601 rows and is NOT used here; Gate 0's base-model analysis used greedy_canonical_correct, which is a different quantity. Neither field feeds the necessity binning, which comes from q_i. (`greedy_correct` == `greedy_canonical_correct` on 598/601 rows; the same 3-item gap is already documented in `reports/m5b_trajectory_v1.md` as 0.4359 vs 0.4309.)

## 8. What could not be computed

1. **Step-400 real-vs-blind gap, and therefore the change in that gap across training.** No geo3k evaluation of any M5 step-400 checkpoint under any blind condition exists (§6.2). No proxy was substituted.
2. **A three-way stratification that is literally blind-solvable / intermediate / image-necessary.** Gate 0 supplies a three-way rule (Δq terciles) and a two-way rule (blind-answerable). The three-way rule's low bin is *not* a blind-solvable bin: only 77/329 of its items are blind-answerable (§3). Both Gate 0 rules are reported; neither was modified and no third rule was invented to close the gap.
3. **Any decomposition of turnover below the item level** (e.g. which template or premise moved) is out of scope here and not attempted.

