#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import random
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from src.fliptrack.render_chart_v08 import (
    COLORS,
    LINESTYLES,
    MARKERS,
    _exact_mask,
    _render,
    adjacent_crossing_count,
    palette_distance_report,
)


SCHEMA_VERSION = "blind-gains.chart-v08-mechanical-audit.v2"
DIAGNOSTIC_SCHEMA_VERSION = "blind-gains.chart-v08-necessity-sidecar.v2"
EXPECTED_TEMPLATES = {
    "chart_v08_legend_target_flip": 50,
    "chart_v08_point_value_flip": 50,
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _image_sha256(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", compress_level=9)
    return hashlib.sha256(buffer.getvalue()).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON at {path}:{line_number}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"non-object row at {path}:{line_number}")
        rows.append(row)
    return rows


def _load_rgb(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return image.convert("RGB")


def _discordant_target(
    values: list[list[int]], target_series: int, target_x: int, key: str
) -> int:
    answer = values[target_series][target_x]
    candidates = [
        index
        for index, series in enumerate(values)
        if index != target_series and series[target_x] != answer
    ]
    if not candidates:
        raise ValueError(f"{key}: no answer-discordant randomized-star target")
    seed = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:16], 16)
    return random.Random(seed).choice(candidates)


def _validate_source_row(root: Path, row: dict[str, Any]) -> dict[str, Any]:
    pair_id = str(row["pair_id"])
    verifier = row["verifier_results"]
    values_a = verifier["values_a"]
    values_b = verifier["values_b"]
    target_x = int(verifier["target_x"]) - 1
    target_a = int(verifier["target_series_a"])
    target_b = int(verifier["target_series_b"])
    series_count = int(verifier["series_count"])
    image_a_path = root / row["image_a_path"]
    image_b_path = root / row["image_b_path"]
    mask_a_path = root / row["changed_region_mask_a"]
    mask_b_path = root / row["changed_region_mask_b"]
    for path in (image_a_path, image_b_path, mask_a_path, mask_b_path):
        if not path.is_file():
            raise FileNotFoundError(f"{pair_id}: missing source artifact: {path}")
    if _sha256(image_a_path) != row["image_a_sha256"]:
        raise ValueError(f"{pair_id}: image A hash mismatch")
    if _sha256(image_b_path) != row["image_b_sha256"]:
        raise ValueError(f"{pair_id}: image B hash mismatch")

    reconstructed_a = _render(values_a, target_a, target_x, series_count=series_count)
    reconstructed_b = _render(values_b, target_b, target_x, series_count=series_count)
    if _image_sha256(reconstructed_a) != row["image_a_sha256"]:
        raise ValueError(f"{pair_id}: metadata does not reconstruct image A")
    if _image_sha256(reconstructed_b) != row["image_b_sha256"]:
        raise ValueError(f"{pair_id}: metadata does not reconstruct image B")

    image_a = _load_rgb(image_a_path)
    image_b = _load_rgb(image_b_path)
    exact_mask = np.asarray(_exact_mask(image_a, image_b))
    with Image.open(mask_a_path) as mask_a_image, Image.open(mask_b_path) as mask_b_image:
        mask_a = np.asarray(mask_a_image.convert("L"))
        mask_b = np.asarray(mask_b_image.convert("L"))
    if not np.array_equal(exact_mask, mask_a) or not np.array_equal(exact_mask, mask_b):
        raise ValueError(f"{pair_id}: stored changed-region mask is not exact")

    answer_a = int(row["answer_a"])
    answer_b = int(row["answer_b"])
    if answer_a != values_a[target_a][target_x] or answer_b != values_b[target_b][target_x]:
        raise ValueError(f"{pair_id}: answer key disagrees with renderer metadata")
    if answer_a == answer_b:
        raise ValueError(f"{pair_id}: pair answers do not flip")
    if verifier.get("answer_pointing_cue") is not False:
        raise ValueError(f"{pair_id}: answer-pointing cue flag is not false")
    if row["provenance"].get("difficulty_controls") != [
        "crossing_density",
        "value_grid_granularity",
    ]:
        raise ValueError(f"{pair_id}: unregistered difficulty control")

    template = row["template_id"]
    changed = [
        (series_index, x_index)
        for series_index, (left, right) in enumerate(zip(values_a, values_b))
        for x_index, (value_a, value_b) in enumerate(zip(left, right))
        if value_a != value_b
    ]
    if template == "chart_v08_legend_target_flip":
        if values_a != values_b or target_a == target_b or changed:
            raise ValueError(f"{pair_id}: invalid legend-target mechanics")
        changed_pixels = np.argwhere(exact_mask > 0)
        if not len(changed_pixels) or int(changed_pixels[:, 1].max()) >= 1080:
            raise ValueError(f"{pair_id}: legend-target mask escapes the star region")
    elif template == "chart_v08_point_value_flip":
        if target_a != target_b or changed != [(target_a, target_x)]:
            raise ValueError(f"{pair_id}: invalid point-value mechanics")
    else:
        raise ValueError(f"{pair_id}: unexpected template: {template}")

    random_target_a = _discordant_target(values_a, target_a, target_x, f"{pair_id}:a")
    random_target_b = _discordant_target(values_b, target_b, target_x, f"{pair_id}:b")
    slots = math.comb(series_count, 2) * 2
    crossings_a = adjacent_crossing_count(values_a, target_x)
    crossings_b = adjacent_crossing_count(values_b, target_x)
    return {
        "pair_id": pair_id,
        "template_id": template,
        "question": row["question"],
        "answer_a": str(answer_a),
        "answer_b": str(answer_b),
        "values_a": values_a,
        "values_b": values_b,
        "target_x": target_x,
        "target_a": target_a,
        "target_b": target_b,
        "random_target_a": random_target_a,
        "random_target_b": random_target_b,
        "series_count": series_count,
        "crossings_a": crossings_a,
        "crossings_b": crossings_b,
        "crossing_fraction_a": crossings_a / slots,
        "crossing_fraction_b": crossings_b / slots,
    }


