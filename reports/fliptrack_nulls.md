# FlipTrack Registered Nulls

Status:
- P0.3 is implemented and tested.
- The primary null shuffles answer-key pairs across examples within each template.
- The auxiliary null independently swaps member predictions within each pair.

Evidence:
- Implementations: `template_key_shuffle_null_pair_accuracy` and `permutation_null_pair_accuracy` in `src/eval/fliptrack_metrics.py`.
- Aggregator: `scripts/aggregate_fliptrack_eval.py` emits `key_shuffle_null_mean`, `key_shuffle_null_p_ge`, `swap_null_mean`, and `swap_null_p_ge` separately.
- Tests: `test_template_key_shuffle_null_runs` and `test_permutation_null_runs` in `tests/test_fliptrack_metrics.py`.
- Frozen R19 caption analysis reports the primary within-template null in `reports/fliptrack_caption_leakage_audit.md`.

Problems:
- A within-template group of one pair cannot be permuted and contributes its observed score unchanged; retained R19 templates have hundreds of pairs, so this edge case does not control the reported null.

Decision:
- Use the within-template key shuffle as the preregistered primary null.
- Keep the within-pair swap as an explicitly labeled auxiliary diagnostic and never substitute it for the primary null.

Next actions:
- Apply both locked null implementations unchanged to future checkpoint evaluations.
