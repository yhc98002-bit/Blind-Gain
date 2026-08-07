# Gate-1 completion: held-out endpoint eval launch commands (arm 1 std, arm 3 necessity)

Commands only — NOTHING here has been launched. Written 2026-08-07 alongside the four-arm
readout instrument `scripts/build_mini_a5_gate1_endpoint_readout.py`.

Sealing (docs/registered_mini_a5_gate1_completion_v1.md): no prediction, metric, or
accuracy file from arm 1 or arm 3 is opened before BOTH arms complete training AND the
section-9 acceptance audit passes. Generation may run per arm after that arm's training
exits 0 with 120 optimizer steps; the readout runs only after the acceptance-audit report
exists. Arm 2 (member) and arm 4 (cp) cells are NOT re-run — the F8 run dirs
`experiments/runs/mini_a5_f8_{r19,r20,chartv08}_{member,cp}_step120_real_an29_20260730T004031Z`
stand and their numbers are not re-decided.

Prerequisites (must exist before generation):

- `checkpoints/mini_a5/mini_a5_std_seed1/global_step_120/actor/huggingface`
- `checkpoints/mini_a5/mini_a5_necessity_seed1/global_step_120/actor/huggingface`

All commands run from the repo root
`/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain` on a login node
(`scripts/launch_fliptrack_eval_shards.sh` ssh-es to the compute node itself). Node an29 is
the F8 precedent; substitute an12 if an29 is occupied. The two arms may run in parallel on
disjoint GPU lists (std on `'0 1 2 3'`, necessity on `'4 5 6 7'`), F8-style.

Common env before every launcher call:

    unset BLIND_GAINS_PILOT_SOURCE_RUN BLIND_GAINS_PILOT_GLOBAL_STEP BLIND_GAINS_M5_SOURCE_RUN BLIND_GAINS_M5_GLOBAL_STEP
    export BLIND_GAINS_EVAL_SEED=0
    TS=$(date -u +%Y%m%dT%H%M%SZ)
    ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain

Regime (pinned, identical to the six F8 cells): greedy, max_new_tokens 32, image_mode
real, eval seed 0, answer-tags-v1 contract. The R19 manifest hash is enforced inside the
launcher (`R19_MANIFEST_SHA256`).

## Arm 1 (std) — checkpoint `mini_a5_std_seed1`

R19 (4 shards):

    bash scripts/launch_fliptrack_eval_shards.sh an29 0 4 ${ROOT}/checkpoints/mini_a5/mini_a5_std_seed1/global_step_120/actor/huggingface experiments/runs/caption_qa_pair_build_fliptrack_v02r19_qwen25vl3b_384_20260710T140200Z/shards/captions_shard_0.jsonl experiments/runs/mini_a5_gate1_r19_std_step120_real_an29_${TS} 32 '0 1 2 3' real

R20 private twin, one shot (4 shards):

    bash scripts/launch_fliptrack_eval_shards.sh an29 0 4 ${ROOT}/checkpoints/mini_a5/mini_a5_std_seed1/global_step_120/actor/huggingface data/fliptrack_r20_source_manifest.jsonl experiments/runs/mini_a5_gate1_r20_std_step120_real_an29_${TS} 32 '0 1 2 3' real

chart_v08 calibration (4 shards):

    bash scripts/launch_fliptrack_eval_shards.sh an29 0 4 ${ROOT}/checkpoints/mini_a5/mini_a5_std_seed1/global_step_120/actor/huggingface data/fliptrack_chart_v08_calibration_v1_manifest.jsonl experiments/runs/mini_a5_gate1_chartv08_std_step120_real_an29_${TS} 32 '0 1 2 3' real

