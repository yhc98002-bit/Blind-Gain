# Multi-Node NCCL/FSDP Smoke

Status:
- P1.3 is prepared but blocked; it is not a pass.
- A prior 16-rank cross-node NCCL all-reduce correctness smoke passed, but it did not measure bandwidth.
- The required 16-GPU measured benchmark and one-step FSDP smoke with the actual Qwen2.5-VL-3B weights have not run because a full-node window is unavailable.

Evidence:
- Prior correctness artifact: `reports/ddp_sanity_crossnode_an12_rank0.json` records world size 16, reduced value 136, expected value 136, and `ok=true`.
- Measured benchmark: `scripts/nccl_allreduce_bench.py`; 256 MiB tensor, five warmups, 20 timed collectives, max-rank latency, algorithm bandwidth, and standard ring-corrected bus bandwidth.
- Actual-model smoke: `scripts/fsdp_qwen25vl_smoke.py`; Qwen2.5-VL-3B local weights, full sharding, BF16, SDPA, synthetic text-only labels, and one optimizer step.
- Orchestration: `scripts/launch_multinode_smoke.sh`; fixed IB interface `ib0`, master `99.72.4.13`, exact run manifests/logs, and a hard requirement that all 16 GPUs be free.
- Focused tests: `tests/test_multinode_smoke.py`, four tests passing on 2026-07-10.
- Script SHA256 values at preparation: all-reduce `35be7f93c9b3d1261e32d7fdf6f1e58b3ffdc3b3b815baa5d13214583c91a504`; FSDP `593dc9337b265e39ef01a73e3553f1543b1da9f4e731c5b74089c2112b79ba10`; launcher `3785cd70e159883b2f686d32f48268061b1faaac88398f4b6862cfc12e3e7439`.

Problems:
- Preflight at `2026-07-10T13:56:00Z` exited 3 because every `an12` GPU was occupied by the active GRPO anchor, R19 caption stores, or ViRL39K gray audit.
- On `an29`, project ViRL39K audits occupied GPUs 1/5/6/7. An unrelated Qwen3-Omni vLLM service occupied GPUs 0/2/3/4 with PIDs 3268166, 3268167, 3268169, and 3268170.
- The launcher intentionally refuses a partial-world substitute because P1.3 explicitly requires 2 nodes x 8 GPUs.
- The FSDP smoke validates distributed model/optimizer plumbing with text-only synthetic tokens; it does not validate multimodal preprocessing, which is covered separately by the anchor and image-condition tests.

Decision:
- Preserve proposal-critical jobs instead of preempting them for an infrastructure smoke.
- Do not terminate the unrelated Qwen3-Omni service without ownership confirmation.
- Keep P1.3 blocked until both full nodes are simultaneously available; do not infer bandwidth from the earlier scalar correctness collective.

Next actions:
- Run `scripts/launch_multinode_smoke.sh bandwidth 29671` in the first full-node window.
- If bandwidth passes, run `scripts/launch_multinode_smoke.sh fsdp 29672` and report both immutable run directories and metrics here.
