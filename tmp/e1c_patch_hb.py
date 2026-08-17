import pathlib

p = pathlib.Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/scripts/e1c_blind_columns.py")
s = p.read_text(encoding="utf-8")
orig = s

s = s.replace("import numpy as np", "import numpy as np\nimport pandas as pd", 1)

# tag each item with the HallusionBench placeholder flag
old = """                    "gold_agrees": json.dumps(blind["gold"], sort_keys=True)
                    == json.dumps(image["gold"], sort_keys=True),
                })"""
new = """                    "gold_agrees": json.dumps(blind["gold"], sort_keys=True)
                    == json.dumps(image["gold"], sort_keys=True),
                    "placeholder_image": placeholder.get(index),
                })"""
assert old in s
s = s.replace(old, new, 1)

old = """            items = []
            for index, blind in blind_rows.items():"""
new = """            # HallusionBench ships 178 text-only rows that the adapter gave a deterministic
            # blank image, so for those rows the with-image condition carried no visual
            # information either and removing the image removes nothing.
            placeholder: dict[str, bool] = {}
            if benchmark == "HallusionBench":
                frame = pd.read_csv(ROOT / manifest["data_manifest"], sep="\\t")
                placeholder = {
                    str(r["index"]): bool(r["image_is_placeholder"])
                    for _, r in frame.iterrows()
                }

            items = []
            for index, blind in blind_rows.items():"""
assert old in s
s = s.replace(old, new, 1)

old = """            elif mode == "binary_yorn":
                assert not mc, (benchmark, "unexpected MC rows")
                rows.append(make_row(
                    benchmark, scale,
                    "all items (free-form null=0, primary)", "free_form", 0, ff, null_override=0.0,
                ))
                rows.append(make_row(
                    benchmark, scale,
                    "all items (binary Yes/No null=0.5, sensitivity)", "binary_yes_no", 2, ff, null_override=0.5,
                ))"""
new = """            elif mode == "binary_yorn":
                assert not mc, (benchmark, "unexpected MC rows")
                rows.append(make_row(
                    benchmark, scale,
                    "all items (free-form null=0, primary)", "free_form", 0, ff, null_override=0.0,
                ))
                rows.append(make_row(
                    benchmark, scale,
                    "all items (binary Yes/No null=0.5, sensitivity)", "binary_yes_no", 2, ff, null_override=0.5,
                ))
                real = [it for it in ff if it["placeholder_image"] is False]
                blank = [it for it in ff if it["placeholder_image"] is True]
                assert len(real) == 951 and len(blank) == 178, (len(real), len(blank))
                rows.append(make_row(
                    benchmark, scale,
                    "real-image rows only (free-form null=0)", "free_form", 0, real, null_override=0.0,
                ))
                rows.append(make_row(
                    benchmark, scale,
                    "text-only rows, blank placeholder image (free-form null=0)",
                    "free_form", 0, blank, null_override=0.0,
                ))
                not_computed.append({
                    "benchmark": benchmark,
                    "model": f"Qwen2.5-VL-{scale}",
                    "subset": "text-only rows (n=178) as evidence of visual necessity",
                    "n": 178,
                    "reason": "HallusionBench_LOCAL_V2.metadata.json records "
                              "text_only_rows_use_deterministic_blank_image=178: these rows carried a "
                              "deterministic blank image in the with-image condition, so removing the "
                              "image removes no visual information and their retention is not evidence "
                              "about visual necessity. They are reported as their own subset and are "
                              "the reason the all-items HallusionBench row is a ceiling on retention.",
                })"""
assert old in s
s = s.replace(old, new, 1)

# note it in the payload
old = '''        "blind_integrity":'''
new = '''        "hallusionbench_null_decision": (
            "HallusionBench stores no option labels on any of its 1129 rows (k=0 everywhere), and "
            "the with-image column scored it with the open_final_span contract. DECISION: it is "
            "treated as FREE-FORM with null=0 for the primary row -- no option labels were "
            "synthesised and no options were extracted. Because its gold vocabulary is in fact "
            "binary ({Yes: 484, No: 645}) while only 170 of 1129 question texts say 'yes or no', a "
            "second row applies null=0.5 and is labelled a sensitivity, not the primary. The "
            "free-form primary is the conservative choice under the existing null rule ('1/k using "
            "that item's own k (count of option labels presented)'): zero labels are presented."
        ),
        "blind_integrity":'''
assert old in s
s = s.replace(old, new, 1)

assert s != orig
p.write_text(s, encoding="utf-8")
print("patched hallusion split")