Catch cell (1 GPU; preflight: on-disk `data/derived/mini_a5_catch_eval_manifest_v1.jsonl`
sha256 must equal `c4bb508f930ec47c9f3a2a4bc905693394f63bf6b4ebbd0f1332eef85afcbe4a` per
`experiments/manifests/mini_a5_catch_eval_manifest_v1.json`; rebuild if absent with
`PYTHONPATH=. .venv/bin/python scripts/build_mini_a5_catch_eval_manifest.py`):

    bash scripts/launch_fliptrack_eval_shards.sh an29 0 1 ${ROOT}/checkpoints/mini_a5/mini_a5_std_seed1/global_step_120/actor/huggingface data/derived/mini_a5_catch_eval_manifest_v1.jsonl experiments/runs/mini_a5_catch_std_step120_real_an29_${TS} 32 5 real

## Arm 3 (necessity) — checkpoint `mini_a5_necessity_seed1`

R19 (4 shards):

    bash scripts/launch_fliptrack_eval_shards.sh an29 0 4 ${ROOT}/checkpoints/mini_a5/mini_a5_necessity_seed1/global_step_120/actor/huggingface experiments/runs/caption_qa_pair_build_fliptrack_v02r19_qwen25vl3b_384_20260710T140200Z/shards/captions_shard_0.jsonl experiments/runs/mini_a5_gate1_r19_necessity_step120_real_an29_${TS} 32 '4 5 6 7' real

R20 private twin, one shot (4 shards):

    bash scripts/launch_fliptrack_eval_shards.sh an29 0 4 ${ROOT}/checkpoints/mini_a5/mini_a5_necessity_seed1/global_step_120/actor/huggingface data/fliptrack_r20_source_manifest.jsonl experiments/runs/mini_a5_gate1_r20_necessity_step120_real_an29_${TS} 32 '4 5 6 7' real

chart_v08 calibration (4 shards):

    bash scripts/launch_fliptrack_eval_shards.sh an29 0 4 ${ROOT}/checkpoints/mini_a5/mini_a5_necessity_seed1/global_step_120/actor/huggingface data/fliptrack_chart_v08_calibration_v1_manifest.jsonl experiments/runs/mini_a5_gate1_chartv08_necessity_step120_real_an29_${TS} 32 '4 5 6 7' real

Catch cell (1 GPU; same manifest preflight as arm 1):

    bash scripts/launch_fliptrack_eval_shards.sh an29 0 1 ${ROOT}/checkpoints/mini_a5/mini_a5_necessity_seed1/global_step_120/actor/huggingface data/derived/mini_a5_catch_eval_manifest_v1.jsonl experiments/runs/mini_a5_catch_necessity_step120_real_an29_${TS} 32 7 real

Note: the catch STABILITY scorer (`src/eval/catch_stability.py`) is hard-coded to the
cp/member two-arm shape (`--cp-scores`/`--member-scores` both required); scoring the new
arms' catch cells needs a scorer extension or wrapper — do not shoehorn a new arm into a
mislabeled cp/member slot.

## Four-arm readout (only after BOTH arms complete + acceptance audit report exists)

    PYTHONPATH=. .venv/bin/python -m scripts.build_mini_a5_gate1_endpoint_readout \
      --arm-std experiments/runs/mini_a5_gate1_r19_std_step120_real_an29_<TS_STD> \
      --arm-member experiments/runs/mini_a5_f8_r19_member_step120_real_an29_20260730T004031Z \
      --arm-necessity experiments/runs/mini_a5_gate1_r19_necessity_step120_real_an29_<TS_NEC> \
      --arm-cp experiments/runs/mini_a5_f8_r19_cp_step120_real_an29_20260730T004031Z \
      --base-report reports/f2d_template_decomposition_v1.json \
      --f8-report reports/f8_mini_a5_endpoint_readout_v1.json \
      --output reports/mini_a5_gate1_endpoint_readout_v1.json

Defaults are the registered values (bootstrap 10000 draws, seed 20260729, `--expect
registered` enforcing the 600/300/300 R19 shape). The instrument fail-closes on missing or
incomplete run manifests, arm-label mismatches, and item-set mismatches; it never
overwrites an existing output.
