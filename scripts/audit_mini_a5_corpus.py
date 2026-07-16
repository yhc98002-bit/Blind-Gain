#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
from PIL import Image, ImageChops

from src.fliptrack.build_mini_a5_train import (
    SCHEMA_VERSION,
    TRAIN_TEMPLATE_IDS,
    _evaluation_identity,
    audit_template_disjointness,
)
from src.fliptrack.schema import sha256_file


EXPECTED_PAIRS = 3000
EXPECTED_TRAIN_ROWS = EXPECTED_PAIRS * 2


def _rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _under(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def audit_pair_files(pair: dict[str, Any], corpus_dir: Path) -> list[str]:
    errors: list[str] = []
    pair_id = str(pair.get("pair_group_uid", "missing"))
    paths = {
        field: Path(str(pair.get(field, "")))
        for field in (
            "image_a_path",
            "image_b_path",
            "changed_region_mask_a",
            "changed_region_mask_b",
        )
    }
    for field, path in paths.items():
        if not path.is_file():
            errors.append(f"{pair_id}: missing {field}: {path}")
        elif not _under(path, corpus_dir):
            errors.append(f"{pair_id}: {field} escapes corpus directory")
    if errors:
        return errors
    if sha256_file(paths["image_a_path"]) != pair.get("image_a_sha256"):
        errors.append(f"{pair_id}: image A hash mismatch")
    if sha256_file(paths["image_b_path"]) != pair.get("image_b_sha256"):
        errors.append(f"{pair_id}: image B hash mismatch")
    mask_hash_a = sha256_file(paths["changed_region_mask_a"])
    mask_hash_b = sha256_file(paths["changed_region_mask_b"])
    if mask_hash_a != pair.get("mask_sha256") or mask_hash_b != pair.get("mask_sha256"):
        errors.append(f"{pair_id}: mask hash mismatch")

    with Image.open(paths["image_a_path"]) as source_a, Image.open(
        paths["image_b_path"]
    ) as source_b, Image.open(paths["changed_region_mask_a"]) as source_mask_a, Image.open(
        paths["changed_region_mask_b"]
    ) as source_mask_b:
        image_a = source_a.convert("RGB")
        image_b = source_b.convert("RGB")
        mask_a = source_mask_a.convert("L")
        mask_b = source_mask_b.convert("L")
    if image_a.size != (720, 520) or image_b.size != (720, 520):
        errors.append(f"{pair_id}: image dimensions are not fixed at 720x520")
    observed = ImageChops.difference(image_a, image_b).convert("L").point(
        lambda value: 255 if value else 0
    )
    if observed.getbbox() is None:
        errors.append(f"{pair_id}: pair images are byte-equivalent in pixels")
    if ImageChops.difference(observed, mask_a).getbbox() is not None:
        errors.append(f"{pair_id}: mask A is not the exact changed-pixel mask")
    if ImageChops.difference(observed, mask_b).getbbox() is not None:
        errors.append(f"{pair_id}: mask B is not the exact changed-pixel mask")
    return errors


def build_audit(corpus_dir: Path, run_manifest_path: Path) -> dict[str, Any]:
    pairs_path = corpus_dir / "pairs.jsonl"
    train_path = corpus_dir / "train.jsonl"
    parquet_path = corpus_dir / "train.parquet"
    decon_path = corpus_dir / "decontamination.json"
    run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
    decon = json.loads(decon_path.read_text(encoding="utf-8"))
    pairs = _rows(pairs_path)
    train_rows = _rows(train_path)

    pair_ids = [str(row.get("pair_group_uid", "")) for row in pairs]
    template_counts = Counter(str(row.get("template_id", "")) for row in pairs)
    pair_errors: list[str] = []
    semantic_checks = True
    for pair in pairs:
        pair_errors.extend(audit_pair_files(pair, corpus_dir))
        semantic_checks = semantic_checks and (
            pair.get("schema_version") == SCHEMA_VERSION
            and str(pair.get("answer_a")) != str(pair.get("answer_b"))
            and pair.get("provenance", {}).get("answer_pointing_cue") is False
            and pair.get("verifier_results", {}).get("exact_by_construction") is True
            and pair.get("verifier_results", {}).get("changed_mask_is_exact_pixel_diff") is True
        )

    expected_training: list[dict[str, Any]] = []
    for pair in pairs:
        for member in ("a", "b"):
            expected_training.append(
                {
                    "problem": f"<image>{pair['question']}",
                    "answer": pair[f"answer_{member}"],
                    "images": [pair[f"image_{member}_path"]],
                    "pair_group_uid": pair["pair_group_uid"],
                    "pair_member": member,
                    "template_id": pair["template_id"],
                    "category": pair["category"],
                }
            )
    parquet_rows = pq.read_table(parquet_path).to_pylist()
    adjacency = all(
        train_rows[index]["pair_group_uid"] == train_rows[index + 1]["pair_group_uid"]
        and train_rows[index]["pair_member"] == "a"
        and train_rows[index + 1]["pair_member"] == "b"
        for index in range(0, len(train_rows) - 1, 2)
    )

    eval_manifest_paths = [Path(row["path"]) for row in decon["evaluation_manifests"]]
    eval_hashes_match = all(
        path.is_file() and sha256_file(path) == row["sha256"]
        for path, row in zip(eval_manifest_paths, decon["evaluation_manifests"], strict=True)
    )
    disjointness_error = None
    try:
        recomputed_disjointness = audit_template_disjointness(
            pairs, _evaluation_identity(eval_manifest_paths)
        )
    except (OSError, ValueError, KeyError) as error:
        disjointness_error = str(error)
        recomputed_disjointness = {}

    source_path = Path(decon["generator_path"])
    checks = {
        "run_manifest_complete_exit0": run_manifest.get("status") == "complete"
        and run_manifest.get("exit_code") == 0,
        "run_manifest_expected_commit": run_manifest.get("git_hash")
        == "46decacd889fa50067e96342bf627e0842809e6f",
        "pair_count_exact": len(pairs) == EXPECTED_PAIRS,
        "training_row_count_exact": len(train_rows) == EXPECTED_TRAIN_ROWS,
        "pair_ids_unique_nonempty": len(pair_ids) == len(set(pair_ids))
        and all(pair_ids),
        "template_counts_exact": template_counts
        == Counter({template: 1000 for template in TRAIN_TEMPLATE_IDS}),
        "all_pair_semantics_exact": semantic_checks,
        "all_file_hashes_and_masks_exact": not pair_errors,
        "training_projection_exact": train_rows == expected_training,
        "training_pair_adjacency_exact": adjacency,
        "parquet_jsonl_row_identity_exact": parquet_rows == train_rows,
        "decontamination_status_pass": decon.get("status") == "pass",
        "evaluation_manifest_hashes_exact": eval_hashes_match,
        "disjointness_recomputed_exact": disjointness_error is None
        and recomputed_disjointness == decon.get("disjointness"),
        "generator_hash_exact": source_path.is_file()
        and sha256_file(source_path) == decon.get("generator_sha256"),
    }
    errors = pair_errors[:100]
    if len(pair_errors) > 100:
        errors.append(f"{len(pair_errors) - 100} additional pair-file errors omitted")
    if disjointness_error:
        errors.append(disjointness_error)
    return {
        "schema_version": "blind-gains.mini-a5-corpus-audit.v1",
        "status": "pass" if all(checks.values()) and not errors else "fail",
        "checks": checks,
        "errors": errors,
        "corpus_dir": str(corpus_dir),
        "run_manifest": str(run_manifest_path),
        "counts": {
            "pairs": len(pairs),
            "training_rows": len(train_rows),
            "images": len(list((corpus_dir / "images").glob("*.png"))),
            "masks": len(list((corpus_dir / "masks").glob("*.png"))),
            "templates": dict(sorted(template_counts.items())),
        },
        "artifact_sha256": {
            "pairs_jsonl": sha256_file(pairs_path),
            "train_jsonl": sha256_file(train_path),
            "train_parquet": sha256_file(parquet_path),
            "decontamination_json": sha256_file(decon_path),
        },
        "semantic_side_assignment_counts": decon.get(
            "semantic_side_assignment_counts", {}
        ),
        "disjointness": recomputed_disjointness,
        "pair_file_error_count": len(pair_errors),
    }


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def render_markdown(payload: dict[str, Any], machine_path: Path) -> str:
    checks = [
        f"| `{name}` | `{'pass' if value else 'fail'}` |"
        for name, value in payload["checks"].items()
    ]
    return "\n".join(
        [
            "# Mini-A5 Corpus V1",
            "",
            "Status:",
            f"- Independent audit status: `{payload['status']}`.",
            "- This is an M6 data-readiness result, not authorization to train and not a PI gate decision.",
            "",
            "Evidence:",
            f"- Machine audit: `{machine_path}`.",
            f"- Corpus: `{payload['corpus_dir']}`.",
            f"- Counts: `{json.dumps(payload['counts'], sort_keys=True)}`.",
            f"- Artifact hashes: `{json.dumps(payload['artifact_sha256'], sort_keys=True)}`.",
            f"- Semantic side assignment: `{json.dumps(payload['semantic_side_assignment_counts'], sort_keys=True)}`.",
            f"- Recomputed disjointness: `{json.dumps(payload['disjointness'], sort_keys=True)}`.",
            "",
            "Checks:",
            "| Check | Result |",
            "| --- | --- |",
            *checks,
            "",
            "Problems:",
            f"- Audit errors: `{payload['errors']}`.",
            "- Step-0 reward statistics, an immutable advantage-tensor artifact, matched configs, and a GPU smoke remain pending.",
            "",
            "Decision:",
            "- Freeze this corpus and its hashes. Do not regenerate or replace failed/hard examples based on model performance.",
            "- Keep M6 blocked until every remaining registered prerequisite is audited.",
            "",
            "Next actions:",
            "- Prepare matched CP/member configs against this exact Parquet hash and compute step-0 reward-hit/variance statistics.",
            "- Run the isolated EasyR1 plumbing smoke when an eight-GPU single-node window becomes available.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-dir", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    if args.output_json.exists() or args.output_md.exists():
        raise FileExistsError("refusing to overwrite mini-A5 corpus audit")
    payload = build_audit(args.corpus_dir, args.run_manifest)
    _atomic_write(args.output_json, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    _atomic_write(args.output_md, render_markdown(payload, args.output_json))
    print(json.dumps({"status": payload["status"], "errors": payload["errors"]}))
    raise SystemExit(0 if payload["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
