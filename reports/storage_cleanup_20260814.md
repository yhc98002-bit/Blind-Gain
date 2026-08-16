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

## Retention-rule application 2026-08-16T08:47:03Z (dispatch 2026-08-16 item 2)

Rule: delete non-terminal checkpoint steps not referenced in §21; keep
terminal + best + every §21-referenced step. Scope: mini_a5, c5, pilot,
smoke, m5_anchor_longhorizon_400{,_resume150}, stage0_repro,
anchor_a0_recipe_3b_geo3k. m7/ and lh2/ untouched. Resolution record in
`scripts/apply_storage_retention_rule_20260816.py` (committed).

| path | bytes | action |
|---|---:|---|
| `checkpoints/mini_a5/mini_a5_cp_seed1/global_step_40` | 8147755867 | deleted |
| `checkpoints/mini_a5/mini_a5_cp_seed1/global_step_60` | 8147755915 | deleted |
| `checkpoints/mini_a5/mini_a5_cp_seed1/global_step_80` | 8147755915 | deleted |
| `checkpoints/mini_a5/mini_a5_cp_seed1/global_step_100` | 8147755852 | deleted |
| `checkpoints/mini_a5/mini_a5_necessity_seed1/global_step_40` | 40973922198 | deleted |
| `checkpoints/mini_a5/mini_a5_necessity_seed1/global_step_60` | 40973922198 | deleted |
| `checkpoints/mini_a5/mini_a5_necessity_seed1/global_step_80` | 40973922198 | deleted |
| `checkpoints/mini_a5/mini_a5_necessity_seed1/global_step_100` | 40973922198 | deleted |
| `checkpoints/mini_a5/mini_a5_same_data_seed1/global_step_40` | 40973922198 | deleted |
| `checkpoints/mini_a5/mini_a5_same_data_seed1/global_step_60` | 40973922198 | deleted |
| `checkpoints/mini_a5/mini_a5_same_data_seed1/global_step_80` | 40973922198 | deleted |
| `checkpoints/mini_a5/mini_a5_same_data_seed1/global_step_100` | 40973922198 | deleted |
| `checkpoints/mini_a5/mini_a5_std_seed1/global_step_40` | 40973922198 | deleted |
| `checkpoints/mini_a5/mini_a5_std_seed1/global_step_60` | 40973922198 | deleted |
| `checkpoints/mini_a5/mini_a5_std_seed1/global_step_80` | 40973922198 | deleted |
| `checkpoints/mini_a5/mini_a5_std_seed1/global_step_100` | 40973922198 | deleted |
| `checkpoints/c5/c5_a1_real_seed1_7b/global_step_20` | 33185896533 | deleted |
| `checkpoints/c5/c5_a1_real_seed1_7b/global_step_40` | 33185896533 | deleted |
| `checkpoints/c5/c5_a1_real_seed1_7b/global_step_60` | 33185896533 | deleted |
| `checkpoints/c5/c5_a1_real_seed1_7b/global_step_80` | 33185896533 | deleted |
| `checkpoints/c5/c5_a2_gray_seed1_7b/global_step_20` | 33185896533 | deleted |
| `checkpoints/c5/c5_a2_gray_seed1_7b/global_step_40` | 33185896533 | deleted |
| `checkpoints/c5/c5_a2_gray_seed1_7b/global_step_60` | 33185896533 | deleted |
| `checkpoints/c5/c5_a2_gray_seed1_7b/global_step_80` | 33185896533 | deleted |
| `checkpoints/pilot/mech_a1_real/global_step_20` | 75114 | deleted |
| `checkpoints/pilot/mech_a1_real/global_step_40` | 77107 | deleted |
| `checkpoints/pilot/mech_a1_real_resume60/global_step_80` | 75137 | deleted |
| `checkpoints/pilot/mech_a1_real_seed2/global_step_20` | 75132 | deleted |
| `checkpoints/pilot/mech_a1_real_seed2/global_step_40` | 77131 | deleted |
| `checkpoints/pilot/mech_a1_real_seed2/global_step_60` | 8147697520 | deleted |
| `checkpoints/pilot/mech_a1_real_seed2/global_step_80` | 77131 | deleted |
| `checkpoints/pilot/mech_a1_real_seed3/global_step_20` | 75132 | deleted |
| `checkpoints/pilot/mech_a1_real_seed3/global_step_40` | 77131 | deleted |
| `checkpoints/pilot/mech_a1_real_seed3/global_step_60` | 8147694105 | deleted |
| `checkpoints/pilot/mech_a2_gray/global_step_20` | 75118 | deleted |
| `checkpoints/pilot/mech_a2_gray/global_step_40` | 77107 | deleted |
| `checkpoints/pilot/mech_a2_gray_seed2_resume20/global_step_40` | 75159 | deleted |
| `checkpoints/pilot/mech_a2_gray_seed2_resume20/global_step_60` | 8147697588 | deleted |
| `checkpoints/pilot/mech_a2_gray_seed2_resume20/global_step_80` | 77163 | deleted |
| `checkpoints/pilot/mech_a2_gray_seed3/global_step_20` | 75132 | deleted |
| `checkpoints/pilot/mech_a2_gray_seed3/global_step_40` | 77131 | deleted |
| `checkpoints/pilot/mech_a2_gray_seed3/global_step_80` | 77131 | deleted |
| `checkpoints/pilot/mech_a2b_noimage_retry4/global_step_20` | 75147 | deleted |
| `checkpoints/pilot/mech_a2b_noimage_retry4/global_step_40` | 77151 | deleted |
| `checkpoints/pilot/mech_a2b_noimage_retry4/global_step_80` | 77151 | deleted |
| `checkpoints/pilot/mech_a2b_noimage_seed2_resume20/global_step_40` | 75171 | deleted |
| `checkpoints/pilot/mech_a2b_noimage_seed2_resume20/global_step_60` | 8147697636 | deleted |
| `checkpoints/pilot/mech_a2b_noimage_seed2_resume20/global_step_80` | 77179 | deleted |
| `checkpoints/pilot/mech_a2b_noimage_seed3/global_step_20` | 75143 | deleted |
| `checkpoints/pilot/mech_a2b_noimage_seed3/global_step_40` | 77144 | deleted |
| `checkpoints/pilot/mech_a2b_noimage_seed3/global_step_60` | 8147694200 | deleted |
| `checkpoints/pilot/mech_a3_caption_resume20/global_step_40` | 75150 | deleted |
| `checkpoints/pilot/mech_a3_caption_resume20/global_step_60` | 77155 | deleted |
| `checkpoints/pilot/mech_a3_caption_seed2/global_step_20` | 75141 | deleted |
| `checkpoints/pilot/mech_a3_caption_seed2/global_step_40` | 77143 | deleted |
| `checkpoints/pilot/mech_a3_caption_seed2/global_step_60` | 8147697602 | deleted |
| `checkpoints/pilot/mech_a3_caption_seed2/global_step_80` | 77143 | deleted |
| `checkpoints/pilot/mech_a3_caption_seed3/global_step_20` | 75141 | deleted |
| `checkpoints/pilot/mech_a3_caption_seed3/global_step_40` | 77143 | deleted |
| `checkpoints/pilot/mech_a3_caption_seed3/global_step_60` | 8147694151 | deleted |
| `checkpoints/pilot/mech_a3_caption_seed3/global_step_80` | 77143 | deleted |
| `checkpoints/m5_anchor_longhorizon_400_resume150/global_step_200` | 79883 | deleted |
| `checkpoints/m5_anchor_longhorizon_400_resume150/global_step_250` | 79883 | deleted |
| `checkpoints/m5_anchor_longhorizon_400_resume150/global_step_300` | 8147705010 | deleted |
| `checkpoints/m5_anchor_longhorizon_400_resume150/global_step_350` | 83974 | deleted |

