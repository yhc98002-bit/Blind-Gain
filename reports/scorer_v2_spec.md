# FlipTrack Scorer V2 Specification

Status:
- Implemented in `src/eval/fliptrack_metrics.py`.
- Canonical answer extraction is shared with `src/rewards/answer_reward.py`.
- Adversarial fixtures are in `tests/test_scorer_adversarial.py`.

Evidence:
- `PYTHONPATH=. python -m pytest tests/test_reward_parser.py tests/test_fliptrack_metrics.py tests/test_scorer_adversarial.py`
- Result during implementation: 21 tests passed.

## Extraction Ladder

`extract_answer_span(prediction)` tries these levels in order:

1. `tag`: last `<answer>...</answer>` span.
2. `boxed`: last balanced `\boxed{...}` span, including nested braces such as `\boxed{\frac{1}{2}}`.
3. `line`: last line beginning with `Answer:` or `Final answer:`.
4. `lastline`: last non-empty line. This sets `extraction_fallback_used=true`.
5. `fulltext`: full text when no non-empty line exists. This sets `extraction_fallback_used=true`.

`format_valid=true` only for `tag`, `boxed`, and `line`.

## Matching Tiers

For each extracted span and candidate gold:

- Tier 2: exact normalized equality or numeric equivalence.
- Tier 1: word-boundary containment of the normalized gold in the extracted span.
- Tier 0: no match.

Numeric equivalence handles floats, fractions, percentages, currency commas, and simple LaTeX fractions.

## Multi-candidate Guard

Each side is scored against its intended gold and the paired counterfactual gold.

- If both golds match at the same highest non-zero tier, the side is incorrect and `ambiguous=true`.
- If exactly one gold wins at a strictly higher tier, the side is not ambiguous and is scored against the winning tier.
- Full prediction mentions of both golds do not change primary accuracy when the extracted final span is unique; they only set `full_text_mentions_both=true`.
- If extraction falls to `fulltext`, the same multi-candidate guard applies to the full text.

## Pair and Aggregate Fields

Per pair, `pair_score(row)` returns compatibility fields plus scorer-v2 diagnostics:

- `correct_a`, `correct_b`, `pair_correct`
- `strict_correct_a`, `strict_correct_b`, `strict_pair_correct`
- `acc_final`, `acc_strict`
- `format_valid`
- `ambiguous`
- `full_text_mentions_both`
- `extraction_fallback_used`
- `extraction_level`
- side-specific extracted answer, extraction level, format validity, ambiguity, and match tiers

Aggregate metrics include:

- `member_accuracy`, `pair_accuracy`
- `strict_member_accuracy`, `strict_pair_accuracy`
- `collapse_rate`
- `ambiguous_rate`
- `full_text_mentions_both_rate`
- `format_valid_rate`
- `extraction_fallback_rate`

Decision:
- Primary accuracy is based on extracted final spans, not raw full-text scans.
- `full_text_mentions_both` is a diagnostic signal only, not a penalty.
