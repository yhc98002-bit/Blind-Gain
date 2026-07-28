import json, os, re, hashlib, collections, datetime
import numpy as np

R = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
B_BOOT = 10000
SEED = 20260728
rng = np.random.default_rng(SEED)

def load(p):
    return [json.loads(l) for l in open(p) if l.strip()]

def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()

INPUTS = {}
def reg(path):
    ap = os.path.join(R, path)
    INPUTS[path] = {"sha256": sha256(ap), "bytes": os.path.getsize(ap)}
    return ap

# ---------------- statistics ----------------
def boot_block(w, b, nul, tag):
    """w,b: 0/1 arrays (with-image, blind). nul: per-item null. paired items."""
    w = np.asarray(w, float); b = np.asarray(b, float); nul = np.asarray(nul, float)
    n = len(w)
    out = {"n": int(n)}
    mw, mb, mn = w.mean(), b.mean(), nul.mean()
    out["with_image_acc"] = float(mw)
    out["blind_acc"] = float(mb)
    out["null"] = float(mn)
    out["naive_retention"] = float(mb / mw) if mw != 0 else None
    den = mw - mn
    out["denominator"] = float(den)
    out["corrected_retention"] = float((mb - mn) / den) if den != 0 else None
    idx = rng.integers(0, n, size=(B_BOOT, n))
    bw = w[idx].mean(axis=1); bb = b[idx].mean(axis=1); bn = nul[idx].mean(axis=1)
    with np.errstate(divide='ignore', invalid='ignore'):
        naive = np.where(bw != 0, bb / bw, np.nan)
        corr = np.where((bw - bn) != 0, (bb - bn) / (bw - bn), np.nan)
    def ci(a, key):
        a2 = a[np.isfinite(a)]
        if len(a2) < 100:
            return {key + "_ci95_low": None, key + "_ci95_high": None, key + "_ci_valid_reps": int(len(a2))}
        lo, hi = np.percentile(a2, [2.5, 97.5])
        return {key + "_ci95_low": float(lo), key + "_ci95_high": float(hi), key + "_ci_valid_reps": int(len(a2))}
    out.update(ci(naive, "naive_retention"))
    out.update(ci(corr, "corrected_retention"))
    for key, arr in (("with_image_acc", bw), ("blind_acc", bb)):
        lo, hi = np.percentile(arr, [2.5, 97.5])
        out[key + "_ci95_low"] = float(lo); out[key + "_ci95_high"] = float(hi)
    dsign = bw - bn
    out["boot_denominator_nonpositive_frac"] = float(np.mean(dsign <= 0))
    out["denominator_crosses_zero"] = bool(np.any(dsign > 0) and np.any(dsign <= 0)) or den <= 0
    out["bootstrap"] = {"reps": B_BOOT, "seed": SEED, "unit": "item", "paired": True, "ci": "percentile-2.5/97.5"}
    return out

def row(family, model, benchmark, subset, fmt, k, items, notes=None):
    """items: list of dicts with w_final,b_final,w_strict,b_strict,null"""
    r = {"family": family, "model": model, "benchmark": benchmark, "subset": subset,
         "answer_format": fmt, "k": k}
    lenient = boot_block([i["w_final"] for i in items], [i["b_final"] for i in items],
                         [i["null"] for i in items], subset)
    r["n"] = lenient.pop("n")
    r["null"] = lenient.pop("null")
    r["lenient_acc_final"] = lenient
    if all(i["w_strict"] is not None for i in items):
        strict = boot_block([i["w_strict"] for i in items], [i["b_strict"] for i in items],
                            [i["null"] for i in items], subset + "|strict")
        strict.pop("n"); strict.pop("null")
        r["strict_acc_strict"] = strict
    else:
        r["strict_acc_strict"] = None
    if notes: r["notes"] = notes
    return r

ROWS = []
UNCOMPUTABLE = []
REFERENCE = []

