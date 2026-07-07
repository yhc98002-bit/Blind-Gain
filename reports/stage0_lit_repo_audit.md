# Stage 0 Literature And Repo Audit

Status:
- Initial current-source scan completed for multimodal RLVR recipes, counterfactual benchmarks, and Qwen model availability.
- EasyR1 and verl both expose Qwen2.5-VL GRPO examples; EasyR1 appears to be the fastest reproduction anchor.
- PAPO, MM-Eureka, Revisual-R1, and newer role-aware / explicit-reward multimodal RL papers are directly relevant.
- VisualFLIP appears publicly visible through paper/index pages, but full benchmark artifact availability still needs verification.

Evidence:
- EasyR1 repository: https://github.com/hiyouga/easyr1
- verl multimodal example: https://verl.readthedocs.io/en/latest/examples/multi_modal_example.html
- PAPO project page: https://mikewangwzhl.github.io/PAPO/
- MM-Eureka example/docs: https://siirl.readthedocs.io/en/stable/examples/mm_eureka_example.html
- VisualFLIP public page found through search: https://www.researchgate.net/publication/406465895_VisualFLIP_Do_Predictions_Depend_on_Task-Critical_Visual_Evidence_in_Multimodal_Reasoning
- Qwen ModelScope targets:
  - https://modelscope.cn/models/Qwen/Qwen2.5-VL-3B-Instruct
  - https://modelscope.cn/models/Qwen/Qwen2.5-VL-7B-Instruct
  - https://modelscope.cn/models/Qwen/Qwen3-VL-8B-Instruct

Problems:
- Need repository-level inspection of EasyR1 versus verl after dependencies are available.
- Dataset licenses are not yet audited.
- VisualFLIP artifact status is not yet resolved enough for novelty positioning.

Decision:
- Use EasyR1 as first reproduction target unless install/runtime compatibility fails; keep verl as fallback/reference.
- Build FlipTrack renderable families regardless of VisualFLIP status because exact-pair generation and blind-training decomposition remain project-specific.

Next actions:
- Clone/inspect EasyR1 and verl recipes after GitHub access is stabilized through login/proxy.
- Build `reports/license_log.csv` for datasets and model artifacts before any release.
- Continue literature watch in `reports/literature_watch.md`.