def _save_exclusive(image: Image.Image, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            image.save(handle, format="PNG", compress_level=9)
    except FileExistsError as exc:
        raise FileExistsError(
            f"refusing to overwrite chart-v08 diagnostic: {path}"
        ) from exc
    return _sha256(path)


def _write_exclusive(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(content)
    except FileExistsError as exc:
        raise FileExistsError(
            f"refusing to overwrite chart-v08 audit artifact: {path}"
        ) from exc


def build_sidecar(
    root: Path,
    source_manifest: Path,
    output_dir: Path,
    sidecar_output: Path,
    *,
    expected_per_template: int = 50,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite chart-v08 diagnostic directory: {output_dir}")
    if sidecar_output.exists():
        raise FileExistsError(f"refusing to overwrite chart-v08 sidecar: {sidecar_output}")
    rows = _read_jsonl(source_manifest)
    pair_ids = [str(row.get("pair_id", "")) for row in rows]
    if len(pair_ids) != len(set(pair_ids)):
        raise ValueError("source manifest has duplicate pair IDs")
    template_counts = Counter(str(row.get("template_id", "")) for row in rows)
    expected_templates = Counter(
        {template: expected_per_template for template in EXPECTED_TEMPLATES}
    )
    if template_counts != expected_templates:
        raise ValueError(f"unexpected template counts: {dict(template_counts)}")

    prepared = [_validate_source_row(root, row) for row in rows]
    source_hash = _sha256(source_manifest)
    output_dir.mkdir(parents=True)
    sidecar_rows: list[dict[str, Any]] = []
    for record in prepared:
        pair_id = record["pair_id"]
        subdir = output_dir / record["template_id"]
        values_a = record["values_a"]
        values_b = record["values_b"]
        target_x = record["target_x"]
        series_count = record["series_count"]
        random_target_a = record["random_target_a"]
        random_target_b = record["random_target_b"]
        images = {
            "no_star_a": _render(values_a, None, target_x, series_count=series_count),
            "no_star_b": _render(values_b, None, target_x, series_count=series_count),
            "random_star_a": _render(values_a, random_target_a, target_x, series_count=series_count),
            "random_star_b": _render(values_b, random_target_b, target_x, series_count=series_count),
        }
        paths = {
            name: subdir / f"{pair_id}_{name}.png" for name in images
        }
        hashes = {
            name: _save_exclusive(image, paths[name]) for name, image in images.items()
        }
        sidecar_rows.append(
            {
                "schema_version": DIAGNOSTIC_SCHEMA_VERSION,
                "pair_id": pair_id,
                "source_manifest_sha256": source_hash,
                "question": record["question"],
                "scoring_rule": "score_each_intervention_against_original_member_answer",
                "answer_a": record["answer_a"],
                "answer_b": record["answer_b"],
                "no_star": {
                    "image_a_path": str(paths["no_star_a"].relative_to(root)),
                    "image_a_sha256": hashes["no_star_a"],
                    "image_b_path": str(paths["no_star_b"].relative_to(root)),
                    "image_b_sha256": hashes["no_star_b"],
                },
                "random_star": {
                    "image_a_path": str(paths["random_star_a"].relative_to(root)),
                    "image_a_sha256": hashes["random_star_a"],
                    "image_b_path": str(paths["random_star_b"].relative_to(root)),
                    "image_b_sha256": hashes["random_star_b"],
                    "target_series_a": random_target_a,
                    "target_series_b": random_target_b,
                    "implied_answer_a": str(values_a[random_target_a][target_x]),
                    "implied_answer_b": str(values_b[random_target_b][target_x]),
                },
            }
        )
    _write_exclusive(
        sidecar_output,
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in sidecar_rows),
    )
    palette = palette_distance_report()
    checks = {
        "source_manifest_exact_expected_unique_pairs": len(rows)
        == expected_per_template * len(EXPECTED_TEMPLATES)
        and len(pair_ids) == len(set(pair_ids)),
        "two_subfamilies_exact_expected_count": template_counts == expected_templates,
        "source_images_hash_and_metadata_reconstruct": True,
        "answers_and_pair_mechanics_exact": True,
        "changed_region_masks_exact": True,
        "no_answer_pointing_cues": True,
        "difficulty_controls_only_crossings_and_granularity": True,
        "dual_coding_distinct": len(set(COLORS)) == len(set(LINESTYLES)) == len(set(MARKERS)) == 6,
        "normal_palette_cie76_at_least_25": palette["normal"] >= 25.0,
        "severe_cvd_palette_cie76_at_least_15": min(
            value for mode, value in palette.items() if mode != "normal"
        )
        >= 15.0,
        "member_specific_no_star_and_random_star_sidecars": len(sidecar_rows) == len(rows),
        "random_star_is_answer_discordant": all(
            row["random_star"]["implied_answer_a"] != row["answer_a"]
            and row["random_star"]["implied_answer_b"] != row["answer_b"]
            for row in sidecar_rows
        ),
    }
    audit = {
        "schema_version": SCHEMA_VERSION,
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "source_manifest": str(source_manifest.relative_to(root)),
        "source_manifest_sha256": source_hash,
        "sidecar": str(sidecar_output.relative_to(root)),
        "sidecar_sha256": _sha256(sidecar_output),
        "diagnostic_directory": str(output_dir.relative_to(root)),
        "pair_count": len(rows),
        "template_counts": dict(sorted(template_counts.items())),
        "palette_cie76_by_vision_mode": {
            mode: round(value, 4) for mode, value in palette.items()
        },
        "crossing_density": {
            "a_min": min(record["crossing_fraction_a"] for record in prepared),
            "a_max": max(record["crossing_fraction_a"] for record in prepared),
            "a_mean": sum(record["crossing_fraction_a"] for record in prepared) / len(prepared),
            "b_min": min(record["crossing_fraction_b"] for record in prepared),
            "b_max": max(record["crossing_fraction_b"] for record in prepared),
            "b_mean": sum(record["crossing_fraction_b"] for record in prepared) / len(prepared),
        },
    }
    return sidecar_rows, audit


def render_markdown(audit: dict[str, Any], audit_json: Path) -> str:
    check_rows = [
        f"| `{name}` | `{str(value).lower()}` |"
        for name, value in audit["checks"].items()
    ]
    palette_rows = [
        f"| {mode} | {distance:.4f} |"
        for mode, distance in audit["palette_cie76_by_vision_mode"].items()
    ]
    crossing = audit["crossing_density"]
    return "\n".join(
        [
            "# Chart V08 Mechanical Audit V2",
            "",
            "Status:",
            f"- Mechanical renderer audit: `{audit['status']}`.",
            "- This closes CPU-side pair construction and diagnostic plumbing only.",
            "- M12 remains incomplete until human legibility, model sensitivity, caption gates, attackers, and the one-shot confirmatory split are reported.",
            "- The declared calibration pair images and answer keys were not edited.",
            "",
            "Evidence:",
            f"- Machine audit: `{audit_json}`.",
            f"- Source: `{audit['source_manifest']}` (`{audit['source_manifest_sha256']}`).",
            f"- Explicit member-level diagnostic sidecar: `{audit['sidecar']}` (`{audit['sidecar_sha256']}`).",
            f"- Pairs: `{audit['pair_count']}`; templates: `{audit['template_counts']}`.",
            "",
            "Checks:",
            "| Check | Result |",
            "| --- | --- |",
            *check_rows,
            "",
            "Color Accessibility:",
            "- Palette separation is measured after severity-100 linear-RGB simulation; color remains supplementary to distinct line and marker coding.",
            "| Vision mode | Minimum CIE76 |",
            "| --- | ---: |",
            *palette_rows,
            "",
            "Crossing Density:",
            f"- Member A fraction: min `{crossing['a_min']:.4f}`, mean `{crossing['a_mean']:.4f}`, max `{crossing['a_max']:.4f}`.",
            f"- Member B fraction: min `{crossing['b_min']:.4f}`, mean `{crossing['b_mean']:.4f}`, max `{crossing['b_max']:.4f}`.",
            "- This measures crossings in the two segments adjacent to the queried x-coordinate; no answer-pointing cue is used as a difficulty control.",
            "",
            "Decision:",
            "- Score each no-star and randomized-star image against that member's original answer. Randomized targets are forced to imply a different answer.",
            "- Keep the original calibration manifest immutable; consumers join the diagnostic sidecar by `pair_id`.",
        ]
    ) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sidecar-output", type=Path, required=True)
    parser.add_argument("--audit-json-output", type=Path, required=True)
    parser.add_argument("--audit-markdown-output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    source_manifest = root / args.source_manifest
    output_dir = root / args.output_dir
    sidecar_output = root / args.sidecar_output
    audit_json = root / args.audit_json_output
    audit_markdown = root / args.audit_markdown_output
    for path in (audit_json, audit_markdown):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite chart-v08 audit: {path}")
    _, audit = build_sidecar(root, source_manifest, output_dir, sidecar_output)
    _write_exclusive(audit_json, json.dumps(audit, indent=2, sort_keys=True) + "\n")
    _write_exclusive(
        audit_markdown,
        render_markdown(audit, args.audit_json_output),
    )
    print(json.dumps({"status": audit["status"], "checks": audit["checks"]}))
    raise SystemExit(0 if audit["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
