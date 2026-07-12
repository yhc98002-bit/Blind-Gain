# Strong Caption Stress

Status:
- R19 and R20 were captioned once with the fixed question-blind 72B prompt at 384 tokens and answered with the standard 7B caption-only QA protocol.
- This measures caption leakage headroom only; it does not repair the document template's 7B visual ceiling.
- This is a stress-test result, not a PI gate declaration.

Evidence:
- Captioner: `Qwen/Qwen2.5-VL-72B-Instruct` revision `master`, one TP4 replica.
- Machine report: `reports/strong_caption_stress.json`.
- Ephemeral model bytes deleted after caption-store commit: `146833336607`.

| Package | Template | Pairs | 7B-caption baseline | 72B-caption stress | Delta | Strong collapse |
|---|---|---:|---:|---:|---:|---:|
| R19 | overall | 1200 | 0.0208 | 0.0533 | +0.0325 | 0.3367 |
| R19 | document | 300 | 0.0600 | 0.0500 | -0.0100 | 0.5667 |
| R19 | geometry | 600 | 0.0083 | 0.0733 | +0.0650 | 0.3100 |
| R19 | chart | 300 | 0.0067 | 0.0167 | +0.0100 | 0.1600 |
| R20 | overall | 1200 | 0.0225 | 0.0617 | +0.0392 | 0.2950 |
| R20 | document | 300 | 0.0633 | 0.0667 | +0.0033 | 0.4567 |
| R20 | geometry | 600 | 0.0100 | 0.0733 | +0.0633 | 0.2717 |
| R20 | chart | 300 | 0.0067 | 0.0333 | +0.0267 | 0.1800 |

Problems:
- A stronger captioner can expose more visual facts, so low leakage under a 3B/7B captioner is not a universal text-channel guarantee.
- Caption-only success remains a property of the fixed captioner-plus-QA protocol, not a proof that pixels are unnecessary for arbitrary policies.

Decision:
- Report per-template headroom and retain the original R19/R20 visual and caption baselines unchanged.
- Treat the document 7B saturation as a separate instrument limitation.
- Keep no model weights on shared storage; the guarded deletion record is required and included.

Next actions:
- Carry the strongest observed caption-only cell into the preregistration caveats and paper limitations.
