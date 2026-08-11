"""Third, orthogonal check on C6.

Both readout instruments compute pair success by calling
src.eval.fliptrack_metrics.pair_score, which RE-DERIVES correctness from
prediction_a / prediction_b at readout time. That shared code path is a common
mode: if it were wrong, two independent instruments would agree and both be
wrong.

This check bypasses it entirely and uses the `pair_correct` /
`strict_pair_correct` fields that were written into each row at GENERATION time,
computing per-role arm-minus-base deltas as plain arithmetic. Agreement with the
instruments' levels means the scoring path is not the thing carrying the result.
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
    rows = {}
    for shard in sorted((run_dir / "shards").glob("shard_*.jsonl")):
        with shard.open() as fh:
            for line in fh:
                if line.strip():
                    r = json.loads(line)
                    rows[r["pair_id"]] = r
    return rows


cells = {
    lab: load(lab)
    for lab in ("r19_base7b", "r19_a1real", "r19_a2gray", "r20_base7b", "r20_a1real", "r20_a2gray")
}

print("Per-role levels from the STORED generation-time fields (no re-scoring):")
print("%-12s %-8s %-8s %8s %8s" % ("cell", "role", "n", "lenient", "strict"))
levels = {}
for lab, rows in cells.items():
    by_role = defaultdict(list)
    for r in rows.values():
        by_role[r["template_id"]].append(r)
    for role in (ANCHOR, CANARY, READOUT):
        rs = by_role[role]
        len_acc = sum(1 for r in rs if r["pair_correct"]) / len(rs)
        str_acc = sum(1 for r in rs if r["strict_pair_correct"]) / len(rs)
        levels[(lab, role)] = (len_acc, str_acc)
        print("%-12s %-8s %8d %8.4f %8.4f" % (lab, SHORT[role], len(rs), len_acc, str_acc))

print()
print("Arm minus base, stored fields, plain arithmetic:")
print("%-28s %-8s %+10s %+10s" % ("contrast", "role", "lenient", "strict"))
for base, arm, tag in (
    ("r19_base7b", "r19_a1real", "c6_1_a1real_r19"),
    ("r19_base7b", "r19_a2gray", "c6_2_a2gray_r19"),
    ("r20_base7b", "r20_a1real", "c6_3_a1real_r20"),
    ("r20_base7b", "r20_a2gray", "c6_4_a2gray_r20"),
):
    for role in (ANCHOR, CANARY, READOUT):
        bl, bs = levels[(base, role)]
        al, as_ = levels[(arm, role)]
        print("%-28s %-8s %+10.4f %+10.4f" % (tag, SHORT[role], al - bl, as_ - bs))

print()
mismatch = 0
total = 0
for lab, rows in cells.items():
    for r in rows.values():
        total += 1
        if r["pair_correct"] != (r["correct_a"] and r["correct_b"]):
            mismatch += 1
        if r["strict_pair_correct"] != (r["strict_correct_a"] and r["strict_correct_b"]):
            mismatch += 1
print("internal row consistency: %d rows checked, %d field disagreements" % (total, mismatch))
print("R19 x R20 pair_id intersection:",
      len(set(cells["r19_base7b"]) & set(cells["r20_base7b"])))
