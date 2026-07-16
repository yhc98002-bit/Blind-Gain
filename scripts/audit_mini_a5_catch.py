#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops

from scripts.audit_mini_a5_corpus import audit_pair_files
from src.fliptrack.build_mini_a5_catch import (
    CATCH_TEMPLATE_IDS,
    SCHEMA_VERSION,
    _identity,
    _jsonl,
    _overlap,
)
from src.fliptrack.build_mini_a5_train import _evaluation_identity
from src.fliptrack.schema import sha256_file


EXPECTED_PAIRS = 300
EXPECTED_PER_TEMPLATE = 100


def recorded_zero_overlap_is_complete(decon: dict[str, Any]) -> bool:
    overlap_fields = {"template_ids", "pair_ids", "image_hashes"}
    return all(
        set(decon.get(source, {})) == overlap_fields
        and all(count == 0 for count in decon[source].values())
        for source in ("training_overlap", "evaluation_overlap")
    )


def audit_pair_semantics(pair: dict[str, Any], corpus_dir: Path) -> list[str]:
    pair_id = str(pair.get("pair_group_uid", "missing"))
    errors = audit_pair_files(pair, corpus_dir)
    verifier = pair.get("verifier_results", {})
    provenance = pair.get("provenance", {})
    answer_a = str(pair.get("answer_a", ""))
    answer_b = str(pair.get("answer_b", ""))
    target_a = str(verifier.get("target_fact_a", ""))
    target_b = str(verifier.get("target_fact_b", ""))
    if not answer_a or answer_a != answer_b:
        errors.append(f"{pair_id}: catch answer is not nonempty and preserved")
    if (target_a, target_b) != (answer_a, answer_b):
        errors.append(f"{pair_id}: target facts do not equal the preserved answers")
    required_true = (
        "answer_preserved",
        "target_fact_preserved",
        "target_region_pixel_invariant",
        "exact_by_construction",
        "changed_mask_is_exact_pixel_diff",
    )
    for field in required_true:
        if verifier.get(field) is not True:
            errors.append(f"{pair_id}: verifier field {field} is not true")
    if provenance.get("answer_pointing_cue") is not False:
        errors.append(f"{pair_id}: answer-pointing cue is not explicitly false")
    if provenance.get("selection_on_model_performance") is not False:
        errors.append(f"{pair_id}: model-performance selection is not explicitly false")
    if pair.get("template_id") not in CATCH_TEMPLATE_IDS:
        errors.append(f"{pair_id}: unregistered catch template")
    if pair.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{pair_id}: schema version mismatch")

    box = verifier.get("target_region_xyxy")
    if (
        not isinstance(box, list)
        or len(box) != 4
        or not all(isinstance(value, int) for value in box)
        or not (0 <= box[0] < box[2] <= 720)
        or not (0 <= box[1] < box[3] <= 520)
    ):
        errors.append(f"{pair_id}: invalid target-region bounds")
        return errors
    image_a_path = Path(str(pair.get("image_a_path", "")))
    image_b_path = Path(str(pair.get("image_b_path", "")))
    if image_a_path.is_file() and image_b_path.is_file():
        with Image.open(image_a_path) as source_a, Image.open(image_b_path) as source_b:
            target_difference = ImageChops.difference(
                source_a.convert("RGB").crop(tuple(box)),
                source_b.convert("RGB").crop(tuple(box)),
            )
        if target_difference.getbbox() is not None:
            errors.append(f"{pair_id}: nuisance edit changes the queried pixel region")
    return errors


def audit_identity_disjointness(
    catch_identity: dict[str, set[str]],
    training_identity: dict[str, set[str]],
    evaluation_identity: dict[str, set[str]],
) -> tuple[dict[str, dict[str, list[str]]], list[str]]:
    overlaps = {
        "training": _overlap(catch_identity, training_identity),
        "evaluation": _overlap(catch_identity, evaluation_identity),
    }
    errors = [
        f"catch/{source} {field} overlap: {values}"
        for source, fields in overlaps.items()
        for field, values in fields.items()
        if values
    ]
    return overlaps, errors


