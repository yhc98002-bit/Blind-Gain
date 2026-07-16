# M5 Restore-and-Resume Plan V1

Status:
- Pre-run implementation and acceptance criteria are frozen; GPU integrity execution is pending capacity.
- This report does not declare M5 or a PI gate passed.

Evidence:
- M4 authorization: `reports/registered_extensions_authorization_v4.json`, SHA256 `081b77dde0af775dc6a846f9f8fa20fd72ca4aaadc307316fddbafc921146361`.
- Original anchor config: `configs/train/anchor_a0_recipe_3b_geo3k.yaml`, SHA256 `fdd39cead00fa6932d03c3040d90e76b71599983623b7478d67a309ce4dc3862`.
- One-step integrity config: `configs/train/m5_anchor_resume_integrity_step101.yaml`, SHA256 `e99535a24e75d451976e7a13caf031c388e7905748b56cdcb3f52cc9bdb04112`.
- Fixed terminal config: `configs/train/m5_anchor_longhorizon_400.yaml`, SHA256 `73ff58bd3b6a5a9a190f6f379a927bc6405c88001bd524f61846ffb22996f48c`.
- Step-100 relocation marker: SHA256 `28679132898ba3d207ce6d8666bf9dfd90c395cfbfb8c3be6f6fa4ca7403b3f9`.
- Archived raw-state manifest: SHA256 `b843071ebba161bb9257c61cd302082f7ca3baf5a9f4464ce863e6bb35d9f2c1`.
- Twelve focused restore/config/continuity tests pass.

Config lock:
- Both derived configs differ from the anchor at exactly `trainer.max_steps`, `trainer.experiment_name`, `trainer.save_freq`, `trainer.save_checkpoint_path`, and `trainer.load_checkpoint_path`.
- Native EasyR1 `r1v.py`, `freeze_vision_tower=false`, seed `1`, batch/GRPO/KL settings, and anchor TP2 rollout placement are unchanged.
- The integrity job targets exactly step 101. The scientific continuation reloads the original verified step-100 state, never the integrity checkpoint.

Predeclared integrity checks:
- The restored eight model/optimizer shard hashes must exactly match the relocation marker, and all 13 resume files must remain stable during a fresh SHA256 audit.
- The integrity log must contain exactly one training metric row at step 101, with source rows 91-100 present.
- Learning rate must remain `1e-6`; KL coefficient must remain `0.01`.
- `abs(pg_loss) <= 1`, `abs(kl_loss) <= 1`, gradient norm in `[0,10]`, reward in `[0,1]`, positive step time, and token count within `[0.5,2.0]` times the source-step-91-100 median.
- The step-101 checkpoint must pass the full resume-checkpoint audit.
- Integrity status is the logical AND of every enumerated check.

Problems:
- No four-GPU project-safe slot is currently available. Existing user processes are normal neighbors and will not be preempted.
- The restore temporarily returns roughly 44 GB of raw optimizer/model state to shared storage; the current allocation has sufficient headroom and the storage guard remains mandatory.

Decision:
- Queue the one-step integrity run on one node as soon as four GPUs pass stable capacity checks. Do not split across nodes.
- After integrity passes, launch the already registered fixed step-400 continuation. Step 400 remains terminal under every outcome.

Next actions:
- Run `scripts/launch_m5_anchor_restore.sh` and retain its immutable checkpoint audit.
- Launch the one-step integrity job, publish `reports/m5_restore_resume_integrity.md`, then start M5 without waiting for scientific interpretation.
