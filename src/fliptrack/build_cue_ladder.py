"""Cue-ladder generator (CL / F4b), registered in docs/registered_cue_ladder_v1.md.

Four rungs rendered from the SAME nine-series scene program, with only the
annotation layer changing (I12). The scene program is not re-sampled: each R19
nine-series pair records its `provenance.pair_seed`, so this replays that exact
RNG stream and asserts the replayed answers match the frozen manifest before
rendering anything. The ladder is therefore item-paired with R19.

`src/fliptrack/build_v02.py` is NOT modified -- R19's generator stays frozen
(I11). The render here is a separate function whose `exact` mode reproduces
build_v02's annotation layer.

Rungs:
  exact   on-point circle+star, legend star, abscissa caption   (= R19 today)
  region  legend star only; the point itself is not marked
  none    no marks at all; the question names the series by label
  decoy   marks placed on a NON-target series; question names the target series;
          gold follows the question, never the cue
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from src.fliptrack.build_v02 import COLORS, _font, _procedural_labels

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
R19_MANIFEST = ROOT / "data/fliptrack_v02r19_artifact_expanded_source_manifest.jsonl"
TEMPLATE = "starred_series_value_nine_v07"
RUNGS = ("exact", "region", "none", "decoy", "named_exact", "named_region")
# v2 amendment: named_* rungs hold the question constant (named series) and vary
# only the annotation layer, per docs/registered_cue_ladder_v2_amendment.md.


def replay_scene(pair_seed: int) -> dict[str, Any]:
    """Replay build_v02.generate_nine_series_chart_pairs' RNG stream exactly."""
    rng = random.Random(pair_seed)
    labels = _procedural_labels(rng, 9)
    values_a = [[rng.randrange(10, 91, 10) for _ in range(6)] for _ in range(9)]
    target_series = rng.randrange(9)
    target_x = rng.randrange(1, 5)
    values_b = [list(s) for s in values_a]
    current = values_a[target_series][target_x]
    candidates = [v for v in range(10, 91, 10) if abs(v - current) >= 20]
    values_b[target_series][target_x] = rng.choice(candidates)
    return {
        "labels": labels, "values_a": values_a, "values_b": values_b,
        "target_series": target_series, "target_x": target_x,
        "answer_a": str(current), "answer_b": str(values_b[target_series][target_x]),
    }


def pick_decoy(scene: dict[str, Any], pair_seed: int) -> int:
    """A non-target series whose value at target_x differs from the gold.

    Following the decoyed cue must therefore produce a wrong answer, so
    CueFollowRate is measurable. Uses its own RNG so the replay stream above is
    untouched.
    """
    rng = random.Random(pair_seed ^ 0x5EED)
    tx, ts = scene["target_x"], scene["target_series"]
    gold = scene["values_a"][ts][tx]
    options = [i for i in range(9) if i != ts and scene["values_a"][i][tx] != gold]
    if not options:
        options = [i for i in range(9) if i != ts]
    return rng.choice(options)


