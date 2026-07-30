# F8 — Mini-A5 endpoint readout and pre-committed branch determination

Binding spec: `docs/registered_mini_a5_endpoint_readout_v1.md`. Plan: `reports/f8_eval_plan_v1.json`. RUN_TS `20260730T004031Z`.
git HEAD at launch `f2e3762986d7`, at readout `b0b316d294a7`. Node `an29`, eval seed 0, global_step 120, image_mode `real`, max_new_tokens 32.
Bootstrap: paired item, 10000 draws, seed 20260729, percentile 2.5/97.5, unit `pair_id`, both arms resampled on the same pair indices per replicate. Exact McNemar two-sided alongside.
Sign convention: delta = CP minus member (`--left` member, `--right` CP).

Numbers, checks and provenance only. No interpretation.

## 1. Primary endpoint — R19 coordinate survey register (primary visual anchor, n=600)

Source: `reports/mini_a5_f8_r19_paired_comparison_v1.json` → `per_template['coordinate_register_twenty_point_x_v02']`.

| contract | member | CP | CP−member | 95% paired-bootstrap CI | McNemar exact 2-sided p | decision rule |
|---|---:|---:|---:|---|---:|---|
| lenient `pair_correct` | 0.4817 | 0.4717 | -0.0100 | [-0.0300, +0.0100] | 0.4050 | **NOT MOVED** |
| contract-strict `strict_pair_correct` | 0.3833 | 0.4533 | +0.0700 | [+0.0417, +0.0983] | 1.397e-06 | **MOVED** |

McNemar discordant cells, lenient: b01 (member wrong / CP right) = 15, b10 (member right / CP wrong) = 21. Strict: b01 = 59, b10 = 17.

**The two registered contracts disagree on the primary endpoint.** Per binding spec §3, "Neither is privileged; if they disagree the disagreement is the result."

## 2. R19 secondaries, each in its own role (I13 — never aggregated with the primary)

### header-cued verification table — saturated positive control / retention canary, a DROP signals damage (n=300)

| contract | member | CP | CP−member | 95% CI | McNemar p | decision rule |
|---|---:|---:|---:|---|---:|---|
| lenient | 0.9233 | 0.9233 | +0.0000 | [-0.0167, +0.0167] | 1.0000 | **NOT MOVED** |
| contract-strict | 0.2600 | 0.2200 | -0.0400 | [-0.0700, -0.0133] | 0.0118 | **MOVED_NEGATIVE_DIRECTION** |

### nine-series calibration trace — oracle-localized readout control (n=300)

| contract | member | CP | CP−member | 95% CI | McNemar p | decision rule |
|---|---:|---:|---:|---|---:|---|
| lenient | 0.5900 | 0.6667 | +0.0767 | [+0.0300, +0.1267] | 0.0027 | **MOVED** |
| contract-strict | 0.5233 | 0.6200 | +0.0967 | [+0.0467, +0.1467] | 3.367e-04 | **MOVED** |

Retention canary, explicit: on the lenient contract the canary is flat (+0.0000, CI contains zero, p = 1.0000). On the contract-strict contract it registers a **DROP** of -0.0400 with CI [-0.0700, -0.0133] excluding zero on the negative side, p = 0.0118. Per the binding spec's role table a drop on this task signals damage; it is recorded as such and not smoothed. Absolute levels: base strict 0.1800, member 0.2600, CP 0.2200 — both arms above base on this contract.

## 3. R20 — one-shot private twin (separate instrument, never averaged with R19)

### coordinate survey register (n=600)

| contract | member | CP | CP−member | 95% CI | McNemar p | decision rule |
|---|---:|---:|---:|---|---:|---|
| lenient | 0.4550 | 0.4617 | +0.0067 | [-0.0133, +0.0267] | 0.6177 | **NOT MOVED** |
| contract-strict | 0.3500 | 0.4450 | +0.0950 | [+0.0667, +0.1233] | 7.033e-11 | **MOVED** |

### header-cued verification table (n=300)

| contract | member | CP | CP−member | 95% CI | McNemar p | decision rule |
|---|---:|---:|---:|---|---:|---|
| lenient | 0.9233 | 0.9167 | -0.0067 | [-0.0233, +0.0100] | 0.6875 | **NOT MOVED** |
| contract-strict | 0.2267 | 0.1533 | -0.0733 | [-0.1067, -0.0400] | 5.948e-05 | **MOVED_NEGATIVE_DIRECTION** |

