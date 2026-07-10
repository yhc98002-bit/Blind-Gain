# GPU Allocation Conflict, 2026-07-10

Status:
- An unrelated service appeared on `an29` after Blind Gains jobs were dispatched and occupied physical GPUs 0, 2, 3, and 4.
- No unrelated process was terminated. Affected Blind Gains attempts were stopped, marked failed, and retried on `an12`.

Evidence:
- Observed at approximately 19:54 CST under the shared Unix account.
- Command: Qwen3-Omni 30B vLLM service with `--tensor-parallel-size 4`, `CUDA_VISIBLE_DEVICES=0,2,3,4`, port 8901, and served name `qwen3-omni-judge`.
- The four worker processes each reserved approximately 65.9 GiB.
- Affected immutable attempts: R16 3B/7B caption QA on `an29` GPUs 0/2/3 and ViRL39K 3B gray on GPU 4.
- Superseding allocation: R16 QA on `an12` GPUs 4/5/6 and ViRL39K 3B gray on `an12` GPU 7.
- Four non-gating 7B ViRL supplemental attempts on `an12` were intentionally preempted before model allocation and retain `exit_code=-15` plus an explicit deviation note.

Problems:
- The prior assumption of exclusive node ownership is false at least for this interval.
- GPU availability can change after launch, so launch-time inspection alone cannot prevent this race.

Decision:
- Preserve every interrupted attempt as failed rather than deleting or relabeling it.
- Prioritize gating jobs over supplemental scale runs and avoid terminating processes not launched by this project.

Next actions:
- Continue five-minute utilization logging and inspect process ownership whenever registered jobs fail to allocate memory.
- Ask the cluster owner to restore exclusivity only if the external service persists long enough to block both nodes; current work has a safe reallocation path.
