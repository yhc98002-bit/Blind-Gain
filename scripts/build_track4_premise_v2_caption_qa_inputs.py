#!/usr/bin/env python3
# =============================================================================
# build_track4_premise_v2_caption_qa_inputs.py
#
# Derive the caption-QA release manifest + key that
# scripts/build_caption_qa_pairs.py (-> src/captioning/qa_pairs.py::
# build_caption_qa_rows) requires, from ONE source of truth:
#
#     data/track4_premise_v2_dev_v1/manifest_causal_pairs.jsonl
#
# WHY THIS EXISTS
#   The dev batch's attacker_release/manifest.jsonl + attacker_key.jsonl are
#   packaged deliberately thin for the E4 artifact-attacker gate, whose reader
#   (src/fliptrack/artifact_attackers.py::build_packaged_member_table) consumes
#   only pair_id / members[].member_id / members[].image_path from the release
#   and pair_id / template_id / members[].member_id / members[].source_side
#   from the key.  E3's caption-stress builder needs strictly more: release
#   .question and members[].image_sha256, key .source_pair_id and
#   members[].answer.  Widening the attacker-visible files with the question and
#   the answers would defeat the purpose of attacker packaging, so this exporter
#   writes a NEW, derived artifact at a NEW path instead.  It never reads,
#   writes, or mutates anything under attacker_release/ or attacker_key.jsonl.
#
# FAITHFULNESS CONTRACT
#   * Every emitted VALUE is copied from the source row.  Nothing is invented,
#     inferred, defaulted, or filled in from another file.
#   * The only synthesized values are structural: the member_id (which does not
#     exist in the source pair manifest at all) is "<pair_id>_<side>", matching
#     both the batch's own convention (scripts/build_track4_premise_v2_dev_batch
#     .py:673) and the image filenames on disk (<pair_id>_a.png), and the
#     image_path, which is the source's own absolute path re-expressed relative
#     to the emitted release directory.
#   * SIDE BINDING (the highest-risk decision; recorded in provenance):
#     source_side is the FILE-SUFFIX side, so member "<pair_id>_a" always
#     carries image_a_sha256/image_a_path AND answer_a.  This matches
#     src/fliptrack/package_v02.py:137-142, where source_side literally indexes
#     the source answer.  It deliberately does NOT apply
#     provenance.semantic_side_assignment_swapped, which the attacker key
#     applies for a different purpose (which side an artifact attacker should
#     call "a").  Applying that swap here while indexing answers by file suffix
#     would silently invert the answers of the 88 swapped pairs and make the
#     caption-stress gate measure garbage.  The answer always travels with the
#     member whose own image it describes.
#   * Refuses (nonzero exit, NOTHING written) on: a missing/null required source
#     field, a duplicate pair_id, a duplicate image sha256 across members, an
#     image path that is not a file on disk, a sha256 that disagrees with the
#     bytes on disk (unless --no-verify-image-hashes), or an output path that
#     already exists.
#   * Deterministic: byte-identical output for a given source manifest and a
#     given output-directory position.  No timestamps, no run ids, no host
#     names are emitted.
#
# OUTPUTS (all under --output-dir)
#   manifest.jsonl   release rows, schema blind-gains.track4-premise-v2-caption-qa-release.v1
#   key.jsonl        key rows,     schema blind-gains.track4-premise-v2-caption-qa-key.v1
#   provenance.json  source path + sha256, row counts, full field mapping
#
# USAGE
#   .venv/bin/python scripts/build_track4_premise_v2_caption_qa_inputs.py \
#     --source-manifest data/track4_premise_v2_dev_v1/manifest_causal_pairs.jsonl \
#     --output-dir data/track4_premise_v2_dev_v1/caption_qa_inputs
# =============================================================================
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

RELEASE_SCHEMA_VERSION = "blind-gains.track4-premise-v2-caption-qa-release.v1"
KEY_SCHEMA_VERSION = "blind-gains.track4-premise-v2-caption-qa-key.v1"
PROVENANCE_SCHEMA_VERSION = "blind-gains.track4-premise-v2-caption-qa-export-provenance.v1"

EXPORTER = "scripts/build_track4_premise_v2_caption_qa_inputs.py"
CONSUMER = (
    "scripts/build_caption_qa_pairs.py -> "
    "src/captioning/qa_pairs.py::build_caption_qa_rows"
)

