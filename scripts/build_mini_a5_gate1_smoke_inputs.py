#!/usr/bin/env python3
"""Build the Gate-1 completion T7 inputs: per-arm 48-row plumbing-smoke
subsets and per-arm 192-pseudo-pair step-0 reward-audit samples.

Registered by docs/registered_mini_a5_gate1_completion_v1.md prework ledger
T7. Both new corpora (arm 1 std, arm 3 necessity) are deterministic frozen
artifacts; the smoke and step-0 inputs are deterministic contiguous slices of
them, so plumbing evidence is collected on exactly the data geometry the main
arms will train on:

- smoke subset  = pseudo-pairs 0..23   (48 rows, adjacency preserved)
- step-0 sample = pseudo-pairs 24..215 (192 pseudo-pairs, disjoint from the
  smoke slice, mirroring the frozen-corpus step-0 sample size)

The step-0 sample uses a per-member schema (v2) because necessity pseudo-pairs
draw their two members i.i.d. -- the members of one synthetic uid may carry
different questions, templates, and renderings, which the frozen-corpus
step-0 schema cannot represent.

Outputs (refuses to overwrite):
- data/mini_a5_std_plumbing_train_v1.jsonl
- data/mini_a5_necessity_plumbing_train_v1.jsonl
- data/mini_a5_std_step0_sample_v1.jsonl
- data/mini_a5_necessity_step0_sample_v1.jsonl
- reports/mini_a5_gate1_smoke_inputs_build_v1.json

Audit: slice rows byte-identical to the pinned corpus rows at the registered
offsets; adjacency; slice disjointness; per-image sha256 resolved against the
frozen pairs.jsonl record for the correct source member (std maps every
member to the kept member-a rendering; necessity maps through the committed
source_map.jsonl); counts exact.

Adversarial fixture (I10): tests/test_build_mini_a5_gate1_smoke_inputs_fixture.py.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from src.fliptrack.schema import sha256_file

ROOT = Path(__file__).resolve().parents[1]

SCHEMA_VERSION = "blind-gains.mini-a5-gate1-smoke-inputs.v1"
STEP0_SCHEMA_VERSION = "blind-gains.mini-a5-gate1-step0-pair.v2"
SMOKE_PAIRS = 24
STEP0_PAIRS = 192
STEP0_OFFSET_PAIRS = SMOKE_PAIRS  # step-0 slice starts where the smoke slice ends

COLUMNS = (
    "problem",
    "answer",
    "images",
    "pair_group_uid",
    "pair_member",
    "template_id",
    "category",
)

# Pinned inputs: the committed Gate-1 corpora and the frozen pair records.
PINNED_HASHES = {
    "data/mini_a5_std_train_v1/train.parquet": (
        "b06373f5fd259e9c77bb66c3332f4ddf1e26a31dd3150e0fd025e3142fe623aa"
    ),
    "data/mini_a5_necessity_train_v1/train.parquet": (
        "205ca7fd007cc03086174ebd25ec0b22d2c76bb68377b87260b51252976fc4c9"
    ),
    "data/mini_a5_necessity_train_v1/source_map.jsonl": (
        "1f60357a91389090f37a6cef4c8223d6aa56208712f6142b606c2797ccd4e448"
    ),
    "data/mini_a5_train_v1/pairs.jsonl": (
        "c592d8560cf3f5544fea36a12b3b52642d0faf0056c4ef9fddc0dde1f75f34bd"
    ),
}
STD_UID_PREFIX = "std1_"
DEFAULT_REPORT = Path("reports/mini_a5_gate1_smoke_inputs_build_v1.json")

ARM_OUTPUTS = {
    "std": {
        "smoke": Path("data/mini_a5_std_plumbing_train_v1.jsonl"),
        "step0": Path("data/mini_a5_std_step0_sample_v1.jsonl"),
        "corpus": Path("data/mini_a5_std_train_v1/train.parquet"),
    },
    "necessity": {
        "smoke": Path("data/mini_a5_necessity_plumbing_train_v1.jsonl"),
        "step0": Path("data/mini_a5_necessity_step0_sample_v1.jsonl"),
        "corpus": Path("data/mini_a5_necessity_train_v1/train.parquet"),
    },
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def pairs_image_index(pairs_rows: list[dict[str, Any]]) -> dict[str, tuple[str, str]]:
    """(source uid:member) -> (image path, image sha256) from frozen pairs.jsonl."""
    index: dict[str, tuple[str, str]] = {}
    for pair in pairs_rows:
        uid = str(pair["pair_group_uid"])
        for member in ("a", "b"):
            index[f"{uid}:{member}"] = (
                str(pair[f"image_{member}_path"]),
                str(pair[f"image_{member}_sha256"]),
            )
    return index


def source_qid_for_row(
    arm: str, row_index: int, row: dict[str, Any], source_map: list[dict[str, Any]]
) -> str:
    """The frozen-corpus identity behind corpus row row_index of the arm."""
    if arm == "std":
        uid = str(row["pair_group_uid"])
        if not uid.startswith(STD_UID_PREFIX):
            raise ValueError(f"std row {row_index}: uid {uid!r} lacks {STD_UID_PREFIX!r}")
        return f"{uid[len(STD_UID_PREFIX):]}:a"
    record = source_map[row_index]
    if int(record["slot"]) != row_index:
        raise ValueError(f"necessity source_map slot mismatch at {row_index}")
    return str(record["source_qid"])


def build_smoke_subset(corpus_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The registered smoke slice: pseudo-pairs 0..23 kept byte-identical."""
    return [dict(row) for row in corpus_rows[: 2 * SMOKE_PAIRS]]


