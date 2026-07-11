# GPU Placement Policy Record

Status:
- Operational policy implemented. This report records placement compliance and does not declare a PI compute gate passed.
- Effective source: PI instruction received 2026-07-11; committed in `docs/PRELAUNCH_BRIEF.md`.

Policy:
- Keep each training or serving job on one node unless it genuinely needs more than eight GPUs.
- Use TP1 for models at or below 7B; scale throughput with independent request-sharded replicas.
- Use TP2/TP4 only for 32B/72B models that cannot fit one GPU.
- Keep synchronous EasyR1/GRPO rollout and training colocated on one node.
- Treat foreign processes and disjoint-GPU colocation as normal neighbors; never kill or label them anomalous.

Manifest contract:
- `node`
- normalized `gpu_ids`
- `tensor_parallel_width`
- `replica_count`
- `placement_justification`
- `placement_policy_version: pi-2026-07-11`

Evidence:
- `src/ops/run_placement.py` validates one-host placement, GPU IDs, TP width, replica count, and nonempty rationale; it atomically refuses conflicting amendments.
- `scripts/record_run_placement.py` added the policy record to active runs launched before the policy was codified.
- Launchers for L7, ViRL39K, VLMEvalKit, caption stores/QA, FlipTrack shards, aggregation/comparison, L10 scheduling, postprocessing, dataset preparation, and anchor resume now write the fields at creation.
- Six placement fixtures pass, including cross-node rejection, TP width exceeding allocation, invalid login GPU records, and conflicting-manifest rejection.
- Audit cutoff `2026-07-11T14:23:00Z`: `19` run manifests inspected, `0` missing required placement fields.
- Active anchor: `an12` GPUs 0-3, TP1, one synchronous FSDP/GRPO continuation.
- Active L7 image conditions: four independent TP1 replicas on `an29` GPUs 1,5,6,7.

Problems:
- The original anchor OOM demonstrates that disjoint GPUs do not isolate host memory. Normal colocation still requires aggregate host-RAM admission checks for high-RAM synchronous training.
- The older historical manifest population predates this policy and was not rewritten wholesale; active pre-policy runs were amended, and all post-policy runs are audited.

Decision:
- Keep the anchor isolated until its first resumed optimizer-step memory peak is measured.
- Resume the paused L7 caption TP1 replica only after measured host-memory headroom supports it.
- Build L9 72B serving as a single-node TP2/TP4 job from ephemeral node-local weights; do not reuse the <=7B independent-TP1 caption launcher.

Next actions:
- Re-run the manifest audit after every new launch wave and include actual placement in the corresponding task report.
