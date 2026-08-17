#!/usr/bin/env python3
"""Rebuild the PI benchmark review package: every distinct task family/variant.

Examples are drawn from the FROZEN MANIFESTS (source of truth for image/question/
gold/metadata), so variants with no cached model outputs still appear. Arm outputs
are joined on where they exist. Selection is first-N per variant in manifest order.
"""
import json, os, shutil, sys, collections

ROOT = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
OUT  = os.path.join(ROOT, "reports/review_packages/pi_review_v2_20260811")
os.chdir(ROOT)

# ---------------------------------------------------------------- loaders
def load_shards(run, key="pair_id"):
    d = os.path.join("experiments/runs", run, "shards")
    out = {}
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".jsonl"):
            for line in open(os.path.join(d, fn)):
                line = line.strip()
                if line:
                    r = json.loads(line)
                    k = r.get(key)
                    if k:
                        out[k] = r
    return out

def load_preds(path, key="pair_id"):
    out = {}
    if not os.path.exists(path):
        return out
    for line in open(path):
        line = line.strip()
        if line:
            r = json.loads(line)
            k = r.get(key)
            if k:
                out[k] = r
    return out

def load_manifest(path):
    rows = []
    for line in open(path):
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows

_cache = {}
def arms_for(spec):
    """spec: list of (label, kind, path, key)."""
    out = []
    for label, kind, path, key in spec:
        ck = (kind, path, key)
        if ck not in _cache:
            _cache[ck] = load_shards(path, key) if kind == "shards" else load_preds(path, key)
        out.append((label, _cache[ck]))
    return out

# ---------------------------------------------------------------- arm sets
# R19 eval records carry a hashed pair_id and the manifest's id in source_pair_id;
# R20 eval records (trained arms) use the manifest id directly as pair_id. Keys below
# are the ones that join to the FROZEN MANIFEST pair_id, verified 1200/1200 each.
A_R19 = [
    ("base",          "shards", "fliptrack_v02r19_packaged_qwen25vl3b_real_an29_20260710T142716Z", "source_pair_id"),
    ("standard GRPO", "shards", "mini_a5_gate1_r19_std_step120_real_an12_20260807T235840Z",        "source_pair_id"),
    ("CP",            "shards", "mini_a5_f8_r19_cp_step120_real_an29_20260730T004031Z",            "source_pair_id"),
]
A_R20 = [
    ("base",          "shards", "fliptrack_r20_qwen25vl3b_real_an12_20260711T131807Z",             "source_pair_id"),
    ("standard GRPO", "shards", "mini_a5_gate1_r20_std_step120_real_an12_20260807T235840Z",        "pair_id"),
    ("CP",            "shards", "mini_a5_f8_r20_cp_step120_real_an29_20260730T004031Z",            "pair_id"),
]
A_CHART = [
    ("base",          "shards", "chart_v08_calibration_qwen25vl3b_real_an29_20260715T185645Z",     "pair_id"),
    ("standard GRPO", "shards", "mini_a5_gate1_chartv08_std_step120_real_an12_20260807T235840Z",   "pair_id"),
    ("CP",            "shards", "mini_a5_f8_chartv08_cp_step120_real_an29_20260730T004031Z",       "pair_id"),
]
A_CHART_NEC = [
    ("base 7B",       "shards", "chart_v08_necessity_qwen25vl7b_real_an12_20260715T194950Z",       "pair_id"),
]
A_DOC = [
    ("base 3B",       "shards", "document_vnext_qwen25vl3b_real_an29_20260711T162020Z",            "pair_id"),
    ("base 7B",       "shards", "document_vnext_qwen25vl7b_real_an29_20260711T161608Z",            "pair_id"),
]
CUE = "experiments/runs/cue_ladder_base_20260727T174414Z"
CUE2 = "experiments/runs/cue_ladder_v2base_20260727T180051Z"
def A_CUE(rung, v2=False):
    base = CUE2 if v2 else CUE
    return [("base", "preds", f"{base}/{rung}/predictions.jsonl", "pair_id")]