RELEASE_FILENAME = "manifest.jsonl"
KEY_FILENAME = "key.jsonl"
PROVENANCE_FILENAME = "provenance.json"

# Present AND non-null on every source row, else refuse.
REQUIRED_NON_NULL = (
    "pair_id",
    "question",
    "template_id",
    "image_a_path",
    "image_b_path",
    "image_a_sha256",
    "image_b_sha256",
    "answer_a",
    "answer_b",
)
# Must be PRESENT (the source is authoritative about them) but may be null.
REQUIRED_PRESENT_NULLABLE = (
    "category",
    "catch_twin_id",
)
# May be absent entirely or null.  manifest_causal_pairs.jsonl carries no
# source_pair_id at all (verified: 0 of 160 rows have the key), because these
# pairs are constructed by the v2 generator rather than re-keyed from an upstream
# batch.  The consumer does str(key["source_pair_id"]) with no .get() and no
# default, so a missing/null value has to be resolved here; the fallback is
# pair_id, matching src/captioning/qa_pairs.py::build_private_caption_qa_rows.
# Every fallback is counted in the provenance block.
OPTIONAL_WITH_PAIR_ID_FALLBACK = "source_pair_id"

FIELD_MAPPING: dict[str, dict[str, str]] = {
    "release_row": {
        "schema_version": f"constant {RELEASE_SCHEMA_VERSION} (I15)",
        "pair_id": "source.pair_id",
        "question": "source.question",
        "members[i].member_id": (
            "synthesized structurally: f'{source.pair_id}_{side}' where side is the "
            "source field suffix; matches the batch's own member_id convention and the "
            "image filename suffix on disk"
        ),
        "members[i].image_path": (
            "source.image_{side}_path, re-expressed relative to the emitted release "
            "directory (os.path.relpath, lexical, no symlink resolution)"
        ),
        "members[i].image_sha256": "source.image_{side}_sha256 (verbatim)",
    },
    "key_row": {
        "schema_version": f"constant {KEY_SCHEMA_VERSION} (I15)",
        "pair_id": "source.pair_id",
        "source_pair_id": (
            "source.source_pair_id when present and non-null; otherwise source.pair_id, "
            "because the consumer does str(key['source_pair_id']) with no .get() and no "
            "default, so an absent/null value would become the literal string 'None'. "
            "Same fallback as the in-repo precedent "
            "src/captioning/qa_pairs.py::build_private_caption_qa_rows, which sets "
            "source_pair_id = pair_id. No upstream id is invented; every fallback is "
            "counted in source_pair_id_fallback_to_pair_id."
        ),
        "category": "source.category (verbatim, may be null)",
        "template_id": "source.template_id (verbatim)",
        "catch_twin_id": "source.catch_twin_id (verbatim, may be null)",
        "members[i].member_id": "same synthesized id as the matching release member",
        "members[i].source_side": (
            "the FILE-SUFFIX side ('a' for the member carrying image_a_*/answer_a). "
            "provenance.semantic_side_assignment_swapped is deliberately NOT applied: "
            "it labels attacker-gate side identity, and applying it here would invert "
            "the answers of the swapped pairs."
        ),
        "members[i].answer": "source.answer_{side} (verbatim, stringified)",
    },
    "not_exported": {
        "masks": (
            "changed_region_mask_a/b are not exported; the caption-QA consumer never "
            "reads mask fields"
        ),
        "other_source_fields": (
            "answers_equal, artifact_gate_score, blind_solvability_qhat, difficulty_knobs, "
            "hard_negatives, intervention_type, premise_*, provenance, scene_*, "
            "schema_version, split, verifier_results are not read by the consumer and are "
            "not exported"
        ),
    },
}


