# Stage 0 Literature And Repo Audit

Status:
- Initial current-source scan completed for multimodal RLVR recipes, counterfactual benchmarks, and Qwen model availability.
- EasyR1 and verl were cloned under `artifacts/repos/`.
- EasyR1 has the most direct Qwen2.5-VL-3B GRPO anchor for Stage 0.
- PAPO, MM-Eureka, Revisual-R1, and role-aware/explicit-reward multimodal RL papers remain directly relevant to positioning.
- VisualFLIP appears publicly visible through paper/index pages, but full benchmark artifact availability still needs verification.

Evidence:
- EasyR1 source: `https://github.com/hiyouga/easyr1`
- EasyR1 clone: `artifacts/repos/EasyR1`, commit `dd71bbd252694f5f850213eec15795b6b88d9fea`
- EasyR1 Qwen recipe: `artifacts/repos/EasyR1/examples/qwen2_5_vl_3b_geo3k_grpo.sh`
- verl source: `https://github.com/volcengine/verl`
- verl clone: `artifacts/repos/verl`, commit `6a4a0784337828523126ddd3d668524bd4578d4d`
- verl multimodal example: `https://verl.readthedocs.io/en/latest/examples/multi_modal_example.html`
- PAPO project page: `https://mikewangwzhl.github.io/PAPO/`
- MM-Eureka docs: `https://siirl.readthedocs.io/en/stable/examples/mm_eureka_example.html`
- VisualFLIP page found through search: `https://www.researchgate.net/publication/406465895_VisualFLIP_Do_Predictions_Depend_on_Task-Critical_Visual_Evidence_in_Multimodal_Reasoning`
- ModelScope targets:
  - `https://modelscope.cn/models/Qwen/Qwen2.5-VL-3B-Instruct`
  - `https://modelscope.cn/models/Qwen/Qwen2.5-VL-7B-Instruct`
  - `https://modelscope.cn/models/Qwen/Qwen3-VL-8B-Instruct`

Problems:
- ViRL39K availability/license still needs source verification before using it for the named reproduction subset.
- EasyR1’s ready recipe uses Geometry3K, not ViRL39K; using it as the first anchor is a controlled deviation unless ViRL39K is quickly available.
- Dataset licenses are not yet audited deeply enough for release.
- VisualFLIP artifact status is not yet resolved enough for novelty positioning.

Decision:
- Use EasyR1 as first reproduction target unless install/runtime compatibility fails; keep upstream verl as fallback/reference.
- Preserve the ViRL39K target in configs, but allow Geometry3K as the first working reproduction anchor because it is the published/local recipe already wired for Qwen2.5-VL-3B GRPO.
- Build FlipTrack renderable families regardless of VisualFLIP status because exact-pair generation and blind-training decomposition remain project-specific.

Next actions:
- Finish the active EasyR1 smoke run and record whether the SDPA workaround is sufficient for longer Qwen2.5-VL-3B GRPO.
- Verify ViRL39K source/license; if blocked, log the deviation and proceed with Geometry3K for Stage 0 reproduction.
- Continue literature and repo watch in `reports/literature_watch.md` and `reports/repo_watch.md`.
