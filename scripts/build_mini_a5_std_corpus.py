#!/usr/bin/env python3
"""Build the Mini-A5 arm-1 (standard GRPO) corpus: deterministic same-scene
unpaired projection of the frozen paired corpus.

Registered by docs/registered_mini_a5_gate1_completion_v1.md section 2 R1
(prework ledger T1): for every pair in the frozen corpus
data/mini_a5_train_v1, keep member a's rendering only and present it twice
per epoch as adjacent pseudo-members a/b of the synthetic uid
``std1_<original pair_group_uid>``. Image paths keep pointing at the frozen
data/mini_a5_train_v1/images/ files -- nothing is re-rendered or copied.

Outputs (refuses to overwrite):
- data/mini_a5_std_train_v1/train.parquet   (6,000 rows, 7-column schema)
- data/mini_a5_std_train_v1/train.jsonl     (same rows, sorted keys)
- reports/mini_a5_std_corpus_build_v1.json  (build report + projection audit)

The projection audit (acceptance condition 7 of the registration) checks:
row-for-row identity with the frozen member-a rows; synthetic-uid
disjointness from real uids; adjacency; 7-column schema; member-b image
exclusion; per-image sha256 against pairs.jsonl; scene exposure exactly
twice; jsonl/parquet row identity; byte-determinism of the parquet.

Adversarial fixture (I10): tests/test_build_mini_a5_std_corpus_fixture.py
plants naive projections (pair kept as-is, original uids kept, block layout,
member-b image swap, schema drift, tampered image bytes) and requires the
audit to reject every one of them.
"""
from __future__ import annotations

import argparse
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from src.fliptrack.schema import sha256_file

ROOT = Path(__file__).resolve().parents[1]

SCHEMA_VERSION = "blind-gains.mini-a5-std-corpus.v1"
SYNTHETIC_UID_PREFIX = "std1_"
COLUMNS = (
    "problem",
    "answer",
    "images",
    "pair_group_uid",
    "pair_member",
    "template_id",
    "category",
)
PARQUET_SCHEMA = pa.schema(
    [
        ("problem", pa.string()),
        ("answer", pa.string()),
        ("images", pa.list_(pa.string())),
        ("pair_group_uid", pa.string()),
        ("pair_member", pa.string()),
        ("template_id", pa.string()),
        ("category", pa.string()),
    ]
)

