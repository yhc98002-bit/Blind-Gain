#!/usr/bin/env python3
from pathlib import Path

p = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/reports/main_progress.md")
t = p.read_text()
lines = t.splitlines()
i = next(i for i, l in enumerate(lines) if l.startswith("| A5 |"))
lines[i] = ("| A5 | Mini-A5 CP vs matched same-data GRPO | running | CP arm on an29:0–7. Matched "
            "same-data standard GRPO arm queued next. **Gate-1 four-arm registration merged** "
            "(`docs/registered_gate1_four_arm_v1.md`) so arms 3–4 can launch without registration "
            "lag if F7 is positive; it does not launch until Mini-A5 completes and a node is free. |")
# add a Gate-1 row to the Paper 2 section if absent
if "| Gate 1 |" not in t:
    j = next(j for j, l in enumerate(lines) if l.startswith("## Paper 2 — Phase 0"))
    block = [
        "",
        "## Paper 2 — Gate 1 (gated on F7)",
        "",
        "| ID | Task | Status | Note |",
        "|---|---|---|---|",
        ("| Gate 1 | Four-arm decomposition (standard / paired-data / necessity / IGPO) | blocked | "
         "Registered before any optimizer step (I9). Blocked on F7 and on a free node. Success is "
         "held-out-template pair accuracy at the scene-program level; margins explicitly excluded "
         "(X2 bottom branch), chained premise excluded (P0.1 branch (b)); no branch reads as success "
         "unless VAG is positive (I8). |"),
        "",
    ]
    lines[j:j] = block
p.write_text("\n".join(lines) + "\n")
print("ledger updated")