def ref_row(family, model, benchmark, items, note):
    """Whole-benchmark NAIVE retention only (no null correction) - reproduces the currently published figure."""
    zeros = [0.0] * len(items)
    lo = boot_block([i["w_final"] for i in items], [i["b_final"] for i in items], zeros, "ref")
    st = boot_block([i["w_strict"] for i in items], [i["b_strict"] for i in items], zeros, "ref|strict")
    keep = ("with_image_acc", "with_image_acc_ci95_low", "with_image_acc_ci95_high",
            "blind_acc", "blind_acc_ci95_low", "blind_acc_ci95_high",
            "naive_retention", "naive_retention_ci95_low", "naive_retention_ci95_high")
    r = {"family": family, "model": model, "benchmark": benchmark, "n": len(items),
         "corrected_retention": None,
         "lenient_acc_final": {k: lo[k] for k in keep},
         "strict_acc_strict": {k: st[k] for k in keep},
         "note": note}
    return r

# ================= MMStar =================
MMSTAR = {
 "Qwen2.5-VL-3B": ("experiments/runs/vlmevalkit_mmstar3b_adapted_an29_20260710T004416Z/postprocessed_v2/rows.jsonl",
                   "experiments/runs/layer1_blind_mmstar3b_an29_20260710T023019Z/predictions.jsonl"),
 "Qwen2.5-VL-7B": ("experiments/runs/vlmevalkit_mmstar7b_adapted_an29_20260710T005355Z/postprocessed_v2/rows.jsonl",
                   "experiments/runs/layer1_blind_mmstar7b_an29_20260710T023019Z/predictions.jsonl"),
}
for model, (wp, bp) in MMSTAR.items():
    W = {r["index"]: r for r in load(reg(wp))}
    Bl = {r["index"]: r for r in load(reg(bp))}
    assert set(W) == set(Bl)
    items = []
    for i in W:
        labs = Bl[i].get("option_labels") or []
        k = len(labs)
        gold_in = Bl[i]["gold"] in labs
        items.append({"index": i, "k": k, "gold_in": gold_in,
                      "null": (1.0 / k) if (k > 0 and gold_in) else 0.0,
                      "w_final": bool(W[i]["acc_final"]), "b_final": bool(Bl[i]["acc_final"]),
                      "w_strict": bool(W[i]["acc_strict"]), "b_strict": bool(Bl[i]["acc_strict"])})
    for k in sorted({it["k"] for it in items if it["gold_in"]}):
        sub = [it for it in items if it["k"] == k and it["gold_in"]]
        ROWS.append(row("qwen-layer1", model, "MMStar", "MC k=%d" % k, "multiple_choice", k, sub))
    deg = [it for it in items if not it["gold_in"]]
    if deg:
        ROWS.append(row("qwen-layer1", model, "MMStar", "MC gold-label absent from presented options",
                        "multiple_choice", None, deg,
                        notes="Gold label is not among the option labels presented in the source TSV "
                              "(source columns present = B,C,D; answer = A). Chance of a label match = 0, so null = 0. "
                              "Both conditions score 0 on every item, so the retention ratio is 0/0."))
    ROWS.append(row("qwen-layer1", model, "MMStar", "all items (MC pooled, item-level null)",
                    "multiple_choice", "mixed(2,3,4)", items,
                    notes="Pooled over per-item nulls; not a single global null."))
    REFERENCE.append(ref_row("qwen-layer1", model, "MMStar", items,
        "Whole-benchmark naive retention (null ignored). Corrected counterpart: MMStar / all items (MC pooled, item-level null)."))