### nine-series calibration trace (n=300)

| contract | member | CP | CP−member | 95% CI | McNemar p | decision rule |
|---|---:|---:|---:|---|---:|---|
| lenient | 0.5100 | 0.5700 | +0.0600 | [+0.0133, +0.1033] | 0.0133 | **MOVED** |
| contract-strict | 0.4200 | 0.5300 | +0.1100 | [+0.0633, +0.1600] | 1.917e-05 | **MOVED** |

## 4. chart-v08 calibration set (third instrument, never averaged)

### legend target flip (n=50)

| contract | member | CP | CP−member | 95% CI | McNemar p | decision rule |
|---|---:|---:|---:|---|---:|---|
| lenient | 0.4400 | 0.3800 | -0.0600 | [-0.1600, +0.0400] | 0.4531 | **NOT MOVED** |
| contract-strict | 0.1400 | 0.0800 | -0.0600 | [-0.1600, +0.0200] | 0.3750 | **NOT MOVED** |

### point value flip (n=50)

| contract | member | CP | CP−member | 95% CI | McNemar p | decision rule |
|---|---:|---:|---:|---|---:|---|
| lenient | 0.5800 | 0.5600 | -0.0200 | [-0.1000, +0.0600] | 1.0000 | **NOT MOVED** |
| contract-strict | 0.2200 | 0.4400 | +0.2200 | [+0.0800, +0.3600] | 0.0074 | **MOVED** |

Set-level pooled (n=100, **not an endpoint** — the registration assigns the set a calibration role but no distinct role per template, so role-homogeneity of the pool is not established): lenient -0.0400 CI [-0.1100, +0.0300]; contract-strict +0.0800 CI [-0.0100, +0.1700].

## 5. Pooled R19 / R20 numbers — labelled NON-ENDPOINT (I13)

These pool three distinct scientific roles. Recorded as diagnostics only; they are not endpoints and the branch is not read from them.

| set | contract | member | CP | CP−member | 95% CI | McNemar p |
|---|---|---:|---:|---:|---|---:|
| R19 pooled 1200 | lenient | 0.6192 | 0.6333 | +0.0142 | [-0.0025, +0.0300] | 0.1038 |
| R19 pooled 1200 | contract-strict | 0.3875 | 0.4367 | +0.0492 | [+0.0283, +0.0700] | 3.306e-06 |
| R20 pooled 1200 | lenient | 0.5858 | 0.6025 | +0.0167 | [+0.0017, +0.0325] | 0.0446 |
| R20 pooled 1200 | contract-strict | 0.3367 | 0.3933 | +0.0567 | [+0.0358, +0.0775] | 1.924e-07 |

## 6. Absolute levels against the frozen base

### R19 — base cited from `reports/f2d_template_decomposition_v1.json` → `.base`

Base run `experiments/runs/fliptrack_v02r19_packaged_qwen25vl3b_real_an29_20260710T142716Z`, model `artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct`, `data_manifest_hash` `e1dde984…` — **identical to the locked R19 manifest used by the F8 cells**, identical `pair_id` keys, same `max_new_tokens` 32 and `image_mode` real. Verified by reading the base `run_manifest.json`.

| task | contract | base | member | CP | member−base | CP−base |
|---|---|---:|---:|---:|---:|---:|
| coordinate survey register | lenient | 0.4717 | 0.4817 | 0.4717 | +0.0100 | +0.0000 |
| coordinate survey register | contract-strict | 0.4433 | 0.3833 | 0.4533 | -0.0600 | +0.0100 |
| header-cued table | lenient | 0.8667 | 0.9233 | 0.9233 | +0.0567 | +0.0567 |
| header-cued table | contract-strict | 0.1800 | 0.2600 | 0.2200 | +0.0800 | +0.0400 |
| nine-series trace | lenient | 0.4367 | 0.5900 | 0.6667 | +0.1533 | +0.2300 |
| nine-series trace | contract-strict | 0.4200 | 0.5233 | 0.6200 | +0.1033 | +0.2000 |

