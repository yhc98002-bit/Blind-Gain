#!/usr/bin/env python3
"""Standing generator census (08-12 dispatch P0.4).

Makes the 2026-08-11 census format a STANDING, inventory-driven review
artifact: every `data/**/*.jsonl` manifest is scanned for rows carrying a
`template_id`; every (family × template × variant) present on disk appears in
the inventory automatically — a new generator family shows up the moment its
manifest exists, with no hand-maintained list to forget. Sampling happens
within variants only (first-N in manifest order, outcome-blind), exactly as
the 08-11 package's README declares.

Differences from the hand-built 08-11 package (reports/review_packages/
pi_review_v2_20260811/examples.json), stated rather than hidden:
- arms_available / n_joinable are NOT computed here — joining cached model
  outputs is review-package work (P2.4's builder), not census work.
- capability_stage comes from the small doc-sourced mapping below (HB.9 /
  PAPER1 §5: header table & chart = L1, coordinate register = L2,
  premise-v2 = L3). Anything the docs do not attribute is exported as
  "unmapped" — fail-visible, never guessed.

Variant identity is mechanical: (manifest, template_id, intervention_type?,
rung?, probe?) — whichever discriminator fields the rows actually carry.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Doc-sourced capability staging (HB.9; PAPER1 §5 "The hierarchy mapping
# (recorded 2026-08-12)"). Keys are template_id substrings, first match wins.
CAPABILITY_STAGE_MAP: list[tuple[str, str, str]] = [
    ("coordinate_register", "L2", "PAPER1 §5 hierarchy mapping: coordinate register = L2"),
    ("t4v2_", "L3", "PAPER1 §5 hierarchy mapping: premise-v2 = L3"),
    ("premise", "L3", "PAPER1 §5 hierarchy mapping: premise-v2 = L3"),
    ("table", "L1", "PAPER1 §5 hierarchy mapping: header table = L1"),
    ("chart", "L1", "PAPER1 §5 hierarchy mapping: chart = L1"),
    ("hier_coord", "L1/L2/L3", "registered_hier_benchmark_v1.md §2 (mother-item layers)"),
    ("hier_chart", "L1/L2/L3", "registered_hier_benchmark_v1.md §2 (mother-item layers)"),
]
UNMAPPED_STAGE = "unmapped"
UNMAPPED_SOURCE = "no doc attribution — needs PI/doc mapping before review use"

DISCRIMINATORS = ("intervention_type", "rung", "probe")


def stage_of(template_id: str) -> tuple[str, str]:
    for needle, stage, source in CAPABILITY_STAGE_MAP:
        if needle in template_id:
            return stage, source
    return UNMAPPED_STAGE, UNMAPPED_SOURCE


def family_of(manifest: Path, data_root: Path) -> str:
    relative = manifest.relative_to(data_root)
    return relative.parts[0] if len(relative.parts) > 1 else manifest.stem


def manifest_relpath(manifest: Path, data_root: Path) -> str:
    try:
        return str(manifest.relative_to(ROOT))
    except ValueError:  # synthetic data roots outside the repo (fixtures)
        return str(manifest.relative_to(data_root.parent))


def variant_key(row: dict) -> tuple:
    return (str(row.get("template_id")),) + tuple(
        str(row.get(field)) for field in DISCRIMINATORS if row.get(field) is not None
    )


def scan_manifest(path: Path, examples_per_variant: int) -> dict | None:
    """Return {variant_key: {count, category, first_rows}} or None if the
    file's first parseable row carries no template_id (not a census manifest)."""
    variants: "OrderedDict[tuple, dict]" = OrderedDict()
    saw_template = False
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                return None
            if not isinstance(row, dict):
                return None
            if row.get("template_id") is None:
                if not saw_template:
                    return None  # fast skip: first row decides
                continue
            saw_template = True
            key = variant_key(row)
            entry = variants.setdefault(
                key,
                {"count": 0, "category": row.get("category"), "examples": []},
            )
            entry["count"] += 1
            if len(entry["examples"]) < examples_per_variant:
                entry["examples"].append(
                    {
                        "pair_id": row.get("pair_id"),
                        "question": row.get("question"),
                        "image_a_path": row.get("image_a_path"),
                        "image_b_path": row.get("image_b_path"),
                        "manifest_line": line_number,
                    }
                )
    return variants if saw_template else None


def build_census(data_root: Path, examples_per_variant: int) -> dict:
    inventory = []
    scanned = skipped = 0
    manifests = sorted(p for p in data_root.rglob("*.jsonl") if p.is_file())
    for manifest in manifests:
        scanned += 1
        variants = scan_manifest(manifest, examples_per_variant)
        if variants is None:
            skipped += 1
            continue
        family = family_of(manifest, data_root)
        for key, entry in variants.items():
            template_id = key[0]
            stage, source = stage_of(template_id)
            inventory.append(
                {
                    "family": family,
                    "family_label": family,
                    "variant": "|".join(key),
                    "variant_label": "|".join(key),
                    "template_id": template_id,
                    "category": entry["category"],
                    "n_in_benchmark": entry["count"],
                    "n_in_package": len(entry["examples"]),
                    "manifest": manifest_relpath(manifest, data_root),
                    "capability_stage": stage,
                    "stage_source": source,
                    "examples": entry["examples"],
                }
            )
    inventory.sort(key=lambda row: (row["family"], row["manifest"], row["variant"]))
    git_hash = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()
    return {
        "schema_version": "blind-gains.generator-census.v2",
        "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_hash": git_hash,
        "data_root": str(data_root),
        "coverage_rule": (
            "census, not selection: every data/**.jsonl whose rows carry "
            "template_id appears; sampling within variants only (first-N, "
            "manifest order, outcome-blind)"
        ),
        "not_computed_here": "arms_available / n_joinable (review-package work, P2.4)",
        "manifests_scanned": scanned,
        "manifests_without_template_id": skipped,
        "n_families": len({row["family"] for row in inventory}),
        "n_variants": len(inventory),
        "n_unmapped_stage": sum(
            1 for row in inventory if row["capability_stage"] == UNMAPPED_STAGE
        ),
        "inventory": inventory,
    }


def render_markdown(census: dict) -> str:
    lines = [
        "# Generator census (standing, inventory-driven) — P0.4",
        "",
        f"Generated {census['generated_utc']} at `{census['git_hash'][:9]}`. "
        f"{census['n_families']} families, {census['n_variants']} variants, "
        f"{census['manifests_scanned']} jsonl files scanned "
        f"({census['manifests_without_template_id']} without template_id, skipped), "
        f"{census['n_unmapped_stage']} variants with unmapped capability stage.",
        "",
        census["coverage_rule"] + ".",
        "",
        "| family | variant | template_id | n | stage | manifest |",
        "|---|---|---|---:|---|---|",
    ]
    for row in census["inventory"]:
        lines.append(
            f"| {row['family']} | {row['variant_label']} | `{row['template_id']}` "
            f"| {row['n_in_benchmark']} | {row['capability_stage']} "
            f"| `{row['manifest']}` |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=ROOT / "data")
    parser.add_argument("--examples-per-variant", type=int, default=2)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    if args.json_output.exists() or args.markdown_output.exists():
        raise FileExistsError("refusing to overwrite an existing census artifact")
    census = build_census(args.data_root.resolve(), args.examples_per_variant)
    args.json_output.write_text(
        json.dumps(census, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    args.markdown_output.write_text(render_markdown(census), encoding="utf-8")
    print(
        json.dumps(
            {k: census[k] for k in ("n_families", "n_variants", "n_unmapped_stage",
                                     "manifests_scanned")},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
