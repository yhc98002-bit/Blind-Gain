#!/usr/bin/env python3
"""Build the Mini-A5 arm-3 (necessity sampling) corpus: Delta-q table plus the
pre-materialized weighted resample of the frozen training corpus.

Registered by docs/registered_mini_a5_gate1_completion_v1.md section 2 R2
(prework ledger T4). Inputs are the two completed T3 blind-solvability passes
(conditions ``real`` and ``none``) over the frozen 6,000 member rows. Per item:

    q_real_i  := p_sample of the ``real`` pass  (mean correctness, 16 samples, T=1)
    q_blind_i := p_sample of the ``none`` pass
    dq_i      := q_real_i - q_blind_i
    w_i       := max(dq_i, 0) + 1/16          (registered sampling law, I1)
    p_i       := w_i / sum(w)

The corpus is 6,000 row-slots drawn i.i.d. WITH replacement from the 6,000
frozen member rows with probability p_i (build seed 20260731), arranged as
3,000 adjacent synthetic pseudo-pairs (``nec1_%06d``, drawn rows relabeled
alternately a/b), same 7-column schema. Necessity enters ONLY through the
draw probabilities: no reward term, no loss weight, no advantage transform.

Outputs (refuses to overwrite):
- data/mini_a5_necessity_metadata_v1/delta_q.jsonl        (6,000 rows, frozen order)
- data/mini_a5_necessity_train_v1/train.parquet           (6,000 rows, 7 columns)
- data/mini_a5_necessity_train_v1/train.jsonl             (same rows, sorted keys)
- data/mini_a5_necessity_train_v1/source_map.jsonl        (slot -> source row)
- reports/mini_a5_necessity_corpus_build_v1.json          (build report + audit)

The resample audit (acceptance condition 7 of the registration) checks:
weight-law exactness against the per-item inputs; support completeness
(no item unreachable, max/min draw ratio bounded by 17); build-seed
reproducibility of the exact draw; the EMPIRICAL DRAW-FREQUENCY AUDIT
(realized draw counts consistent with the registered p_i vector: per-item
upper bound plus a 10-group chi-square over p-sorted strata at the
pre-registered threshold); slot-for-slot byte identity with the frozen
source rows; adjacency; synthetic-uid disjointness; 7-column schema.

Adversarial fixture (I10): tests/test_build_mini_a5_necessity_corpus_fixture.py
plants naive implementations (uniform draw that ignores w_i, one-pass
permutation without replacement, floorless weights that strand negative-dq
items, a delta_q reward column smuggled into the schema, block layout,
original-uid passthrough, tampered slot content, wrong build seed) and
requires the audit to reject every one of them.
"""
from __future__ import annotations

import argparse
import io
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from src.fliptrack.schema import sha256_file

ROOT = Path(__file__).resolve().parents[1]

SCHEMA_VERSION = "blind-gains.mini-a5-necessity-corpus.v1"
DELTA_Q_SCHEMA_VERSION = "blind-gains.mini-a5-delta-q.v1"
SYNTHETIC_UID_PREFIX = "nec1_"
BUILD_SEED = 20260731
FLOOR_WEIGHT = 1.0 / 16.0
SAMPLE_COUNT = 16
EXPECTED_ROWS = 6000
# Empirical draw-frequency audit constants (pre-registered here, before any
# draw is inspected): 10 contiguous strata of the p-sorted items; the
# chi-square statistic over strata must stay below CHI2_THRESHOLD
# (upper-tail ~1e-8 for df=9); no single item may exceed its expected count
# by more than max(PER_ITEM_ABS_SLACK, PER_ITEM_SIGMA * sqrt(expected)).
FREQUENCY_STRATA = 10
CHI2_THRESHOLD = 60.0
PER_ITEM_ABS_SLACK = 8.0
PER_ITEM_SIGMA = 6.0

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

# Frozen inputs pinned by docs/registered_mini_a5_gate1_completion_v1.md section 5
# and by the committed T2 build report.
PINNED_SOURCE_HASHES = {
    "train.jsonl": "07d785ee6ae4a3b5325e12595f7830c5924e31c49565554f1e88b2abffc5fa5c",
    "train.parquet": "0b0f0965987d1c340c3ebd78da742c9d99b319b61524b5cb42960519fd9c9b28",
}
PINNED_T2_MANIFEST_SHA256 = (
    "4eb4ddd28b1e95874f68bebb07347e80418c6c9e073705fd2517eae3e6c7ce7d"
)
REQUIRED_RUN_MANIFEST = {
    "status": "complete",
    "exit_code": 0,
    "sample_count": SAMPLE_COUNT,
    "sample_temperature": 1.0,
    "group_size": 5,
    "data_manifest_hash": PINNED_T2_MANIFEST_SHA256,
    "model_revision": "artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct",
}