### R20 — base cited from `reports/fliptrack_r20_confirmatory.json` → `.cells['3b_real']`

Base run `experiments/runs/fliptrack_r20_qwen25vl3b_real_an12_20260711T131807Z`, `data_manifest_hash` `525e1104…`. This is a **different manifest file** from the pinned F8 R20 manifest (`20222e60…`), but the eval plan preflight verified the two describe the same 1200 items with different `pair_id` keys, so set-level and per-template comparison is valid while per-item joins are not.

| task | contract | base | member | CP | member−base | CP−base |
|---|---|---:|---:|---:|---:|---:|
| coordinate survey register | lenient | 0.3967 | 0.4550 | 0.4617 | +0.0583 | +0.0650 |
| coordinate survey register | contract-strict | 0.3617 | 0.3500 | 0.4450 | -0.0117 | +0.0833 |
| header-cued table | lenient | 0.8667 | 0.9233 | 0.9167 | +0.0567 | +0.0500 |
| header-cued table | contract-strict | 0.1600 | 0.2267 | 0.1533 | +0.0667 | -0.0067 |
| nine-series trace | lenient | 0.3900 | 0.5100 | 0.5700 | +0.1200 | +0.1800 |
| nine-series trace | contract-strict | 0.3833 | 0.4200 | 0.5300 | +0.0367 | +0.1467 |

Both base runs record `prompt_contract_sha256: null` and `seed: null` (they predate contract hashing into manifests), while the F8 cells record `7ac39f53…`. Contract identity for the base columns is therefore not evidenced by the base manifests — this bears mainly on the contract-strict base column.

### chart-v08 — no base number exists in `reports/`

Every `reports/*.json` mentioning `chart_v08` was grepped for `pair_accuracy`, and every `reports/*.md` mentioning `chart_v08` was grepped for `accuracy`: only the three F8 comparison/verification files and `reports/f8_eval_plan_v1.json` match, and none carries a base number. `reports/chart_v08_calibration_execution_status_v5.json` is status `blocked` and holds no accuracy field.

A base-model chart-v08 run **directory** does exist — `experiments/runs/chart_v08_calibration_qwen25vl3b_real_an29_20260715T185645Z` — verified by reading its `run_manifest.json`: status complete, model `artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct`, `data_manifest_hash` `d90f3f13…` **identical** to the hash the F8 chart-v08 cells recorded, `image_mode` real, `max_new_tokens` 32. Aggregating it would yield a directly comparable base. The instruction is to cite a base number from `reports/` rather than recompute one, so **no number is computed, invented or proxied here.** The cell is left explicitly empty and the exact way to fill it is recorded.

## 7. Why the two contracts disagree — exact arithmetic, not interpretation

By construction, `src/eval/fliptrack_metrics.py::_score_member` line 97 sets `acc_strict = contract_valid and acc_final`. So `strict_pair_correct` == `pair_correct` **and** both members satisfy the response-format contract. `response_satisfies_contract` (`src/eval/prompt_contract.py`, contract `answer-tags-v1`) requires exactly one `<answer` opening tag, exactly one `</answer>` closing tag, and non-empty content between them — a check on emitted response **form** only; it does not inspect answer content.

Empirical confirmations: `strict_correct_not_lenient == 0.0` in all 12 template-cells (**True**); the identity `strict_pair_accuracy == pair_accuracy − lenient_correct_not_strict` holds to a maximum absolute residual of 1.1e-16; and `contract_valid_rate + extraction_fallback_rate == 1.0` in all 12 cells (max residual 0.0e+00), i.e. the contract-invalid rows are exactly the rows needing fallback extraction. `max_new_tokens` was 32 in all six F8 cells and in both cited base runs.

On the primary anchor:

- lenient delta: -0.0100
- CP pairs lenient-correct but contract-invalid: 0.0183
- member pairs lenient-correct but contract-invalid: 0.0983
- strict delta = lenient delta − (CP loss − member loss) = -0.0100 − (0.0183 − 0.0983) = +0.0700, versus reported +0.0700 — residual 1.4e-17
- `contract_valid_rate`: CP 0.9683, member 0.8133, difference +0.1550

The entire contract-strict primary-anchor gap is accounted for by the difference in response-format contract validity. Recomputed from stored per-row prediction text with `src.eval.fliptrack_metrics.pair_score`.

