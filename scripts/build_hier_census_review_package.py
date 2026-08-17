#!/usr/bin/env python3
"""HB P2.4: census review package v3 for the human gates queue.

Packages the standing generator census (v3, which now includes the hier_v1
families) with a deterministic hier_v1 sample for human review, mirroring the
R19/R20 audit-package discipline: no RNG — the sample is the first
N mother-pairs per (family, cell, role) in frozen L3 manifest order, with
sibling layers joined by mother_item_id. The package NEVER self-certifies:
queue.md lists the human gates and their blocking relations as registered.

Output: reports/review_packages/hier_v1_census_v3/ (+ .zip + build report).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CELLS = {"hier_coord_v1": ("n8", "n12", "n20"),
         "hier_chart_v1": ("s5_low", "s5_high", "s9_low", "s9_high")}
LAYERS = ("l3", "l2", "l1", "probe")
PAIRS_PER_CELL_ROLE = 2
SELECTION_RULE = "first_n_per_cell_role_in_l3_manifest_order"

QUEUE_MD = """# Human gates queue — HB P2.4 (census review package v3)

None of these gates are self-certifiable; each requires the named human
reviewer or the PI. Status below reflects the registered blocking relations.

| gate | reviewer | scope | blocking relation |
|---|---|---|---|
| chart-v08 no-zoom audit | Richard | chart-v08 calibration images | Blocks chart-side P2 progression to freeze (EXPERIMENT_TODO Part 3). |
| hier_coord_v1 legibility + cue-visibility review | Richard (or PI-designated) | samples/hier_coord_v1_* in this package | P3 freeze prerequisite (HB.8 human audit). |
| hier_chart_v1 review | PI decision first | samples/hier_chart_v1_* in this package | hier_chart_v1 FAILED the P2.3 artifact-attacker gate (see reports/hier_p23_readout_v1.md); a registered switch-symmetrization revision is expected — review of the current batch is diagnostic only. |
| census v3 coverage sign-off | PI | census_v3.md (51 families, 217 variants, 84 stage-unmapped) | P3 freeze prerequisite; stage-unmapped variants must be dispositioned or acknowledged. |
"""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(data_dir: Path, family: str, cell: str, layer: str) -> list[dict]:
    path = data_dir / f"manifest_{family}_{cell}_{layer}.jsonl"
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/hier_v1_dev")
    parser.add_argument("--census-md", type=Path,
                        default=ROOT / "reports/generator_census_v3.md")
    parser.add_argument("--census-json", type=Path,
                        default=ROOT / "reports/generator_census_v3.json")
    parser.add_argument("--output-dir", type=Path,
                        default=ROOT / "reports/review_packages/hier_v1_census_v3")
    parser.add_argument("--report", type=Path,
                        default=ROOT / "reports/hier_census_review_package_v3.json")
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(args.output_dir)
    if args.report.exists():
        raise FileExistsError(args.report)

    samples_dir = args.output_dir / "samples"
    n_pairs = 0
    n_images = 0
    sampled: dict[str, list[str]] = {}
    for family, cells in CELLS.items():
        for cell in cells:
            by_layer = {layer: load_manifest(args.data_dir, family, cell, layer)
                        for layer in LAYERS}
            if not by_layer["l3"]:
                raise FileNotFoundError(f"missing L3 manifest for {family}/{cell}")
            picked: dict[str, list[dict]] = {}
            for row in by_layer["l3"]:
                picked.setdefault(row["role"], [])
                if len(picked[row["role"]]) < PAIRS_PER_CELL_ROLE:
                    picked[row["role"]].append(row)
            for role, rows in sorted(picked.items()):
                for l3_row in rows:
                    mother = l3_row["mother_item_id"]
                    pair_dir = samples_dir / f"{family}_{cell}" / l3_row["pair_id"]
                    pair_dir.mkdir(parents=True)
                    item = {"mother_item_id": mother, "role": role,
                            "family": family, "cell": cell, "layers": {}}
                    for layer in LAYERS:
                        match = next((r for r in by_layer[layer]
                                      if r["mother_item_id"] == mother), None)
                        if match is None:
                            continue
                        images = {}
                        for side in ("a", "b"):
                            src = Path(match[f"image_{side}_path"])
                            dst = pair_dir / f"{layer}_{side}.png"
                            if not dst.exists():
                                shutil.copy2(src, dst)
                                n_images += 1
                            images[side] = dst.name
                        item["layers"][layer] = {
                            "question": match["question"],
                            "answer_a": match["answer_a"],
                            "answer_b": match["answer_b"],
                            "pair_id": match["pair_id"],
                            "images": images}
                    (pair_dir / "item.json").write_text(
                        json.dumps(item, indent=2, sort_keys=True) + "\n")
                    sampled.setdefault(f"{family}_{cell}", []).append(
                        l3_row["pair_id"])
                    n_pairs += 1

    shutil.copy2(args.census_md, args.output_dir / "census_v3.md")
    (args.output_dir / "queue.md").write_text(QUEUE_MD, encoding="utf-8")
    (args.output_dir / "README.md").write_text(
        "# HB P2.4 census review package v3\n\n"
        f"Selection rule: `{SELECTION_RULE}` with N={PAIRS_PER_CELL_ROLE} "
        "(no RNG; frozen manifest order), mirroring the R19/R20 audit-package "
        "discipline. Each sampled mother-pair ships every derived layer that "
        "exists for it (target_switch derives at L3 only, per Amendment A2) "
        "with questions, gold answers, and both side images.\n\n"
        "Contents: `census_v3.md` (standing generator census), `queue.md` "
        "(human gates queue — nothing here is self-certified), `samples/` "
        "(per-cell review items).\n\n"
        "Context numbers live in `reports/hier_p23_readout_v1.md` (attacker "
        "gates, blind floors, leak verification) and "
        "`reports/hier_p2_gate_readout_v1.md` (informativeness gates).\n",
        encoding="utf-8")

    zip_base = str(args.output_dir)
    archive = shutil.make_archive(zip_base, "zip",
                                  root_dir=args.output_dir.parent,
                                  base_dir=args.output_dir.name)
    git_hash = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True).stdout.strip()
    report = {"schema_version": "blind-gains.hier-census-review-package.v3",
              "selection_rule": SELECTION_RULE,
              "pairs_per_cell_role": PAIRS_PER_CELL_ROLE,
              "n_sampled_pairs": n_pairs, "n_images_copied": n_images,
              "sampled_pair_ids": sampled,
              "census_json_sha256": sha256_file(args.census_json),
              "census_md_sha256": sha256_file(args.census_md),
              "package_dir": str(args.output_dir),
              "archive": archive, "archive_sha256": sha256_file(Path(archive)),
              "git_hash": git_hash}
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({k: report[k] for k in
                      ("n_sampled_pairs", "n_images_copied", "archive",
                       "archive_sha256")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