def build_step0_sample(
    arm: str,
    corpus_rows: list[dict[str, Any]],
    source_map: list[dict[str, Any]],
    image_index: dict[str, tuple[str, str]],
) -> list[dict[str, Any]]:
    """The registered step-0 slice: pseudo-pairs 24..215, per-member schema."""
    sample: list[dict[str, Any]] = []
    for pair_offset in range(STEP0_PAIRS):
        pair_index = STEP0_OFFSET_PAIRS + pair_offset
        first = corpus_rows[2 * pair_index]
        second = corpus_rows[2 * pair_index + 1]
        uid = str(first["pair_group_uid"])
        if str(second["pair_group_uid"]) != uid:
            raise ValueError(f"pseudo-pair {pair_index}: rows are not adjacent")
        if str(first["pair_member"]) != "a" or str(second["pair_member"]) != "b":
            raise ValueError(f"pseudo-pair {pair_index}: members are not a,b")
        record: dict[str, Any] = {
            "schema_version": STEP0_SCHEMA_VERSION,
            "arm": arm,
            "pair_group_uid": uid,
        }
        for member, row, row_index in (
            ("a", first, 2 * pair_index),
            ("b", second, 2 * pair_index + 1),
        ):
            source_qid = source_qid_for_row(arm, row_index, row, source_map)
            image_path, image_sha = image_index[source_qid]
            if [image_path] != [str(p) for p in row["images"]]:
                raise ValueError(
                    f"pseudo-pair {pair_index} member {member}: image path "
                    f"{row['images']} != frozen record {image_path}"
                )
            record[f"question_{member}"] = str(row["problem"])
            record[f"answer_{member}"] = str(row["answer"])
            record[f"image_{member}_path"] = image_path
            record[f"image_{member}_sha256"] = image_sha
            record[f"template_id_{member}"] = str(row["template_id"])
            record[f"category_{member}"] = str(row["category"])
            record[f"source_qid_{member}"] = source_qid
        sample.append(record)
    return sample


