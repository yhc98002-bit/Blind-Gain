#!/usr/bin/env python3
"""B1 declared calibration batch — one-shot report over the three cells.

Collects the real, blind (no-image), and caption cells for the declared
100-pair batch, reports pair-correct per intervention type per cell, attaches
the single-sample blind-solvability estimate per item, and stops. Facts only;
no acceptance iteration.
"""
from __future__ import annotations

import datetime as dt
import glob
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import re

from src.eval.visual_evidence_ranking import mathematically_equivalent

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
TYPES = ("fact_read", "chained_premise", "binding_swap", "distractor_only", "style_twin", "prior_conflict")
ANSWER_RE = re.compile(r"<answer>\s*(.*?)\s*</answer>", re.DOTALL)


def single_gold_correct(prediction: str, gold: str) -> bool:
    """Single-gold scoring for consistency pairs: the frozen FlipTrack member
    scorer's two-gold ambiguity guard structurally fails equal-gold items, so
    correctness is the canonical equivalence of the extracted answer to the
    single gold."""
    match = ANSWER_RE.search(prediction or "")
    value = match.group(1).strip() if match else (prediction or "").strip()
    if not value:
        return False
    try:
        return bool(mathematically_equivalent(value, gold))
    except Exception:
        return value == gold


def rescore_consistency(cells: dict[str, dict[str, dict[str, Any]]], manifest: dict[str, dict[str, Any]]) -> None:
    for pair_id, row in manifest.items():
        if not row.get("answers_equal"):
            continue
        gold = str(row["answer_a"])
        for cell_rows in cells.values():
            scored = cell_rows[pair_id]
            scored["correct_a"] = single_gold_correct(str(scored.get("prediction_a", "")), gold)
            scored["correct_b"] = single_gold_correct(str(scored.get("prediction_b", "")), gold)
            scored["pair_correct"] = scored["correct_a"] and scored["correct_b"]
            scored["consistency_single_gold_scored"] = True


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def collect_shard_cell(pattern: str) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for shard in sorted(glob.glob(str(ROOT / pattern))):
        for row in _read_jsonl(Path(shard)):
            pair_id = str(row["pair_id"])
            if pair_id in rows:
                raise ValueError(f"duplicate pair {pair_id} in {pattern}")
            rows[pair_id] = row
    if len(rows) != 100:
        raise ValueError(f"cell incomplete for {pattern}: {len(rows)}")
    return rows


def main() -> None:
    out_json = ROOT / "reports/geometry_track_prototype_v1.json"
    out_md = ROOT / "reports/geometry_track_prototype_v1.md"
    if out_json.exists() or out_md.exists():
        raise FileExistsError("refusing to overwrite the one-shot B1 report")

    manifest_path = ROOT / "data/b1_geometry_track_v1/manifest.jsonl"
    manifest = {str(row["pair_id"]): row for row in _read_jsonl(manifest_path)}
    caption_run = Path((ROOT / "tmp/b1_caption_run.txt").read_text().strip())
    if not caption_run.is_absolute():
        caption_run = ROOT / str(caption_run)

    cells = {
        "real": collect_shard_cell("experiments/runs/b1_calibration_real_shard*/predictions_shard_*.jsonl"),
        "blind_no_image": collect_shard_cell(
            "experiments/runs/b1_calibration_no_image_shard*/predictions_shard_*.jsonl"
        ),
        "caption": {
            str(row["pair_id"]): row
            for row in _read_jsonl(caption_run / "caption_qa_predictions.jsonl")
        },
    }
    if len(cells["caption"]) != 100:
        raise ValueError(f"caption cell incomplete: {len(cells['caption'])}")
    rescore_consistency(cells, manifest)

    by_type: dict[str, list[str]] = defaultdict(list)
    for pair_id, row in manifest.items():
        by_type[str(row["intervention_type"])].append(pair_id)

    table: dict[str, Any] = {}
    for intervention in TYPES:
        pair_ids = sorted(by_type[intervention])
        entry: dict[str, Any] = {"pairs": len(pair_ids)}
        for cell_name, cell_rows in cells.items():
            correct = [bool(cell_rows[p]["pair_correct"]) for p in pair_ids]
            entry[f"{cell_name}_pair_correct"] = sum(correct) / len(correct)
            members = [
                float(bool(cell_rows[p][f"correct_{side}"]))
                for p in pair_ids
                for side in ("a", "b")
            ]
            entry[f"{cell_name}_member_correct"] = sum(members) / len(members)
        table[intervention] = entry

    overall = {
        cell_name: sum(bool(rows[p]["pair_correct"]) for p in manifest) / len(manifest)
        for cell_name, rows in cells.items()
    }

    qhat: dict[str, float] = {}
    for pair_id in manifest:
        row = cells["blind_no_image"][pair_id]
        qhat[pair_id] = (float(bool(row["correct_a"])) + float(bool(row["correct_b"]))) / 2.0

    result = {
        "schema_version": "blind-gains.b1-geometry-track-calibration.v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "declared_batch": "data/b1_geometry_track_v1/manifest.jsonl",
        "declared_batch_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "one_shot": "declared batch; no acceptance iteration",
        "overall_pair_correct": overall,
        "per_intervention": table,
        "blind_solvability_qhat_single_sample": qhat,
        "caption_run": str(caption_run.relative_to(ROOT)),
    }

    lines = [
        "# B1 renderable geometry track — declared calibration batch (v1)",
        "",
        "One declared 100-pair batch (docs/EXPERIMENT_TODO.md Track B), scored on",
        "the real, blind (no-image), and question-blind-caption cells with the",
        "frozen base model. One shot; no acceptance iteration. Facts only.",
        "",
        f"- Batch SHA-256: `{result['declared_batch_sha256'][:16]}…`",
        f"- Overall pair-correct: real {overall['real']:.3f}, blind {overall['blind_no_image']:.3f},"
        f" caption {overall['caption']:.3f}",
        "",
        "## Pair-correct by intervention type",
        "",
        "| intervention | pairs | real pair | real member | blind pair | blind member | caption pair | caption member |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for intervention in TYPES:
        entry = table[intervention]
        lines.append(
            f"| {intervention} | {entry['pairs']} | {entry['real_pair_correct']:.3f}"
            f" | {entry['real_member_correct']:.3f}"
            f" | {entry['blind_no_image_pair_correct']:.3f}"
            f" | {entry['blind_no_image_member_correct']:.3f}"
            f" | {entry['caption_pair_correct']:.3f}"
            f" | {entry['caption_member_correct']:.3f} |"
        )
    lines += [
        "",
        "Scoring note: consistency pairs (distractor_only, style_twin) are scored",
        "single-gold — the frozen FlipTrack member scorer's two-gold ambiguity",
        "guard structurally fails equal-gold items (a correct answer matches both",
        "golds and is treated as ambiguous). Flip pairs keep the frozen scorer.",
        "",
        "Per-item single-sample blind-solvability estimates are in the machine JSON",
        "(`blind_solvability_qhat_single_sample`). Premise probes for the chained",
        "items are stored in the batch metadata for future scoring; they are not",
        "part of the declared three-cell calibration.",
        "",
    ]

    out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"overall": overall, "output_sha256": hashlib.sha256(out_json.read_bytes()).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
