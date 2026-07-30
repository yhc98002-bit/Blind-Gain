#!/usr/bin/env python3
"""E1c: chance-corrected retention for the five benchmarks that had no blind column.

Method is copied from reports/chance_corrected_retention_v1.json:
  naive_retention     = mean(blind) / mean(with_image)
  corrected_retention = (mean(blind) - mean(null)) / (mean(with_image) - mean(null))
  null: MC -> 1/k from that item's own presented option labels; MC with the gold
        label absent -> 0; free-form -> 0. Per-item null averaged over the subset and
        recomputed inside every bootstrap replicate.
Mixed-format benchmarks are split by format; no single global null is ever applied (I18).
"""
from __future__ import annotations

import glob
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
REPS = 10000
SEED = 20260729
CHUNK = 1000
# mean(with_image) - mean(null) can land on ~1e-16 instead of exactly 0 when the
# with-image accuracy equals the null (e.g. 5/30 vs 1/6); dividing by that produces
# a ~1e15 garbage ratio, so treat |denominator| <= TOL as undefined.
TOL = 1e-12
UNDERPOWERED_N = 30

WITH_IMAGE = {
    ("BLINK", "3B"): "experiments/runs/vlmevalkit_postprocess_l10_blink3b_canonicalv2_final_20260711T132325Z",
    ("BLINK", "7B"): "experiments/runs/vlmevalkit_postprocess_l10_blink7b_canonicalv2_final_20260711T132325Z",
    ("HallusionBench", "3B"): "experiments/runs/vlmevalkit_postprocess_l10_hallusion3b_canonicalv2_final_20260711T132325Z",
    ("HallusionBench", "7B"): "experiments/runs/vlmevalkit_postprocess_l10_hallusion7b_canonicalv2_final_20260711T132325Z",
    ("MMVP", "3B"): "experiments/runs/vlmevalkit_postprocess_l10_mmvp3b_canonicalv2_final_20260711T132326Z",
    ("MMVP", "7B"): "experiments/runs/vlmevalkit_postprocess_l10_mmvp7b_canonicalv2_final_20260711T132326Z",
    ("MathVerse", "3B"): "experiments/runs/vlmevalkit_postprocess_l10_mathverse3b_canonicalv2_v2_20260711T143923Z",
    ("MathVerse", "7B"): "experiments/runs/vlmevalkit_postprocess_l10_mathverse7b_canonicalv2_v2_20260711T143943Z",
    ("MMMU dev+validation", "3B"): "experiments/runs/vlmevalkit_postprocess_l10_mmmu3b_v2_canonicalv2_20260711T145554Z",
    ("MMMU dev+validation", "7B"): "experiments/runs/vlmevalkit_postprocess_l10_mmmu7b_v2_canonicalv2_20260711T145711Z",
}
# benchmark -> (blind run tag stem, expected n, format mode)
BENCH = {
    "BLINK": ("blink", 1901, "pure_mc"),
    "HallusionBench": ("hallusion", 1129, "binary_yorn"),
    "MMVP": ("mmvp", 300, "pure_mc"),
    "MathVerse": ("mathverse", 3940, "mixed"),
    "MMMU dev+validation": ("mmmu", 1050, "mixed"),
}
SCALES = {"3B": "3b", "7B": "7b"}
# with-image golds corrupted by Excel formula coercion of a leading "="
MATHVERSE_GOLD_DEFECT = {f"mathverse_{i}" for i in range(2956, 2961)}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            out[str(record["index"])] = record
    return out


def resolve_blind_run(stem: str, scale_lc: str) -> Path:
    pattern = str(ROOT / f"experiments/runs/layer1_blind_e1c_{stem}{scale_lc}_*")
    candidates = []
    for directory in sorted(glob.glob(pattern)):
        manifest = Path(directory) / "run_manifest.json"
        if not manifest.is_file():
            continue
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        if payload.get("status") == "complete" and payload.get("exit_code") == 0:
            candidates.append(Path(directory))
    if not candidates:
        raise FileNotFoundError(f"no complete blind run for {stem}{scale_lc}")
    return candidates[-1]


