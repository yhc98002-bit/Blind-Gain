# M11 InternVL Blind-Sample Recovery V1

Status:
- Recovery implementation and relaunch are complete; M11 remains blocked while the three fresh 4,096-row cells run.
- No model-performance value was opened during diagnosis, staging, or relaunch.

Evidence:
- Failed immutable real-image run: `experiments/runs/m11_blind_internvl3_virl4096_real_internvl3_real_s0of1_an29_20260716T155531Z`.
- Failed immutable no-image run: `experiments/runs/m11_blind_internvl3_virl4096_none_internvl3_none_s0of1_an29_20260716T155536Z`.
- Both failed before inference with `ModuleNotFoundError: No module named 'mathruler'`. `scripts/eval_nonqwen_blind_sample.py` imported data-conditioning helpers from `src.eval.blind_solvability`, whose module-level pilot-reward import unnecessarily pulled `mathruler` into the inference-only runtime.
- Commit `70444e715ac944017a2cc3ffb3c199fef2116cff` moves the three input helpers to `src/eval/conditioned_inputs.py`; `src.eval.blind_solvability` re-exports them for compatibility, while the non-Qwen script imports the lightweight module directly.
- Adversarial fixture: `test_nonqwen_blind_script_import_does_not_require_mathruler` blocks every `mathruler` import in a fresh subprocess. The old import path fails this fixture; the fixed path imports successfully.
- Verification: 32 focused non-Qwen and blind-solvability tests passed. The frozen `.venv-m11` imports `scripts.eval_nonqwen_blind_sample` without installing or mutating any package.
- Hash-verified ModelScope stage: `experiments/runs/m11_stage_InternVL3-9B_an12_20260716T170439Z`; 18,282,482,992 source bytes, 25 files, status `complete`, SHA256 manifest `8344c367d2c6cec273d212baf6cce902fac78fbc513871e67588c51511923cd8`.
- Fresh real-image run: `experiments/runs/m11_virl4096_retry1_internvl3_real_s0of1_an12_20260716T170736Z`, an12 GPU 4, TP1, one replica.
- Fresh no-image run: `experiments/runs/m11_virl4096_retry1_internvl3_none_s0of1_an12_20260716T170739Z`, an12 GPU 5, TP1, one replica.
- Fresh fixed-caption run: `experiments/runs/m11_virl4096_retry1_internvl3_caption_s0of1_an12_20260716T170744Z`, an12 GPU 6, TP1, one replica.

Problems:
- The retries are active and do not yet have complete per-item or aggregate artifacts.
- Nine Gemma-3 cells remain queued. The four ongoing InternVL FlipTrack cells on an29 are undisturbed.

Decision:
- Repair the import boundary rather than mutate the frozen inference environment. This keeps the scientific runtime dependency set unchanged and removes a training-only dependency from inference.
- Use an12 GPUs 4-6 because M5 is isolated on GPUs 0-3 and seed-2 A1 is isolated on an29 GPUs 2/5/6/7. All M11 jobs remain single-node TP1.

Next actions:
- Monitor each retry for process health and row advancement without opening accuracy values.
- Reconcile complete InternVL cells into the M11 matrix, then schedule the nine Gemma cells according to PI priority and free capacity.