def render(labels, values, target_series, target_x, *, rung, decoy_series=None) -> Image.Image:
    """`exact` reproduces build_v02._render_chart's annotation layer."""
    width, height = 1200, 760
    image = Image.new("RGB", (width, height), (249, 250, 248))
    draw = ImageDraw.Draw(image)
    left, top, right, bottom = 90, 78, 820, 650
    draw.text((width // 2, 30), "Multi-Series Calibration Trace", anchor="mm",
              font=_font(24, True), fill=(25, 25, 25))
    draw.rectangle((left, top, right, bottom), fill=(255, 255, 255), outline=(45, 45, 45), width=2)
    for tick in range(0, 101, 10):
        y = bottom - round(tick / 100 * (bottom - top))
        draw.line((left, y, right, y), fill=(232, 232, 232), width=1)
        if tick % 20 == 0:
            draw.text((left - 12, y), str(tick), anchor="rm", font=_font(13), fill=(55, 55, 55))
    x_positions = [left + 55 + index * 128 for index in range(6)]
    for index, x in enumerate(x_positions, start=1):
        draw.line((x, top, x, bottom), fill=(242, 242, 242), width=1)
        draw.text((x, bottom + 24), str(index), anchor="mm", font=_font(14), fill=(55, 55, 55))
    draw.text(((left + right) // 2, bottom + 54), "x", anchor="mm", font=_font(17, True), fill=(40, 40, 40))

    # which series carries the on-point mark and the legend star
    marked = {"exact": target_series, "region": None, "none": None,
              "decoy": decoy_series, "named_exact": target_series,
              "named_region": None}[rung]
    legend_star = {"exact": target_series, "region": target_series, "none": None,
                   "decoy": decoy_series, "named_exact": target_series,
                   "named_region": target_series}[rung]

    for series_index, series_values in enumerate(values):
        points = [(x, bottom - round(v / 100 * (bottom - top)))
                  for x, v in zip(x_positions, series_values)]
        color = COLORS[series_index]
        draw.line(points, fill=color, width=3)
        for x, y in points:
            draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=color, outline=(255, 255, 255), width=1)
        if marked is not None and series_index == marked:
            p = points[target_x]
            draw.ellipse((p[0] - 15, p[1] - 15, p[0] + 15, p[1] + 15),
                         fill=(255, 255, 255), outline=(0, 0, 0), width=2)
            draw.text(p, "*", anchor="mm", font=_font(26, True), fill=(0, 0, 0))

    legend_left = 855
    draw.rectangle((legend_left, 74, 1168, 650), fill=(255, 255, 255), outline=(175, 175, 175), width=2)
    draw.text((1010, 100), "Series key", anchor="mm", font=_font(19, True), fill=(25, 25, 25))
    for index, label in enumerate(labels):
        y = 142 + index * 48
        draw.line((legend_left + 28, y, legend_left + 65, y), fill=COLORS[index], width=5)
        draw.ellipse((legend_left + 43, y - 4, legend_left + 51, y + 4), fill=COLORS[index])
        draw.text((legend_left + 82, y), label, anchor="lm", font=_font(16), fill=(20, 20, 20))
        if legend_star is not None and index == legend_star:
            draw.text((legend_left + 16, y), "*", anchor="mm", font=_font(25, True), fill=(0, 0, 0))

    caption = {
        "exact": f"The black star marks the queried point at x = {target_x + 1}.",
        "region": "The black star in the legend marks the target series.",
        "none": None,
        "decoy": f"The black star marks the queried point at x = {target_x + 1}.",
        "named_exact": f"The black star marks the queried point at x = {target_x + 1}.",
        "named_region": "The black star in the legend marks the target series.",
    }[rung]
    if caption:
        draw.text((90, 714), caption, font=_font(14), fill=(75, 75, 75))
    return image


def question_for(rung: str, scene: dict[str, Any]) -> str:
    tx = scene["target_x"] + 1
    if rung in ("exact", "region"):
        return f"What is the value of the starred series at x = {tx}?"
    # named_* rungs, `none` and `decoy` all use the identical named-series form
    # so that only the annotation layer differs between them (I12)
    label = scene["labels"][scene["target_series"]]
    return f"What is the value of series {label} at x = {tx}?"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/cue_ladder_v1")
    ap.add_argument("--only", default="", help="comma-separated rungs to build")
    args = ap.parse_args()
    out_root = ROOT / args.out

    src = [json.loads(l) for l in R19_MANIFEST.read_text().splitlines() if l.strip()]
    nine = [r for r in src if r.get("template_id") == TEMPLATE]
    if len(nine) != 300:
        raise SystemExit(f"expected 300 nine-series rows, got {len(nine)}")

    # integrity gate: the replay must reproduce the frozen answers exactly
    scenes = {}
    n_swapped = 0
    for row in nine:
        seed = int(row["provenance"]["pair_seed"])
        s = replay_scene(seed)
        fa, fb = str(row["answer_a"]), str(row["answer_b"])
        if (s["answer_a"], s["answer_b"]) == (fa, fb):
            pass
        elif (s["answer_a"], s["answer_b"]) == (fb, fa):
            # R19 packaging randomizes member presentation order (I4). Adopt the
            # frozen orientation so the ladder stays item-paired with R19.
            s["values_a"], s["values_b"] = s["values_b"], s["values_a"]
            s["answer_a"], s["answer_b"] = s["answer_b"], s["answer_a"]
            n_swapped += 1
        else:
            raise SystemExit(
                f"REPLAY MISMATCH {row['pair_id']}: replayed "
                f"({s['answer_a']},{s['answer_b']}) vs frozen ({fa},{fb})")
        scenes[row["pair_id"]] = (seed, s)
    print(f"replay integrity: {len(scenes)}/300 pairs reproduce the frozen answer "
          f"pair exactly ({n_swapped} adopted the frozen member order)")

    summary = {}
    wanted = [r for r in RUNGS if not args.only or r in args.only.split(",")]
    for rung in wanted:
        img_dir = out_root / rung / "images"
        img_dir.mkdir(parents=True, exist_ok=True)
        rows = []
        for row in nine:
            pid = row["pair_id"]
            seed, s = scenes[pid]
            decoy = pick_decoy(s, seed) if rung == "decoy" else None
            paths = {}
            for side, values in (("a", s["values_a"]), ("b", s["values_b"])):
                img = render(s["labels"], values, s["target_series"], s["target_x"],
                             rung=rung, decoy_series=decoy)
                p = img_dir / f"{pid}_{side}.png"
                img.save(p)
                paths[side] = p
            entry = {
                "pair_id": f"cl_{rung}_{pid}",
                "source_pair_id": pid,
                "rung": rung,
                "question": question_for(rung, s),
                "answer_a": s["answer_a"],
                "answer_b": s["answer_b"],
                "image_a_path": str(paths["a"].relative_to(ROOT)),
                "image_b_path": str(paths["b"].relative_to(ROOT)),
                "image_a_sha256": [sha256_file(paths["a"])],
                "image_b_sha256": [sha256_file(paths["b"])],
                "category": "chart_two_hop_read",
                "template_id": f"cue_ladder_{rung}_v1",
                "schema_version": "blind-gains.cue-ladder.v1",
                "provenance": {
                    "generator": "src.fliptrack.build_cue_ladder",
                    "pair_seed": seed,
                    "replayed_from": TEMPLATE,
                    "registration": "docs/registered_cue_ladder_v1.md",
                },
                "verifier_results": {
                    "target_series_index": s["target_series"],
                    "target_x": s["target_x"] + 1,
                    "decoy_series_index": decoy,
                    "decoy_value_at_target_x": (
                        s["values_a"][decoy][s["target_x"]] if decoy is not None else None),
                    "gold_follows_question": True,
                },
            }
            rows.append(entry)
        man = out_root / f"{rung}_manifest.jsonl"
        blob = "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)
        man.write_text(blob)
        summary[rung] = {"n": len(rows), "manifest": str(man.relative_to(ROOT)),
                         "sha256": hashlib.sha256(blob.encode()).hexdigest()}
        print(f"  {rung:7s} n={len(rows)} sha256={summary[rung]['sha256'][:16]}")

    (out_root / "build_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"wrote {out_root}")


if __name__ == "__main__":
    main()
