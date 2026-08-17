"""Independent recomputation of the registered E1/E2 endpoints from raw banked
predictions. Deliberately shares no code with the instrument under review."""
import json
import sys
from collections import defaultdict
from pathlib import Path

RUN = Path(sys.argv[1])
CELLS = {
    "probe_real": RUN / "premise_probe",
    "probe_gray": RUN / "premise_probe_gray",
    "probe_no_image": RUN / "premise_probe_no_image",
    "final_real": RUN / "final",
    "final_gray": RUN / "final_gray",
    "final_no_image": RUN / "final_no_image",
}

rows_by_cell = {}
for key, d in CELLS.items():
    rows = [json.loads(l) for l in (d / "predictions.jsonl").read_text().splitlines() if l.strip()]
    rows_by_cell[key] = rows

out = {}
for key, rows in rows_by_cell.items():
    by_type = defaultdict(list)
    for r in rows:
        by_type[r["intervention_type"]].append(r)
    cell = {}
    for t, rs in sorted(by_type.items()):
        n = len(rs)
        len_mc = sum(bool(r["correct_a"]) + bool(r["correct_b"]) for r in rs)
        str_mc = sum(bool(r["strict_correct_a"]) + bool(r["strict_correct_b"]) for r in rs)
        len_pc = sum(1 for r in rs if r["pair_correct"])
        str_pc = sum(1 for r in rs if r["strict_pair_correct"])
        cell[t] = {
            "n_pairs": n,
            "lenient_member_acc": len_mc / (2 * n),
            "lenient_member_correct": len_mc,
            "strict_member_acc": str_mc / (2 * n),
            "lenient_pair_acc": len_pc / n,
            "strict_pair_acc": str_pc / n,
            "n_points": sorted({r["difficulty_knobs"]["n_points"] for r in rs}),
            "image_modes": sorted({r["eval_image_mode"] for r in rs}),
        }
    out[key] = cell

print(json.dumps(out, indent=1, sort_keys=True))

# Are the gray and no_image cells actually distinct files/responses?
for fam, a, b in (("probe", "probe_gray", "probe_no_image"), ("final", "final_gray", "final_no_image")):
    ra = {r["pair_id"]: r for r in rows_by_cell[a]}
    rb = {r["pair_id"]: r for r in rows_by_cell[b]}
    same_resp = sum(1 for k in ra if ra[k]["prediction_a"] == rb[k]["prediction_a"]
                    and ra[k]["prediction_b"] == rb[k]["prediction_b"])
    same_verdict = sum(1 for k in ra if ra[k]["correct_a"] == rb[k]["correct_a"]
                       and ra[k]["correct_b"] == rb[k]["correct_b"])
    print(f"# {fam}: n={len(ra)} identical_raw_responses={same_resp} identical_lenient_verdicts={same_verdict}")

# E1 carrier
c = out["probe_real"]["chained_premise_easy"]
print("# E1 carrier chained_premise_easy premise member acc lenient=%r strict=%r n_pairs=%d"
      % (c["lenient_member_acc"], c["strict_member_acc"], c["n_pairs"]))

# E2 evaluation, done independently
print("# E2 independent:")
for t in sorted(out["final_gray"]):
    npts = out["final_gray"][t]["n_points"]
    ceil = 2.0 / (npts[0] - 1) if len(npts) == 1 else None
    for mode in ("gray", "no_image"):
        f = out["final_" + mode][t]["lenient_member_acc"]
        p = out["probe_" + mode].get(t)
        pv = p["lenient_member_acc"] if p else None
        f_ok = f <= 0.133
        p_ok = (pv <= ceil) if pv is not None else "N/A"
        print(f"#  {t} {mode}: final={f} <=0.133 {f_ok} | premise={pv} <= {ceil} {p_ok}")
