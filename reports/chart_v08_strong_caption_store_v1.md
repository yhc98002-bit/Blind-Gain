# Chart-v08 Strong-Caption Store V1

Status:
- The question-blind 72B caption store is complete and independently structure-audited.
- This does not complete M12: caption-only QA scoring, human no-zoom audit, calibration interpretation, template freeze, and one-shot confirmation remain pending.
- No model-performance value was opened or computed in this job.

Evidence:
- GPU run: `experiments/runs/chart_v08_strong_caption_store_m12_v08_calibration_v1_an12_20260718T003420Z`.
- Placement: `an12` GPUs `4,5,6,7`, TP4, one replica. Qwen2.5-VL-72B cannot fit on one A800.
- Source commit: `456a11912d7e1029d92066bea8f1037f8dc58962`.
- Input: the immutable 100-pair chart-v08 calibration manifest, comprising 50 legend-target flips and 50 point-value flips; 200 unique images.
- Output: `experiments/runs/chart_v08_strong_caption_store_m12_v08_calibration_v1_an12_20260718T003420Z/captions.jsonl`, 200 rows, SHA256 `00f2aa36f2683264f10f725cd23f537eafc071b318bf4735ba053061e86a21ed`.
- Audit: `reports/chart_v08_strong_caption_store_v1.json`; all 10 checks pass. Coverage, source paths, and source-image bytes match exactly; captions are non-empty and unique by source-image hash.
- Frozen contract: question-blind prompt SHA256 `9e8a66fb1fd5b8edc40647c670b0c8d75a99c1552a8edf307131d7648bd00ae0`; greedy decoding (`temperature=0`, `top_p=1`, `n=1`, seed 0); maximum 384 new tokens; model `Qwen/Qwen2.5-VL-72B-Instruct@master`.
- Ephemeral cleanup: `reports/chart_v08_ephemeral_weights_deletion_v1.json`. After the caption audit passed and GPUs 4–7 had no compute process, exactly `146,833,337,667` bytes at `/dev/shm/blind-gains/models/Qwen2.5-VL-72B-Instruct` were removed. The hash-manifested source checkout is recorded by SHA256 `3d8a67e28485c9c7c95e737ad11ff7f165f107c9326d946b1dca77419fee5e58`.

Problems:
- The 72B serving job overlapped M5 on the same host. Although GPU allocations were disjoint, combined host memory crossed Ray's 95% threshold and M5 was killed. This operational incident is documented separately in `reports/m5_host_memory_incident_v1.md`.
- Caption generation alone does not establish the strong-caption leakage cell. QA scoring remains unopened pending the existing M12 human-audit sequence.

Decision:
- Preserve the audited caption store on shared storage.
- Do not reload the 72B weights for this batch.
- Future 72B launchers refuse any node that already hosts a Blind Gains RL trainer, in addition to checking GPU and host-memory capacity.

Next actions:
- Complete Richard's fixed-size, no-zoom human audit.
- Run the frozen caption-only QA protocol using this exact store after the audit dependency is satisfied.
- Keep legend-target and point-value subfamilies separate in every M12 table.
