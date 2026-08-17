import pathlib

p = pathlib.Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/scripts/e1c_blind_columns.py")
s = p.read_text(encoding="utf-8")
orig = s

s = s.replace("REPS = 10000\nSEED = 20260729\nCHUNK = 1000",
              "REPS = 10000\nSEED = 20260729\nCHUNK = 1000\n"
              "# mean(with_image) - mean(null) can land on ~1e-16 instead of exactly 0 when the\n"
              "# with-image accuracy equals the null (e.g. 5/30 vs 1/6); dividing by that produces\n"
              "# a ~1e15 garbage ratio, so treat |denominator| <= TOL as undefined.\n"
              "TOL = 1e-12\n"
              "UNDERPOWERED_N = 30", 1)

old = """        with np.errstate(divide="ignore", invalid="ignore"):
            naive.append(np.where(mw > 0, mb / mw, np.nan))
            denominator = mw - mn
            corrected.append(np.where(denominator != 0, (mb - mn) / denominator, np.nan))
        nonpositive += int((denominator <= 0).sum())"""
new = """        with np.errstate(divide="ignore", invalid="ignore"):
            naive.append(np.where(mw > 0, mb / mw, np.nan))
            denominator = mw - mn
            corrected.append(
                np.where(np.abs(denominator) > TOL, (mb - mn) / denominator, np.nan)
            )
        nonpositive += int((denominator <= 0).sum())"""
assert old in s
s = s.replace(old, new, 1)

old = """    mb, mw, mn = float(blind.mean()), float(image.mean()), float(null.mean())
    denom = mw - mn"""
new = """    mb, mw, mn = float(blind.mean()), float(image.mean()), float(null.mean())
    denom = mw - mn
    denom_defined = abs(denom) > TOL"""
assert old in s
s = s.replace(old, new, 1)

old = """    frac = nonpositive / REPS
    return {
        "with_image_acc": mw,
        "blind_acc": mb,
        "naive_retention": (mb / mw) if mw > 0 else None,
        "denominator": denom,
        "corrected_retention": ((mb - mn) / denom) if denom != 0 else None,
        "naive_retention_ci95_low": naive_low,
        "naive_retention_ci95_high": naive_high,
        "naive_retention_ci_valid_reps": naive_reps,
        "corrected_retention_ci95_low": corr_low,
        "corrected_retention_ci95_high": corr_high,
        "corrected_retention_ci_valid_reps": corr_reps,"""
new = """    frac = nonpositive / REPS
    if not denom_defined:
        # The statistic is undefined at the point estimate, so its interval is reported
        # as undefined too rather than borrowed from the replicates that happened to move
        # the denominator off zero.
        corr_low = corr_high = None
    return {
        "with_image_acc": mw,
        "blind_acc": mb,
        "naive_retention": (mb / mw) if mw > 0 else None,
        "denominator": denom,
        "corrected_retention": ((mb - mn) / denom) if denom_defined else None,
        "corrected_retention_undefined": not denom_defined,
        "naive_retention_ci95_low": naive_low,
        "naive_retention_ci95_high": naive_high,
        "naive_retention_ci_valid_reps": naive_reps,
        "corrected_retention_ci95_low": corr_low,
        "corrected_retention_ci95_high": corr_high,
        "corrected_retention_ci_valid_reps": corr_reps if denom_defined else 0,"""
assert old in s
s = s.replace(old, new, 1)

# flag underpowered subsets
old = """        "n": len(items),
        "null": float(null.mean()),
        "lenient_acc_final": bootstrap(blind, image, null),
        "strict_acc_strict": bootstrap(blind_s, image_s, null),
    }"""
new = """        "n": len(items),
        "null": float(null.mean()),
        "underpowered_subset": len(items) < UNDERPOWERED_N,
        "lenient_acc_final": bootstrap(blind, image, null),
        "strict_acc_strict": bootstrap(blind_s, image_s, null),
    }"""
assert old in s
s = s.replace(old, new, 1)

# document both in method
old = '''            "scoring_contracts": {"lenient": "acc_final", "strict": "acc_strict"},'''
new = '''            "scoring_contracts": {"lenient": "acc_final", "strict": "acc_strict"},
            "undefined_denominator": "Where mean(with_image) equals mean(null) the corrected "
                                     f"denominator is 0 (guarded at |d| <= {TOL:g} against floating "
                                     "point residue); corrected retention and its CI are reported "
                                     "as null with corrected_retention_undefined=true.",
            "underpowered_subsets": f"Subsets with n < {UNDERPOWERED_N} carry "
                                    "underpowered_subset=true. Their intervals are reported for "
                                    "completeness but are not interpretable; MMMU k=6 (n=6), k=7 "
                                    "(n=2) and k=9 (n=5) are the affected cells.",'''
assert old in s
s = s.replace(old, new, 1)

assert s != orig
p.write_text(s, encoding="utf-8")
print("patched analysis script")
