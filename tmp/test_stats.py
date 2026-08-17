#!/usr/bin/env python3
"""Sanity-check the two statistics helpers in scripts/analyze_mini_a5_s1.py
against hand-computable cases before the real data lands."""
import importlib.util
from pathlib import Path
from scipy.stats import binomtest

spec = importlib.util.spec_from_file_location(
    "an", "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/scripts/analyze_mini_a5_s1.py"
)
an = importlib.util.module_from_spec(spec)
spec.loader.exec_module(an)

# --- McNemar --------------------------------------------------------------
c1 = an.mcnemar_exact_bool([True, True, False, False], [True, False, True, False])
print("mcnemar b01=1,b10=1 ->", c1, "(expect b01=1 b10=1 p=1.0)")
assert (c1["b01"], c1["b10"]) == (1, 1) and abs(c1["p_value"] - 1.0) < 1e-12

c2 = an.mcnemar_exact_bool([True] * 10 + [False] * 0, [False] * 10)
print("mcnemar all a-only ->", c2)
assert (c2["b01"], c2["b10"]) == (0, 10)
assert abs(c2["p_value"] - float(binomtest(0, 10, 0.5).pvalue)) < 1e-12, "must equal exact binomial"

c3 = an.mcnemar_exact_bool([True, True], [True, True])
print("mcnemar no discordance ->", c3, "(expect p=1.0)")
assert c3["n_discordant"] == 0 and c3["p_value"] == 1.0

# cross-check a mixed case against scipy's exact binomial test
a = [True] * 7 + [False] * 3 + [True] * 5
b = [False] * 7 + [True] * 3 + [True] * 5
c4 = an.mcnemar_exact_bool(a, b)
expect = float(binomtest(min(c4["b01"], c4["b10"]), c4["n_discordant"], 0.5).pvalue)
print(f"mcnemar mixed -> {c4}  scipy exact p={expect:.6g}")
assert abs(c4["p_value"] - expect) < 1e-12

# --- paired bootstrap -----------------------------------------------------
d1 = an.paired_bootstrap_diff([1.0] * 50, [0.0] * 50, seed=20260729)
print("bootstrap separated ->", {k: d1[k] for k in ("point", "ci95_low", "ci95_high", "excludes_zero")})
assert d1["point"] == 1.0 and d1["ci95_low"] == 1.0 and d1["ci95_high"] == 1.0 and d1["excludes_zero"]

d2 = an.paired_bootstrap_diff([1.0, 0.0] * 25, [1.0, 0.0] * 25, seed=20260729)
print("bootstrap identical ->", {k: d2[k] for k in ("point", "ci95_low", "ci95_high", "excludes_zero")})
assert d2["point"] == 0.0 and not d2["excludes_zero"], "identical vectors must give a zero diff"

# determinism under the same seed, difference under another
d3a = an.paired_bootstrap_diff([1.0, 0.0, 1.0] * 40, [0.0, 1.0, 1.0] * 40, seed=20260729)
d3b = an.paired_bootstrap_diff([1.0, 0.0, 1.0] * 40, [0.0, 1.0, 1.0] * 40, seed=20260729)
d3c = an.paired_bootstrap_diff([1.0, 0.0, 1.0] * 40, [0.0, 1.0, 1.0] * 40, seed=20260730)
assert (d3a["ci95_low"], d3a["ci95_high"]) == (d3b["ci95_low"], d3b["ci95_high"]), "same seed must reproduce"
assert (d3a["ci95_low"], d3a["ci95_high"]) != (d3c["ci95_low"], d3c["ci95_high"]), "different seed must differ"
print("bootstrap determinism -> OK")

print("\nseed table (indicator_index, template_index) -> seed")
for i in range(6):
    print("  ", i, [an.resolve_seed(i, t) for t in range(3)])
print("\nALL STATS CHECKS PASSED")
