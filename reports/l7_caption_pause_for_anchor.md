# L7 Caption Pause for Anchor Recovery

Status:
- `resumed`. The L7 caption condition was deliberately paused to create a low-host-memory window for the unchanged anchor step-80 continuation, then resumed after optimizer step 81 established a safe observed margin.
- The pause is orchestration-only; no caption, prompt, decoding, reward, parser, corpus, or model setting changed.

Evidence:
- Paused run: `experiments/runs/blind_solvability_v2_geo3k_filtered_v2_caption_an12_20260711T142842Z` on `an12` GPU 6, TP1, one replica.
- Final manifest status: `fail`, exit `-15`, end `2026-07-11T15:01:03Z`; the recorded orchestration event is `paused_for_anchor_host_memory_isolation`.
- Durable prefix: `experiments/runs/blind_solvability_v2_geo3k_filtered_v2_caption_an12_20260711T142842Z/per_item.jsonl`.
- Prefix rows: `332 / 1,889`, aligned to batch size 4.
- Prefix SHA256: `9ca0ae90cff47b30d68a427e855ebadf31714eb01d7ef41cd860df9b3bfe76ee`.
- `load_validated_v2_resume_prefix` passes all 332 rows against the frozen filtered train plus untouched test corpus, caption condition, seed 20260710, 2,048-token contract, canonical-v2, and pilot-reward-v1.
- Replacement run: `experiments/runs/blind_solvability_v2_geo3k_filtered_v2_timeoutguard_caption_an12_20260711T154213Z`, started at `2026-07-11T15:42:13Z` on `an12` GPU 6, TP1, one replica.
- The replacement manifest records git `14680b6`, the fixed 3B caption store, the preserved prefix, symbolic guard `posix-itimer-v1`, and a 5-second per-call deadline.
- The anchor watcher observed at least 795,235,916 KiB available through the first resumed optimizer step and its transition before the caption replica was released.

Problems:
- The caption condition needs approximately three hours at observed throughput. Waiting for natural completion would delay the proposal-critical anchor recovery; running it concurrently during anchor initialization would recreate an avoidable host-memory risk.

Decision:
- Preserve the failed paused run and its immutable prefix.
- Resume in a new run through `scripts/launch_blind_solvability_v2_condition.sh ... RESUME_FROM`, which recopies only a fully validated prefix before model inference continues.
- Do not count the paused run as a completed L7 condition and do not combine its rows outside the registered resume path.

Next actions:
- Keep the anchor host-memory watcher active while the single caption replica runs; stop only this project-owned caption process if the anchor's host-memory margin degrades materially.
- Do not count the caption condition complete until the replacement manifest finalizes and all 1,889 rows pass L7's recomputation audit.
