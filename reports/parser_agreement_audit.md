# Parser Agreement Audit

Status:
- Complete. The recovered step-30 checkpoint was re-evaluated on 320 deterministic Geometry3K test examples.
- Canonical-vs-EasyR1 accuracy agreement is 92.1875%, below the 95% warning threshold; all 25 disagreements are preserved row by row.

Evidence:
- Original recovery run: `experiments/runs/easyr1_geo3k_recovery30_20260708T043244Z`.
- Original `generations.log` contained only two examples, so it could not satisfy the registered sample floor.
- Recovered actor merge: `experiments/runs/easyr1_checkpoint_merge_recovery30_step30_retry_an12_20260710T063231Z`.
- Generation run: `experiments/runs/parser_agreement_geo3k_step30_an12_20260710T063542Z`; four immutable shards of 80 rows each.
- Audit run: `experiments/runs/parser_agreement_audit_geo3k_step30_320_20260710T065140Z`.
- Machine metrics: `metrics.json`; every response, extracted span, score, and disagreement direction is in `rows.jsonl`.

Agreement table:

| Source | n | Canonical accuracy | EasyR1 accuracy | Agreement | Disagreements |
| --- | ---: | ---: | ---: | ---: | ---: |
| recovered `global_step_30`, Geometry3K test | 320 | 0.109375 | 0.075000 | 0.921875 | 25 |

Disagreement breakdown:

| Direction | Count | Primary cause |
| --- | ---: | --- |
| canonical correct, EasyR1 wrong | 18 | 14 multiline `<answer>` spans missed by EasyR1's non-DOTALL regex; 4 simple exact answers rejected by `mathruler` |
| EasyR1 correct, canonical wrong | 7 | benign unit suffixes or LaTeX presentation wrappers rejected by canonical normalization |

Problems:
- This is a logged re-evaluation of the old recovery checkpoint, not a sample recovered from the original training log. That deviation is necessary because the original run preserved only two generations.
- EasyR1 `r1v.py` uses `re.search(r"<answer>(.*?)</answer>")` without `re.DOTALL`; answers formatted on separate lines fall through to grading the full response.
- The canonical matcher is intentionally conservative and currently rejects semantically benign forms such as `5 meters`, `163 degrees`, and `\(\sqrt{21}\)` when the gold omits units or wrappers.
- A diagnostic DOTALL-only EasyR1 extraction raises agreement to 0.94375, still below 0.95 because the two matchers implement different mathematical normalization.

Decision:
- Treat P0.2's audit deliverable as complete, but do not claim parser equivalence.
- Keep current result tables versioned under the existing canonical scorer; do not silently rescore them after normalization changes.
- Before P2.1 headline evaluation, add adversarial fixtures for safe unit stripping and LaTeX delimiter normalization, version the canonical matcher, and use its extractor in the EasyR1 custom reward path.
- Preserve native EasyR1 reward accuracy and canonical evaluation accuracy as separate fields until a versioned re-audit exceeds 95%.

Next actions:
- Implement canonical v2 normalization for explicit units and math delimiters with false-positive fixtures.
- Replace the future custom EasyR1 reward extractor with the canonical extraction function, including multiline answer tags.
- Re-run this exact 320-row audit after that versioned change and publish both old and new agreement rates.
