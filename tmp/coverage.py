#!/usr/bin/env python3
"""Coverage check: is every result-bearing artifact represented in RESULTS.md?"""
import re
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
txt = (ROOT / "reports/RESULTS.md").read_text()

# artifact stem -> what it should contribute
EXPECT = {
    "three_seed_summary_v1": "C1 three-seed task gains",
    "correction_three_seed_fliptrack_v1": "the FlipTrack equivalence correction",
    "pooled_item_equivalence_v1": "pooled item-level equivalence / contract validity / power",
    "d2_testtime_ablation_v1": "D2 test-time access",
    "d3_condition_matrix_v1": "D3 train x test matrix",
    "d3_trainshare_v1": "TrainShare",
    "d4_caption_column_v1": "D4 caption column",
    "x1_image_condition_matrix_v1": "X1 sharpening",
    "x2_hard_negative_ranking_v1": "X2 hard negatives",
    "x3_a2_degradation_forensics_v1": "X3 corrosion forensics",
    "x4_visual_evidence_calibration_v1": "X4 calibration",
    "x5_seed2_image_condition_matrix_v1": "X5 seed-2 matrix",
    "gate0_stratification_v1": "Gate 0",
    "p01_premise_probe_v1": "P0.1 premise probe",
    "p04_task_roles_v1": "P0.4 task roles",
    "b1_trained_scoring_v1": "B1 trained scoring",
    "b1_rescored_p02_v1": "B1 rescore under the fixed scorer",
    "f2d_template_decomposition_v1": "F3d template decomposition",
    "cue_ladder_readout_v1": "cue ladder",
    "m5_terminal_readout_v1": "R2 terminal readout",
    "generalization_audits_v2": "R5 cross-family",
    "geometry_track_prototype_v1": "B1 base calibration",
    "fliptrack_r20_confirmatory": "R20 one-shot",
    "strong_caption_stress": "72B caption stress",
    "blind_solvability_geo3k_v3_audited": "blind reward-opportunity audit",
    "fliptrack_v02r19_human_audit": "human audit",
    "base_external_benchmarks": "base external benchmarks",
    "mini_a5_acceptance_audit_v1": "F8 acceptance gate",
}

print(f"{'artifact':<44}{'exists':>8}{'cited':>8}  contribution")
missing_cite, missing_file = [], []
for stem, what in sorted(EXPECT.items()):
    exists = any((ROOT / "reports" / f"{stem}{ext}").is_file() for ext in (".json", ".md"))
    # cited if the stem appears, or a distinctive token of it
    cited = stem in txt
    if not cited:
        # allow citation by concept for a few that are referenced by name not path
        alias = {
            "d2_testtime_ablation_v1": ["D2"],
            "x1_image_condition_matrix_v1": ["X1"],
            "x2_hard_negative_ranking_v1": ["X2"],
            "x3_a2_degradation_forensics_v1": ["X3"],
            "x4_visual_evidence_calibration_v1": ["X4"],
            "x5_seed2_image_condition_matrix_v1": ["X5"],
            "three_seed_summary_v1": ["three seeds", "three-seed"],
            "geometry_track_prototype_v1": ["B1 geometry track"],
            "fliptrack_r20_confirmatory": ["R20"],
            "strong_caption_stress": ["caption stress"],
            "blind_solvability_geo3k_v3_audited": ["blind reward-opportunity"],
            "fliptrack_v02r19_human_audit": ["human audit"],
            "b1_trained_scoring_v1": ["B1 geometry track", "fact-read"],
            "p04_task_roles_v1": ["task roles", "P0.4"],
            "correction_three_seed_fliptrack_v1": ["equivalence overstated", "A2 gray equivalence"],
            "mini_a5_acceptance_audit_v1": ["acceptance audit"],
            "base_external_benchmarks": ["external benchmark"],
        }.get(stem, [])
        cited = any(a in txt for a in alias)
    print(f"{stem:<44}{'yes' if exists else 'NO':>8}{'yes' if cited else 'NO':>8}  {what}")
    if exists and not cited:
        missing_cite.append((stem, what))
    if not exists:
        missing_file.append(stem)

print()
if missing_cite:
    print("NOT REPRESENTED IN RESULTS.md:")
    for s, w in missing_cite:
        print(f"  - {s}: {w}")
else:
    print("every existing artifact is represented.")
if missing_file:
    print(f"\nartifacts not on disk (expected for pending work): {', '.join(missing_file)}")