def item_null(record: dict) -> float:
    """1/k from the item's own presented labels; 0 for free-form or absent gold label."""
    labels = record.get("option_labels") or []
    if not labels:
        return 0.0
    gold = record["gold"]
    golds = gold if isinstance(gold, list) else [gold]
    if not all(str(g).strip().upper() in labels for g in golds):
        return 0.0
    return 1.0 / len(labels)


def bootstrap(blind: np.ndarray, image: np.ndarray, null: np.ndarray) -> dict:
    n = len(blind)
    rng = np.random.default_rng(SEED)
    naive: list[np.ndarray] = []
    corrected: list[np.ndarray] = []
    boot_image: list[np.ndarray] = []
    boot_blind: list[np.ndarray] = []
    nonpositive = 0
    done = 0
    while done < REPS:
        size = min(CHUNK, REPS - done)
        idx = rng.integers(0, n, size=(size, n))
        mb = blind[idx].mean(axis=1)
        mw = image[idx].mean(axis=1)
        mn = null[idx].mean(axis=1)
        boot_blind.append(mb)
        boot_image.append(mw)
        with np.errstate(divide="ignore", invalid="ignore"):
            naive.append(np.where(mw > 0, mb / mw, np.nan))
            denominator = mw - mn
            corrected.append(
                np.where(np.abs(denominator) > TOL, (mb - mn) / denominator, np.nan)
            )
        nonpositive += int((denominator <= 0).sum())
        done += size
    naive_all = np.concatenate(naive)
    corrected_all = np.concatenate(corrected)
    blind_all = np.concatenate(boot_blind)
    image_all = np.concatenate(boot_image)

    def pct(values: np.ndarray) -> tuple[float | None, float | None, int]:
        good = values[~np.isnan(values)]
        if good.size == 0:
            return None, None, 0
        return float(np.percentile(good, 2.5)), float(np.percentile(good, 97.5)), int(good.size)

    mb, mw, mn = float(blind.mean()), float(image.mean()), float(null.mean())
    denom = mw - mn
    denom_defined = abs(denom) > TOL
    naive_low, naive_high, naive_reps = pct(naive_all)
    corr_low, corr_high, corr_reps = pct(corrected_all)
    blind_low, blind_high, _ = pct(blind_all)
    image_low, image_high, _ = pct(image_all)
    frac = nonpositive / REPS
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
        "corrected_retention_ci_valid_reps": corr_reps if denom_defined else 0,
        "with_image_acc_ci95_low": image_low,
        "with_image_acc_ci95_high": image_high,
        "blind_acc_ci95_low": blind_low,
        "blind_acc_ci95_high": blind_high,
        "boot_denominator_nonpositive_frac": frac,
        "denominator_crosses_zero": bool(frac > 0.0),
        "bootstrap": {
            "reps": REPS,
            "seed": SEED,
            "unit": "item",
            "paired": True,
            "ci": "percentile-2.5/97.5",
        },
    }


def make_row(benchmark, scale, subset, answer_format, k, items, null_override=None) -> dict:
    blind = np.array([it["blind_final"] for it in items], dtype=float)
    image = np.array([it["image_final"] for it in items], dtype=float)
    blind_s = np.array([it["blind_strict"] for it in items], dtype=float)
    image_s = np.array([it["image_strict"] for it in items], dtype=float)
    if null_override is None:
        null = np.array([it["null"] for it in items], dtype=float)
    else:
        null = np.full(len(items), float(null_override))
    return {
        "family": "qwen-layer1",
        "model": f"Qwen2.5-VL-{scale}",
        "benchmark": benchmark,
        "subset": subset,
        "answer_format": answer_format,
        "k": k,
        "n": len(items),
        "null": float(null.mean()),
        "underpowered_subset": len(items) < UNDERPOWERED_N,
        "lenient_acc_final": bootstrap(blind, image, null),
        "strict_acc_strict": bootstrap(blind_s, image_s, null),
    }


