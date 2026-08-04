#!/usr/bin/env python3
"""Build the portable R20 human-audit package, mirroring the accepted R19 audit design.

R20 is the one-shot private FlipTrack twin (1,200 pairs). The sample is drawn with
the same deterministic rule as the delivered R19 audit: the first 20 source-order
pairs per template (60 pairs, 120 images), mapped to opaque release IDs through the
private key. No RNG is used; the selection is fully determined by the frozen source
manifest order. The bundle layout, viewer, and answer-sheet exposure are identical
to `blind_gains_r19_human_audit_20260712_v3.zip`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_human_audit_bundle import build_bundle, sha256_file

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "blind-gains.r20-human-audit-bundle.v1"

SOURCE_MANIFEST = "data/fliptrack_r20_source_manifest.jsonl"
RELEASE_MANIFEST = "data/fliptrack_r20/manifest.jsonl"
ANSWER_KEY = ".private/fliptrack_r20_key.jsonl"
PACKAGE_DIR = "data/fliptrack_r20"
VIEWER = "tools/human_audit_viewer.html"
GUIDE = "docs/R20_HUMAN_AUDIT_GUIDE.md"
PAIRS_PER_TEMPLATE = 20

R19_DESIGN_PROVENANCE = {
    "delivered_bundle": "reports/review_packages/blind_gains_r19_human_audit_20260712_v3.zip",
    "delivered_bundle_sha256": "e455de54c4d00d024cc8eea18c98141ff326ba4188844e3661dc1025e0fcd25a",
    "r19_guide": "docs/HUMAN_AUDIT_GUIDE.md",
    "r19_audit_report": "reports/fliptrack_v02r19_human_audit.md",
    "selection_rule": "first_n_per_template_in_source_manifest_order",
    "pairs_per_template": PAIRS_PER_TEMPLATE,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-zip",
        type=Path,
        default=ROOT / "reports/human_packages/blind_gains_r20_human_audit_20260804_v1.zip",
    )
    parser.add_argument("--bundle-name", default="blind_gains_r20_human_audit_20260804_v1")
    parser.add_argument(
        "--report-json",
        type=Path,
        default=ROOT / "reports/r20_human_audit_bundle_v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.report_json.exists():
        raise FileExistsError(f"refusing to overwrite report: {args.report_json}")

    source_sha256 = {
        "source_manifest": sha256_file(ROOT / SOURCE_MANIFEST),
        "release_manifest": sha256_file(ROOT / RELEASE_MANIFEST),
        "private_answer_key": sha256_file(ROOT / ANSWER_KEY),
        "viewer": sha256_file(ROOT / VIEWER),
        "reviewer_guide": sha256_file(ROOT / GUIDE),
    }

    result = build_bundle(
        source_manifest=ROOT / SOURCE_MANIFEST,
        release_manifest=ROOT / RELEASE_MANIFEST,
        answer_key=ROOT / ANSWER_KEY,
        package_dir=ROOT / PACKAGE_DIR,
        viewer=ROOT / VIEWER,
        guide=ROOT / GUIDE,
        output_zip=args.output_zip,
        bundle_name=args.bundle_name,
        pairs_per_template=PAIRS_PER_TEMPLATE,
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "status": "pass",
        "scientific_gate_decision": None,
        "human_audit_outcome": "pending",
        "pair_count": result["pair_count"],
        "image_count": result["image_count"],
        "template_counts": result["template_counts"],
        "audit_contract": {
            "mode": "standard",
            "decision_count": 6,
        },
        "selection": {
            "strategy": "first_n_per_template_in_source_manifest_order",
            "pairs_per_template": PAIRS_PER_TEMPLATE,
            "rng": "none; deterministic given the frozen R20 source manifest order",
        },
        "source_paths": {
            "source_manifest": SOURCE_MANIFEST,
            "release_manifest": RELEASE_MANIFEST,
            "private_answer_key": ANSWER_KEY,
            "package_dir": PACKAGE_DIR,
            "viewer": VIEWER,
            "reviewer_guide": GUIDE,
        },
        "source_sha256": source_sha256,
        "r19_design_provenance": R19_DESIGN_PROVENANCE,
        "portable_zip": str(Path(result["output_zip"]).resolve()),
        "portable_zip_sha256": result["output_sha256"],
        "portable_zip_bytes": result["output_bytes"],
    }
    args.report_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
