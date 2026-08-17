#!/usr/bin/env python3
"""Update RESEARCH_DOC §4 (evidence) and §5 (pending) per its §8 protocol.

Only §4 and §5 are touched; §1–§3 and §7 are never edited.
"""
from pathlib import Path
import sys

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
DOC = ROOT / "docs/RESEARCH_DOC.md"

NEW_ROWS = """| X1/X5 image-condition matrix (seeds 1–2) | Margin inflation is content-bound: mismatched-real inflation statistically zero for every arm in both seeds (|mean| ≤ 0.0006, CIs span zero) while correct-image inflation is far from zero (A1 +0.150/+0.129; A3 +0.090/+0.076; A2b +0.035/+0.058; A2 +0.036/+0.037). Twin-image condition: the twin's gold is preferred for 0.948–0.955 of members in every model including base |
| X2 hard-negative ranking (registered ladder) | Golds-only margin pair-success is candidate-set-invariant and reproduces at exactly 0.9067; against the structured negative sets base pair-success is 0.5167 [0.4750, 0.5567] (A1 step-60 0.5267, step-100 0.5133) → registered bottom branch: the 0.9067 is predominantly candidate-set structure and the realization gap is a measurement-methods finding |
| X3 A2-gray degradation forensics | The −4.5pp geometry decline is item-identifiable and answer-deterministic across seeds: correct→wrong sets 51/49 with 42 shared (Jaccard 0.724 vs permutation null 0.098, p = 1e-4), same extracted wrong answer in 41/42 shared slots; dominant taxon nearest-gridline off-by-one (19/20) |
| X4 calibration (EXPLORATORY) | Under real images all models are underconfident (confidence ~0.18–0.20 vs accuracy ~0.75); under twin-counterfactual images confidence is unchanged by construction while accuracy collapses to ~0.012 (overconfidence gap +0.17–0.19) |
| B1 renderable geometry track (declared batch) | Base pair-correct: fact-read 0.600, style-twin invariance 0.643, distractor invariance 0.438, binding swap 0.188, prior-conflict 0.143, chained two-hop 0.000 (member 0.150); blind 0.03, caption 0.04 overall |
| D2 test-time image access (registered) | The Geometry3K gain is image-mediated at test time in both seeds: RetainedGainBlind 0.158 (seed 1) / 0.122 (seed 2), registered band (a); reproduction check reproduced published step-100 exactly. Secondary: A2b evaluated **with** images reaches 0.3195/0.2962 vs its published blind 0.0982/0.1231 (test-time image benefit +0.221/+0.173) |
"""

NEW_PENDING = """## 5. Pending → what each buys

Seed-3 four-arm endpoints + three-seed summary and pooled equivalence verdict (replication rung R2; evaluation lifecycle armed, cohort release on A3 completion) · M5 step-400 terminal readout (horizon rung R3; segments self-driving, step-300 boundary recovered and merged checkpoint regenerated on quota) · M6 mini-A5 two-arm (Paper-2 gate + RL positive control; registered, launcher and checkpoint watcher built, launches when an29 clears the seed-3 evaluations) · M7 ViRL 3B stratified (dose-response rung R4; frozen subset and audited caption store complete, image-disjoint held-out split registered and built, eight matched arm configs and the amendment-bound launcher committed — awaiting a free node) · M8/M9 7B ×3 seeds, 4 arms (scale rung R5) · M11 non-Qwen (family rung R6) · X6 related-work audit table (PI-owned) · human passes: chart-v08 no-zoom audit, 24 expansion candidates, R19/R20 audit samples · merge-back readouts.
"""


def main() -> int:
    text = DOC.read_text(encoding="utf-8")
    if "X1/X5 image-condition matrix" in text:
        print("already updated")
        return 0
    anchor = "| Instrument dossier | R19 + one-shot R20 + 72B caption ≤0.062 + human audit 60/60 + attacker CIs |\n"
    if text.count(anchor) != 1:
        print("ABORT: §4 anchor row not found uniquely")
        return 1
    text = text.replace(anchor, anchor + NEW_ROWS)
    start = text.index("## 5. Pending")
    end = text.index("## 6. Pre-committed")
    text = text[:start] + NEW_PENDING + "\n" + text[end:]
    DOC.write_text(text, encoding="utf-8")
    print("RESEARCH_DOC §4/§5 updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