# ================= MathVista =================
MV = {
 "Qwen2.5-VL-3B": ("experiments/runs/vlmevalkit_postprocess_mathvista3b_20260710T022024Z/rows.jsonl",
                   "experiments/runs/layer1_blind_mathvista3b_an29_20260710T023019Z/predictions.jsonl"),
 "Qwen2.5-VL-7B": ("experiments/runs/vlmevalkit_postprocess_mathvista7b_20260710T022024Z/rows.jsonl",
                   "experiments/runs/layer1_blind_mathvista7b_an29_20260710T023019Z/predictions.jsonl"),
}
mv_split = {}
for model, (wp, bp) in MV.items():
    W = {r["index"]: r for r in load(reg(wp))}
    Bl = {r["index"]: r for r in load(reg(bp))}
    assert set(W) == set(Bl)
    items = []
    for i in W:
        labs = Bl[i].get("option_labels") or []
        k = len(labs)
        qt = W[i].get("question_type")
        mc = (qt == "multi_choice")
        assert (k > 0) == mc, (i, k, qt)
        gold_in = (Bl[i]["gold"] in labs) if mc else True
        items.append({"index": i, "k": k if mc else 0, "mc": mc, "gold_in": gold_in,
                      "answer_type": W[i].get("answer_type"),
                      "null": (1.0 / k) if (mc and gold_in) else 0.0,
                      "w_final": bool(W[i]["acc_final"]), "b_final": bool(Bl[i]["acc_final"]),
                      "w_strict": bool(W[i]["acc_strict"]), "b_strict": bool(Bl[i]["acc_strict"])})
    mv_split[model] = collections.Counter((it["mc"], it["k"]) for it in items)
    for k in sorted({it["k"] for it in items if it["mc"]}):
        sub = [it for it in items if it["mc"] and it["k"] == k]
        ROWS.append(row("qwen-layer1", model, "MathVista-testmini", "MC k=%d" % k, "multiple_choice", k, sub))
    mcall = [it for it in items if it["mc"]]
    ROWS.append(row("qwen-layer1", model, "MathVista-testmini", "MC pooled (item-level null)",
                    "multiple_choice", "mixed(2-8)", mcall))
    ff = [it for it in items if not it["mc"]]
    ROWS.append(row("qwen-layer1", model, "MathVista-testmini", "free-form", "free_form_numeric", None, ff,
                    notes="question_type=free_form; answer_type in {integer,float,list}; null = 0, no correction."))
    REFERENCE.append(ref_row("qwen-layer1", model, "MathVista-testmini", items,
        "Whole-benchmark naive retention (null ignored) over the mixed benchmark. No corrected counterpart is "
        "reported at this level; see the MC and free-form subset rows."))
    UNCOMPUTABLE.append({"benchmark": "MathVista-testmini", "model": model,
        "subset": "whole benchmark (single global null)",
        "reason": "Mixed benchmark: %d MC items and %d free-form items. Per the null rule a single global "
                  "null is not permitted, so no whole-benchmark corrected retention is reported." % (len(mcall), len(ff))})

# ================= cross-family ViRL39K 4096 sample =================
XF = {
 ("Gemma-3", "none"): "experiments/runs/m11_blind_gemma3_virl4096_none_gemma3_none_s0of1_an29_20260716T200132Z/per_item.jsonl",
 ("Gemma-3", "real"): "experiments/runs/m11_blind_gemma3_virl4096_real_gemma3_real_s0of1_an29_20260716T191637Z/per_item.jsonl",
 ("Gemma-3", "caption"): "experiments/runs/m11_blind_gemma3_virl4096_caption_gemma3_caption_s0of1_an29_20260716T231512Z/per_item.jsonl",
 ("InternVL3-9B", "none"): "experiments/runs/m11_virl4096_retry1_internvl3_none_s0of1_an12_20260716T170739Z/per_item.jsonl",
 ("InternVL3-9B", "real"): "experiments/runs/m11_virl4096_patchbudgetv2_internvl3_real_s0of1_an29_20260717T072527Z/per_item.jsonl",
 ("InternVL3-9B", "caption"): "experiments/runs/m11_virl4096_retry1_internvl3_caption_s0of1_an12_20260716T170744Z/per_item.jsonl",
}
def norm(p): return p.replace('\\n', '\n').replace('/n', '\n')
PATS = [re.compile(r'(?:(?<=^)|(?<=[\s\n(]))\(([A-Z])\)\s*'),
        re.compile(r'^[ \t]*([A-Z])[\.．\)）、:：]\s*', re.M),
        re.compile(r'(?<![A-Za-z0-9])([A-Z])[\.．][ \t]+', re.M)]
def parse_opts(prob):
    prob = norm(prob); best = []
    for p in PATS:
        labs = []
        for m in p.finditer(prob):
            L = m.group(1)
            if L not in labs: labs.append(L)
        exp = [chr(65 + i) for i in range(len(labs))]
        if labs == exp and len(labs) >= 2 and len(labs) > len(best): best = labs
    return best

XD = {}
for key, p in XF.items():
    XD[key] = {r["qid"]: r for r in load(reg(p))}
