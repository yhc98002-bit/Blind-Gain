import pathlib
p = pathlib.Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/scripts/render_e1c_blind_columns_md.py")
s = p.read_text(encoding="utf-8")
orig = s
old = '''    add(f"**Blind integrity.** {payload['blind_integrity']}")
    add("")'''
new = '''    add(f"**Blind integrity.** {payload['blind_integrity']}")
    add("")
    add("## HallusionBench null: which rule was applied")
    add("")
    add(payload["hallusionbench_null_decision"])
    add("")'''
assert old in s
s = s.replace(old, new, 1)
assert s != orig
p.write_text(s, encoding="utf-8")
print("patched renderer 2")