PV2 = "experiments/runs/track4_premise_v2_gates_an29_20260811T095522Z"
A_PROBE = [
    ("base (real)",     "preds", f"{PV2}/premise_probe/predictions.jsonl",          "pair_id"),
    ("base (gray)",     "preds", f"{PV2}/premise_probe_gray/predictions.jsonl",     "pair_id"),
    ("base (no_image)", "preds", f"{PV2}/premise_probe_no_image/predictions.jsonl", "pair_id"),
]
A_CAUSAL = [
    ("base (real)",     "preds", f"{PV2}/final/predictions.jsonl",          "pair_id"),
    ("base (gray)",     "preds", f"{PV2}/final_gray/predictions.jsonl",     "pair_id"),
    ("base (no_image)", "preds", f"{PV2}/final_no_image/predictions.jsonl", "pair_id"),
]
A_B1 = [
    ("base", "preds", "experiments/runs/b1_premise_probe_20260727T143725Z/base/predictions.jsonl", "pair_id"),
]

# ---------------------------------------------------------------- variants
# (family, family_label, variant_key, variant_label, manifest, filter, arms, n, stage, stage_src)
R19M = "data/fliptrack_v02r19_artifact_expanded_source_manifest.jsonl"
R20M = "data/fliptrack_r20_source_manifest.jsonl"
CHM  = "data/fliptrack_chart_v08_calibration_v1_manifest.jsonl"
CHN  = "data/fliptrack_chart_v08_calibration_v1_necessity_eval_manifest_v1.jsonl"
DOCM = "data/fliptrack_document_vnext_calibration_manifest.jsonl"
P2   = "data/track4_premise_v2_dev_v1"

def tf(field, val):
    return lambda r: r.get(field) == val

S_ANCHOR = ("primary visual anchor - search and binding",
            'PAPER1_RESEARCH_DOC.md: "locate the label, bind it to the point, read the coordinate... The only R19 task requiring search and binding"; role name from EXPERIMENT_TODO.md P0.4')
S_ORACLE = ("oracle-localized readout control",
            'PAPER1_RESEARCH_DOC.md: "the circle marks the queried point, supplying localization. The certified construct is oracle-localized visual readout... A control condition, never chart reasoning"')
S_SAT    = ("saturated positive control + retention canary",
            "EXPERIMENT_TODO.md P0.4 (task roles)")