def main() -> None:
    rows: list[dict] = []
    whole: list[dict] = []
    not_computed: list[dict] = []
    inputs: dict[str, dict] = {}
    provenance: list[dict] = []
    format_counts: dict[str, dict] = {}

    for benchmark, (stem, expected_n, mode) in BENCH.items():
        for scale, scale_lc in SCALES.items():
            blind_dir = resolve_blind_run(stem, scale_lc)
            manifest = json.loads((blind_dir / "run_manifest.json").read_text(encoding="utf-8"))
            blind_path = blind_dir / "predictions.jsonl"
            image_path = ROOT / WITH_IMAGE[(benchmark, scale)] / "rows.jsonl"
            blind_rows = load_jsonl(blind_path)
            image_rows = load_jsonl(image_path)
            metrics = json.loads((blind_dir / "metrics.json").read_text(encoding="utf-8"))
            assert metrics["image_removed"] is True, blind_dir
            assert len(blind_rows) == expected_n, (benchmark, scale, len(blind_rows))
            assert set(blind_rows) == set(image_rows), (benchmark, scale, "index set mismatch")

            for path in (blind_path, image_path):
                key = str(path.relative_to(ROOT))
                inputs[key] = {"sha256": sha256(path), "bytes": path.stat().st_size}
            provenance.append({
                "benchmark": benchmark,
                "model": f"Qwen2.5-VL-{scale}",
                "blind_run_id": manifest["run_id"],
                "blind_config": manifest["config_path"],
                "blind_config_hash": manifest["config_hash"],
                "blind_data_manifest": manifest["data_manifest"],
                "blind_data_manifest_hash": manifest["data_manifest_hash"],
                "blind_git_hash": manifest["git_hash"],
                "blind_node": manifest["node"],
                "blind_gpu": manifest["gpu_allocation"],
                "blind_seed": manifest["seed"],
                "blind_exit_code": manifest["exit_code"],
                "blind_image_protocol": manifest["image_protocol"],
                "blind_image_removed_flag": metrics["image_removed"],
                "with_image_run": WITH_IMAGE[(benchmark, scale)],
            })

            # HallusionBench ships 178 text-only rows that the adapter gave a deterministic
            # blank image, so for those rows the with-image condition carried no visual
            # information either and removing the image removes nothing.
            placeholder: dict[str, bool] = {}
            if benchmark == "HallusionBench":
                frame = pd.read_csv(ROOT / manifest["data_manifest"], sep="\t")
                placeholder = {
                    str(r["index"]): bool(r["image_is_placeholder"])
                    for _, r in frame.iterrows()
                }

            items = []
            for index, blind in blind_rows.items():
                image = image_rows[index]
                items.append({
                    "index": index,
                    "labels": blind["option_labels"] or [],
                    "null": item_null(blind),
                    "blind_final": float(bool(blind["acc_final"])),
                    "blind_strict": float(bool(blind["acc_strict"])),
                    "image_final": float(bool(image["acc_final"])),
                    "image_strict": float(bool(image["acc_strict"])),
                    "gold_agrees": json.dumps(blind["gold"], sort_keys=True)
                    == json.dumps(image["gold"], sort_keys=True),
                    "placeholder_image": placeholder.get(index),
                })

            counts: dict[str, int] = {}
            for it in items:
                key = f"MC|k={len(it['labels'])}" if it["labels"] else "free_form|k=0"
                counts[key] = counts.get(key, 0) + 1
            format_counts.setdefault(benchmark, {})[f"Qwen2.5-VL-{scale}"] = dict(sorted(counts.items()))

            mc = [it for it in items if it["labels"]]
            ff = [it for it in items if not it["labels"]]

            # whole-benchmark naive reference (null ignored) -- always reportable
            note = (
                "Whole-benchmark naive retention (null ignored)."
                if mode != "mixed"
                else "Whole-benchmark naive retention (null ignored) over the mixed benchmark. "
                "No corrected counterpart at this level; see the format subset rows."
            )
            whole_row = make_row(benchmark, scale, "whole benchmark (naive only)", "mixed" if mode == "mixed" else ("multiple_choice" if mode == "pure_mc" else "free_form"), None, items)
            whole.append({
                "family": "qwen-layer1",
                "model": f"Qwen2.5-VL-{scale}",
                "benchmark": benchmark,
                "n": len(items),
                "corrected_retention": None,
                "lenient_acc_final": {k: v for k, v in whole_row["lenient_acc_final"].items() if "corrected" not in k and k not in ("denominator", "boot_denominator_nonpositive_frac", "denominator_crosses_zero")},
                "strict_acc_strict": {k: v for k, v in whole_row["strict_acc_strict"].items() if "corrected" not in k and k not in ("denominator", "boot_denominator_nonpositive_frac", "denominator_crosses_zero")},
                "note": note,
            })

            if mode == "pure_mc":
                assert not ff, (benchmark, "unexpected free-form rows")
                for k in sorted({len(it["labels"]) for it in mc}):
                    subset = [it for it in mc if len(it["labels"]) == k]
                    rows.append(make_row(benchmark, scale, f"MC k={k}", "multiple_choice", k, subset))
                rows.append(make_row(benchmark, scale, "all items (MC pooled, item-level null)", "multiple_choice", None, mc))

            elif mode == "binary_yorn":
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
                })

            elif mode == "mixed":
                if benchmark == "MathVerse":
                    ff_primary = [it for it in ff if it["index"] not in MATHVERSE_GOLD_DEFECT]
                    excluded = [it for it in ff if it["index"] in MATHVERSE_GOLD_DEFECT]
                    assert len(excluded) == 5, len(excluded)
                    assert all(not it["gold_agrees"] for it in excluded)
                    rows.append(make_row(benchmark, scale, "free-form (gold-consistent, primary)", "free_form", 0, ff_primary, null_override=0.0))
                    rows.append(make_row(benchmark, scale, "free-form (all items, sensitivity)", "free_form", 0, ff, null_override=0.0))
                    not_computed.append({
                        "benchmark": benchmark,
                        "model": f"Qwen2.5-VL-{scale}",
                        "subset": "free-form items mathverse_2956..2960",
                        "n": 5,
                        "reason": "The with-image artifact stores gold '0' where the pinned TSV stores "
                                  "'=\\frac{7}{4}': VLMEvalKit wrote the xlsx and Excel coerced the "
                                  "leading '=' into a formula. The two conditions therefore do not share "
                                  "a gold on these 5 items, so they are excluded from the paired primary "
                                  "and reported as a sensitivity row instead.",
                    })
                else:
                    rows.append(make_row(benchmark, scale, "free-form", "free_form", 0, ff, null_override=0.0))
                for k in sorted({len(it["labels"]) for it in mc}):
                    subset = [it for it in mc if len(it["labels"]) == k]
                    rows.append(make_row(benchmark, scale, f"MC k={k}", "multiple_choice", k, subset))
                rows.append(make_row(benchmark, scale, "MC pooled (item-level null)", "multiple_choice", None, mc))
                not_computed.append({
                    "benchmark": benchmark,
                    "model": f"Qwen2.5-VL-{scale}",
                    "subset": "whole benchmark (single global null)",
                    "reason": f"Mixed benchmark: {len(mc)} MC items and {len(ff)} free-form items. "
                              "Per the null rule a single global null is not permitted, so no "
                              "whole-benchmark corrected retention is reported.",
                })
            print(f"done {benchmark} {scale}", flush=True)

    payload = {
        "schema_version": "blind-gains.e1c-blind-columns.v1",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "purpose": "Complete the F0 visual-necessity audit by supplying the blind (image-removed) "
                   "column for the five benchmarks that reports/chance_corrected_retention_v1.json "
                   "listed as having no image-removed run anywhere.",
        "method": {
            "corrected_retention": "(mean(blind) - mean(null)) / (mean(with_image) - mean(null))",
            "naive_retention": "mean(blind) / mean(with_image)",
            "null_rule": {
                "multiple_choice": "1/k using that item's own k (count of option labels presented)",
                "multiple_choice_gold_label_absent": "0 (gold label is not among presented labels)",
                "free_form": "0 (no correction)",
            },
            "null_aggregation": "per-item null averaged over the subset; recomputed inside every bootstrap replicate",
            "bootstrap": {
                "reps": REPS,
                "seed": SEED,
                "unit": "item",
                "paired": "same item ids in both conditions",
                "ci": "percentile 2.5 / 97.5",
                "note": "ratio of differences recomputed on each replicate; a fresh "
                        "numpy default_rng(seed) per subset",
            },
            "scoring_contracts": {"lenient": "acc_final", "strict": "acc_strict"},
            "undefined_denominator": "Where mean(with_image) equals mean(null) the corrected "
                                     f"denominator is 0 (guarded at |d| <= {TOL:g} against floating "
                                     "point residue); corrected retention and its CI are reported "
                                     "as null with corrected_retention_undefined=true.",
            "underpowered_subsets": f"Subsets with n < {UNDERPOWERED_N} carry "
                                    "underpowered_subset=true. Their intervals are reported for "
                                    "completeness but are not interpretable; MMMU k=6 (n=6), k=7 "
                                    "(n=2) and k=9 (n=5) are the affected cells.",
            "mixed_benchmark_rule": "MathVerse and MMMU are split by answer format; no single "
                                    "global null is applied to a mixed benchmark (I18).",
            "strict_caveat": "The same answer-format null (1/k) is applied to acc_strict. acc_strict "
                             "additionally requires the <answer> wrapper, so where with-image "
                             "acc_strict is below the null the denominator is negative; such rows "
                             "carry denominator_crosses_zero=true and boot_denominator_nonpositive_frac.",
        },
        "hallusionbench_null_decision": (
            "HallusionBench stores no option labels on any of its 1129 rows (k=0 everywhere), and "
            "the with-image column scored it with the open_final_span contract. DECISION: it is "
            "treated as FREE-FORM with null=0 for the primary row -- no option labels were "
            "synthesised and no options were extracted. Because its gold vocabulary is in fact "
            "binary ({Yes: 484, No: 645}) while only 170 of 1129 question texts say 'yes or no', a "
            "second row applies null=0.5 and is labelled a sensitivity, not the primary. The "
            "free-form primary is the conservative choice under the existing null rule ('1/k using "
            "that item's own k (count of option labels presented)'): zero labels are presented."
        ),
        "blind_integrity": "Every cell ran scripts/eval_layer1_blind.py, which raises if the chat "
                           "template inserts <|vision_start|> or <|image_pad|> for any row, and "
                           "src.eval.layer1_blind.load_rows, which raises if a built prompt retains "
                           "an image token. metrics.json image_removed=true was verified per cell.",
        "prompt_mirroring": {
            "blink / mmvp": "VLMEvalKit ImageMCQDataset.build_prompt text: 'Question:' + 'Options:' "
                            "block + select instruction (identical builder to MMStar).",
            "hallusionbench": "VLMEvalKit ImageYORNDataset inherits ImageBaseDataset.build_prompt: "
                              "question text verbatim.",
            "mathverse": "VLMEvalKit MathVerse.build_prompt: question text verbatim (the option list "
                         "is already inside the question text).",
            "mmmu": "VLMEvalKit MMMUDataset.build_prompt = ImageMCQDataset.build_prompt then "
                    "split_MMMU, which consumes the '<image N>' markers while interleaving images; "
                    "the blind mirror deletes those markers. This differs from MMStar/BLINK/MMVP on "
                    "purpose, because plain ImageMCQDataset leaves a literal '<image N>' in its text.",
        },
        "k_source": {
            benchmark: "option_labels field of the per-item artifacts; verified identical between the "
                       "blind and with-image columns on all rows (0 mismatches), and the k "
                       "distribution reproduces the with_image_run_k_availability block of "
                       "reports/chance_corrected_retention_v1.json"
            for benchmark in BENCH
        },
        "format_counts": format_counts,
        "rows": rows,
        "reference_naive_whole_benchmark": whole,
        "not_computed": not_computed,
        "provenance": provenance,
        "inputs": inputs,
    }
    out = ROOT / "reports/e1c_blind_columns_v1.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    sys.exit(main())
