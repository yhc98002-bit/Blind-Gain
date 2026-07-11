# Pilot Reward Smoke Failure: Image-Grid Drift

Status:
- Failed. `pilot_reward_smoke_an29_20260711T111616Z` completed rollout generation but failed during the first actor log-probability pass, before optimizer step 1.
- L3 remains blocked. This report records a failed/superseded run and does not satisfy the L3 deliverable.

Evidence:
- Run: `experiments/runs/pilot_reward_smoke_an29_20260711T111616Z`.
- Node/GPU allocation: `an29`, physical GPUs `1,5,6,7`.
- Start/end: `2026-07-11T11:16:23Z` / `2026-07-11T11:24:34Z`; exit code `1`.
- The rollout reached the registered batch size of 512 and wrote 2,182 parseable reward-shadow rows before Ray terminated the workers.
- Failure: `ValueError: Image features and image tokens do not match: tokens: 3018, features 3032` in Qwen2.5-VL actor log-probability computation.
- The failed run and its shadow JSONL are retained unchanged.

Problems:
- The first image-condition patch resized each image before prompt tokenization and stored that resized image in `multi_modal_data`. EasyR1's rollout and FSDP workers then called `process_image` again. Integer resize rounding can change a dimension on the second pass, so prompt image-token counts and worker-produced visual features can diverge.
- The adversarial 20x36 fixture at `min_pixels=262144` exposes the old behavior: the first pass yields 381x686, while applying the same minimum-pixel resize to that result can produce 381x687.

Decision:
- Preserve the registered preprocessing thresholds. Send the unresized real image, or unresized deterministic gray/noise sibling, as the worker payload; independently derive prompt-processor pixels from that same payload exactly once.
- The reproducible follow-up is `docs/easyr1_multimodal_grid_patch.diff` plus `scripts/apply_easyr1_multimodal_grid_patch.sh`. It applies after the existing image/caption patches at pinned EasyR1 revision `dd71bbd252694f5f850213eec15795b6b88d9fea`.
- A clean-checkout image -> caption -> grid patch sequence applies and compiles. Nine focused image-condition fixtures pass; the frozen-corpus integration fixture was excluded from this focused command because its dataset teardown is independently slow.

Next actions:
- Relaunch the unchanged five-step A1 reward-plumbing smoke on the same four free GPUs.
- Require five completed optimizer steps and a passing shadow-log audit before changing L3 from `blocked`.
