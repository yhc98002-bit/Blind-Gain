# GRPO Chat Template Audit V2

Status:
- `pass` for the dedicated 8-train/8-test rendered-prompt audit.
- This is an implementation audit, not a published-reproduction or PI gate verdict.
- The predecessor `reports/grpo_chat_template_audit.md` remains unchanged and is superseded by this version.

Evidence:
- Machine artifact: `reports/grpo_chat_template_audit_v2.json`; all `11` checks true.
- Config SHA256: `fdd39cead00fa6932d03c3040d90e76b71599983623b7478d67a309ce4dc3862`.
- Source manifest SHA256: `0ac91fb836f39776acd5137ccd5cca7259d4ad0a836347be60f96f535d00f639`.
- r1v format prompt SHA256: `f1b62cb8332bdbec38efc8689aff6e9ce65174c0db8967937307880f95f58fca`.
- Qwen processor chat-template SHA256: `a0bc6f6fc7a29a80017a433e8f03a1cc1236e838a944a2d034295a60c4f2fddb`.
- Prompt-token ranges: train `436-501`; test `446-635`; configured maximum `2048`.
- Every source image has exactly one rendered Qwen vision marker, and every prompt contains the registered think/answer contract plus assistant generation prompt.

Problems:
- This sample proves deterministic rendering and contract wiring for 16 fixed rows; the full-corpus image-grid audit is reported separately in `reports/easyr1_image_grid_audit_v1.md`.
- Prompt rendering does not establish reward-parser equivalence; `reports/parser_agreement_audit_v2.md` retains the below-0.95 native/canonical warning.

Decision:
- Pin the resolved r1v and Qwen chat-template hashes for the engineering anchor and pilot configs.
- Treat any future template/hash change as a new evaluation contract.

Next actions:
- Stamp both hashes in future training/evaluation manifests and retain rendered samples for any new model family.
