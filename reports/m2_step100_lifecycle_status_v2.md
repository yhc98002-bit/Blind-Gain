# M2 Step-100 Lifecycle Status V2

Status:
- M2 remains `blocked`; this report makes no scientific gate decision.
- V2 supersedes the operational snapshot in V1 without modifying V1 or any run.
- A1, A2b, and A3 now each have a complete, independently audited 601-row
  Geometry3K-test step-100 readout in addition to their complete R19 markers.
- A2-gray is mechanically at step 70; its fail-closed step-100 queue is active in
  `waiting_training` state.
- No pilot performance value was opened or interpreted for this lifecycle report.

Evidence:
- Readout implementation: `01839373c176b8f1b6247b3583301bb4ce707558`.
- Independent audit implementation: `aa83b645566fc3a6770dd023bf183bd79522f1bf`.
- A2 queue implementation/config: `c0e8b39c741ff34ac7e0e11e2e4a4b0a5d3918c9`.

| Arm | Rows | Readout status | Audit status | Audit SHA256 | Static / score / strict mismatches |
| --- | ---: | --- | --- | --- | --- |
| A1 real | 601 | complete, exit 0 | pass | `81cca198e1a0496b07d671daab32f2e60bdd14435f9a3ce463e820a0b8e6b2b8` | `0 / 0 / 0` |
| A2b no-image | 601 | complete, exit 0 | pass | `b2d88f529f209c49615e06f188abcd7c41e8f30c0447d7a643ae7d265878fbce` | `0 / 0 / 0` |
| A3 caption | 601 | complete, exit 0 | pass | `2044a44668010eeeb85eff7e863e3bda63fbcd4d44fae11d3ffe8a9c9dacc4c0` | `0 / 0 / 0` |
| A2 gray | n/a | training at step 70 | pending | n/a | n/a |

- Each audit checked the exact 601 source identities and order, prompt/parser/reward
  stamps, decoding contract, source-training manifest hash, checkpoint index,
  retention marker, every retained merged model file, and every stored score.
- Output SHA256 values are:
  - A1: `541b7cb18be0ac357aaeddea3cce94c47aa39ccf827c842666399b6e61d7dda5`.
  - A2b: `2589d1eb5e12ac22545144448a536e49382b8baf8fb9c4fd27ca88b883993f27`.
  - A3: `ec4bdc6a5782fbf6c4337e463cb3a38ddb824163b8e6c54e44e2afcfda7a665c`.
- The A2 queue is
  `experiments/runs/pilot_step100_eval_queue_a2_gray_login_20260715T211716Z`.
  Its live dependency state is `waiting_training`; it allocates no GPU and cannot
  launch before exact training completion, primary retention completion, and two
  clean capacity polls on `an12:4-7`.
- The queue accepts the active primary retention watcher only with exact parent,
  node, run root, `[80,100]` schedule, and final artifact paths. A malformed primary
  watcher is a terminal dependency failure.

Problems:
- A2-gray still requires steps 71-100, step-80/100 retention, R19 scoring, and the
  locked Geometry3K readout plus independent audit.
- Four-arm joins, paired intervals, StrictGain accounting, hurdle/rank analyses,
  and the final registered M2 report cannot be computed until A2 lands.

Decision:
- Preserve the three audited per-item outputs unchanged and do not compute or
  inspect partial three-arm scientific comparisons.
- Let the committed A2 queue perform the step-100 handoff automatically; it waits
  rather than weakening retention identity or consuming occupied GPUs.
- Keep M11 fail-closed until all four exact R19 markers validate.

Next actions:
- Monitor A2 training and its retention watcher without inspecting model metrics.
- Let the queue run A2 R19 scoring when its exact prerequisites and capacity hold.
- Run the same 601-row Geometry3K evaluator and independent audit for A2.
- Only then build `reports/pilot_4arm_seed1_results_v1.md` from the four audited
  readouts and frozen L7 baselines.

Machine-readable companion:
- `reports/m2_step100_lifecycle_status_v2.json`.
