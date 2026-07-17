# M10 Support-Sharpening Execution Status V2

Status:
- All four registered frozen-base follow-up arms completed with exit 0.
- The fail-closed V2 finalizer accepted all 5,120 draw rows and all four run manifests.
- M10 execution and reporting are complete; no scientific gate decision is made.

Evidence:

| Arm | Node | GPU | Candidates | Draw rows | Run directory |
| --- | --- | ---: | ---: | ---: | --- |
| A1 real | an12 | 4 | 47 | 3,008 | `experiments/runs/m10_support_seed1_a1_real_an12_gpu4_20260717T073205Z` |
| A2 gray | an12 | 7 | 8 | 512 | `experiments/runs/m10_support_seed1_a2_gray_an12_gpu7_20260717T081241Z` |
| A2b no-image | an12 | 7 | 7 | 448 | `experiments/runs/m10_support_seed1_a2b_noimage_an12_gpu7_20260717T082403Z` |
| A3 caption | an12 | 7 | 18 | 1,152 | `experiments/runs/m10_support_seed1_a3_caption_an12_gpu7_20260717T073450Z` |

- Machine readout: `reports/support_sharpening_seed1_v2.json`, SHA256
  `8ad68b170c5334bcbec6c2d0722aa4b00283eb6cefaa99843ecb1a6352f47cbc`.
- Human readout: `reports/support_sharpening_seed1_v2.md`, SHA256
  `415d66812703d3b39c7d588f7cace27e5ab3c9683c648e3b67817f29ac5322e7`.
- Execution config SHA256:
  `6cddeb4c3871759e239c698df02333beb104b6ec8e1c0684a0aebae6aac79cd8`.
- Every candidate has exactly draw indices 16 through 79 and seeds
  `20260716 + j`; each request used `n=1`, and duplicate texts were retained.
- The remaining-arm queue completed with `performance_values_opened=false`.

Problems:
- The first direct finalizer invocation omitted `PYTHONPATH=.` and failed at
  import time before reading a row or writing an artifact. The finalizer now
  bootstraps the repository path, and a direct-CLI regression runs with
  `PYTHONPATH` removed.
- V1 remains immutable. V2 supersedes it as the human-facing report because V2
  prints the registered numeric Jeffreys interval for 0/80 items.

Decision:
- Record M10 as operationally complete and fold V2 into the seed-one evidence.
- Retain the registered non-causal wording; these draws do not establish that RL
  created or taught a capability.
