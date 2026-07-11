from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from src.fliptrack.build_v02 import (
    generate_coordinate_register_high_entropy_pairs,
    generate_header_table_pairs,
    generate_nine_series_chart_pairs,
    write_contact_sheets,
)
from src.fliptrack.schema import write_jsonl


ROOT = Path(__file__).resolve().parents[2]
FROZEN_INPUT_HASHES = {
    "src/fliptrack/build_v02.py": "f2e5ddba99eefdbb28045b66a50f5cc946df0485d03e730281814f9b36148061",
    "src/fliptrack/schema.py": "701b52efa040a757f69452c60f6f7dc4260e66b5d61325e5cfa52f0b5375f9a5",
    "src/eval/fliptrack_metrics.py": "935efc67d027a020a1e1e4dc011d1b1a41fb01ac63f6a8b1c17f3c05cfc3b655",
    "configs/data/fliptrack_v02r19_artifact_expanded.json": "16bb1903e9b4ddd0732e84edfaa2ba1d2c7f1e030e319b2804c3e72888bd5152",
    "reports/fliptrack_v02r19_exact_package.json": "5056eb2be0c97793dedb4c9f87ad75b817ed727dd85239beec5c2b1be9cc860a",
    "data/fliptrack_v02r19_artifact_expanded_source_manifest.jsonl": "23dd24452670392d6355c06b6b167a1c868660c11d21b20e0bae393dc82126f0",
}
FROZEN_INPUT_SNAPSHOTS = {
    "src/eval/fliptrack_metrics.py": "src/fliptrack/frozen_r20/fliptrack_metrics.py",
}
FROZEN_SNAPSHOT_SOURCE_COMMITS = {
    "src/eval/fliptrack_metrics.py": "4058924530ee70b98a9d1ce3a6b448a8fe2baa70",
}
R20_SEEDS = {
    "document": 20261001,
    "geometry": 20261002,
    "chart": 20261003,
}
R20_TEMPLATE_COUNTS = {
    "header_cued_table_code_v02": 300,
    "coordinate_register_twenty_point_x_v02": 600,
    "starred_series_value_nine_v07": 300,
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_frozen_inputs(root: Path = ROOT) -> dict[str, str]:
    observed = {}
    for relative, expected in FROZEN_INPUT_HASHES.items():
        path = root / FROZEN_INPUT_SNAPSHOTS.get(relative, relative)
        if not path.is_file():
            raise FileNotFoundError(
                f"frozen R20 input or dedicated snapshot is missing: {path}"
            )
        observed[relative] = _sha256(path)
        if observed[relative] != expected:
            raise RuntimeError(
                f"frozen R20 input drift for {relative}: expected {expected}, found {observed[relative]}"
            )
    return observed


def _read_pair_ids(path: Path) -> set[str]:
    with path.open(encoding="utf-8") as handle:
        return {str(json.loads(line)["pair_id"]) for line in handle if line.strip()}


def build_r20(
    *,
    out_dir: Path,
    manifest: Path,
    contact_sheet_dir: Path,
    metadata_output: Path,
    r19_source_manifest: Path,
    template_counts: dict[str, int] | None = None,
    seeds: dict[str, int] | None = None,
    verify_hashes: bool = True,
) -> dict[str, Any]:
    counts = dict(template_counts or R20_TEMPLATE_COUNTS)
    seeds = dict(seeds or R20_SEEDS)
    required_templates = set(R20_TEMPLATE_COUNTS)
    if set(counts) != required_templates or any(value <= 0 for value in counts.values()):
        raise ValueError("R20 requires positive counts for exactly the three frozen templates")
    if set(seeds) != {"document", "geometry", "chart"} or len(set(seeds.values())) != 3:
        raise ValueError("R20 requires three distinct frozen family seeds")
    if manifest.exists() or metadata_output.exists() or contact_sheet_dir.exists():
        raise FileExistsError("refusing to overwrite an R20 generation artifact")
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to write into nonempty R20 source directory: {out_dir}")
    frozen_hashes = verify_frozen_inputs() if verify_hashes else {}

    rows = []
    rows.extend(
        generate_header_table_pairs(
            out_dir / "document",
            counts["header_cued_table_code_v02"],
            seeds["document"],
        )
    )
    rows.extend(
        generate_coordinate_register_high_entropy_pairs(
            out_dir / "geometry",
            counts["coordinate_register_twenty_point_x_v02"],
            seeds["geometry"],
        )
    )
    rows.extend(
        generate_nine_series_chart_pairs(
            out_dir / "chart",
            counts["starred_series_value_nine_v07"],
            seeds["chart"],
        )
    )
    observed_counts = dict(sorted(Counter(str(row["template_id"]) for row in rows).items()))
    if observed_counts != counts:
        raise RuntimeError(f"R20 template count mismatch: expected {counts}, found {observed_counts}")
    pair_ids = [str(row["pair_id"]) for row in rows]
    if len(pair_ids) != len(set(pair_ids)):
        raise RuntimeError("R20 generator produced duplicate pair IDs")
    overlap = sorted(set(pair_ids) & _read_pair_ids(r19_source_manifest))
    if overlap:
        raise RuntimeError(f"R20 seeds overlap R19 pair IDs: {overlap[:5]}")

    write_jsonl(manifest, rows)
    sheets = write_contact_sheets(rows, contact_sheet_dir)
    payload: dict[str, Any] = {
        "schema_version": "blind-gains.fliptrack-r20-generation.v1",
        "status": "pass",
        "selection_applied": False,
        "regeneration_applied": False,
        "threshold_change_applied": False,
        "n_pairs": len(rows),
        "template_counts": observed_counts,
        "seeds": seeds,
        "manifest": str(manifest),
        "manifest_sha256": _sha256(manifest),
        "r19_pair_id_overlap": 0,
        "contact_sheets": [str(path) for path in sheets],
        "frozen_input_hashes": frozen_hashes,
        "interpretation_rule": (
            "R20 is confirmatory. A template failing here has its certification downgraded to "
            "R19-selected; we do not mint R21. Generator-level pass = R20 meets the pre-frozen "
            "criteria without selection."
        ),
        "provenance_limit": (
            "The R10 generation manifest records worktree_dirty=true; current geometry generator AST "
            "matches the clean R18 generation commit and the retained template implementation."
        ),
    }
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("data/fliptrack_r20_source/renderable"))
    parser.add_argument("--manifest", type=Path, default=Path("data/fliptrack_r20_source_manifest.jsonl"))
    parser.add_argument(
        "--contact-sheet-dir", type=Path, default=Path("reports/contact_sheets/fliptrack_r20")
    )
    parser.add_argument(
        "--metadata-output", type=Path, default=Path("data/fliptrack_r20_generation.json")
    )
    parser.add_argument(
        "--r19-source-manifest",
        type=Path,
        default=Path("data/fliptrack_v02r19_artifact_expanded_source_manifest.jsonl"),
    )
    args = parser.parse_args()
    payload = build_r20(
        out_dir=args.out_dir,
        manifest=args.manifest,
        contact_sheet_dir=args.contact_sheet_dir,
        metadata_output=args.metadata_output,
        r19_source_manifest=args.r19_source_manifest,
    )
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
