# Pilot Seed-2 Execution Status V1

Status:
- This is an operational status report, not an M3 scientific pass.
- A1-real is complete at step 100; performance values remain unopened.
- A2-gray is healthy at step 81 on `an12` GPUs `0,1,2,3`.
- A2b-no-image completed step 100 with exit code 0 at `2026-07-20T11:59:01Z`.
- A3-caption launched at `2026-07-20T12:52:21Z` on `an29` GPUs `0,1,2,3`; its four TP1 workers loaded the model and no fatal pattern was present at the startup check.

Evidence:
- A2 run: `experiments/runs/mech_a2_gray_seed2_resume20_an12_20260719T125918Z`.
- A2b run: `experiments/runs/mech_a2b_noimage_seed2_resume20_an29_20260719T125447Z`.
- A3 run: `experiments/runs/mech_a3_caption_seed2_an29_20260720T125144Z`.
- A3 authorization: `reports/pilot_followup_launch_authorization_seed2_a3_caption_20260720T125144Z.json`; all eleven fail-closed checks are true.
- A3 checkpoint watcher: `experiments/runs/pilot_checkpoint_watch_mech_a3_caption_seed2_login_20260720T125243Z`.
- A3 placement is single-node, four GPUs, TP1 x4, with its fixed question-blind caption-store hashes recorded in the run manifest.
- At `2026-07-20T13:03:28Z`, A3 held about 48.5 GiB on each assigned GPU and its fatal-pattern count was zero.
- Current Lustre project usage was `1,402,410,300` KiB, leaving about 162.6 GiB under the conservative 1,500-GiB accounting ceiling.

Problems:
- The original seed-2 capacity queue did not dispatch A3 after A2b released `an29`; manual fail-closed launch was required.
- The A2b checkpoint watcher still awaits the registered step-60 evaluation marker before completing step-80/100 merge and retention work. This does not block A3 training, but it must be closed before the seed-2 readout.

Decision:
- Launch A3 immediately on the released `an29` GPUs `0,1,2,3` under the merged seed-2 registration rather than leave it queued.
- Keep `an29` GPUs `4,5,6,7` available for checkpoint evaluation and cleanup work; do not colocate another synchronous EasyR1 trainer.
- Continue the no-peeking rule: only lifecycle, step, resource, hash, and error evidence may be inspected until the registered multi-arm readout opens values.

Next actions:
- Confirm A3 completes initialization and advances its first optimizer step.
- Let A2 continue from step 81 to the fixed terminal step 100.
- Complete A2b step-60 and step-100 registered evaluations, then allow its watcher to finish final merge and retention.
- Run the four-arm seed-2 readout only after every required lifecycle and identity audit passes.
