#!/usr/bin/env python3
"""P2.3 leak verification (numbers only): per cell/role over L3 causal pairs,
tabulate (1) the sign of the single numeric scene delta between the semantic
base and edited sides, (2) PNG byte-size deltas edited-minus-base.
Read-only; honors the recorded semantic side swap."""
import json
import os


def flatten(o, p=()):
    if isinstance(o, dict):
        for k, v in sorted(o.items()):
            yield from flatten(v, p + (str(k),))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from flatten(v, p + (str(i),))
    else:
        yield p, o


CELLS = {"hier_coord_v1": ("n8", "n12", "n20"),
         "hier_chart_v1": ("s5_low", "s5_high", "s9_low", "s9_high")}

out = {}
for fam, cs in CELLS.items():
    for cell in cs:
        stats = {}
        path = f"data/hier_v1_dev/manifest_{fam}_{cell}_l3.jsonl"
        for line in open(path):
            row = json.loads(line)
            if row["role"] == "invariance":
                continue
            sw = bool(row["provenance"]["semantic_side_assignment_swapped"])
            base_sc, edit_sc = ((row["scene_b"], row["scene_a"]) if sw
                                else (row["scene_a"], row["scene_b"]))
            base_im, edit_im = ((row["image_b_path"], row["image_a_path"]) if sw
                                else (row["image_a_path"], row["image_b_path"]))
            fa = dict(flatten(base_sc))
            fb = dict(flatten(edit_sc))
            deltas = [(k, fb[k] - fa[k]) for k in fa
                      if k in fb
                      and isinstance(fa[k], (int, float)) and isinstance(fb[k], (int, float))
                      and not isinstance(fa[k], bool) and not isinstance(fb[k], bool)
                      and fa[k] != fb[k]]
            szd = os.path.getsize(edit_im) - os.path.getsize(base_im)
            s = stats.setdefault(row["role"], dict(
                n=0, neg=0, pos=0, multi=0, sz_pos=0, sz_neg=0, sz_zero=0,
                sz_sum=0, delta_paths=set()))
            s["n"] += 1
            if len(deltas) != 1:
                s["multi"] += 1
            for k, d in deltas:
                s["delta_paths"].add("/".join(k[:-1]) or "/".join(k))
                if len(deltas) == 1:
                    s["neg" if d < 0 else "pos"] += 1
            s["sz_pos"] += szd > 0
            s["sz_neg"] += szd < 0
            s["sz_zero"] += szd == 0
            s["sz_sum"] += szd
        for role, s in sorted(stats.items()):
            print(f"{fam} {cell} {role}: n={s['n']} "
                  f"value_delta neg={s['neg']} pos={s['pos']} multi_field={s['multi']} | "
                  f"png edited>base={s['sz_pos']} edited<base={s['sz_neg']} "
                  f"equal={s['sz_zero']} mean_delta={s['sz_sum'] / s['n']:+.0f}B")
            out.setdefault(fam, {}).setdefault(cell, {})[role] = {
                "n": s["n"], "value_delta_neg": s["neg"], "value_delta_pos": s["pos"],
                "multi_field_edits": s["multi"], "png_size_edited_gt_base": s["sz_pos"],
                "png_size_edited_lt_base": s["sz_neg"], "png_size_equal": s["sz_zero"],
                "png_size_mean_delta_bytes": round(s["sz_sum"] / s["n"], 1),
                "changed_scene_paths": sorted(s["delta_paths"])[:6]}

with open("reports/hier_p2_leak_verification_v1.json", "w") as fh:
    json.dump({"schema_version": "blind-gains.hier-leak-verification.v1",
               "inputs": "data/hier_v1_dev manifest_*_l3.jsonl causal rows + PNG byte sizes",
               "semantics": "delta = edited_side - base_side (swap-honoring)",
               "cells": out}, fh, indent=2, sort_keys=True)
print("WROTE reports/hier_p2_leak_verification_v1.json")