def audit_gate1_smoke_inputs(
    arm: str,
    corpus_rows: list[dict[str, Any]],
    smoke_rows: list[dict[str, Any]],
    step0_sample: list[dict[str, Any]],
    source_map: list[dict[str, Any]],
    image_index: dict[str, tuple[str, str]],
) -> dict[str, Any]:
    errors: list[str] = []
    checks: dict[str, bool] = {}

    checks["smoke_row_count_exact"] = len(smoke_rows) == 2 * SMOKE_PAIRS
    checks["step0_pair_count_exact"] = len(step0_sample) == STEP0_PAIRS
    if not checks["smoke_row_count_exact"]:
        errors.append(f"smoke subset has {len(smoke_rows)} rows != {2 * SMOKE_PAIRS}")
    if not checks["step0_pair_count_exact"]:
        errors.append(f"step-0 sample has {len(step0_sample)} pairs != {STEP0_PAIRS}")

    identical = checks["smoke_row_count_exact"]
    for index, row in enumerate(smoke_rows if identical else []):
        if tuple(row.keys()) != COLUMNS or row != corpus_rows[index]:
            identical = False
            errors.append(
                f"smoke row {index} is not byte-identical to corpus row {index}"
            )
            break
    checks["smoke_rows_identical_to_corpus_prefix"] = identical

    adjacency = identical
    for pair_index in range(SMOKE_PAIRS) if adjacency else []:
        first, second = smoke_rows[2 * pair_index], smoke_rows[2 * pair_index + 1]
        if (
            str(first["pair_group_uid"]) != str(second["pair_group_uid"])
            or str(first["pair_member"]) != "a"
            or str(second["pair_member"]) != "b"
        ):
            adjacency = False
            errors.append(f"smoke pseudo-pair {pair_index} is not adjacent a/b")
            break
    checks["smoke_adjacency_preserved"] = adjacency

    step0_ok = checks["step0_pair_count_exact"]
    smoke_uids = {str(row["pair_group_uid"]) for row in smoke_rows}
    for offset, record in enumerate(step0_sample if step0_ok else []):
        pair_index = STEP0_OFFSET_PAIRS + offset
        first = corpus_rows[2 * pair_index]
        second = corpus_rows[2 * pair_index + 1]
        uid = str(record.get("pair_group_uid"))
        if uid != str(first["pair_group_uid"]) or uid in smoke_uids:
            step0_ok = False
            errors.append(
                f"step-0 pair {offset}: uid {uid!r} misaligned or overlaps the smoke slice"
            )
            break
        content_ok = True
        for member, row, row_index in (
            ("a", first, 2 * pair_index),
            ("b", second, 2 * pair_index + 1),
        ):
            source_qid = source_qid_for_row(arm, row_index, row, source_map)
            expected_path, expected_sha = image_index[source_qid]
            if (
                str(record.get(f"question_{member}")) != str(row["problem"])
                or str(record.get(f"answer_{member}")) != str(row["answer"])
                or str(record.get(f"template_id_{member}")) != str(row["template_id"])
                or str(record.get(f"category_{member}")) != str(row["category"])
                or str(record.get(f"image_{member}_path")) != expected_path
                or str(record.get(f"image_{member}_sha256")) != expected_sha
                or str(record.get(f"source_qid_{member}")) != source_qid
            ):
                content_ok = False
                break
        if not content_ok:
            step0_ok = False
            errors.append(
                f"step-0 pair {offset} member {member}: content or frozen image "
                "record deviates from the corpus slice"
            )
            break
    checks["step0_pairs_identical_to_registered_slice"] = step0_ok

    checks["status_pass"] = all(checks.values())
    return {"checks": checks, "errors": errors}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    report_path = ROOT / args.report
    if report_path.exists():
        raise FileExistsError(f"refusing to overwrite report: {report_path}")
    for arm, outputs in ARM_OUTPUTS.items():
        for kind in ("smoke", "step0"):
            if (ROOT / outputs[kind]).exists():
                raise FileExistsError(
                    f"refusing to overwrite existing {arm} {kind}: {outputs[kind]}"
                )

    observed_hashes = {
        name: sha256_file(ROOT / name) for name in PINNED_HASHES
    }
    for name, expected in PINNED_HASHES.items():
        if observed_hashes[name] != expected:
            raise ValueError(
                f"pinned input {name} drifted: {observed_hashes[name]} != {expected}"
            )

    pairs_rows = load_jsonl(ROOT / "data/mini_a5_train_v1/pairs.jsonl")
    image_index = pairs_image_index(pairs_rows)
    necessity_source_map = load_jsonl(
        ROOT / "data/mini_a5_necessity_train_v1/source_map.jsonl"
    )

    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "registration": "docs/registered_mini_a5_gate1_completion_v1.md#6-T7",
        "builder": "scripts/build_mini_a5_gate1_smoke_inputs.py",
        "pinned_sha256": observed_hashes,
        "smoke_pairs": SMOKE_PAIRS,
        "step0_pairs": STEP0_PAIRS,
        "step0_offset_pairs": STEP0_OFFSET_PAIRS,
        "arms": {},
    }
    for arm, outputs in ARM_OUTPUTS.items():
        corpus_rows = pq.read_table(ROOT / outputs["corpus"]).to_pylist()
        source_map = necessity_source_map if arm == "necessity" else []
        smoke_rows = build_smoke_subset(corpus_rows)
        step0_sample = build_step0_sample(arm, corpus_rows, source_map, image_index)
        audit = audit_gate1_smoke_inputs(
            arm, corpus_rows, smoke_rows, step0_sample, source_map, image_index
        )
        if not audit["checks"]["status_pass"]:
            raise RuntimeError(f"{arm} smoke-input audit failed: {audit['errors'][:5]}")
        with (ROOT / outputs["smoke"]).open("w", encoding="utf-8") as handle:
            for row in smoke_rows:
                handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
        with (ROOT / outputs["step0"]).open("w", encoding="utf-8") as handle:
            for record in step0_sample:
                handle.write(json.dumps(record, sort_keys=True, ensure_ascii=True) + "\n")
        template_counts: dict[str, int] = {}
        for record in step0_sample:
            for member in ("a", "b"):
                key = str(record[f"template_id_{member}"])
                template_counts[key] = template_counts.get(key, 0) + 1
        report["arms"][arm] = {
            "corpus": str(outputs["corpus"]),
            "smoke_subset": str(outputs["smoke"]),
            "smoke_subset_sha256": sha256_file(ROOT / outputs["smoke"]),
            "step0_sample": str(outputs["step0"]),
            "step0_sample_sha256": sha256_file(ROOT / outputs["step0"]),
            "step0_member_template_counts": dict(sorted(template_counts.items())),
            "audit": audit,
        }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "pass",
                "std_smoke_sha256": report["arms"]["std"]["smoke_subset_sha256"],
                "necessity_smoke_sha256": report["arms"]["necessity"][
                    "smoke_subset_sha256"
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
