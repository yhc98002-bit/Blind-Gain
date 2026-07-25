# X4 — Visual-evidence calibration endpoint (v1) — EXPLORATORY

Computed from the X1 candidate-evidence ranking dumps only. Confidence is
the softmax probability of the top-ranked candidate; correctness is the
member's own gold ranked first. Facts only.

## ECE and overconfidence gap (member level, 2,400 members per cell)

| model | condition | accuracy | mean confidence | overconfidence gap | ECE (10-bin) |
|---|---|---|---|---|---|
| base | real | 0.7529 | 0.1788 | -0.5741 | 0.5741 |
| base | mismatched_real | 0.0779 | 0.1040 | +0.0261 | 0.0261 |
| base | twin_counterfactual | 0.0121 | 0.1788 | +0.1667 | 0.1667 |
| base | gray | 0.0725 | 0.0917 | +0.0192 | 0.0192 |
| base | no_image | 0.0650 | 0.0927 | +0.0277 | 0.0277 |
| a1_step100 | real | 0.7696 | 0.1999 | -0.5697 | 0.5697 |
| a1_step100 | mismatched_real | 0.0746 | 0.1088 | +0.0342 | 0.0342 |
| a1_step100 | twin_counterfactual | 0.0121 | 0.1999 | +0.1878 | 0.1878 |
| a1_step100 | gray | 0.0708 | 0.0933 | +0.0225 | 0.0225 |
| a1_step100 | no_image | 0.0667 | 0.0940 | +0.0273 | 0.0273 |
| a2_step100 | real | 0.7538 | 0.1867 | -0.5671 | 0.5671 |
| a2_step100 | mismatched_real | 0.0750 | 0.1051 | +0.0301 | 0.0301 |
| a2_step100 | twin_counterfactual | 0.0138 | 0.1867 | +0.1729 | 0.1729 |
| a2_step100 | gray | 0.0629 | 0.0938 | +0.0308 | 0.0308 |
| a2_step100 | no_image | 0.0671 | 0.0943 | +0.0272 | 0.0272 |
| a2b_step100 | real | 0.7504 | 0.1866 | -0.5638 | 0.5638 |
| a2b_step100 | mismatched_real | 0.0779 | 0.1058 | +0.0279 | 0.0279 |
| a2b_step100 | twin_counterfactual | 0.0133 | 0.1866 | +0.1733 | 0.1733 |
| a2b_step100 | gray | 0.0708 | 0.0942 | +0.0234 | 0.0234 |
| a2b_step100 | no_image | 0.0683 | 0.0942 | +0.0259 | 0.0259 |
| a3_step100 | real | 0.7600 | 0.1924 | -0.5676 | 0.5676 |
| a3_step100 | mismatched_real | 0.0767 | 0.1071 | +0.0304 | 0.0304 |
| a3_step100 | twin_counterfactual | 0.0125 | 0.1924 | +0.1799 | 0.1799 |
| a3_step100 | gray | 0.0700 | 0.0934 | +0.0234 | 0.0234 |
| a3_step100 | no_image | 0.0737 | 0.0938 | +0.0200 | 0.0200 |

Reliability-curve bin tables are in the machine JSON.
