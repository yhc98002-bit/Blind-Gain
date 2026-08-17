#!/usr/bin/env python3
"""Integrity check: A1 and A3 caption cells came out at identical accuracy.

Confirm they are distinct runs over distinct checkpoints producing distinct
predictions, so the tie is a coincidence rather than a cell mix-up.
"""
import json
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
rec = json.loads((ROOT / "reports/d4_cell_reconciliation_v1.json").read_text())["kept"]


def load(cell):
    d = ROOT / "experiments/runs" / rec[cell]["run"]
    rows = [json.loads(l) for l in (d / "predictions.jsonl").read_text().splitlines() if l.strip()]
    man = json.loads((d / "run_manifest.json").read_text())
    return rows, man


for s in (1, 2, 3):
    a, ma = load(f"a1_seed{s}")
    b, mb = load(f"a3_seed{s}")
    ka = {r["problem"]: r for r in a}
    kb = {r["problem"]: r for r in b}
    common = sorted(set(ka) & set(kb))
    same = sum(1 for p in common if ka[p].get("extracted_answer") == kb[p].get("extracted_answer"))
    acc_a = sum(bool(r["acc_final"]) for r in a) / len(a)
    acc_b = sum(bool(r["acc_final"]) for r in b) / len(b)
    ck_a = str(ma.get("model_path") or ma.get("checkpoint") or "?")
    ck_b = str(mb.get("model_path") or mb.get("checkpoint") or "?")
    print(f"seed{s}: a1_acc={acc_a:.4f} a3_acc={acc_b:.4f} "
          f"identical_extracted_answers={same}/{len(common)}")
    print(f"        a1 ckpt ...{ck_a[-46:]}")
    print(f"        a3 ckpt ...{ck_b[-46:]}")