# Frozen inputs pinned by docs/registered_mini_a5_gate1_completion_v1.md section 5.
PINNED_SOURCE_HASHES = {
    "train.jsonl": "07d785ee6ae4a3b5325e12595f7830c5924e31c49565554f1e88b2abffc5fa5c",
    "train.parquet": "0b0f0965987d1c340c3ebd78da742c9d99b319b61524b5cb42960519fd9c9b28",
    "pairs.jsonl": "c592d8560cf3f5544fea36a12b3b52642d0faf0056c4ef9fddc0dde1f75f34bd",
}
DEFAULT_SOURCE_DIR = Path("data/mini_a5_train_v1")
DEFAULT_OUTPUT_DIR = Path("data/mini_a5_std_train_v1")
DEFAULT_REPORT = Path("reports/mini_a5_std_corpus_build_v1.json")
EXPECTED_PAIRS = 3000


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def project_std_rows(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The registered projection: member a kept per pair, presented twice as
    adjacent pseudo-members a/b of the synthetic uid std1_<original uid>."""
    if len(source_rows) % 2 != 0:
        raise ValueError(f"source corpus has odd row count {len(source_rows)}")
    projected: list[dict[str, Any]] = []
    for index in range(0, len(source_rows), 2):
        row_a, row_b = source_rows[index], source_rows[index + 1]
        uid = str(row_a["pair_group_uid"])
        if str(row_b["pair_group_uid"]) != uid:
            raise ValueError(f"source rows {index},{index + 1} are not an adjacent pair")
        if str(row_a["pair_member"]) != "a" or str(row_b["pair_member"]) != "b":
            raise ValueError(f"source pair {uid} is not ordered a,b")
        synthetic_uid = f"{SYNTHETIC_UID_PREFIX}{uid}"
        for pseudo_member in ("a", "b"):
            projected.append(
                {
                    "problem": str(row_a["problem"]),
                    "answer": str(row_a["answer"]),
                    "images": [str(path) for path in row_a["images"]],
                    "pair_group_uid": synthetic_uid,
                    "pair_member": pseudo_member,
                    "template_id": str(row_a["template_id"]),
                    "category": str(row_a["category"]),
                }
            )
    return projected


def parquet_bytes(rows: list[dict[str, Any]]) -> bytes:
    sink = io.BytesIO()
    pq.write_table(pa.Table.from_pylist(rows, schema=PARQUET_SCHEMA), sink)
    return sink.getvalue()


def audit_std_projection(
    source_rows: list[dict[str, Any]],
    std_rows: list[dict[str, Any]],
    pairs_rows: list[dict[str, Any]],
    corpus_root: Path,
    *,
    verify_image_hashes: bool = True,
) -> dict[str, Any]:
    """Projection audit per acceptance condition 7. Returns checks + errors."""
    errors: list[str] = []
    checks: dict[str, bool] = {}

    source_a_rows = [row for row in source_rows if str(row.get("pair_member")) == "a"]
    source_uids = [str(row["pair_group_uid"]) for row in source_a_rows]
    source_uid_set = set(str(row["pair_group_uid"]) for row in source_rows)
    image_a_sha = {}
    image_b_paths = set()
    for pair in pairs_rows:
        image_a_sha[str(pair["pair_group_uid"])] = (
            str(pair["image_a_path"]),
            str(pair["image_a_sha256"]),
        )
        image_b_paths.add(str(pair["image_b_path"]))

    checks["row_count_is_twice_pair_count"] = len(std_rows) == 2 * len(source_a_rows)
    if not checks["row_count_is_twice_pair_count"]:
        errors.append(
            f"row count {len(std_rows)} != 2 x {len(source_a_rows)} source member-a rows"
        )

    checks["seven_column_schema"] = all(
        tuple(row.keys()) == COLUMNS
        and isinstance(row["images"], list)
        and all(isinstance(item, str) for item in row["images"])
        for row in std_rows
    )
    if not checks["seven_column_schema"]:
        errors.append("at least one row deviates from the 7-column schema")

    adjacency_ok = len(std_rows) % 2 == 0
    identity_ok = True
    member_b_excluded = True
    synthetic_uids: list[str] = []
    if adjacency_ok:
        for index in range(0, min(len(std_rows), 2 * len(source_a_rows)), 2):
            first, second = std_rows[index], std_rows[index + 1]
            uid = str(first.get("pair_group_uid"))
            if (
                str(second.get("pair_group_uid")) != uid
                or str(first.get("pair_member")) != "a"
                or str(second.get("pair_member")) != "b"
            ):
                adjacency_ok = False
                errors.append(f"rows {index},{index + 1} are not an adjacent a/b pseudo-pair")
                break
            synthetic_uids.append(uid)
            pair_index = index // 2
            if pair_index >= len(source_a_rows):
                break
            source = source_a_rows[pair_index]
            expected_uid = f"{SYNTHETIC_UID_PREFIX}{source['pair_group_uid']}"
            if uid != expected_uid:
                identity_ok = False
                errors.append(
                    f"pair {pair_index}: synthetic uid {uid!r} != expected {expected_uid!r}"
                )
                break
            for copy_name, copy_row in (("first", first), ("second", second)):
                for field in ("problem", "answer", "template_id", "category"):
                    if str(copy_row.get(field)) != str(source[field]):
                        identity_ok = False
                        errors.append(
                            f"pair {pair_index} {copy_name} copy: field {field} deviates "
                            "from the frozen member-a row"
                        )
                if list(copy_row.get("images", [])) != [str(p) for p in source["images"]]:
                    identity_ok = False
                    errors.append(
                        f"pair {pair_index} {copy_name} copy: images deviate from the "
                        "frozen member-a rendering"
                    )
            if not identity_ok:
                break
    checks["adjacent_pseudo_pairs"] = adjacency_ok
    checks["row_for_row_identity_with_member_a"] = identity_ok

    for row in std_rows:
        for path in row.get("images", []):
            if str(path) in image_b_paths:
                member_b_excluded = False
                errors.append(f"member-b rendering referenced: {path}")
                break
        if not member_b_excluded:
            break
    checks["no_member_b_rendering_referenced"] = member_b_excluded

    uid_counter = Counter(str(row.get("pair_group_uid")) for row in std_rows)
    checks["synthetic_uids_disjoint_from_real_uids"] = not (
        set(uid_counter) & source_uid_set
    )
    if not checks["synthetic_uids_disjoint_from_real_uids"]:
        errors.append("synthetic uids collide with real frozen uids")
    checks["synthetic_uid_prefix_and_uniqueness"] = (
        all(uid.startswith(SYNTHETIC_UID_PREFIX) for uid in uid_counter)
        and all(count == 2 for count in uid_counter.values())
        and len(uid_counter) == len(source_uids)
    )
    if not checks["synthetic_uid_prefix_and_uniqueness"]:
        errors.append("synthetic uid prefix/uniqueness violated")

    exposure = Counter(path for row in std_rows for path in row.get("images", []))
    checks["every_kept_scene_exposed_exactly_twice"] = (
        len(exposure) == len(source_a_rows)
        and all(count == 2 for count in exposure.values())
    )
    if not checks["every_kept_scene_exposed_exactly_twice"]:
        errors.append("scene exposure is not exactly twice per kept rendering")

    if verify_image_hashes:
        hash_ok = True
        seen_paths: set[str] = set()
        for row in std_rows:
            for path in row.get("images", []):
                if path in seen_paths:
                    continue
                seen_paths.add(path)
                uid = str(row["pair_group_uid"])
                original_uid = uid[len(SYNTHETIC_UID_PREFIX):]
                expected = image_a_sha.get(original_uid)
                file_path = corpus_root / path
                if expected is None:
                    hash_ok = False
                    errors.append(f"{uid}: no pairs.jsonl record for {original_uid}")
                elif expected[0] != path:
                    hash_ok = False
                    errors.append(f"{uid}: image path {path} != pairs.jsonl member-a path")
                elif not file_path.is_file():
                    hash_ok = False
                    errors.append(f"{uid}: image file missing: {path}")
                elif sha256_file(file_path) != expected[1]:
                    hash_ok = False
                    errors.append(f"{uid}: image sha256 mismatch against pairs.jsonl")
        checks["image_sha256_matches_pairs_record"] = hash_ok
    else:
        checks["image_sha256_matches_pairs_record"] = False
        errors.append("image hash verification skipped")

    checks["status_pass"] = all(checks.values())
    return {"checks": checks, "errors": errors}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    source_dir = ROOT / args.source_dir
    output_dir = ROOT / args.output_dir
    report_path = ROOT / args.report
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing corpus: {output_dir}")
    if report_path.exists():
        raise FileExistsError(f"refusing to overwrite existing report: {report_path}")

    source_hashes = {
        name: sha256_file(source_dir / name) for name in PINNED_SOURCE_HASHES
    }
    for name, expected in PINNED_SOURCE_HASHES.items():
        if source_hashes[name] != expected:
            raise ValueError(
                f"frozen input {name} drifted: {source_hashes[name]} != registered {expected}"
            )

    source_rows = load_jsonl(source_dir / "train.jsonl")
    pairs_rows = load_jsonl(source_dir / "pairs.jsonl")
    if len(source_rows) != 2 * EXPECTED_PAIRS or len(pairs_rows) != EXPECTED_PAIRS:
        raise ValueError(
            f"frozen corpus counts unexpected: {len(source_rows)} rows, {len(pairs_rows)} pairs"
        )

    # Tie the projection to the parquet the trainer actually reads.
    source_parquet_rows = pq.read_table(source_dir / "train.parquet").to_pylist()
    if source_parquet_rows != source_rows:
        raise ValueError("frozen train.parquet rows differ from frozen train.jsonl rows")

    std_rows = project_std_rows(source_rows)

    first_bytes = parquet_bytes(std_rows)
    second_bytes = parquet_bytes(project_std_rows(source_rows))
    if first_bytes != second_bytes:
        raise RuntimeError("projection parquet serialization is not deterministic")

    audit = audit_std_projection(source_rows, std_rows, pairs_rows, ROOT)
    if not audit["checks"]["status_pass"]:
        raise RuntimeError(f"projection audit failed: {audit['errors'][:5]}")

    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "train.parquet").write_bytes(first_bytes)
    with (output_dir / "train.jsonl").open("w", encoding="utf-8") as handle:
        for row in std_rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")

    written_parquet_rows = pq.read_table(output_dir / "train.parquet").to_pylist()
    if written_parquet_rows != std_rows:
        raise RuntimeError("written parquet does not round-trip the projected rows")

    report = {
        "schema_version": SCHEMA_VERSION,
        "registration": "docs/registered_mini_a5_gate1_completion_v1.md#2-R1",
        "builder": "scripts/build_mini_a5_std_corpus.py",
        "source_dir": str(args.source_dir),
        "source_sha256": source_hashes,
        "output_dir": str(args.output_dir),
        "output_sha256": {
            "train.parquet": sha256_file(output_dir / "train.parquet"),
            "train.jsonl": sha256_file(output_dir / "train.jsonl"),
        },
        "rows": len(std_rows),
        "pseudo_pairs": len(std_rows) // 2,
        "kept_member": "a",
        "synthetic_uid_prefix": SYNTHETIC_UID_PREFIX,
        "parquet_serialization_deterministic": True,
        "projection_audit": audit,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "pass" if audit["checks"]["status_pass"] else "fail",
                "rows": len(std_rows),
                "train_parquet_sha256": report["output_sha256"]["train.parquet"],
            }
        )
    )


if __name__ == "__main__":
    main()