class ExportError(RuntimeError):
    """Raised for any refusal; the caller writes nothing and exits nonzero."""


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ExportError(f"{path}:{lineno}: not valid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise ExportError(f"{path}:{lineno}: row is not a JSON object")
            rows.append(row)
    return rows


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_export(
    source_rows: list[dict[str, Any]],
    source_dir: Path,
    output_dir: Path,
    *,
    verify_image_hashes: bool = True,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Pure builder: returns (release_rows, key_rows, stats). Raises ExportError."""
    if not source_rows:
        raise ExportError("source manifest contains no rows")

    source_dir = Path(os.path.abspath(source_dir))
    output_dir = Path(os.path.abspath(output_dir))

    release_rows: list[dict[str, Any]] = []
    key_rows: list[dict[str, Any]] = []
    seen_pairs: set[str] = set()
    seen_hashes: dict[str, str] = {}
    template_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    split_counts: dict[str, int] = {}
    swapped_counts: dict[str, int] = {"true": 0, "false": 0, "absent": 0}
    source_pair_id_absent = 0
    source_pair_id_null = 0

    for index, source in enumerate(source_rows):
        where = f"source row {index} (0-based)"
        for field in REQUIRED_NON_NULL:
            if field not in source:
                raise ExportError(f"{where}: missing required field {field!r}")
            if source[field] is None or str(source[field]).strip() == "":
                raise ExportError(f"{where}: required field {field!r} is null/empty")
        for field in REQUIRED_PRESENT_NULLABLE:
            if field not in source:
                raise ExportError(f"{where}: missing required field {field!r}")

        pair_id = str(source["pair_id"])
        where = f"pair {pair_id}"
        if pair_id in seen_pairs:
            raise ExportError(f"duplicate pair_id in source manifest: {pair_id}")
        seen_pairs.add(pair_id)

        release_members: list[dict[str, Any]] = []
        key_members: list[dict[str, Any]] = []
        for side in ("a", "b"):
            member_id = f"{pair_id}_{side}"
            raw_path = str(source[f"image_{side}_path"])
            image_abs = Path(raw_path)
            if not image_abs.is_absolute():
                image_abs = source_dir / raw_path
            image_abs = Path(os.path.abspath(image_abs))
            if not image_abs.is_file():
                raise ExportError(
                    f"{where} side {side}: image path is not a file on disk: {image_abs}"
                )
            digest = str(source[f"image_{side}_sha256"])
            if digest in seen_hashes:
                raise ExportError(
                    f"{where} side {side}: image sha256 {digest} already used by "
                    f"{seen_hashes[digest]}; the caption-QA consumer refuses reused hashes"
                )
            seen_hashes[digest] = f"{member_id}"
            if verify_image_hashes:
                actual = _sha256_file(image_abs)
                if actual != digest:
                    raise ExportError(
                        f"{where} side {side}: manifest sha256 {digest} != on-disk sha256 "
                        f"{actual} for {image_abs}"
                    )
            rel_path = os.path.relpath(image_abs, output_dir)
            release_members.append(
                {
                    "member_id": member_id,
                    "image_path": rel_path,
                    "image_sha256": digest,
                }
            )
            key_members.append(
                {
                    "member_id": member_id,
                    "source_side": side,
                    "answer": str(source[f"answer_{side}"]),
                }
            )

        release_rows.append(
            {
                "schema_version": RELEASE_SCHEMA_VERSION,
                "pair_id": pair_id,
                "question": str(source["question"]),
                "members": release_members,
            }
        )
        if OPTIONAL_WITH_PAIR_ID_FALLBACK not in source:
            source_pair_id_absent += 1
            resolved_source_pair_id = pair_id
        elif source[OPTIONAL_WITH_PAIR_ID_FALLBACK] is None:
            source_pair_id_null += 1
            resolved_source_pair_id = pair_id
        else:
            resolved_source_pair_id = str(source[OPTIONAL_WITH_PAIR_ID_FALLBACK])
        key_rows.append(
            {
                "schema_version": KEY_SCHEMA_VERSION,
                "pair_id": pair_id,
                "source_pair_id": resolved_source_pair_id,
                "category": source["category"],
                "template_id": source["template_id"],
                "catch_twin_id": source["catch_twin_id"],
                "members": key_members,
            }
        )

        template = str(source["template_id"])
        template_counts[template] = template_counts.get(template, 0) + 1
        category = str(source["category"])
        category_counts[category] = category_counts.get(category, 0) + 1
        split = str(source.get("split"))
        split_counts[split] = split_counts.get(split, 0) + 1
        provenance = source.get("provenance")
        swapped = provenance.get("semantic_side_assignment_swapped") if isinstance(provenance, dict) else None
        if swapped is True:
            swapped_counts["true"] += 1
        elif swapped is False:
            swapped_counts["false"] += 1
        else:
            swapped_counts["absent"] += 1

    stats = {
        "n_pairs": len(release_rows),
        "n_members": 2 * len(release_rows),
        "n_distinct_image_sha256": len(seen_hashes),
        "template_counts": template_counts,
        "category_counts": category_counts,
        "split_counts": split_counts,
        "semantic_side_assignment_swapped_counts": swapped_counts,
        "source_pair_id_absent_in_source": source_pair_id_absent,
        "source_pair_id_null_in_source": source_pair_id_null,
        "source_pair_id_fallback_to_pair_id": source_pair_id_absent + source_pair_id_null,
        "image_hashes_verified_against_disk": bool(verify_image_hashes),
    }
    return release_rows, key_rows, stats


def build_provenance(
    source_manifest: str,
    source_sha256: str,
    source_bytes: int,
    source_rows: int,
    stats: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "exporter": EXPORTER,
        "consumer": CONSUMER,
        "source_manifest": source_manifest,
        "source_manifest_sha256": source_sha256,
        "source_manifest_bytes": source_bytes,
        "source_rows": source_rows,
        "release_manifest_file": RELEASE_FILENAME,
        "key_file": KEY_FILENAME,
        "release_row_schema_version": RELEASE_SCHEMA_VERSION,
        "key_row_schema_version": KEY_SCHEMA_VERSION,
        "image_path_convention": (
            "relative to the directory holding this release manifest; the consumer "
            "resolves str(release_dir / image_path)"
        ),
        "derived_from": [source_manifest],
        "mutates_source_batch": False,
        "reads_attacker_release_or_key": False,
        "side_binding_note": FIELD_MAPPING["key_row"]["members[i].source_side"],
        "source_pair_id_note": FIELD_MAPPING["key_row"]["source_pair_id"],
        "field_mapping": FIELD_MAPPING,
        **stats,
    }


def _publish(output_dir: Path, payloads: dict[str, str]) -> None:
    finals = {name: output_dir / name for name in payloads}
    for final_path in finals.values():
        if final_path.exists():
            raise ExportError(f"refusing to overwrite caption-QA export artifact: {final_path}")
    partials = {name: Path(f"{path}.partial") for name, path in finals.items()}
    for partial_path in partials.values():
        if partial_path.exists():
            raise ExportError(f"stale caption-QA export partial requires inspection: {partial_path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    published: list[Path] = []
    try:
        for name, text in payloads.items():
            partials[name].write_text(text, encoding="utf-8")
        for name in payloads:
            os.replace(partials[name], finals[name])
            published.append(finals[name])
    except BaseException:
        for partial_path in partials.values():
            partial_path.unlink(missing_ok=True)
        for final_path in published:
            final_path.unlink(missing_ok=True)
        raise


def export_caption_qa_inputs(
    source_manifest: Path,
    output_dir: Path,
    *,
    verify_image_hashes: bool = True,
) -> dict[str, Any]:
    source_manifest = Path(source_manifest)
    output_dir = Path(output_dir)
    if not source_manifest.is_file():
        raise ExportError(f"source manifest is not a file: {source_manifest}")
    source_rows = _read_jsonl(source_manifest)
    release_rows, key_rows, stats = build_export(
        source_rows,
        source_manifest.parent,
        output_dir,
        verify_image_hashes=verify_image_hashes,
    )
    provenance = build_provenance(
        str(source_manifest),
        _sha256_file(source_manifest),
        source_manifest.stat().st_size,
        len(source_rows),
        stats,
    )
    payloads = {
        RELEASE_FILENAME: "".join(
            json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n" for row in release_rows
        ),
        KEY_FILENAME: "".join(
            json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n" for row in key_rows
        ),
        PROVENANCE_FILENAME: json.dumps(provenance, indent=2, sort_keys=True) + "\n",
    }
    _publish(output_dir, payloads)
    return provenance


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Derive the E3 caption-QA release manifest + key for the track-4 premise-v2 "
            "dev batch from manifest_causal_pairs.jsonl only."
        )
    )
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--no-verify-image-hashes",
        dest="verify_image_hashes",
        action="store_false",
        help="skip re-hashing every referenced image (default: verify against disk)",
    )
    parser.set_defaults(verify_image_hashes=True)
    args = parser.parse_args(argv)
    try:
        provenance = export_caption_qa_inputs(
            args.source_manifest,
            args.output_dir,
            verify_image_hashes=args.verify_image_hashes,
        )
    except ExportError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(provenance, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
