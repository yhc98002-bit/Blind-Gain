import json, os
R = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
J = json.load(open(os.path.join(R, "reports/chance_corrected_retention_v1.json")))

def f(x, nd=4):
    if x is None: return "n/a"
    if isinstance(x, str): return x
    return ("%." + str(nd) + "f") % x

def ci(d, key, nd=4):
    lo, hi = d.get(key + "_ci95_low"), d.get(key + "_ci95_high")
    if lo is None or hi is None: return "n/a"
    return "[%s, %s]" % (f(lo, nd), f(hi, nd))

L = []
w = L.append
w("# Null-corrected blind retention — external benchmarks (v1)")
w("")
w("Generated: `%s`  ·  machine-readable twin: `reports/chance_corrected_retention_v1.json`  ·  generator: `scripts/chance_corrected_retention_v1.py`" % J["generated_utc"])
w("")
w("## Definitions")
w("")
w("- `corrected retention = (mean(blind) - mean(null)) / (mean(with_image) - mean(null))`")
w("- `naive retention = mean(blind) / mean(with_image)`")
w("- Null rule (closed form, no empirical null): multiple-choice item -> `1/k` using that item's own presented option count `k`; free-form item -> `0`; multiple-choice item whose gold label is absent from the presented option labels -> `0`.")
w("- Subset null = mean of the per-item nulls in that subset; recomputed inside every bootstrap replicate.")
w("- CI: item-level paired bootstrap, %d replicates, seed %d, percentile 2.5/97.5. The ratio of differences is recomputed on each replicate." % (J["method"]["bootstrap"]["reps"], J["method"]["bootstrap"]["seed"]))
w("- Two scoring contracts are carried throughout: lenient = `Acc_final`, contract-strict = `Acc_strict`.")
w("- `den<=0` column: `true` when the corrected-retention denominator `mean(with_image) - null` is non-positive in the point estimate or changes sign across bootstrap replicates. Ratios in those rows are not on a 0-1 scale.")
w("")
w("## 1. Headline rows — naive vs corrected (lenient `Acc_final`)")
w("")
w("| Model | Benchmark | Subset | n | with-image | blind | null | naive ret. | corrected ret. | corrected 95% CI | den<=0 |")
w("| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |")
HEAD = [
 ("Qwen2.5-VL-3B", "MMStar", "all items (MC pooled, item-level null)"),
 ("Qwen2.5-VL-7B", "MMStar", "all items (MC pooled, item-level null)"),
 ("Qwen2.5-VL-3B", "MathVista-testmini", "MC pooled (item-level null)"),
 ("Qwen2.5-VL-3B", "MathVista-testmini", "free-form"),
 ("Qwen2.5-VL-7B", "MathVista-testmini", "MC pooled (item-level null)"),
 ("Qwen2.5-VL-7B", "MathVista-testmini", "free-form"),
 ("Gemma-3", "ViRL39K audit sample (4096) [blind condition=none]", "MC pooled, k determinable (item-level null)"),
 ("Gemma-3", "ViRL39K audit sample (4096) [blind condition=none]", "free-form pooled (numeric+text_or_expression)"),
 ("InternVL3-9B", "ViRL39K audit sample (4096) [blind condition=none]", "MC pooled, k determinable (item-level null)"),
 ("InternVL3-9B", "ViRL39K audit sample (4096) [blind condition=none]", "free-form pooled (numeric+text_or_expression)"),
]
byk = {(r["model"], r["benchmark"], r["subset"]): r for r in J["rows"]}
for key in HEAD:
    r = byk[key]; d = r["lenient_acc_final"]
    w("| %s | %s | %s | %d | %s | %s | %s | %s | %s | %s | %s |" % (
        r["model"], r["benchmark"].replace("ViRL39K audit sample (4096) [blind condition=none]", "ViRL39K sample, blind=none"),
        r["subset"], r["n"], f(d["with_image_acc"]), f(d["blind_acc"]), f(r["null"]),
        f(d["naive_retention"]), f(d["corrected_retention"]), ci(d, "corrected_retention"),
        "yes" if d["denominator_crosses_zero"] else "no"))
w("")
w("## 2. All subsets — lenient contract (`Acc_final`)")
w("")
w("| Model | Benchmark | Subset | format | k | n | with-image | with-image 95% CI | blind | blind 95% CI | null | naive ret. | naive 95% CI | corrected ret. | corrected 95% CI | den<=0 | boot den<=0 frac |")
w("| --- | --- | --- | --- | :---: | ---: | ---: | :---: | ---: | :---: | ---: | ---: | :---: | ---: | :---: | :---: | ---: |")
for r in J["rows"]:
    d = r["lenient_acc_final"]
    w("| %s | %s | %s | %s | %s | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
        r["model"], r["benchmark"], r["subset"], r["answer_format"], r["k"] if r["k"] is not None else "n/a",
        r["n"], f(d["with_image_acc"]), ci(d, "with_image_acc"), f(d["blind_acc"]), ci(d, "blind_acc"),
        f(r["null"]), f(d["naive_retention"]), ci(d, "naive_retention"),
        f(d["corrected_retention"]), ci(d, "corrected_retention"),
        "yes" if d["denominator_crosses_zero"] else "no", f(d["boot_denominator_nonpositive_frac"], 3)))