DEFAULT_SOURCE_DIR = Path("data/mini_a5_train_v1")
DEFAULT_REAL_RUN = Path(
    "experiments/runs/blind_solvability_mini_a5_train_v1_real_an12_20260806T153316Z"
)
DEFAULT_NONE_RUN = Path(
    "experiments/runs/blind_solvability_mini_a5_train_v1_none_an12_20260806T153317Z"
)
DEFAULT_METADATA_DIR = Path("data/mini_a5_necessity_metadata_v1")
DEFAULT_OUTPUT_DIR = Path("data/mini_a5_necessity_train_v1")
DEFAULT_REPORT = Path("reports/mini_a5_necessity_corpus_build_v1.json")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def compute_weight(delta_q: float) -> float:
    """The registered sampling law f(dq) = max(dq, 0) + 1/16 (I1)."""
    return max(float(delta_q), 0.0) + FLOOR_WEIGHT


def validate_run_manifest(manifest: dict[str, Any], condition: str) -> list[str]:
    errors = []
    if manifest.get("condition") != condition:
        errors.append(
            f"run manifest condition {manifest.get('condition')!r} != {condition!r}"
        )
    for key, expected in REQUIRED_RUN_MANIFEST.items():
        if manifest.get(key) != expected:
            errors.append(
                f"run manifest[{key!r}] = {manifest.get(key)!r} != required {expected!r}"
            )
    return errors


def _index_per_item(
    rows: list[dict[str, Any]], condition: str, expected_rows: int
) -> dict[int, dict[str, Any]]:
    indexed: dict[int, dict[str, Any]] = {}
    for row in rows:
        if row.get("condition") != condition:
            raise ValueError(
                f"per-item row condition {row.get('condition')!r} != {condition!r}"
            )
        row_index = int(row["row_index"])
        if row_index in indexed:
            raise ValueError(f"duplicate row_index {row_index} in {condition} per_item")
        if int(row.get("sample_count", -1)) != SAMPLE_COUNT:
            raise ValueError(
                f"{condition} row {row_index}: sample_count != {SAMPLE_COUNT}"
            )
        p_sample = float(row["p_sample"])
        if not (0.0 <= p_sample <= 1.0) or abs(
            p_sample * SAMPLE_COUNT - round(p_sample * SAMPLE_COUNT)
        ) > 1e-9:
            raise ValueError(
                f"{condition} row {row_index}: p_sample {p_sample} is not a multiple of 1/{SAMPLE_COUNT}"
            )
        indexed[row_index] = row
    if sorted(indexed) != list(range(expected_rows)):
        raise ValueError(
            f"{condition} per_item does not cover row_index 0..{expected_rows - 1} exactly"
        )
    return indexed