VARIANTS = [
 # ---- R19
 ("r19","R19 - FlipTrack v02r19 (frozen primary benchmark)","r19_coord","coordinate_register_twenty_point_x_v02",
  R19M, tf("template_id","coordinate_register_twenty_point_x_v02"), A_R19, 4, *S_ANCHOR),
 ("r19","R19 - FlipTrack v02r19 (frozen primary benchmark)","r19_starred","starred_series_value_nine_v07",
  R19M, tf("template_id","starred_series_value_nine_v07"), A_R19, 4, *S_ORACLE),
 ("r19","R19 - FlipTrack v02r19 (frozen primary benchmark)","r19_header","header_cued_table_code_v02",
  R19M, tf("template_id","header_cued_table_code_v02"), A_R19, 4, *S_SAT),
 # ---- R20
 ("r20","R20 - private twin (one-shot confirmatory)","r20_coord","coordinate_register_twenty_point_x_v02",
  R20M, tf("template_id","coordinate_register_twenty_point_x_v02"), A_R20, 3, *S_ANCHOR),
 ("r20","R20 - private twin (one-shot confirmatory)","r20_starred","starred_series_value_nine_v07",
  R20M, tf("template_id","starred_series_value_nine_v07"), A_R20, 3, *S_ORACLE),
 ("r20","R20 - private twin (one-shot confirmatory)","r20_header","header_cued_table_code_v02",
  R20M, tf("template_id","header_cued_table_code_v02"), A_R20, 3, *S_SAT),
 # ---- cue ladder
 ("cue","Cue ladder (CL / F4b) - nine-series scene family, 6 rungs","cue_exact","cue_ladder_exact_v1 (rung: exact)",
  "data/cue_ladder_v1/exact_manifest.jsonl", None, A_CUE("exact"), 3,
  "oracle-localized readout - on-point mark, question says 'the starred series'",
  'registered_cue_ladder_v1.md rung table; v1 gate 1 PASS = reproduces R19 nine-series'),
 ("cue","Cue ladder (CL / F4b) - nine-series scene family, 6 rungs","cue_region","cue_ladder_region_v1 (rung: region)",
  "data/cue_ladder_v1/region_manifest.jsonl", None, A_CUE("region"), 3,
  "search and binding - legend star only, question says 'the starred series'",
  "registered_cue_ladder_v1.md rung table"),
 ("cue","Cue ladder (CL / F4b) - nine-series scene family, 6 rungs","cue_named_exact","cue_ladder_named_exact_v1 (rung: named_exact)",
  "data/cue_ladder_v1/named_exact_manifest.jsonl", None, A_CUE("named_exact", True), 3,
  "oracle-localized readout - on-point mark, question names the series",
  "registered_cue_ladder_v2_amendment.md v2 rung table"),
 ("cue","Cue ladder (CL / F4b) - nine-series scene family, 6 rungs","cue_named_region","cue_ladder_named_region_v1 (rung: named_region)",
  "data/cue_ladder_v1/named_region_manifest.jsonl", None, A_CUE("named_region", True), 3,
  "search and binding - legend star only, question names the series",
  "registered_cue_ladder_v2_amendment.md v2 rung table"),
 ("cue","Cue ladder (CL / F4b) - nine-series scene family, 6 rungs","cue_none","cue_ladder_none_v1 (rung: none) - UNANNOTATED",
  "data/cue_ladder_v1/none_manifest.jsonl", None, A_CUE("none"), 3,
  "search and binding with no annotation - no on-point mark, no legend star; question names the series",
  "registered_cue_ladder_v2_amendment.md v2 rung table (reused byte-identical from v1)"),
 ("cue","Cue ladder (CL / F4b) - nine-series scene family, 6 rungs","cue_decoy","cue_ladder_decoy_v1 (rung: decoy)",
  "data/cue_ladder_v1/decoy_manifest.jsonl", None, A_CUE("decoy"), 3,
  "distractor suppression - mark on a NON-target series; gold follows the question, never the cue (I12)",
  "registered_cue_ladder_v1.md rung table + EXPERIMENT_TODO.md I12; stress condition, never averaged"),
 # ---- chart v08 calibration
 ("chart","Chart v08 calibration (legend-to-series)","chart_legend","chart_v08_legend_target_flip",
  CHM, tf("template_id","chart_v08_legend_target_flip"), A_CHART, 3,
  "chart_legend_to_series_localization",
  "category field of the frozen manifest"),
 ("chart","Chart v08 calibration (legend-to-series)","chart_point","chart_v08_point_value_flip",
  CHM, tf("template_id","chart_v08_point_value_flip"), A_CHART, 3,
  "chart_legend_to_series_value_reading",
  "category field of the frozen manifest"),
 # ---- chart v08 necessity (annotation ablation)
 ("chartnec","Chart v08 necessity eval (annotation ablation; scoring_target = original_member_answer)",
  "chartnec_legend_nostar","chart_v08_legend_target_flip__no_star - UNANNOTATED",
  CHN, tf("template_id","chart_v08_legend_target_flip__no_star"), A_CHART_NEC, 3,
  "visual necessity of the star - star REMOVED, chart_legend_to_series_localization",
  "manifest fields intervention=no_star, scoring_target=original_member_answer"),
 ("chartnec","Chart v08 necessity eval (annotation ablation; scoring_target = original_member_answer)",
  "chartnec_legend_random","chart_v08_legend_target_flip__random_star",
  CHN, tf("template_id","chart_v08_legend_target_flip__random_star"), A_CHART_NEC, 3,
  "visual necessity of the star - star MISPLACED, chart_legend_to_series_localization",
  "manifest fields intervention=random_star, scoring_target=original_member_answer"),
 ("chartnec","Chart v08 necessity eval (annotation ablation; scoring_target = original_member_answer)",
  "chartnec_point_nostar","chart_v08_point_value_flip__no_star - UNANNOTATED",
  CHN, tf("template_id","chart_v08_point_value_flip__no_star"), A_CHART_NEC, 3,
  "visual necessity of the star - star REMOVED, chart_legend_to_series_value_reading",
  "manifest fields intervention=no_star, scoring_target=original_member_answer"),
 ("chartnec","Chart v08 necessity eval (annotation ablation; scoring_target = original_member_answer)",
  "chartnec_point_random","chart_v08_point_value_flip__random_star",
  CHN, tf("template_id","chart_v08_point_value_flip__random_star"), A_CHART_NEC, 3,
  "visual necessity of the star - star MISPLACED, chart_legend_to_series_value_reading",
  "manifest fields intervention=random_star, scoring_target=original_member_answer"),
 # ---- document vnext
 ("doc","Document vNext calibration (dense table)","doc_dense","dense_control_register_code_v01",
  DOCM, None, A_DOC, 3,
  "document_dense_row_column_binding",
  "category field of the frozen manifest"),
]