w("")
w("## 3. All subsets — contract-strict (`Acc_strict`)")
w("")
w("Same items, same nulls; `Acc_strict` additionally requires the `<answer>` wrapper.")
w("")
w("| Model | Benchmark | Subset | n | null | with-image | blind | naive ret. | corrected ret. | corrected 95% CI | den<=0 |")
w("| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |")
for r in J["rows"]:
    d = r["strict_acc_strict"]
    if d is None:
        w("| %s | %s | %s | %d | %s | n/a | n/a | n/a | n/a | n/a | n/a |" % (r["model"], r["benchmark"], r["subset"], r["n"], f(r["null"])))
        continue
    w("| %s | %s | %s | %d | %s | %s | %s | %s | %s | %s | %s |" % (
        r["model"], r["benchmark"], r["subset"], r["n"], f(r["null"]),
        f(d["with_image_acc"]), f(d["blind_acc"]), f(d["naive_retention"]),
        f(d["corrected_retention"]), ci(d, "corrected_retention"),
        "yes" if d["denominator_crosses_zero"] else "no"))
w("")
w("## 4. Whole-benchmark naive retention (reference; reproduces the currently published figures)")
w("")
w("No corrected value is given at this level for mixed benchmarks.")
w("")
w("| Model | Benchmark | n | with-image `Acc_final` | blind `Acc_final` | naive ret. (lenient) | naive 95% CI | with-image `Acc_strict` | blind `Acc_strict` | naive ret. (strict) | naive strict 95% CI |")
w("| --- | --- | ---: | ---: | ---: | ---: | :---: | ---: | ---: | ---: | :---: |")
for r in J["reference_naive_whole_benchmark"]:
    a, b = r["lenient_acc_final"], r["strict_acc_strict"]
    w("| %s | %s | %d | %s | %s | %s | %s | %s | %s | %s | %s |" % (
        r["model"], r["benchmark"], r["n"], f(a["with_image_acc"]), f(a["blind_acc"]),
        f(a["naive_retention"]), ci(a, "naive_retention"),
        f(b["with_image_acc"]), f(b["blind_acc"]), f(b["naive_retention"]), ci(b, "naive_retention")))
w("")
w("## 5. Not computed")
w("")
w("| Benchmark | Model | Subset | n | reason |")
w("| --- | --- | --- | ---: | --- |")
for u in J["not_computed"]:
    w("| %s | %s | %s | %s | %s |" % (u["benchmark"], u["model"], u["subset"],
        u.get("n", "n/a"), u["reason"].replace("\n", " ")))
w("")
w("### With-image `k` availability for the five benchmarks that have no blind arm")
w("")
w("| Benchmark | with-image postprocessed run | n | k distribution (option-label count -> rows) |")
w("| --- | --- | ---: | --- |")
for u in J["not_computed"]:
    if "with_image_run_k_availability" not in u: continue
    for d, info in u["with_image_run_k_availability"].items():
        if "error" in info:
            w("| %s | `%s` | n/a | %s |" % (u["benchmark"], d, info["error"]))
        else:
            w("| %s | `%s` | %d | %s |" % (u["benchmark"], d, info["n"],
              ", ".join("k=%s:%d" % (a, b) for a, b in info["k_distribution"].items())))
w("")
w("## 6. Answer-format census")
w("")
w("MathVista-testmini (`question_type` x option-label count):")
w("")
w("| Model | mc=False/True | k | rows |")
w("| --- | :---: | ---: | ---: |")
for m, v in J["mathvista_format_counts"].items():
    for key, c in v.items():
        mc, k = key.split("|")
        w("| %s | %s | %s | %d |" % (m, mc.split("=")[1], k.split("=")[1], c))
w("")
w("ViRL39K audit sample, 4096 rows (`source_metadata.answer_type` x parsed k; `k=None` = option list absent from the stored prompt):")
w("")
w("| answer_type | k | rows |")
w("| --- | :---: | ---: |")
for key, c in J["virl_sample_format_counts"].items():
    at, k = key.rsplit("|k=", 1)
    w("| %s | %s | %d |" % (at, k, c))
w("")
w("## 7. Checks")
w("")
w("| Check | Result |")
w("| --- | --- |")
w("| MMStar: with-image and blind item id sets identical | 1500 / 1500 for 3B and 7B |")
w("| MMStar: `option_labels` length identical between with-image and blind rows | 1500 / 1500 for 3B and 7B |")
w("| MMStar: `k` cross-checked against `data/vlmevalkit/MMStar_VLMEVAL.tsv` option columns | option-presence patterns ABCD:1321, AB:85, ABC:90, ABD:1, ACD:1, BCD:2 |")
w("| MathVista: with-image and blind item id sets identical | 999 / 999 for 3B and 7B |")
w("| MathVista: `question_type == multi_choice` agrees with non-empty `option_labels` | 999 / 999 rows |")
w("| ViRL sample: all six run files carry the same 4096 `qid` set | true |")
w("| ViRL sample: parsed ground-truth label lies inside the parsed option list | 1215 / 1215 parsed MC items |")
w("| ViRL sample: MC items whose option list is absent from the stored prompt | 92 of 1307 |")
w("")
w("## 8. Provenance — input artifacts")
w("")
w("| File | bytes | sha256 |")
w("| --- | ---: | --- |")
for p, m in J["inputs"].items():
    w("| `%s` | %d | `%s` |" % (p, m["bytes"], m["sha256"]))
w("")
w("Cross-family run keys are the `path` fields of `reports/generalization_audits_v2.json` under `blind_sample.{gemma3,internvl3}|{real,none,caption}`.")
w("")
out = os.path.join(R, "reports/chance_corrected_retention_v1.md")
open(out, "w").write("\n".join(L) + "\n")
print("wrote", out, len(L), "lines")