def build_delta_q_records(
    real_rows: list[dict[str, Any]],
    none_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Frozen-order Delta-q table; validates alignment of both passes."""
    expected_rows = len(source_rows)
    real = _index_per_item(real_rows, "real", expected_rows)
    none = _index_per_item(none_rows, "none", expected_rows)
    records: list[dict[str, Any]] = []
    for row_index, source in enumerate(source_rows):
        qid = f"{source['pair_group_uid']}:{source['pair_member']}"
        for condition, indexed in (("real", real), ("none", none)):
            observed_qid = str(indexed[row_index]["qid"])
            if observed_qid != qid:
                raise ValueError(
                    f"{condition} row {row_index}: qid {observed_qid!r} != frozen {qid!r}"
                )
        q_real = float(real[row_index]["p_sample"])
        q_blind = float(none[row_index]["p_sample"])
        delta_q = q_real - q_blind
        records.append(
            {
                "schema_version": DELTA_Q_SCHEMA_VERSION,
                "row_index": row_index,
                "qid": qid,
                "pair_group_uid": str(source["pair_group_uid"]),
                "pair_member": str(source["pair_member"]),
                "template_id": str(source["template_id"]),
                "category": str(source["category"]),
                "q_real": q_real,
                "q_blind": q_blind,
                "delta_q": delta_q,
                "weight": compute_weight(delta_q),
            }
        )
    total = sum(record["weight"] for record in records)
    for record in records:
        record["draw_probability"] = record["weight"] / total
    return records


def draw_indices(probabilities: np.ndarray, slot_count: int, seed: int) -> np.ndarray:
    """The registered i.i.d.-with-replacement draw (build seed pinned)."""
    rng = np.random.default_rng(seed)
    return rng.choice(len(probabilities), size=slot_count, replace=True, p=probabilities)


def materialize_rows(
    source_rows: list[dict[str, Any]], indices: np.ndarray
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Slots -> adjacent synthetic pseudo-pairs nec1_%06d with alternate a/b."""
    if len(indices) % 2 != 0:
        raise ValueError(f"slot count {len(indices)} is not even")
    nec_rows: list[dict[str, Any]] = []
    source_map: list[dict[str, Any]] = []
    for slot, source_index in enumerate(int(i) for i in indices):
        source = source_rows[source_index]
        pseudo_pair = slot // 2
        synthetic_uid = f"{SYNTHETIC_UID_PREFIX}{pseudo_pair:06d}"
        pseudo_member = "a" if slot % 2 == 0 else "b"
        nec_rows.append(
            {
                "problem": str(source["problem"]),
                "answer": str(source["answer"]),
                "images": [str(path) for path in source["images"]],
                "pair_group_uid": synthetic_uid,
                "pair_member": pseudo_member,
                "template_id": str(source["template_id"]),
                "category": str(source["category"]),
            }
        )
        source_map.append(
            {
                "slot": slot,
                "pair_group_uid": synthetic_uid,
                "pair_member": pseudo_member,
                "source_row_index": source_index,
                "source_qid": f"{source['pair_group_uid']}:{source['pair_member']}",
            }
        )
    return nec_rows, source_map


def parquet_bytes(rows: list[dict[str, Any]]) -> bytes:
    sink = io.BytesIO()
    pq.write_table(pa.Table.from_pylist(rows, schema=PARQUET_SCHEMA), sink)
    return sink.getvalue()


def audit_necessity_resample(
    source_rows: list[dict[str, Any]],
    delta_q_records: list[dict[str, Any]],
    nec_rows: list[dict[str, Any]],
    source_map: list[dict[str, Any]],
    *,
    build_seed: int = BUILD_SEED,
) -> dict[str, Any]:
    """Resample audit per acceptance condition 7. Returns checks + errors + stats."""
    errors: list[str] = []
    checks: dict[str, bool] = {}
    item_count = len(source_rows)
    slot_count = len(nec_rows)

    # --- Weight law: w_i = max(dq_i, 0) + 1/16, p_i = w_i / sum(w), exact.
    weight_ok = len(delta_q_records) == item_count
    if not weight_ok:
        errors.append(
            f"delta_q table has {len(delta_q_records)} rows != {item_count} source rows"
        )
    total_weight = sum(float(r.get("weight", 0.0)) for r in delta_q_records) or 1.0
    for record in delta_q_records if weight_ok else []:
        dq = float(record["q_real"]) - float(record["q_blind"])
        expected_weight = compute_weight(dq)
        if (
            abs(float(record["delta_q"]) - dq) > 1e-12
            or abs(float(record["weight"]) - expected_weight) > 1e-12
            or abs(
                float(record["draw_probability"]) - expected_weight / total_weight
            )
            > 1e-12
        ):
            weight_ok = False
            errors.append(
                f"row {record.get('row_index')}: delta_q/weight/draw_probability "
                "deviate from the registered law max(dq,0)+1/16"
            )
            break
    checks["weight_law_exact"] = weight_ok

    probabilities = np.array(
        [float(r.get("draw_probability", 0.0)) for r in delta_q_records], dtype=float
    )
    support_ok = (
        weight_ok
        and len(probabilities) == item_count
        and bool(np.all(probabilities > 0.0))
        and abs(float(probabilities.sum()) - 1.0) < 1e-9
    )
    ratio = (
        float(probabilities.max() / probabilities.min())
        if support_ok
        else float("nan")
    )
    if support_ok and ratio > 17.0 + 1e-9:
        support_ok = False
        errors.append(f"max/min draw ratio {ratio:.6f} exceeds the registered bound 17")
    elif not support_ok:
        errors.append("draw-probability support is incomplete or unnormalized")
    checks["support_complete_and_ratio_bounded"] = support_ok

    # --- Source map consistency.
    map_ok = len(source_map) == slot_count
    for slot, record in enumerate(source_map if map_ok else []):
        if int(record.get("slot", -1)) != slot:
            map_ok = False
            errors.append(f"source_map slot {slot} is out of order")
            break
        source_index = int(record.get("source_row_index", -1))
        if not (0 <= source_index < item_count):
            map_ok = False
            errors.append(f"source_map slot {slot}: source_row_index out of range")
            break
    checks["source_map_contiguous"] = map_ok

    # --- Build-seed reproducibility: the materialized draw IS the registered draw.
    reproducible = map_ok and support_ok
    if reproducible:
        expected_indices = draw_indices(probabilities, slot_count, build_seed)
        observed_indices = np.array(
            [int(r["source_row_index"]) for r in source_map], dtype=int
        )
        reproducible = bool(np.array_equal(expected_indices, observed_indices))
        if not reproducible:
            errors.append(
                f"materialized draw differs from the registered seed-{build_seed} draw"
            )
    checks["draw_reproducible_from_build_seed"] = reproducible

    # --- Empirical draw-frequency audit against the registered p_i vector.
    frequency_ok = map_ok and support_ok
    stats: dict[str, Any] = {}
    if frequency_ok:
        counts = np.zeros(item_count, dtype=float)
        for record in source_map:
            counts[int(record["source_row_index"])] += 1.0
        expected = probabilities * slot_count
        if counts.sum() != slot_count:
            frequency_ok = False
            errors.append("realized draw counts do not sum to the slot count")
        over = counts - expected
        per_item_bound = np.maximum(
            PER_ITEM_ABS_SLACK, PER_ITEM_SIGMA * np.sqrt(expected)
        )
        worst = int(np.argmax(over - per_item_bound))
        if frequency_ok and bool(np.any(over > per_item_bound)):
            frequency_ok = False
            errors.append(
                f"item {worst}: realized count {counts[worst]:.0f} exceeds expected "
                f"{expected[worst]:.3f} beyond the per-item tolerance"
            )
        order = np.argsort(probabilities, kind="stable")
        strata = np.array_split(order, FREQUENCY_STRATA)
        chi_square = 0.0
        stratum_rows = []
        for stratum in strata:
            observed_total = float(counts[stratum].sum())
            expected_total = float(expected[stratum].sum())
            contribution = (
                (observed_total - expected_total) ** 2 / expected_total
                if expected_total > 0
                else float("inf")
            )
            chi_square += contribution
            stratum_rows.append(
                {
                    "items": int(len(stratum)),
                    "expected_draws": expected_total,
                    "realized_draws": observed_total,
                }
            )
        if chi_square > CHI2_THRESHOLD:
            frequency_ok = False
            errors.append(
                f"draw-frequency chi-square {chi_square:.2f} over "
                f"{FREQUENCY_STRATA} p-sorted strata exceeds the registered "
                f"threshold {CHI2_THRESHOLD}"
            )
        stats = {
            "chi_square_over_strata": chi_square,
            "chi_square_threshold": CHI2_THRESHOLD,
            "strata": stratum_rows,
            "unique_source_rows_drawn": int(np.count_nonzero(counts)),
            "max_realized_count": int(counts.max()),
        }
    checks["empirical_draw_frequency_consistent"] = frequency_ok

    # --- Slot-for-slot byte identity with the frozen source rows.
    identity_ok = map_ok and len(nec_rows) == slot_count
    for record, row in zip(source_map, nec_rows) if identity_ok else []:
        source = source_rows[int(record["source_row_index"])]
        if (
            str(row.get("problem")) != str(source["problem"])
            or str(row.get("answer")) != str(source["answer"])
            or list(row.get("images", [])) != [str(p) for p in source["images"]]
            or str(row.get("template_id")) != str(source["template_id"])
            or str(row.get("category")) != str(source["category"])
        ):
            identity_ok = False
            errors.append(
                f"slot {record['slot']}: content deviates from frozen source row "
                f"{record['source_row_index']}"
            )
            break
    checks["slots_byte_identical_to_source"] = identity_ok

    # --- Schema, adjacency, uid discipline.
    checks["seven_column_schema"] = all(
        tuple(row.keys()) == COLUMNS
        and isinstance(row["images"], list)
        and all(isinstance(item, str) for item in row["images"])
        for row in nec_rows
    )
    if not checks["seven_column_schema"]:
        errors.append("at least one row deviates from the 7-column schema")

    adjacency_ok = slot_count % 2 == 0
    for pseudo_pair in range(slot_count // 2) if adjacency_ok else []:
        first, second = nec_rows[2 * pseudo_pair], nec_rows[2 * pseudo_pair + 1]
        expected_uid = f"{SYNTHETIC_UID_PREFIX}{pseudo_pair:06d}"
        if (
            str(first.get("pair_group_uid")) != expected_uid
            or str(second.get("pair_group_uid")) != expected_uid
            or str(first.get("pair_member")) != "a"
            or str(second.get("pair_member")) != "b"
        ):
            adjacency_ok = False
            errors.append(
                f"pseudo-pair {pseudo_pair}: rows are not adjacent {expected_uid} a/b"
            )
            break
    checks["adjacent_synthetic_pseudo_pairs"] = adjacency_ok

    source_uid_set = {str(row["pair_group_uid"]) for row in source_rows}
    observed_uids = {str(row.get("pair_group_uid")) for row in nec_rows}
    checks["synthetic_uids_disjoint_from_real_uids"] = all(
        uid.startswith(SYNTHETIC_UID_PREFIX) for uid in observed_uids
    ) and not (observed_uids & source_uid_set)
    if not checks["synthetic_uids_disjoint_from_real_uids"]:
        errors.append("synthetic uid prefix/disjointness violated")

    checks["status_pass"] = all(checks.values())
    return {"checks": checks, "errors": errors, "frequency_stats": stats}


def delta_q_summary(delta_q_records: list[dict[str, Any]]) -> dict[str, Any]:
    values = np.array([float(r["delta_q"]) for r in delta_q_records], dtype=float)
    weights = np.array([float(r["weight"]) for r in delta_q_records], dtype=float)
    quantiles = {
        f"p{int(q * 100):02d}": float(np.quantile(values, q))
        for q in (0.05, 0.25, 0.5, 0.75, 0.95)
    }
    return {
        "rows": len(values),
        "n_delta_q_positive": int(np.count_nonzero(values > 0)),
        "n_delta_q_zero": int(np.count_nonzero(values == 0)),
        "n_delta_q_negative_clipped_to_floor": int(np.count_nonzero(values < 0)),
        "n_weight_at_floor": int(np.count_nonzero(values <= 0)),
        "delta_q_mean": float(values.mean()),
        "delta_q_min": float(values.min()),
        "delta_q_max": float(values.max()),
        "delta_q_quantiles": quantiles,
        "q_real_mean": float(
            np.mean([float(r["q_real"]) for r in delta_q_records])
        ),
        "q_blind_mean": float(
            np.mean([float(r["q_blind"]) for r in delta_q_records])
        ),
        "weight_min": float(weights.min()),
        "weight_max": float(weights.max()),
        "max_min_draw_ratio": float(weights.max() / weights.min()),
        "weight_floor": FLOOR_WEIGHT,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--real-run", type=Path, default=DEFAULT_REAL_RUN)
    parser.add_argument("--none-run", type=Path, default=DEFAULT_NONE_RUN)
    parser.add_argument("--metadata-dir", type=Path, default=DEFAULT_METADATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    source_dir = ROOT / args.source_dir
    metadata_dir = ROOT / args.metadata_dir
    output_dir = ROOT / args.output_dir
    report_path = ROOT / args.report
    for path in (metadata_dir, output_dir):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite existing output: {path}")
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

    manifest_errors: list[str] = []
    run_provenance: dict[str, Any] = {}
    per_item: dict[str, list[dict[str, Any]]] = {}
    for condition, run_dir in (("real", args.real_run), ("none", args.none_run)):
        manifest = json.loads(
            (ROOT / run_dir / "run_manifest.json").read_text(encoding="utf-8")
        )
        manifest_errors.extend(validate_run_manifest(manifest, condition))
        per_item_path = ROOT / run_dir / "per_item.jsonl"
        per_item[condition] = load_jsonl(per_item_path)
        run_provenance[condition] = {
            "run_id": manifest.get("run_id"),
            "run_dir": str(run_dir),
            "per_item_sha256": sha256_file(per_item_path),
            "config_hash": manifest.get("config_hash"),
            "git_hash": manifest.get("git_hash"),
            "seed": 20260710,
            "end_time_utc": manifest.get("end_time_utc"),
        }
    if manifest_errors:
        raise ValueError(f"T3 run manifests failed validation: {manifest_errors}")

    source_rows = load_jsonl(source_dir / "train.jsonl")
    if len(source_rows) != EXPECTED_ROWS:
        raise ValueError(f"frozen corpus has {len(source_rows)} rows != {EXPECTED_ROWS}")
    source_parquet_rows = pq.read_table(source_dir / "train.parquet").to_pylist()
    if source_parquet_rows != source_rows:
        raise ValueError("frozen train.parquet rows differ from frozen train.jsonl rows")

    delta_q_records = build_delta_q_records(
        per_item["real"], per_item["none"], source_rows
    )
    probabilities = np.array(
        [record["draw_probability"] for record in delta_q_records], dtype=float
    )
    indices = draw_indices(probabilities, EXPECTED_ROWS, BUILD_SEED)
    nec_rows, source_map = materialize_rows(source_rows, indices)

    first_bytes = parquet_bytes(nec_rows)
    second_rows, _ = materialize_rows(
        source_rows, draw_indices(probabilities, EXPECTED_ROWS, BUILD_SEED)
    )
    if first_bytes != parquet_bytes(second_rows):
        raise RuntimeError("resample parquet serialization is not deterministic")

    audit = audit_necessity_resample(
        source_rows, delta_q_records, nec_rows, source_map, build_seed=BUILD_SEED
    )
    if not audit["checks"]["status_pass"]:
        raise RuntimeError(f"resample audit failed: {audit['errors'][:5]}")

    metadata_dir.mkdir(parents=True, exist_ok=False)
    with (metadata_dir / "delta_q.jsonl").open("w", encoding="utf-8") as handle:
        for record in delta_q_records:
            handle.write(json.dumps(record, sort_keys=True, ensure_ascii=True) + "\n")
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "train.parquet").write_bytes(first_bytes)
    with (output_dir / "train.jsonl").open("w", encoding="utf-8") as handle:
        for row in nec_rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
    with (output_dir / "source_map.jsonl").open("w", encoding="utf-8") as handle:
        for record in source_map:
            handle.write(json.dumps(record, sort_keys=True, ensure_ascii=True) + "\n")

    written_rows = pq.read_table(output_dir / "train.parquet").to_pylist()
    if written_rows != nec_rows:
        raise RuntimeError("written parquet does not round-trip the resampled rows")

    report = {
        "schema_version": SCHEMA_VERSION,
        "registration": "docs/registered_mini_a5_gate1_completion_v1.md#2-R2",
        "builder": "scripts/build_mini_a5_necessity_corpus.py",
        "build_seed": BUILD_SEED,
        "numpy_version": np.__version__,
        "source_dir": str(args.source_dir),
        "source_sha256": source_hashes,
        "t2_manifest_sha256": PINNED_T2_MANIFEST_SHA256,
        "t3_runs": run_provenance,
        "sampling_law": "w_i = max(delta_q_i, 0) + 1/16; p_i = w_i / sum(w); "
        "6000 slots i.i.d. with replacement; necessity enters only through p_i (I1)",
        "output_sha256": {
            "delta_q.jsonl": sha256_file(metadata_dir / "delta_q.jsonl"),
            "train.parquet": sha256_file(output_dir / "train.parquet"),
            "train.jsonl": sha256_file(output_dir / "train.jsonl"),
            "source_map.jsonl": sha256_file(output_dir / "source_map.jsonl"),
        },
        "rows": len(nec_rows),
        "pseudo_pairs": len(nec_rows) // 2,
        "synthetic_uid_prefix": SYNTHETIC_UID_PREFIX,
        "parquet_serialization_deterministic": True,
        "delta_q_summary": delta_q_summary(delta_q_records),
        "resample_audit": audit,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "pass" if audit["checks"]["status_pass"] else "fail",
                "rows": len(nec_rows),
                "train_parquet_sha256": report["output_sha256"]["train.parquet"],
                "delta_q_positive": report["delta_q_summary"]["n_delta_q_positive"],
                "chi_square": audit["frequency_stats"]["chi_square_over_strata"],
            }
        )
    )


if __name__ == "__main__":
    main()
