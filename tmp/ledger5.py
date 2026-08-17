#!/usr/bin/env python3
from pathlib import Path

p = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/reports/main_progress.md")
t = p.read_text()
old = [l for l in t.splitlines() if "single-gold workaround" in l]
if not old:
    raise SystemExit("anchor line not found")
# the defect note spans two lines; rebuild from the bullet start
lines = t.splitlines()
i = next(i for i, l in enumerate(lines) if "single-gold workaround" in l)
start = i
while not lines[start].lstrip().startswith("- "):
    start -= 1
end = start + 1
while end < len(lines) and lines[end].startswith("  ") and not lines[end].lstrip().startswith("- "):
    end += 1
new = [
    "- B1 invariance types (`style_twin` 14/14, `distractor_only` 16/16) were scored",
    "  with a single-gold workaround before P0.2. **Rescored under the fixed scorer:",
    "  0 of 30 cells move** — all differences are 3-dp rounding in the published",
    "  table — so the published B1 numbers stand. The workaround was fragile in",
    "  principle (never validated against the two-gold path; a response matching the",
    "  other member's gold would have been mis-scored) but was equivalent on these",
    "  items. `reports/b1_rescored_p02_v1.json`. **Closed.**",
]
lines[start:end] = new
p.write_text("\n".join(lines) + ("\n" if t.endswith("\n") else ""))
print(f"ledger updated (replaced lines {start}-{end})")