qids = sorted(XD[("Gemma-3", "none")])
meta = XD[("Gemma-3", "none")]
kmap, atmap = {}, {}
for q in qids:
    at = meta[q]["source_metadata"]["answer_type"]
    atmap[q] = at
    if at == "multiple_choice":
        o = parse_opts(meta[q]["problem"])
        kmap[q] = len(o) if o else None
    else:
        kmap[q] = 0
xf_counts = collections.Counter((atmap[q], kmap[q]) for q in qids)

for backend in ("Gemma-3", "InternVL3-9B"):
    real = XD[(backend, "real")]
    for cond in ("none", "caption"):
        blind = XD[(backend, cond)]
        assert set(real) == set(blind) == set(qids)
        items = []
        for q in qids:
            at = atmap[q]; k = kmap[q]
            if at == "multiple_choice":
                nul = (1.0 / k) if k else None
            else:
                nul = 0.0
            items.append({"qid": q, "at": at, "k": k, "null": nul,
                          "w_final": bool(real[q]["acc_final"]), "b_final": bool(blind[q]["acc_final"]),
                          "w_strict": bool(real[q]["acc_strict"]), "b_strict": bool(blind[q]["acc_strict"])})
        bench = "ViRL39K audit sample (4096) [blind condition=%s]" % cond
        for k in sorted({it["k"] for it in items if it["at"] == "multiple_choice" and it["k"]}):
            sub = [it for it in items if it["at"] == "multiple_choice" and it["k"] == k]
            ROWS.append(row("cross-family", backend, bench, "MC k=%d" % k, "multiple_choice", k, sub))
        mcdet = [it for it in items if it["at"] == "multiple_choice" and it["k"]]
        ROWS.append(row("cross-family", backend, bench, "MC pooled, k determinable (item-level null)",
                        "multiple_choice", "mixed(2-5)", mcdet))
        for at in ("numeric", "text_or_expression"):
            sub = [it for it in items if it["at"] == at]
            ROWS.append(row("cross-family", backend, bench, "free-form %s" % at,
                            "free_form_%s" % at, None, sub, notes="null = 0, no correction."))
        ff = [it for it in items if it["at"] in ("numeric", "text_or_expression")]
        ROWS.append(row("cross-family", backend, bench, "free-form pooled (numeric+text_or_expression)",
                        "free_form", None, ff, notes="null = 0, no correction."))
        REFERENCE.append(ref_row("cross-family", backend, bench, items,
            "Whole-sample naive retention (null ignored) over all 4096 rows; this reproduces the figure in "
            "reports/generalization_audits_v2.json. No corrected counterpart at this level (mixed sample)."))
        # uncorrectable MC
        und = [it for it in items if it["at"] == "multiple_choice" and not it["k"]]
        nw = sum(it["w_final"] for it in und); nb = sum(it["b_final"] for it in und)
        UNCOMPUTABLE.append({"benchmark": bench, "model": backend,
            "subset": "MC, k indeterminable", "n": len(und),
            "with_image_acc_final": nw / len(und), "blind_acc_final": nb / len(und),
            "reason": "answer_type=multiple_choice but the option list is not present in the stored prompt text "
                      "(options appear only in the image); k cannot be determined per item, so no null is assigned."})
        UNCOMPUTABLE.append({"benchmark": bench, "model": backend,
            "subset": "whole 4096-row sample (single global null)",
            "reason": "Mixed sample (MC + free-form); a single global null is not permitted by the null rule."})

