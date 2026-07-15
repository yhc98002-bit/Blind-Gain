# Chart V08 Calibration Execution Status V5

Status:
- M12 remains `blocked`; no calibration, freeze, or scientific gate is declared.
- V5 supersedes the operational snapshot in V4 without modifying earlier reports.
- The guarded 72B strong-captioner download is active on `an12` as a CPU/network-only
  job. No serving process or caption evaluation has started.
- All chart-v08 model-performance, floor, attacker, and necessity values remain
  unopened pending the no-zoom human audit.

Evidence:
- Download run:
  `experiments/runs/modelscope_ephemeral_qwen25vl72b_m12_chartv08_an12_20260715T211129Z`.
- Model: `Qwen/Qwen2.5-VL-72B-Instruct`, revision `master`, ModelScope-first with
  the previously audited reverse-proxy fallback.
- Run Git hash: `aa83b645566fc3a6770dd023bf183bd79522f1bf`.
- Destination:
  `an12:/dev/shm/blind-gains/models/Qwen2.5-VL-72B-Instruct`.
- Declared guard budget: `160,000,000,000` bytes. Free space before launch was
  `427,770,232,832` bytes, leaving a declared post-download projection of
  `267,770,232,832` bytes, above the 40 GiB Tier-T floor.
- The ModelScope inventory measured previously is `146,833,336,607` bytes. The
  transfer log showed active weight-shard progress after the remote guard passed.
- Placement fields are GPU allocation `[]`, TP width `0`, and replica count `0`;
  all A2 and M2 evaluation GPU assignments remain unchanged.
- Full V4 evidence for local real/caption/gray/noise, necessity, and grouped
  attacker lifecycles remains in
  `reports/chart_v08_calibration_execution_status_v4.md` and its machine JSON.

Problems:
- The 72B checkout is incomplete and volatile until its persistent checkout hash
  manifest is written.
- The 100-pair no-zoom human-legibility audit remains pending.
- TP4 serving, question-blind caption generation, caption-only QA, aggregation,
  and the strong-caption gate audit remain pending.
- Freeze and one-shot confirmatory generation remain prohibited.

Decision:
- Overlap only the CPU/network download with M2. Do not allocate GPUs to the 72B
  model while M2 readouts use `an12:4-6`.
- After download verification, serve at TP4 on one node only when a four-GPU block
  is free and no M2 checkpoint evaluation needs it.
- Generate fixed question-blind captions for the frozen v08 calibration images,
  run the standard caption-only QA protocol, commit the caption store and results,
  then hash-delete the ephemeral weights and record that deletion.

Next actions:
- Monitor download health, storage headroom, and checkout-manifest creation.
- Complete the no-zoom human audit independently of model results.
- Launch TP4 strong-caption work only after the M2-critical GPU block is released.
- Preserve a failed strong-caption gate as evidence; do not tune v08 from that
  readout or mint a confirmatory split unless every frozen criterion holds.

Machine-readable companion:
- `reports/chart_v08_calibration_execution_status_v5.json`.