The same gap decomposed against the frozen base, exactly (`(CP−member) == (CP−base) − (member−base)`):

- CP − base (strict): +0.0100
- member − base (strict): -0.0600
- reconstructed CP − member: +0.0700 versus reported +0.0700 — residual 5.6e-17
- share of the gap from CP rising above base: 14.3%
- share of the gap from the member arm falling below base: 85.7%

Point-estimate decomposition; the base column carries no CI, so these shares are not interval-bounded.

## 8. Branch determination

Decision rule, quoted from binding spec §5:

> "moves" means the CP-member difference on the primary anchor has a 95% paired-bootstrap CI EXCLUDING ZERO in the positive direction. A positive point estimate whose interval contains zero is reported as NOT MOVED, not as a trend.

| contract | CP−member on primary anchor | 95% CI | outcome under the rule |
|---|---:|---|---|
| lenient | -0.0100 | [-0.0300, +0.0100] | **NOT MOVED** |
| contract-strict | +0.0700 | [+0.0417, +0.0983] | **MOVED** |

Steps, each either rule-mechanical or exact arithmetic:

1. Registered rule on the primary anchor, lenient contract: CP-member = -0.010000, 95% CI [-0.030000, +0.010000] contains zero, point estimate negative -> NOT MOVED. Exact McNemar two-sided p = 0.405032. This is a null and is reported as a null, not as a trend.

2. Registered rule on the primary anchor, contract-strict: CP-member = +0.070000, 95% CI [+0.041667, +0.098333] excludes zero positive -> MOVED. Exact McNemar two-sided p = 1.397e-06.

3. The registration forbids privileging either contract, so steps 1 and 2 alone select no branch.

4. Branch 1's antecedent is 'CP moves ... while matched same-data GRPO does not', not merely 'the difference is positive'. Against the frozen base on the primary anchor, CP is +0.0000 lenient and +0.0100 strict. CP does not move. Branch 1's antecedent is unsatisfied on both contracts.

5. The entire contract-strict primary-anchor gap is a response-format contract difference, by exact arithmetic: strict_delta = lenient_delta - (CP contract loss - member contract loss) = -0.010000 - (0.018333 - 0.098333) = +0.070000, matching the reported +0.070000 to 1.4e-17. CP contract_valid_rate 0.968333 vs member 0.813333.

6. Branch 3 is instrument-absent (no blind control arm; VAG not measurable here).

7. Branch 2's antecedent ('both flat') is the only pre-committed antecedent satisfied by the primary anchor as measured. Branch 2 fires.

### Branch fired: **branch_2** — Both flat -> reported as-is and the Paper-2 gate is reconsidered; premise-first redesign (C3 before C2), with C1 retained.

Scope of the read: Per binding spec section 3 the branch is read from the R19 coordinate survey register ONLY -- that task is THE primary endpoint, not the average of R19's three tasks and not any R20 or chart-v08 quantity. R19/R20/chart-v08 are three instruments and are never averaged (I13).

Recorded for completeness, not used to select the branch: R20's coordinate survey register shows the same lenient null in the CP-minus-member differential (+0.006667, CI [-0.013333, +0.026667], p = 0.617719) and the same contract-strict positive gap. Note separately that on R20's coordinate register BOTH arms sit above the cited R20 base on the lenient contract (member +0.0583, CP +0.0650) while being statistically indistinguishable from each other. That is a level fact about both arms, not a CP-versus-member difference, and it carries no CI.

Branch 3 ("components move attribution but not competence → engage C4") is **INSTRUMENT-ABSENT**: `PAPER2_RESEARCH_DOC.md` line 51 defines attribution as VAG against a matched same-data **blind** control on the real-image test. No blind arm is among the six F8 cells, so VAG is not measurable here. The lenient/strict contrast is a response-format contract and is **not** a proxy for VAG; it is not used as one.

Recorded alternative reading, so it is not hidden: A reader who privileges the contract-strict contract and applies section 5 in isolation -- ignoring both the section-3 no-privilege clause and the vs-base content of branch 1's antecedent -- would fire branch 1. That reading is recorded here so it is not hidden. It requires privileging one contract, which the registration forbids, and it requires reading 'CP moves' as satisfied by a gap that arithmetic attributes to member-arm contract-validity loss.

