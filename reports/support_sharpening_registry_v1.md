# Support-Sharpening Registry V1

Status:
- Protocol and adapter: `pass`.
- M10 remains `blocked` until applicable post-training readouts exist and every selected item receives the registered 64-sample follow-up.
- No scientific gate is declared.

Evidence:
- Machine contract: `configs/eval/support_sharpening_v1.json`.
- Implementation: `src/analysis/support_sharpening.py`.
- Tests: `tests/test_support_sharpening.py`.
- Fixed initial audit size: 16 samples; fixed follow-up: 64 samples; fixed total: 80 base-model samples.

Eligibility:
- Join baseline and post-training rows exactly by `(split, row_index)`.
- Bind each arm to its own frozen baseline condition.
- Select only rows with baseline `sample_correct_count == 0`, `sample_count == 16`, step-0 greedy `Acc_final == false`, and greedy `Acc_final == true` at that readout's registered target checkpoint (step 100 for M2).
- Any duplicate identity, row-set mismatch, condition mismatch, non-boolean readout, or non-16 baseline fails closed.

Readout:
- Draw exactly 64 additional samples from the frozen base checkpoint under the same prompt, condition, decoding, parser, and reward contract as the initial audit.
- Recompute a Jeffreys posterior from all 80 outcomes and report its 95% interval.
- Use `high-confidence support-expansion candidate` only when all 64 follow-up samples are also incorrect, leaving zero observed successes in 80.
- Otherwise report `observed in support-sharpening samples`.

Language lock:
- Allowed: `mass sharpening within observed support`.
- Allowed: `not observed in the base K-sample set`.
- Forbidden: claims that RL `created` or `taught` a capability.

Problems:
- M2 has no final four-arm per-item readout yet, so no candidate manifest can be frozen.
- Every candidate row carries its registered target-step label; later checkpoints cannot be silently treated as step 100.

Next actions:
- Build one immutable candidate manifest per arm when the audited per-item M2 readout lands.
- Run 64 base samples per candidate and attach the summary artifact to the corresponding readout.