# ================= benchmarks with no blind arm =================
NO_BLIND = {
 "BLINK": ["experiments/runs/vlmevalkit_postprocess_l10_blink3b_canonicalv2_final_20260711T132325Z",
           "experiments/runs/vlmevalkit_postprocess_l10_blink7b_canonicalv2_final_20260711T132325Z"],
 "HallusionBench": ["experiments/runs/vlmevalkit_postprocess_l10_hallusion3b_canonicalv2_final_20260711T132325Z",
                    "experiments/runs/vlmevalkit_postprocess_l10_hallusion7b_canonicalv2_final_20260711T132325Z"],
 "MMVP": ["experiments/runs/vlmevalkit_postprocess_l10_mmvp3b_canonicalv2_final_20260711T132326Z",
          "experiments/runs/vlmevalkit_postprocess_l10_mmvp7b_canonicalv2_final_20260711T132326Z"],
 "MathVerse": ["experiments/runs/vlmevalkit_postprocess_l10_mathverse3b_canonicalv2_v2_20260711T143923Z",
               "experiments/runs/vlmevalkit_postprocess_l10_mathverse7b_canonicalv2_v2_20260711T143943Z"],
 "MMMU dev+validation": ["experiments/runs/vlmevalkit_postprocess_l10_mmmu3b_v2_canonicalv2_20260711T145554Z",
                         "experiments/runs/vlmevalkit_postprocess_l10_mmmu7b_v2_canonicalv2_20260711T145711Z"],
}
for bench, dirs in NO_BLIND.items():
    kinfo = {}
    for d in dirs:
        for cand in ("rows.jsonl", "postprocessed_v2/rows.jsonl"):
            fp = os.path.join(R, d, cand)
            if os.path.exists(fp):
                rows = load(fp)
                kd = collections.Counter(len(r.get("option_labels") or []) for r in rows)
                kinfo[d] = {"n": len(rows), "k_distribution": {str(a): b for a, b in sorted(kd.items())}}
                break
        else:
            kinfo[d] = {"error": "rows.jsonl not found"}
    UNCOMPUTABLE.append({"benchmark": bench, "model": "Qwen2.5-VL-3B and 7B",
        "subset": "all", "reason": "No image-removed (blind) run exists under experiments/runs; blind accuracy is "
                                   "not available, so retention (naive or corrected) cannot be computed.",
        "with_image_run_k_availability": kinfo})

OUT = {
 "schema_version": "blind-gains.chance-corrected-retention.v1",
 "generated_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
 "method": {
   "corrected_retention": "(mean(blind) - mean(null)) / (mean(with_image) - mean(null))",
   "naive_retention": "mean(blind) / mean(with_image)",
   "null_rule": {"multiple_choice": "1/k using that item's own k (count of option labels presented)",
                 "multiple_choice_gold_label_absent": "0 (gold label is not among presented labels)",
                 "free_form": "0 (no correction)"},
   "null_aggregation": "per-item null averaged over the subset; recomputed inside every bootstrap replicate",
   "bootstrap": {"reps": B_BOOT, "seed": SEED, "unit": "item", "paired": "same item ids in both conditions",
                 "ci": "percentile 2.5 / 97.5", "note": "ratio of differences recomputed on each replicate"},
   "scoring_contracts": {"lenient": "acc_final", "strict": "acc_strict"},
   "strict_caveat": "The same answer-format null (1/k) is applied to acc_strict. acc_strict additionally requires the "
                    "<answer> wrapper, so where with-image acc_strict is below the null the denominator is negative; "
                    "such rows carry denominator_crosses_zero=true and boot_denominator_nonpositive_frac."
 },
 "k_source": {
   "MMStar": "option_labels field of the per-item artifacts (identical in with-image and blind runs); "
             "cross-checked against data/vlmevalkit/MMStar_VLMEVAL.tsv option columns A-D",
   "MathVista-testmini": "option_labels field; question_type field (multi_choice / free_form) agrees with option_labels non-empty on 999/999 rows",
   "ViRL39K audit sample": "source_metadata.answer_type for format; k parsed from the stored prompt text (per_item.problem). "
                           "Validation: the ground-truth label lies inside the parsed option list on 1215/1215 parsed MC items."
 },
 "virl_sample_format_counts": {"%s|k=%s" % (a, b): c for (a, b), c in sorted(xf_counts.items(), key=lambda x: str(x[0]))},
 "mathvista_format_counts": {m: {"mc=%s|k=%d" % (a, b): c for (a, b), c in sorted(v.items())} for m, v in mv_split.items()},
 "rows": ROWS,
 "reference_naive_whole_benchmark": REFERENCE,
 "not_computed": UNCOMPUTABLE,
 "inputs": INPUTS,
}
def _j(o):
    if isinstance(o, (np.bool_,)): return bool(o)
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return float(o)
    raise TypeError(repr(type(o)))

op = os.path.join(R, "reports/chance_corrected_retention_v1.json")
with open(op, "w") as f:
    json.dump(OUT, f, indent=2, sort_keys=False, default=_j)
print("wrote", op, "rows:", len(ROWS), "not_computed:", len(UNCOMPUTABLE))
