#!/usr/bin/env python3
"""Fast per-template validity decomposition for the 6 F8 cells. No bootstrap."""
import json
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
from src.eval.fliptrack_metrics import pair_score

RUN_TS = "20260730T004031Z"
ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
CELLS = {
    "r19_cp": f"mini_a5_f8_r19_cp_step120_real_an29_{RUN_TS}",
    "r19_member": f"mini_a5_f8_r19_member_step120_real_an29_{RUN_TS}",
    "r20_cp": f"mini_a5_f8_r20_cp_step120_real_an29_{RUN_TS}",
    "r20_member": f"mini_a5_f8_r20_member_step120_real_an29_{RUN_TS}",
    "chartv08_cp": f"mini_a5_f8_chartv08_cp_step120_real_an29_{RUN_TS}",
    "chartv08_member": f"mini_a5_f8_chartv08_member_step120_real_an29_{RUN_TS}",
}

out = {}
for key, rundir in CELLS.items():
    rows = []
    for p in sorted((ROOT / "experiments/runs" / rundir / "shards").glob("shard_*.jsonl")):
        with p.open(encoding="utf-8") as fh:
            rows.extend(json.loads(ln) for ln in fh if ln.strip())
    by_t = defaultdict(list)
    for r in rows:
        by_t[str(r.get("template_id"))].append(pair_score(r))
    cell = {}
    for t, sc in sorted(by_t.items()):
        n = len(sc)
        cell[t] = {
            "n_pairs": n,
            "pair_accuracy": sum(s["pair_correct"] for s in sc) / n,
            "strict_pair_accuracy": sum(s["strict_pair_correct"] for s in sc) / n,
            "contract_valid_rate": sum(s["contract_valid"] for s in sc) / n,
            "extractor_valid_rate": sum(s["extractor_valid"] for s in sc) / n,
            "extraction_fallback_rate": sum(s["extraction_fallback_used"] for s in sc) / n,
            "collapse_rate": sum(s["collapsed"] for s in sc) / n,
            "ambiguous_rate": sum(s["ambiguous"] for s in sc) / n,
            # lenient-correct-but-not-strict: the contract-only loss
            "lenient_correct_not_strict": sum(
                s["pair_correct"] and not s["strict_pair_correct"] for s in sc
            ) / n,
            "strict_correct_not_lenient": sum(
                s["strict_pair_correct"] and not s["pair_correct"] for s in sc
            ) / n,
        }
    out[key] = cell

print(json.dumps(out, indent=2, sort_keys=True))