**Not softened:** The primary-anchor lenient result is a null with a negative point estimate. It is not reported as a trend, a partial move, or a directional signal.

## 9. Per-arm aggregates

From scripts/aggregate_fliptrack_eval.py. Its pair_accuracy_ci95_low/high fields are SINGLE-ARM descriptive intervals with seed hard-coded to 0 inside src.eval.fliptrack_metrics.pair_accuracy_ci and lenient-only; they are NOT the registered endpoint interval (reports/f8_eval_plan_v1.json blocking_limitations.aggregate_script_ci_is_not_the_registered_interval).

| cell | n | lenient pair acc | strict pair acc | contract valid | extraction fallback | collapse |
|---|---:|---:|---:|---:|---:|---:|
| chartv08_cp | 100 | 0.4700 | 0.2600 | 0.6600 | 0.3400 | 0.4000 |
| chartv08_member | 100 | 0.5100 | 0.1800 | 0.4800 | 0.5200 | 0.3300 |
| r19_cp | 1200 | 0.6333 | 0.4367 | 0.8496 | 0.1504 | 0.0417 |
| r19_member | 1200 | 0.6192 | 0.3875 | 0.8129 | 0.1871 | 0.0442 |
| r20_cp | 1200 | 0.6025 | 0.3933 | 0.8300 | 0.1700 | 0.0358 |
| r20_member | 1200 | 0.5858 | 0.3367 | 0.7937 | 0.2062 | 0.0408 |

## 10. Provenance and carried caveats

- All six cells: `run_manifest.status` = complete; `prompt_contract_sha256` = `['7ac39f53a2a824490fc5ee22671a888d2d79d55e1d8351919006d7d71c7a8f3f']` identically; binding env vars present at launch = [].
- `data_manifest_hash` by set: R19 `e1dde984…`, R20 `20222e60…`, chart-v08 `d90f3f13…`.
- Checkpoint index sha256 recomputed from disk: cp `4bb3b752…`, member `b4270b12…`.

- checkpoint_index_sha256 is null in all six run_manifest.json files. The launcher grants a provenance binding only for job_type l13_mechanical_pilot_arm / m3_mechanical_pilot_arm / m5_anchor_longhorizon_400; both Mini-A5 training runs carry m6_mini_a5_registered_main. The index sha256 was recomputed from disk and matches the plan's pinned values. The launcher, a git-diff-gated M5 contract file, was not amended.
- Per-worker exit codes are not captured anywhere by the harness. Launcher exit code 0 was captured for all six cells; worker success is evidenced by clean terminal state (all 24 worker logs end with the metrics JSON line, no tracebacks, no .partial files, finalizer validated every artifact). This is strong evidence, not a captured exit status.
- Intervals quantify evaluation uncertainty on a fixed pair set. They do NOT estimate run-to-run RL variance, and each arm is ONE run at ONE seed (docs/registered_mini_a5_endpoint_readout_v1.md section 4).
- The repo working tree was dirty at launch (one modified reports file plus many untracked tmp/ files) and HEAD is shared with the live M7 workstream. Verified: no dirty or concurrently-committed file is in the FlipTrack evaluation path. Verbatim git status at launch is recorded in reports/mini_a5_f8_run_provenance_v1.json.
- Registered secondaries not run here: catch-trial stability is INSTRUMENT-ABSENT (scripts/audit_mini_a5_catch.py never instantiates a checkpoint); 'the registered task benchmark' is UNRESOLVABLE from the registration; free-generation vs candidate-ranking is runnable but is not one of the six F8 cells. (docs/registered_mini_a5_endpoint_readout_v1.md section 6)
- No blind control arm was evaluated, so VAG / attribution (PAPER2 line 51) is not measurable from this readout and branch 3 could not be tested.

Artifacts: `reports/f8_mini_a5_endpoint_readout_v1.json` (this file's source of every number), `reports/mini_a5_f8_{r19,r20,chartv08}_paired_comparison_v1.json`, `reports/mini_a5_f8_*_aggregate_v1.json`, `reports/mini_a5_f8_run_provenance_v1.json`, `reports/mini_a5_f8_cell_verification_v1.json`.
