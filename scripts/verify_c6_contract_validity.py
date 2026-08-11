"""Why strict == lenient on two of the three C6 roles.

The C6 levels show identical lenient and contract-strict pair accuracy on the
anchor and readout roles for all six cells, while the canary role separates.
Two very different things produce that pattern:

  (i) a degenerate strict channel (the reason registration section 6 excluded the
      2026-07-10 base cells), or
  (ii) contract validity saturated at 1.000 on those roles for these 7B models,
      with a live strict channel that still discriminates elsewhere.

This distinguishes them by reading contract validity directly.  If (ii) holds,
the strict channel is working and the C6 anchor movement cannot be a
format-compliance artifact -- there is no format headroom on that role to move.
"""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
POINTERS = ROOT / "logs" / "c6_cells"
ANCHOR = "coordinate_register_twenty_point_x_v02"
CANARY = "header_cued_table_code_v02"
READOUT = "starred_series_value_nine_v07"
SHORT = {ANCHOR: "ANCHOR", CANARY: "CANARY", READOUT: "READOUT"}


def load(label):
    run_dir = Path((POINTERS / label).read_text().strip())
    if not run_dir.is_absolute():
        run_dir = ROOT / run_dir
    rows = []
    for shard in sorted((run_dir / "shards").glob("shard_*.jsonl")):
        with shard.open() as fh:
            rows.extend(json.loads(l) for l in fh if l.strip())
    return rows


print("%-12s %-8s %6s %14s %14s %10s" % (
    "cell", "role", "n", "contract_valid", "both_members_cv", "strict<len"))
for lab in ("r19_base7b", "r19_a1real", "r19_a2gray",
            "r20_base7b", "r20_a1real", "r20_a2gray"):
    by_role = defaultdict(list)
    for r in load(lab):
        by_role[r["template_id"]].append(r)
    for role in (ANCHOR, CANARY, READOUT):
        rs = by_role[role]
        n = len(rs)
        cv_pair = sum(1 for r in rs if r["contract_valid"]) / n
        cv_members = sum(
            1 for r in rs if r["contract_valid_a"] and r["contract_valid_b"]) / n
        gap = (sum(1 for r in rs if r["pair_correct"])
               - sum(1 for r in rs if r["strict_pair_correct"])) / n
        print("%-12s %-8s %6d %14.4f %14.4f %10.4f" % (
            lab, SHORT[role], n, cv_pair, cv_members, gap))
