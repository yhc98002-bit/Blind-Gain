# M11 Model Access Readiness

Status:
- InternVL3-9B acquisition is unblocked through ModelScope.
- Gemma-3-12B-IT acquisition is unblocked through ModelScope; Hugging Face
  remains manually gated without a local token.
- Both downloads are assigned to `an29` node-local `/dev/shm`. M11
  evaluation remains in progress.

Access evidence:
| Model | Preferred source | Access | Declared size | License | Revision |
| --- | --- | --- | ---: | --- | --- |
| OpenGVLab/InternVL3-9B | `https://modelscope.cn/models/OpenGVLab/InternVL3-9B` | public, ungated | 18,282,474,800 bytes | MIT | ModelScope `master`; HF mirror `5f618513...` |
| google/gemma-3-12b-it | `https://modelscope.cn/models/google/gemma-3-12b-it` | public ModelScope mirror | 24,414,163,682 bytes | Gemma | ModelScope `master`; HF mirror `96b6f1ec...` |

Policy checks:
- ModelScope-first: true.
- Domestic route without international proxy: true.
- Shared checkpoint/model quota consumed: zero.
- Node-local destination is explicitly re-derivable: true.
- Gemma terms retained for release review: true.
- Molmo-7B-D substitution: absent.

Evaluation contract:
- Conditions: real, no-image, and fixed question-blind caption.
- Instruments: FlipTrack R19, FlipTrack R20, and the frozen blind-solvability
  sample.
- Greedy lock: temperature 0, top_p 1, n 1, fixed maximum tokens and prompt
  contract.
- Each model runs on one node with the narrowest fitting TP width; the TP width
  is fixed only after a memory smoke.

Next actions:
- Hash each downloaded artifact and run a 20-item multimodal smoke.
- Implement model-specific message adapters behind the common evaluator.
- Publish only final measurements in `reports/generalization_audits_v1.md`.