# premise-v2: probe / causal / invariance x intervention_type
PV2_TYPES = ["premise_transition", "premise_transition_easy",
             "chained_premise", "chained_premise_easy", "fact_read"]
PV2_PURPOSE = {  # verbatim from registered_track4_premise_v2_design_v1.md build table
 "premise_transition":      "the new construct, reference difficulty (n_points=20)",
 "premise_transition_easy": "new construct x easier lever (n_points=8)",
 "chained_premise_easy":    "easier variant carrying the section-5 band (n_points=8)",
 "chained_premise":         "frozen-construction control, anchors against P0.1's 0.275 (n_points=20)",
 "fact_read":               "reading control, no premise (n_points=20)",
}
PV2_SETS = [
 ("pv2probe","premise-v2 - premise probe (manifest_premise_probe.jsonl)",
  f"{P2}/manifest_premise_probe.jsonl", A_PROBE, "premise accuracy"),
 ("pv2causal","premise-v2 - causal pairs (manifest_causal_pairs.jsonl)",
  f"{P2}/manifest_causal_pairs.jsonl", A_CAUSAL, "causal sensitivity / reasoning given a correct premise / full chained pair accuracy"),
 ("pv2inv","premise-v2 - invariance pairs (manifest_invariance_pairs.jsonl)",
  f"{P2}/manifest_invariance_pairs.jsonl", [], "invariance specificity"),
]
for fkey, flabel, man, arms, stage in PV2_SETS:
    for t in PV2_TYPES:
        VARIANTS.append((fkey, flabel, f"{fkey}_{t}", f"intervention_type: {t}",
                         man, tf("intervention_type", t), arms, 3,
                         f"{stage} - {PV2_PURPOSE[t]}",
                         "reporting profile PAPER2_RESEARCH_DOC.md section 4; item-type purpose verbatim from registered_track4_premise_v2_design_v1.md build table"))

VARIANTS.append(("b1","B1 premise probe v1 (frozen, 20 pairs)","b1_chained","b1_coordinate_register_v1 (chained_premise)",
                 "data/b1_premise_probe_v1.jsonl", None, A_B1, 2,
                 "premise accuracy - the frozen 20-pair anchor (P0.1)",
                 "registered_b1_premise_probe_v1.md; referenced as the 0.275 anchor in registered_track4_premise_v2_design_v1.md"))

# ---------------------------------------------------------------- build
os.makedirs(os.path.join(OUT, "images"), exist_ok=True)
def copy_image(src):
    if not src:
        return None
    p = src if os.path.isabs(src) else os.path.join(ROOT, src)
    if not os.path.exists(p):
        return None
    base = os.path.basename(p)
    dst = os.path.join(OUT, "images", base)
    if not os.path.exists(dst):
        shutil.copyfile(p, dst)
    return "images/" + base

PRED_FIELDS = ["prediction_a","prediction_b","extracted_answer_a","extracted_answer_b",
               "correct_a","correct_b","pair_correct","strict_pair_correct",
               "contract_valid","collapsed","extraction_level"]

