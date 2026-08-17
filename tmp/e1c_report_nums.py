import json, pathlib
ROOT = pathlib.Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
payload = json.loads((ROOT/"reports/e1c_blind_columns_v1.json").read_text())
KEEP = ("pooled", "primary", "free-form", "real-image", "text-only")
for row in payload["rows"]:
    if not any(t in row["subset"] for t in KEEP):
        continue
    if "sensitivity" in row["subset"] and "binary" not in row["subset"]:
        continue
    b = row["lenient_acc_final"]
    def f(v): return "None" if v is None else f"{v:.4f}"
    print(f"{row['benchmark']:<20} {row['model'][-2:]:<3} {row['subset']:<58} n={row['n']:<5} "
          f"null={row['null']:.4f} img={b['with_image_acc']:.4f} blind={b['blind_acc']:.4f} "
          f"naive={f(b['naive_retention'])}[{f(b['naive_retention_ci95_low'])},{f(b['naive_retention_ci95_high'])}] "
          f"corr={f(b['corrected_retention'])}[{f(b['corrected_retention_ci95_low'])},{f(b['corrected_retention_ci95_high'])}]")
