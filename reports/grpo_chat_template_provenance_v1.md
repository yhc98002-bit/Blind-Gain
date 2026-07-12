# GRPO Chat-Template Provenance V1

Status:
- `pass` for binding `reports/grpo_chat_template_audit_v2.*` to the successful 100-step anchor’s prompt-critical configuration.
- This resolves a report discrepancy; it does not change the engineering-anchor or proposal-gate classification.

Evidence:
- Successful parent run: `experiments/runs/anchor_a0_recipe_3b_geo3k_20260709T224852Z`; recorded `base_config_hash=fdd39cead00fa6932d03c3040d90e76b71599983623b7478d67a309ce4dc3862`.
- Completed step-80 resume: `experiments/runs/anchor_a0_recipe_3b_geo3k_resume80_20260711T150633Z`; records the same base config hash.
- Tracked config at commit `93fead5` and current audited config both hash to `fdd39cead00fa6932d03c3040d90e76b71599983623b7478d67a309ce4dc3862`.
- Resolved checkpoint config: `checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z/experiment_config.json`, SHA256 `fdbc29d475c23afce00f9cfa8ffd3a7a894e72a7be5027245ba9c161c61bbcaa`.
- Resolved/current values are identical for `prompt_key`, `answer_key`, `image_key`, `max_prompt_length`, `format_prompt`, `override_chat_template`, `min_pixels`, and `max_pixels`.
- The anchor and L3 logs both record the same Transformers fast-image-processor default warning used by the V2 rendering audit.

Discrepancy:
- `reports/anchor_recipe_report.md` cites config hash `5bed99b9...` while describing the later successful run. Run manifests show that hash on earlier failed launch attempts `20260709T213030Z`, `213103Z`, `215715Z`, and `215854Z`.
- The successful `20260709T224852Z` run instead records base config hash `fdd39...` and effective override hash `45a99272...`.
- The launch commit `680f1fa` did not yet track the config file, so Git alone cannot reconstruct it at that commit. The run manifest’s base hash, later byte-identical tracked file, and resolved EasyR1 config provide the surviving provenance chain.

Decision:
- Retain the V2 chat-template implementation status as pass.
- Treat `reports/anchor_recipe_report.md` as stale for config identity and completion status; use `reports/anchor_recipe_report_v2.md` instead.
- Continue to classify the run as an engineering anchor, not a published reproduction.

Next actions:
- Require immutable effective-config snapshots in every pilot run directory; the L13 launcher already does this.