AUDIT = collections.Counter()
examples, inventory = [], []
for (fkey, flabel, vkey, vlabel, man, filt, armspec, n, stage, stage_src) in VARIANTS:
    if not os.path.exists(man):
        print(f"!! missing manifest {man}", file=sys.stderr); continue
    rows = load_manifest(man)
    rows = [r for r in rows if (filt is None or filt(r))]
    loaded = arms_for(armspec)
    joinable = 0
    picked = rows[:n]
    for r in rows:
        if loaded and any(r["pair_id"] in d for _, d in loaded):
            joinable += 1
    for r in picked:
        pid = r["pair_id"]
        ex = {
            "family": fkey, "family_label": flabel,
            "variant": vkey, "variant_label": vlabel,
            "pair_id": pid,
            "template_id": r.get("template_id"),
            "category": r.get("category"),
            "rung": r.get("rung"),
            "intervention_type": r.get("intervention_type") or r.get("intervention"),
            "question": r.get("question"),
            "premise_question": r.get("premise_question"),
            "gold_a": r.get("answer_a"), "gold_b": r.get("answer_b"),
            "premise_gold_a": r.get("premise_answer_a") or r.get("premise_answer"),
            "premise_gold_b": r.get("premise_answer_b"),
            "image_a": copy_image(r.get("image_a_path")),
            "image_b": copy_image(r.get("image_b_path")),
            "mask_a": copy_image(r.get("changed_region_mask_a")) if fkey.startswith("pv2") else None,
            "mask_b": copy_image(r.get("changed_region_mask_b")) if fkey.startswith("pv2") else None,
            "manifest": man,
            "record": r,
            "arms": {},
        }
        for label, d in loaded:
            a = d.get(pid)
            if a:
                ex["arms"][label] = {k: a.get(k) for k in PRED_FIELDS}
                # the joined row must describe the same item as the manifest row
                for fld in ("image_a_sha256", "image_b_sha256", "question"):
                    if a.get(fld) is not None and r.get(fld) is not None and a[fld] != r[fld]:
                        AUDIT[f"{vkey}:{label}:{fld}"] += 1
                for gf, mf in (("answer_a", "answer_a"), ("answer_b", "answer_b")):
                    if a.get(gf) is not None and r.get(mf) is not None and str(a[gf]) != str(r[mf]):
                        AUDIT[f"{vkey}:{label}:{gf}"] += 1
        examples.append(ex)
    inventory.append({
        "family": fkey, "family_label": flabel, "variant": vkey, "variant_label": vlabel,
        "template_id": picked[0].get("template_id") if picked else None,
        "category": picked[0].get("category") if picked else None,
        "n_in_benchmark": len(rows),
        "n_in_package": len(picked),
        "manifest": man,
        "arms_available": [l for l, _ in loaded] if loaded else [],
        "n_joinable": joinable,
        "capability_stage": stage,
        "stage_source": stage_src,
        "note": ("not applicable by design - manifest_premise_probe.jsonl covers every "
                 "intervention_type EXCEPT fact_read, which carries no premise fields "
                 "(registered_track4_premise_v2_design_v1.md)") if len(rows) == 0 else None,
    })
    print(f"[{vkey:26s}] n={len(rows):5d} picked={len(picked)} arms={[l for l,_ in loaded]} joinable={joinable}", file=sys.stderr)

meta = {
    "selection_rule": "first N per variant in frozen manifest order; outcome-blind, no filtering on correctness",
    "n_examples": len(examples),
    "n_variants": len(inventory),
    "families": sorted({i["family"] for i in inventory}),
    "arm_models": {
        "base (R19/R20/chart v08/cue ladder/premise-v2/doc 3B)": "artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct",
        "base 7B (chart v08 necessity, doc vNext 7B column)":    "artifacts/models/Qwen/Qwen2.5-VL-7B-Instruct",
        "standard GRPO": "checkpoints/mini_a5/mini_a5_std_seed1/global_step_120 (registered Gate-1 arm 1)",
        "CP":            "checkpoints/mini_a5/mini_a5_cp_seed1/global_step_120 (registered Gate-1 arm 4, CP-GRPO)",
    },
}
meta["manifest_to_run_join_audit"] = dict(AUDIT) or "no mismatches: every joined arm row matches its manifest row on image_a_sha256, image_b_sha256, question, answer_a, answer_b"
print("JOIN AUDIT:", dict(AUDIT) or "clean", file=sys.stderr)
json.dump({"meta": meta, "inventory": inventory, "examples": examples},
          open(os.path.join(OUT, "examples.json"), "w"), indent=1)
print("TOTAL examples", len(examples), "variants", len(inventory), file=sys.stderr)
