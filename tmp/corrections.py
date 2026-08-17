#!/usr/bin/env python3
"""Two corrections found by the adversarial verification pass."""
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")

# --- 1. M11 / R5 is COMPLETE, not blocked -------------------------------------
p = ROOT / "reports/main_progress.md"
t = p.read_text()
lines = t.splitlines()
i = next(i for i, l in enumerate(lines) if l.startswith("| M11 |"))
lines[i] = (
    "| M11 | Cross-family completion | **pass** | **Corrected 2026-07-28 — R5 is LANDED.** The full "
    "18-cell matrix completed via `m11_reconciled_backfill_v2_login_20260717T075457Z` "
    "(status complete, exit 0): 12 FlipTrack cells (InternVL3-9B, Gemma-3 x {R19,R20} x "
    "{real,caption,none}) plus a 6-cell blind-sample matrix. `reports/generalization_audits_v2.json` "
    "has status pass, zero errors, all six completeness checks true, and "
    "`performance_values_opened_only_after_complete_queue_gate=true`. My 2026-07-27 entry claiming "
    "\"the 18-cell full matrix never ran\" was wrong. |"
)
# fix the known-defect note that recorded the wrong conclusion
j = next((j for j, l in enumerate(lines) if "status report v10 describes it as" in l or
          "a status report is not a" in l or "Status reports are not" in l), None)
if j is not None:
    start = j
    while not lines[start].lstrip().startswith("- "):
        start -= 1
    end = start + 1
    while end < len(lines) and lines[end].startswith("  ") and not lines[end].lstrip().startswith("- "):
        end += 1
    lines[start:end] = [
        "- `reports/m11_execution_queue_status_v10.md` describes its queue as `running` while that",
        "  queue's manifest says `fail`. **Both were stale**: the work was completed two days later by",
        "  `m11_reconciled_backfill_v2`. The real lesson is stronger than \"check the manifest, not the",
        "  status report\" — a failed run manifest does not mean the work never happened. Search for a",
        "  successor run before recording anything as never-ran.",
    ]
p.write_text("\n".join(lines) + "\n")
print("1. ledger M11 corrected")

# --- 2. MDE gloss: 0.0348 is ~70% of 0.05, not half ---------------------------
q = ROOT / "reports/pooled_item_equivalence_v1.md"
s = q.read_text()
old = ("For A1 the minimum detectable effect is ~0.035, comfortably below the")
if old in s:
    s = s.replace(
        "the design could have detected an effect half the size of the equivalence\nbound.",
        "the design could have detected an effect about 70% of the equivalence bound\n(0.0348 / 0.05).")
    s = s.replace(
        "the design could have detected an effect half the size of the\nequivalence bound.",
        "the design could have detected an effect about 70% of the equivalence\nbound (0.0348 / 0.05).")
q.write_text(s)
print("2. pooled_item_equivalence MDE gloss checked")

r = ROOT / "reports/RESULTS.md"
u = r.read_text()
before = u
u = u.replace("the design could have detected an effect roughly half the size of the\nequivalence bound.",
              "the design could have detected an effect about 70% of the equivalence\nbound (0.0348 / 0.05).")
u = u.replace("the design could have detected an effect roughly half the size of the equivalence bound.",
              "the design could have detected an effect about 70% of the equivalence bound (0.0348 / 0.05).")
r.write_text(u)
print("3. RESULTS.md MDE gloss", "changed" if u != before else "UNCHANGED (check wording)")
