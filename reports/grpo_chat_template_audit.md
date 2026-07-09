# GRPO Chat Template Audit

Status:
- Recovery GRPO uses EasyR1's r1v prompt template.
- The prompt path is fixed in config and included in the run manifest hash.

Evidence:
- Prompt template: `artifacts/repos/EasyR1/examples/format_prompt/r1v.jinja`
- Recovery config field: `data.format_prompt`
- EasyR1 dataset path calls `processor.apply_chat_template(..., add_generation_prompt=True)`.

Risk:
- No side-by-side rendered prompt sample is committed yet for the recovery run.
- Chat template deviations can affect reward format compliance and should be frozen before longer runs.

Decision:
- Accept for recovery anchor.
- Require rendered prompt examples before long GRPO runs or A1/A2 pilot.

Next actions:
- Dump 8 train and 8 validation rendered prompts with image counts and token lengths.
- Confirm `<think>`/`<answer>` format aligns with reward parser expectations.