def build_audit(corpus_dir: Path, generation_manifest_path: Path) -> dict[str, Any]:
    pairs_path = corpus_dir / "pairs.jsonl"
    decon_path = corpus_dir / "decontamination.json"
    generation_manifest = json.loads(
        generation_manifest_path.read_text(encoding="utf-8")
    )
    decon = json.loads(decon_path.read_text(encoding="utf-8"))
    pairs = _jsonl(pairs_path)

    pair_ids = [str(row.get("pair_group_uid", "")) for row in pairs]
    image_hashes = [
        str(value)
        for row in pairs
        for value in (row.get("image_a_sha256", ""), row.get("image_b_sha256", ""))
    ]
    template_counts = Counter(str(row.get("template_id", "")) for row in pairs)
    pair_errors: list[str] = []
    for pair in pairs:
        pair_errors.extend(audit_pair_semantics(pair, corpus_dir))

    training_record = decon.get("training_manifest", {})
    training_path = Path(str(training_record.get("path", "")))
    eval_records = decon.get("evaluation_manifests", [])
    eval_paths = [Path(str(row.get("path", ""))) for row in eval_records]
    source_path = Path(str(decon.get("generator_path", "")))
    source_hash_exact = source_path.is_file() and sha256_file(source_path) == decon.get(
        "generator_sha256"
    )
    training_hash_exact = training_path.is_file() and sha256_file(
        training_path
    ) == training_record.get("sha256")
    eval_hashes_exact = bool(eval_records) and all(
        path.is_file() and sha256_file(path) == record.get("sha256")
        for path, record in zip(eval_paths, eval_records, strict=True)
    )

    overlap_errors: list[str] = []
    overlaps: dict[str, dict[str, list[str]]] = {}
    if training_hash_exact and eval_hashes_exact:
        catch_identity = _identity(pairs, "pair_group_uid")
        training_identity = _identity(_jsonl(training_path), "pair_group_uid")
        overlaps, overlap_errors = audit_identity_disjointness(
            catch_identity,
            training_identity,
            _evaluation_identity(eval_paths),
        )
    else:
        overlap_errors.append("source manifests are absent or their hashes changed")

    recorded_zero_overlap = recorded_zero_overlap_is_complete(decon)
    expected_artifacts = {
        str(corpus_dir / "pairs.jsonl"),
        str(corpus_dir / "decontamination.json"),
    }
    checks = {
        "generation_manifest_complete_exit0": generation_manifest.get("status")
        == "complete"
        and generation_manifest.get("exit_code") == 0,
        "generation_manifest_identity": generation_manifest.get("job_type")
        == "m6_mini_a5_catch_generation"
        and generation_manifest.get("n_pairs_expected") == EXPECTED_PAIRS,
        "generation_artifacts_registered": expected_artifacts.issubset(
            set(generation_manifest.get("expected_artifacts", []))
        ),
        "pair_count_exact": len(pairs) == EXPECTED_PAIRS,
        "pair_ids_unique_nonempty": len(pair_ids) == len(set(pair_ids))
        and all(pair_ids),
        "image_hashes_unique_nonempty": len(image_hashes) == len(set(image_hashes))
        and all(image_hashes),
        "template_counts_exact": template_counts
        == Counter({template: EXPECTED_PER_TEMPLATE for template in CATCH_TEMPLATE_IDS}),
        "pair_semantics_files_masks_and_target_regions_exact": not pair_errors,
        "image_file_count_exact": len(list((corpus_dir / "images").glob("*.png")))
        == EXPECTED_PAIRS * 2,
        "mask_file_count_exact": len(list((corpus_dir / "masks").glob("*.png")))
        == EXPECTED_PAIRS * 2,
        "decontamination_status_pass": decon.get("status") == "pass",
        "decontamination_templates_and_counts_exact": decon.get(
            "catch_template_ids"
        )
        == sorted(CATCH_TEMPLATE_IDS)
        and decon.get("template_counts")
        == {template: EXPECTED_PER_TEMPLATE for template in CATCH_TEMPLATE_IDS},
        "source_generator_hash_exact": source_hash_exact,
        "training_manifest_hash_exact": training_hash_exact,
        "evaluation_manifest_hashes_exact": eval_hashes_exact,
        "recorded_zero_overlap": recorded_zero_overlap,
        "disjointness_recomputed_zero": not overlap_errors,
        "no_model_performance_selection": decon.get("selection_on_model_performance")
        is False,
    }
    errors = (pair_errors + overlap_errors)[:100]
    if len(pair_errors) + len(overlap_errors) > 100:
        errors.append(
            f"{len(pair_errors) + len(overlap_errors) - 100} additional errors omitted"
        )
    side_counts = Counter(
        str(row.get("provenance", {}).get("nuisance_side_assignment_swapped"))
        for row in pairs
    )
    return {
        "schema_version": "blind-gains.mini-a5-catch-audit.v1",
        "status": "pass" if all(checks.values()) and not errors else "fail",
        "checks": checks,
        "errors": errors,
        "corpus_dir": str(corpus_dir),
        "generation_manifest": str(generation_manifest_path),
        "counts": {
            "pairs": len(pairs),
            "images": len(list((corpus_dir / "images").glob("*.png"))),
            "masks": len(list((corpus_dir / "masks").glob("*.png"))),
            "templates": dict(sorted(template_counts.items())),
            "side_assignment": dict(sorted(side_counts.items())),
        },
        "artifact_sha256": {
            "pairs_jsonl": sha256_file(pairs_path),
            "decontamination_json": sha256_file(decon_path),
        },
        "recomputed_overlaps": overlaps,
        "pair_error_count": len(pair_errors),
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
    rows = [
        f"| `{name}` | `{'pass' if result else 'fail'}` |"
        for name, result in payload["checks"].items()
    ]
    return "\n".join(
        [
            "# Mini-A5 Answer-Preserving Catch Set V1",
            "",
            "Status:",
            f"- Independent mechanical audit: `{payload['status']}`.",
            "- This result establishes catch-set data readiness only. It does not authorize an M6 optimizer step and is not a PI gate decision.",
            "",
            "Evidence:",
            f"- Machine audit: `{machine_path}`.",
            f"- Catch set: `{payload['corpus_dir']}`.",
            f"- Generation manifest: `{payload['generation_manifest']}`.",
            f"- Counts: `{json.dumps(payload['counts'], sort_keys=True)}`.",
            f"- Hashes: `{json.dumps(payload['artifact_sha256'], sort_keys=True)}`.",
            f"- Recomputed overlaps: `{json.dumps(payload['recomputed_overlaps'], sort_keys=True)}`.",
            "",
            "Checks:",
            "| Check | Result |",
            "| --- | --- |",
            *rows,
            "",
            "Problems:",
            f"- Errors: `{payload['errors']}`.",
            "",
            "Decision:",
            "- Freeze these 300 held-out-template catch pairs. Both members retain the answer while a nonqueried visual nuisance changes.",
            "- No pair was selected or replaced using model performance.",
            "",
            "Next actions:",
            "- Bind these artifact hashes into the Mini-A5 registration marker.",
            "- Run the separately registered real EasyR1 plumbing smoke before either main M6 arm is launched.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-dir", type=Path, required=True)
    parser.add_argument("--generation-manifest", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    if args.output_json.exists() or args.output_md.exists():
        raise FileExistsError("refusing to overwrite mini-A5 catch audit")
    payload = build_audit(args.corpus_dir, args.generation_manifest)
    _atomic_write(args.output_json, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    _atomic_write(args.output_md, render_markdown(payload, args.output_json))
    print(json.dumps({"status": payload["status"], "errors": payload["errors"]}))
    raise SystemExit(0 if payload["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
