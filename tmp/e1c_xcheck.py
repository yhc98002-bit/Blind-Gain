import json, pathlib
ROOT = pathlib.Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
payload = json.loads((ROOT/"reports/e1c_blind_columns_v1.json").read_text())
whole = {(r["benchmark"], r["model"]): r for r in payload["reference_naive_whole_benchmark"]}
prov = {(p["benchmark"], p["model"]): p for p in payload["provenance"]}
print(f"{'benchmark':<22}{'model':<16}{'my with-img':>12}{'src metrics':>12}{'my blind':>10}{'blind metrics':>14}  match")
bad = 0
for key, p in sorted(prov.items()):
    src = json.loads((ROOT/p["with_image_run"]/"metrics.json").read_text())
    # find the overall acc_final in the with-image metrics
    cand = src.get("overall", src)
    src_acc = cand.get("Acc_final", cand.get("acc_final"))
    blind_dir = ROOT/"experiments/runs"/p["blind_run_id"]
    bm = json.loads((blind_dir/"metrics.json").read_text())["overall"]["Acc_final"]
    mine = whole[key]["lenient_acc_final"]
    ok = abs(mine["with_image_acc"] - src_acc) < 1e-9 and abs(mine["blind_acc"] - bm) < 1e-9
    if not ok: bad += 1
    print(f"{key[0]:<22}{key[1]:<16}{mine['with_image_acc']:>12.6f}{src_acc:>12.6f}"
          f"{mine['blind_acc']:>10.6f}{bm:>14.6f}  {'OK' if ok else 'MISMATCH'}")
print("\nmismatches:", bad)
