# Canonical-v2 Parser Agreement Audit

Status:

- Complete for the exact registered 320-row sample. Parser fixtures, including unit-conflict and malformed-answer negatives, pass.
- The 0.95 agreement warning threshold is not met. The result requires PI review and is not evidence that canonical-v2 and native EasyR1 are equivalent.
- This report versions the old result; `reports/parser_agreement_audit.md` and its canonical-v1 numbers remain unchanged.

Evidence:

- Source generations: `experiments/runs/parser_agreement_geo3k_step30_an12_20260710T063542Z/shards/`, exactly four immutable 80-row shards.
- V2 audit: `experiments/runs/parser_agreement_audit_geo3k_step30_320_canonical_v2_20260711T095111Z/`.
- Audit git hash: `bf30af0fa6b13a1bf1f3812f14226504a408d85f`.
- Config hash: `247102fdbbd2b4d022d248b8cf38067155382048530c265e24ff744a3351365b`.
- Input manifest hash: `c60217a7174633f0791e46e52194f67aec5e53da9048810451ca36e5f50b5db0`.
- `rows.jsonl` SHA256: `0e394dd87dc84f2f6733a31112d48e5fd67473fab617da3b879390d7f852349e9`.
- `metrics.json` SHA256: `aa53838431bc21f1510ec9ccae7ed163e34120d17745707551a6e0cd2f2a6b89`.
- Focused test command: `python -m pytest tests/test_reward_parser.py tests/test_parser_agreement.py tests/test_scorer_adversarial.py tests/test_fliptrack_metrics.py -q`.
- Focused result: 28 tests passed.

## Exact Comparison

| Parser | n | Canonical accuracy | Native EasyR1 accuracy | Agreement | Disagreements | Canonical only | EasyR1 only |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| canonical-v1 | 320 | 0.109375 | 0.075000 | 0.921875 | 25 | 18 | 7 |
| canonical-v2 | 320 | 0.159375 | 0.075000 | 0.915625 | 27 | 27 | 0 |

The lower agreement is not an observed accuracy regression. Canonical-v2 resolves every former EasyR1-only row and accepts nine additional semantically compatible unit-suffixed answers that native mathruler rejects. Native EasyR1 accuracy is unchanged.

## Closed V1 Classes

| Class | V1 row indices | V2 outcome |
| --- | --- | --- |
| Unit suffixes omitted by unitless gold | 75, 166, 198, 260 | Canonical and EasyR1 both correct |
| TeX presentation wrappers and spacing | 83, 190, 304 | Canonical and EasyR1 both correct |

The unit matcher compares explicit units before stripping. `5 cm` versus `5 m` is false, as are the corresponding `\\text{}` forms. It performs no unit conversion. Stripping is permitted only when both units are the same or one answer is unitless and the core is numeric or mathematical.

## Residual Taxonomy

| Residual class | Count | Row indices | Explanation |
| --- | ---: | --- | --- |
| Multiline `<answer>` rejected by native extractor | 14 | 16, 18, 58, 61, 68, 90, 121, 139, 163, 177, 212, 261, 306, 309 | Native `r1v.py` uses a non-DOTALL answer regex and grades the full response. Canonical-v2 extracts the correct span. |
| Unit-suffixed answer rejected by native mathruler | 9 | 1, 7, 22, 47, 101, 159, 199, 224, 283 | Canonical-v2 safely matches the unitless gold; native reward returns zero. |
| Exact or boxed answer rejected by native mathruler | 4 | 54, 137, 180, 275 | Canonical-v2 extracts an exact gold answer; native mathruler returns zero. |

All 27 residual disagreements are canonical-only. There are no EasyR1-only residuals.

Problems:

- Agreement is 0.915625, below the registered 0.95 warning threshold.
- Agreement is not an appropriate sole quality target here: matching the native non-DOTALL behavior would intentionally reintroduce a known extraction error.
- The L3 pilot reward must log mathruler-versus-canonical disagreement explicitly because these graders remain asymmetric.

Decision:

- Retain `canonical-v2`; do not weaken it to imitate native extraction failures.
- Keep the anchor bound to native `r1v` unchanged.
- Use canonical-v2 extraction in the pilot reward, with mathruler verdict precedence and shadow disagreement reason codes exactly as specified in L3.
- Mark the L1 ledger note for PI review because the warning threshold is not met.

Next actions:

- Stamp `parser_version: canonical-v2` into every newly generated scoring row and aggregate.
- Complete L2's independent `extractor_valid` and `contract_valid` fields before changing strict metrics in any new table.
