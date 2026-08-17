import pathlib

p = pathlib.Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/scripts/render_e1c_blind_columns_md.py")
s = p.read_text(encoding="utf-8")
orig = s

# a value plus its interval, collapsing to a single "n/a" when undefined
old = '''def ci(block, key, digits=4):
    low = block.get(f"{key}_ci95_low")
    high = block.get(f"{key}_ci95_high")
    if low is None or high is None:
        return "n/a"
    return f"[{low:.{digits}f}, {high:.{digits}f}]"'''
new = '''def ci(block, key, digits=4):
    low = block.get(f"{key}_ci95_low")
    high = block.get(f"{key}_ci95_high")
    if low is None or high is None:
        return ""
    return f"[{low:.{digits}f}, {high:.{digits}f}]"


def est(block, key, digits=4):
    """Point estimate plus interval, collapsed to a single 'n/a' when undefined."""
    point = num(block.get(key), digits)
    interval = ci(block, key, digits)
    if point == "n/a" and not interval:
        return "n/a"
    return f"{point} {interval}".strip()'''
assert old in s
s = s.replace(old, new, 1)

# use est() everywhere a retention value is printed
s = s.replace(
    """            f"{num(lenient['naive_retention'])} {ci(lenient, 'naive_retention')} |"
        )""",
    """            f"{est(lenient, 'naive_retention')} |"
        )""",
    1,
)
old = """            f"{num(lenient['naive_retention'])} {ci(lenient, 'naive_retention')} | "
            f"{num(lenient['corrected_retention'])} {ci(lenient, 'corrected_retention')} | "
            f"{num(lenient['boot_denominator_nonpositive_frac'], 3)} |\""""
new = """            f"{est(lenient, 'naive_retention')} | "
            f"{est(lenient, 'corrected_retention')} | "
            f"{num(lenient['boot_denominator_nonpositive_frac'], 3)} |\""""
assert old in s
s = s.replace(old, new, 1)
old = """            f"{num(strict['naive_retention'])} {ci(strict, 'naive_retention')} | "
            f"{num(strict['corrected_retention'])} {ci(strict, 'corrected_retention')} | "
            f"{num(strict['denominator_crosses_zero'])} |\""""
new = """            f"{est(strict, 'naive_retention')} | "
            f"{est(strict, 'corrected_retention')} | "
            f"{num(strict['denominator_crosses_zero'])} |\""""
assert old in s
s = s.replace(old, new, 1)

# mark subsets in the Subset column
old = '''    for row in payload["rows"]:
        lenient = row["lenient_acc_final"]
        add(
            f"| {row['benchmark']} | {row['model']} | {row['subset']} | "'''
new = '''    for row in payload["rows"]:
        lenient = row["lenient_acc_final"]
        add(
            f"| {row['benchmark']} | {row['model']} | {label(row)} | "'''
assert old in s
s = s.replace(old, new, 1)
old = '''    for row in payload["rows"]:
        strict = row["strict_acc_strict"]
        add(
            f"| {row['benchmark']} | {row['model']} | {row['subset']} | {row['n']} | "'''
new = '''    for row in payload["rows"]:
        strict = row["strict_acc_strict"]
        add(
            f"| {row['benchmark']} | {row['model']} | {label(row)} | {row['n']} | "'''
assert old in s
s = s.replace(old, new, 1)

old = '''def main() -> None:'''
new = '''def label(row):
    return row["subset"] + (" **(underpowered)**" if row.get("underpowered_subset") else "")


def main() -> None:'''
assert old in s
s = s.replace(old, new, 1)

# surface the two method notes in the md
old = '''    add(f"- {method['mixed_benchmark_rule']}")'''
new = '''    add(f"- {method['mixed_benchmark_rule']}")
    add(f"- {method['undefined_denominator']}")
    add(f"- {method['underpowered_subsets']}")'''
assert old in s
s = s.replace(old, new, 1)

assert s != orig
p.write_text(s, encoding="utf-8")
print("patched renderer")
