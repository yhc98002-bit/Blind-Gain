# Storage cleanup — 2026-08-14

Deadlock: storage guard refusing all checkpoint saves since 2026-08-12
(free 63.5 GB < required 55 GB + floor 21.5 GB against 2.5 TiB capacity).
Policy (PI-approved 2026-08-14): delete only archived failed-attempt dirs and
non-terminal global_step dirs of complete + eval-banked + ledgered runs;
keep every evaluated/best step; do not touch live seed-2 trainer dirs,
mini_a5, completed c5 runs, pilot, smoke, m5 (those stay on the PI menu).

Kept on purpose: a1_real_seed1 step100 (best+evaluated); a1_real_seed2
step80 (best) + step100 (evaluated); every other m7 run's step100;
all c5 completed-run steps (C6 evaluated their terminal checkpoints).

| deleted path (repo-relative) | bytes |
|---|---|
| checkpoints/c5/c5_a1_real_seed1_7b_attempt1_hostoom_20260803 | 132743902315 |
| checkpoints/m7/m7_virl_a2_gray_seed2_attempt1_hostoom_20260810 | 16280694947 |
| checkpoints/m7/m7_virl_a3_caption_seed2_attempt1_hostram_20260810 | 16280705124 |
| checkpoints/m7/m7_virl_a1_real_seed1/global_step_20 | 40970253322 |
| checkpoints/m7/m7_virl_a1_real_seed1/global_step_40 | 40970253322 |
| checkpoints/m7/m7_virl_a1_real_seed1/global_step_60 | 40970253322 |
| checkpoints/m7/m7_virl_a1_real_seed1/global_step_80 | 40970253322 |
| checkpoints/m7/m7_virl_a1_real_seed2/global_step_20 | 40970253322 |
| checkpoints/m7/m7_virl_a1_real_seed2/global_step_40 | 40970253322 |
| checkpoints/m7/m7_virl_a1_real_seed2/global_step_60 | 40970253322 |
| checkpoints/m7/m7_virl_a2b_noimage_seed1/global_step_20 | 16280545574 |
| checkpoints/m7/m7_virl_a2b_noimage_seed1/global_step_40 | 16280545574 |
| checkpoints/m7/m7_virl_a2b_noimage_seed1/global_step_60 | 16280545574 |
| checkpoints/m7/m7_virl_a2b_noimage_seed1/global_step_80 | 16280545574 |
| checkpoints/m7/m7_virl_a2b_noimage_seed2/global_step_20 | 16280545574 |
| checkpoints/m7/m7_virl_a2b_noimage_seed2/global_step_40 | 16280545574 |
| checkpoints/m7/m7_virl_a2b_noimage_seed2/global_step_60 | 16280545574 |
| checkpoints/m7/m7_virl_a2b_noimage_seed2/global_step_80 | 16280545574 |
| checkpoints/m7/m7_virl_a2_gray_seed1/global_step_20 | 16280545574 |
| checkpoints/m7/m7_virl_a2_gray_seed1/global_step_40 | 16280545574 |
| checkpoints/m7/m7_virl_a2_gray_seed1/global_step_60 | 16280545574 |
| checkpoints/m7/m7_virl_a2_gray_seed1/global_step_80 | 16280545574 |
| checkpoints/m7/m7_virl_a3_caption_seed1/global_step_20 | 16280545574 |
| checkpoints/m7/m7_virl_a3_caption_seed1/global_step_40 | 16280545574 |
| checkpoints/m7/m7_virl_a3_caption_seed1/global_step_60 | 16280545574 |
| checkpoints/m7/m7_virl_a3_caption_seed1/global_step_80 | 16280545574 |

Total bytes deleted: 712585804824

Executed 2026-08-14T15:17:24Z on ln206 at git da0751d.