TOTAL_BYTES_DELETED=854949371942
Kept (39 step dirs): `checkpoints/mini_a5/mini_a5_cp_seed1/global_step_20` (best); `checkpoints/mini_a5/mini_a5_cp_seed1/global_step_120` (terminal+§21); `checkpoints/mini_a5/mini_a5_necessity_seed1/global_step_20` (best); `checkpoints/mini_a5/mini_a5_necessity_seed1/global_step_120` (terminal+§21); `checkpoints/mini_a5/mini_a5_same_data_seed1/global_step_20` (best); `checkpoints/mini_a5/mini_a5_same_data_seed1/global_step_120` (terminal+§21); `checkpoints/mini_a5/mini_a5_std_seed1/global_step_20` (best); `checkpoints/mini_a5/mini_a5_std_seed1/global_step_120` (terminal+§21); `checkpoints/c5/c5_a1_real_seed1_7b/global_step_100` (best+terminal+§21); `checkpoints/c5/c5_a2_gray_seed1_7b/global_step_100` (best+terminal+§21); `checkpoints/pilot/mech_a1_real/global_step_60` (best+terminal); `checkpoints/pilot/mech_a1_real_resume60/global_step_100` (best+terminal); `checkpoints/pilot/mech_a1_real_seed2/global_step_100` (best+terminal); `checkpoints/pilot/mech_a1_real_seed3/global_step_80` (best); `checkpoints/pilot/mech_a1_real_seed3/global_step_100` (terminal); `checkpoints/pilot/mech_a2_gray/global_step_60` (best+terminal); `checkpoints/pilot/mech_a2_gray_resume60_retry2/global_step_80` (best); `checkpoints/pilot/mech_a2_gray_resume60_retry2/global_step_100` (terminal); `checkpoints/pilot/mech_a2_gray_seed2/global_step_20` (best+terminal); `checkpoints/pilot/mech_a2_gray_seed2_resume20/global_step_100` (best+terminal); `checkpoints/pilot/mech_a2_gray_seed3/global_step_60` (best); `checkpoints/pilot/mech_a2_gray_seed3/global_step_100` (terminal); `checkpoints/pilot/mech_a2b_noimage_retry4/global_step_60` (best); `checkpoints/pilot/mech_a2b_noimage_retry4/global_step_100` (terminal); `checkpoints/pilot/mech_a2b_noimage_seed2/global_step_20` (best+terminal); `checkpoints/pilot/mech_a2b_noimage_seed2_resume20/global_step_100` (best+terminal); `checkpoints/pilot/mech_a2b_noimage_seed3/global_step_80` (best); `checkpoints/pilot/mech_a2b_noimage_seed3/global_step_100` (terminal); `checkpoints/pilot/mech_a3_caption/global_step_20` (best+terminal); `checkpoints/pilot/mech_a3_caption_resume20/global_step_80` (best); `checkpoints/pilot/mech_a3_caption_resume20/global_step_100` (terminal); `checkpoints/pilot/mech_a3_caption_seed2/global_step_100` (best+terminal); `checkpoints/pilot/mech_a3_caption_seed3/global_step_100` (best+terminal); `checkpoints/smoke/mini_a5_cp_plumbing_smoke_v1/global_step_1` (best+terminal); `checkpoints/smoke/mini_a5_member_plumbing_smoke_v1/global_step_1` (best+terminal); `checkpoints/smoke/mini_a5_necessity_plumbing_smoke_v1/global_step_1` (best+terminal); `checkpoints/smoke/mini_a5_std_plumbing_smoke_v1/global_step_1` (best+terminal); `checkpoints/m5_anchor_longhorizon_400/global_step_150` (best+terminal+§21); `checkpoints/m5_anchor_longhorizon_400_resume150/global_step_400` (best+terminal+§21)
Skipped fail-closed: /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/checkpoints/pilot/pilot_storage_dry_cycle_login_20260711T094144Z: no parseable checkpoint_tracker.json — SKIPPED (fail-closed)
