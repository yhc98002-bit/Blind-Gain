# Seed-1 M10 Support-Sharpening Follow-Up V2

Status:
- Four-arm frozen-base follow-up complete under the registered 64-seed rule.
- This is a support-sharpening readout, not a claim that RL created or taught a capability.
- No scientific gate decision is made.

Evidence:
- Machine artifact: `reports/support_sharpening_seed1_v2.json`.
- Draw indices `16..79`; seeds `20260732..20260795`; one `n=1` output row per item and seed.
- Duplicate text responses were retained as distinct registered draws.
- Every 0/80 item has Jeffreys 95% posterior interval `[0.00000612, 0.03081626]`.

| Arm | Candidates | Follow-up draws | High-confidence support-expansion candidates | Observed in support-sharpening samples |
| --- | ---: | ---: | ---: | ---: |
| A1 real | 47 | 3008 | 16 | 31 |
| A2 gray | 8 | 512 | 1 | 7 |
| A2b no-image | 7 | 448 | 5 | 2 |
| A3 caption | 18 | 1152 | 2 | 16 |

Interpretation lock:
- Zero successes in 80 is `not observed in the base K-sample set` and carries the per-item Jeffreys 95% interval in the machine artifact.
- Any success in the new draws is `mass sharpening within observed support`.

Problems:
- Item-level sampling uncertainty does not measure run-to-run RL variance.

Decision:
- None. These classifications are folded into the seed-1 readout under the registered non-causal language.
