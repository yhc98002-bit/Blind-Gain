#!/usr/bin/env python3
"""Add the missing external-benchmark section and repair artifact citations."""
from pathlib import Path

p = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/reports/RESULTS.md")
t = p.read_text()

SEC = """
---

## 13b. Standard benchmarks are largely answerable blind — our own model family

`reports/base_external_benchmarks.md`. The frozen base evaluated on public
benchmarks with and without the image, at two scales. Same locked contract and
parser as everything else.

| benchmark | model | with image | image removed | retained blind |
|---|---|---|---|---|
| MMStar (n=1,500) | 3B | 0.5540 | 0.2607 | **47%** |
| MMStar | 7B | 0.6320 | 0.2880 | **46%** |
| MathVista-testmini (n=999) | 3B | 0.6236 | 0.3293 | **53%** |
| MathVista-testmini | 7B | 0.6627 | 0.3393 | **51%** |

Roughly **half of standard-benchmark accuracy survives deleting the image
entirely**, at both 3B and 7B. This is the blind reward-opportunity thesis
measured on our own model family, and it is the reason the corpus audit exists:
an RLVR run on these benchmarks can collect most of its available reward without
consulting the image at all.

Read together with §13, the point generalises across model families as well as
scales — Gemma-3 retains 71% and InternVL3-9B 55% blind on the blind-sample
benchmark, while FlipTrack collapses to exactly 0.0000 with collapse rate 1.0 for
every model tested. **The contrast between those two lines is the case for the
instrument**: it is not that FlipTrack is harder, but that it is image-necessary
by construction where ordinary benchmarks are not.

Also complete for the base at both scales, without blind variants: BLINK
(0.4929 / 0.5565), HallusionBench (0.5979 / 0.6829), MMVP (0.6600 / 0.7433),
MathVerse (0.2817 / 0.3406), MMMU dev+validation (0.4819 / 0.5133).
"""

anchor = "\n---\n\n## 14. The instrument (C4)"
assert t.count(anchor) == 1, "anchor 14"
t = t.replace(anchor, SEC + anchor, 1)

# artifact citations that were missing (content was present, provenance was not)
fixes = [
    ("**P0.3** intervention-group schema frozen",
     "Artifacts: `reports/b1_rescored_p02_v1.json` (rescore), "
     "`reports/p04_task_roles_v1.md` (roles).\n\n**P0.3** intervention-group schema frozen"),
    ("Base pair accuracy by rung: exact 0.4533",
     "Artifacts: `reports/cue_ladder_readout_v1.{json,md}`, "
     "`reports/cue_ladder_base_gates_v1.json`.\n\nBase pair accuracy by rung: exact 0.4533"),
    ("An acceptance audit of all six conditions",
     "An acceptance audit of all six conditions "
     "(`reports/mini_a5_acceptance_audit_v1.json`)"),
    ("Δq = q_real − q_blind per item, taken from the registered blind reward-opportunity\naudit's own `q_i`",
     "Δq = q_real − q_blind per item, taken from the registered blind reward-opportunity\n"
     "audit's own `q_i` (`reports/blind_solvability_geo3k_v3_audited.json`)"),
]
for old, new in fixes:
    if old in t and new.split("\n")[0] not in t.replace(old, ""):
        t = t.replace(old, new, 1)
        print(f"  cited: {old[:50]}...")
    else:
        print(f"  SKIP (anchor absent or already cited): {old[:50]}...")

# refresh the in-flight section
old_flight = """- **D4 caption column** — 4/12 cells complete; 2 failed on CUDA OOM from a
  scheduler double-booking and are queued for retry. Registered reading (ordering
  under caption-at-test: pixel-specific vs evidence-general) filed before any
  cell ran."""
new_flight = """- **D4 caption column** — **complete**, see §2b. Branch (a), evidence-general."""
if old_flight in t:
    t = t.replace(old_flight, new_flight, 1)
    print("  refreshed: D4 in-flight entry")

old_m7 = "- **R3 M7** — ready; per-stratum estimands and the merged pre-launch prediction\n  verified present."
new_m7 = ("- **R3 M7** — **launched** 2026-07-28 on an12 (arm 1 of 8, `a1_real` seed 1);\n"
          "  per-stratum estimands and the merged pre-launch prediction verified present.")
if old_m7 in t:
    t = t.replace(old_m7, new_m7, 1)
    print("  refreshed: M7 in-flight entry")

p.write_text(t)
print("\nwrote RESULTS.md")
