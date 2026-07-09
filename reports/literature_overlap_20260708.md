# Literature Overlap Audit - 2026-07-08

Status:
- Blind Gains remains strongest as a controlled decomposition and public counterfactual measurement paper.
- CP-GRPO should be framed as a constructive arm unless a deeper audit proves standalone novelty.
- If CPPO/CFPO implementations are runnable, add at least a small conceptual or empirical comparison.

Items:

| Item | Claim / role | Public code/data status | Threat | Action |
| --- | --- | --- | --- | --- |
| PAPO | Perception-aware multimodal policy optimization lineage for VLM RL. | Project page/repo references found; exact recipe still needs pinning. | C3 constructive novelty risk. | Use as primary related work and compare reward/grouping differences. |
| CPPO | Counterfactual/preference policy optimization family. | Needs implementation/source verification. | C3 risk if it already uses paired counterfactual reward. | Audit runnable code and add comparison if feasible. |
| CFPO | Counterfactual feedback/policy optimization family. | Needs implementation/source verification. | C2/C3 risk depending on measurement vs training claim. | Add conceptual ablation or cite as repair-method overlap. |
| Dr. Seg | Segmentation-grounded or diagnostic VLM method; exact overlap unresolved. | Search did not identify a stable local artifact yet. | Possible C2 measurement overlap. | Continue targeted search before paper positioning. |
| VisualFLIP | Counterfactual visual dependence benchmark. | Public paper/index visible; full benchmark availability unresolved. | C2 FlipTrack novelty risk. | Position FlipTrack around controlled generation, decomposition arms, and release value; compare protocol if public. |
| MM-Eureka | Multimodal RL recipe/evaluation lineage. | Docs/examples available. | C1/C3 related-work risk. | Use for recipe comparison and benchmark context. |
| VL-Rethinker / ViRL39K | VLM RLVR dataset/lineage. | ViRL39K HF path found but loader failed locally. | C1 reproduction source dependency. | Fix acquisition path or log Geometry3K fallback. |
| EasyR1 | Practical Qwen2.5-VL GRPO recipes. | Local clone and examples exist. | Not novelty threat; infrastructure anchor. | Primary recovery stack until verl is cleaner. |
| verl | Broad RLHF/RLVR stack with Qwen2.5-VL/Qwen3-VL examples. | Local clone has Qwen2.5-VL-7B GRPO and Qwen3-VL examples. | Infrastructure alternative. | Keep as fallback/reference; avoid Qwen3-VL env mixing. |

Decision:
- Lead the paper with the vulnerable assumption and decomposition, not with CP-GRPO novelty.
- Treat CP-GRPO as a repair/constructive arm and measure whether it improves certified visual dependence.

Next actions:
- Pin exact PAPO/CPPO/CFPO citations and code URLs.
- If VisualFLIP data is public, run a compatibility subset or compare protocols.
