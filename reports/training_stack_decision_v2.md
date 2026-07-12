# Training Stack Decision V2

Status:
- EasyR1 remains the primary Qwen2.5-VL-3B GRPO engineering stack for prelaunch and the four-arm pilot.
- The native-reward anchor completed 100 optimizer steps and produced a verified final checkpoint, but it is not labeled a published reproduction because the resume truncated steps 1–80 from the structured metric log.
- `verl` remains the fallback/reference stack; no cross-stack switch is justified during the current prelaunch run.

Evidence:
- EasyR1 revision: `dd71bbd252694f5f850213eec15795b6b88d9fea`.
- verl revision: `6a4a0784337828523126ddd3d668524bd4578d4d`.
- Runtime: PyTorch `2.5.1+cu121`, Transformers `4.56.2`, vLLM `0.7.3`, with `EASYR1_ATTN_IMPLEMENTATION=sdpa`.
- Anchor completion and final checkpoint hashes: `reports/anchor_step100_oom_recovery_v2.md`.
- Metric-continuity limitation: `reports/anchor_metric_continuity_audit_v1.md` and `.json`.
- Replacement pilot-smoke launcher snapshots the current EasyR1 worktree diff and patched logger in each immutable run directory; the v6 audit verifies both hashes.

Tracked EasyR1 patch set:
| Patch | SHA256 | Purpose |
| --- | --- | --- |
| `docs/easyr1_sdpa_patch.diff` | `12a7692496bec81dc272a10a41ecfadb2fd40c8e065a7fd37b3f7fb1c97eb095` | Explicit SDPA fallback instead of an untracked FlashAttention mutation |
| `docs/easyr1_image_condition_patch.diff` | `ad06e17e417e2505f78ba03f5a570da78d68997a47617d4fe2fba42844b906d0` | Real/gray/noise/none condition handling |
| `docs/easyr1_caption_condition_patch.diff` | `eda01a273fe3f1039ee5d555341150310c263922de749489aed3800d4260557d` | Fixed caption-only arm with no image payload |
| `docs/easyr1_multimodal_grid_patch.diff` | `a2441fa85794d94fe4ed6fa0833119988e98aa02b8f9fc4914f9a5f40b8f85b6` | Prevent double-resized visual-grid drift |
| `docs/easyr1_storage_guard_patch.diff` | `9dbb9a1c70dc294011fec531bad8bbf69f131c27e079ce8b1c39a2d6c5d957ae` | Guard shared checkpoint writes against the 20 GiB quota floor |
| `docs/easyr1_resume_safe_logger_patch.diff` | `d6a18bd37b7a4c6326854bf6857c3cd38a8843c50ebc410421dd2c8311efa4c8` | Refuse non-resume overwrite and preserve existing logs on explicit resume |

Problems:
- This is a reproducible patched recovery environment, not a clean upstream container.
- EasyR1's declared dependency range expects newer vLLM and FlashAttention; upgrading the live Qwen2.5-VL environment would risk the validated path.
- Qwen3-VL requires a separate environment and remains outside the current pilot stack.
- Resume-safe logging prevents future truncation but cannot recover the anchor's already-lost structured rows.

Decision:
- Keep EasyR1 for the four matched pilot arms, with all six patches applied explicitly and their full worktree diff pinned per run.
- Keep synchronous GRPO training and rollout colocated on one node; Qwen2.5-VL-3B rollout serving uses TP1.
- Do not change Torch, Transformers, vLLM, chat template, reward, or image preprocessing between pilot arms.
- Use verl only after a documented persistent EasyR1 failure, with a new config-diff and reward-plumbing audit before any scientific comparison.
- Keep Qwen3-VL in a separate environment if evaluated later.

Next actions:
- Complete the replacement five-step TP1 reward smoke under audit v6.
- Before L13, freeze an environment inventory and full EasyR1 worktree patch snapshot in each arm's run manifest.
