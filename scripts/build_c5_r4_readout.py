#!/usr/bin/env python3
"""Registered R4 readout for C5: the 7B Geometry3K access pair.

Registered specification (no free parameters):
- docs/registered_c5_7b_access_pair_v1.md   "Registered Readout": cells,
  estimands, M7 stability rule, bootstrap (5,000 item-paired draws, seed
  20260730, percentile 95%), cross-scale comparisons descriptive only
- docs/registered_extensions_v1.md          global contract; Extension 4
  relation (C5 does not discharge the ViRL39K flagship)

Data contracts:
- Cells are {7B base, A1-real, A2-gray} x test condition {real, gray}; all
  six are reported. Each cell is one blind-solvability-v2 evaluation run
  directory (per_item.jsonl + run_manifest.json) passed via --cell; nothing
  is hardcoded because the arm run directories are produced by the endgame
  waiter (state files logs/c5_endgame_state/cell_*).
- The geo3k evaluation split is the split == "test" rows of per_item.jsonl
  (601 rows on the registered corpus; the 1,288 split == "train" rows are
  never used in any estimand and are counted in provenance only). Train and
  test row_index ranges OVERLAP in this harness, so pairing identity is
  row_index WITHIN the test split.
- Both scoring contracts (I7) are computed separately and never merged:
  canonical = greedy_canonical_correct, strict = greedy_acc_strict.
- Discipline: before both arms complete, --partial verifies schema, pairing,
  manifests, and registered hashes ONLY, refuses every estimand, and emits
  no accuracy or performance value (docs/registered_c5_7b_access_pair_v1.md
  inspection discipline).

This script reports numbers, checks, and provenance only; it makes no
interpretation. Every number carries the one-seed tag.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.pilot_fourarm import (  # noqa: E402
    deterministic_seed,
    mean_with_paired_bootstrap,
    paired_ratio,
)

SCHEMA_VERSION = "blind-gains.c5-r4-readout.v1"
MODELS = ("base", "a1_real", "a2_gray")
TESTS = ("real", "gray")
CELLS = tuple(f"{model}:{test}" for model in MODELS for test in TESTS)
BASE_CELLS = ("base:real", "base:gray")
CONTRACTS = {
    "canonical": "greedy_canonical_correct",
    "strict": "greedy_acc_strict",
}
DISPLAY_NAMES = {"base": "7B base", "a1_real": "A1 real", "a2_gray": "A2 gray"}

REGISTERED_BOOTSTRAP_DRAWS = 5000
REGISTERED_BOOTSTRAP_SEED = 20260730
REGISTERED_TEST_ROWS = 601
REGISTERED_SOURCE_MANIFEST_SHA256 = (
    "0ac91fb836f39776acd5137ccd5cca7259d4ad0a836347be60f96f535d00f639"
)
REGISTERED_TRAIN_FILTER_SHA256 = (
    "8631d015ee8593669b46cc707b9fe1fb3690391520bccf416b64bbb2306ff7d1"
)
REGISTERED_FORMAT_PROMPT_SHA256 = (
    "f1b62cb8332bdbec38efc8689aff6e9ce65174c0db8967937307880f95f58fca"
)
REGISTERED_PROMPT_CONTRACT_SHA256 = (
    "7ac39f53a2a824490fc5ee22671a888d2d79d55e1d8351919006d7d71c7a8f3f"
)
REGISTERED_DECODING_SEED = 20260710
REGISTERED_BASE_MODEL_PATH = "artifacts/models/Qwen/Qwen2.5-VL-7B-Instruct"
ARM_MODEL_MARKERS = {"a1_real": "c5_a1_real", "a2_gray": "c5_a2_gray"}

SEED_SCOPE_TAG = "one seed (data.seed 1; single 7B training pair)"
SEED_SCOPE_STATEMENT = (
    "Seed scope: one seed (data.seed 1) and a single 7B training pair; every "
    "accuracy, gain, and recovery below is a one-seed number and no "
    "between-seed variance claim is made "
    "(docs/registered_c5_7b_access_pair_v1.md)."
)
CONTRACT_POLICY = (
    "Both scoring contracts (I7) are computed separately and never merged: "
    "canonical = greedy_canonical_correct, strict = greedy_acc_strict."
)
STABILITY_RULE = (
    "gain[A1, test real] > 0 and gain[A1, test real] >= 2 * paired_se "
    "(M7 stability rule); otherwise undefined-unstable-denominator and the "
    "ratio is not computed"
)
REGISTERED_DOCUMENTS = (
    "docs/registered_c5_7b_access_pair_v1.md",
    "docs/registered_extensions_v1.md",
)
REFUSED_IN_PARTIAL = (
    "cell_accuracy",
    "matched_gain_a1_real",
    "matched_gain_a2_gray",
    "crossed_gain_a2_gray",
    "descriptive_a1_tested_gray",
    "crossed_recovery_trainshare_a2_gray",
    "bootstrap_intervals",
)
CROSS_SCALE_ANCHOR = {
    "label": (
        "cross-scale descriptive anchor (3B pilot, three seeds pooled); "
        "not a 7B estimand; not recomputed"
    ),
    "pilot_pooled_crossed_trainshare_a2_gray": {
        "estimate": 0.487,
        "ci95": [0.383, 0.588],
        "source": "reports/d3_trainshare_v1.md",
    },
    "comparison_policy": (
        "scale comparisons against the 3B pilot are descriptive and labeled "
        "cross-scale; no cross-scale statistic is computed "
        "(docs/registered_c5_7b_access_pair_v1.md Registered Readout)"
    ),
}
CONSISTENT_ROW_FIELDS = (
    "prompt_contract_sha256",
    "format_prompt_sha256",
    "source_manifest_sha256",
    "train_filter_sha256",
    "parser_version",
    "scoring_mode",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid JSONL at {path}:{line_number}") from error
        if not isinstance(row, dict):
            raise ValueError(f"non-object JSONL row at {path}:{line_number}")
        rows.append(row)
    return rows


def _write_text(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def _resolve(root: Path, value: str) -> Path:
    candidate = Path(value)
    result = (candidate if candidate.is_absolute() else root / candidate).resolve()
    try:
        result.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"input path escapes the analysis root: {value}") from error
    return result


def _git_head(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


# --------------------------------------------------------------------------
# Loading and hard gates (all before any estimand)
# --------------------------------------------------------------------------

def load_cell(
    root: Path,
    cell: str,
    run_value: str,
    *,
    expected_test_rows: int,
) -> dict[str, Any]:
    model, _, test = cell.partition(":")
    run_dir = _resolve(root, run_value)
    per_item_path = run_dir / "per_item.jsonl"
    manifest_path = run_dir / "run_manifest.json"
    if not per_item_path.is_file():
        raise ValueError(f"{cell}: per_item.jsonl is absent in {run_dir}")
    if not manifest_path.is_file():
        raise ValueError(f"{cell}: run_manifest.json is absent in {run_dir}")
    manifest = _read_json(manifest_path)

    rows = _read_jsonl(per_item_path)
    test_rows: dict[int, dict[str, Any]] = {}
    train_row_count = 0
    consistent: dict[str, Any] | None = None
    schema_version: Any = None
    for line_number, row in enumerate(rows, 1):
        split = row.get("split")
        if split not in ("train", "test"):
            raise ValueError(
                f"{cell} row {line_number}: split must be 'train' or 'test', "
                f"found {split!r}"
            )
        if split == "train":
            train_row_count += 1
            continue
        row_index = row.get("row_index")
        if not isinstance(row_index, int) or isinstance(row_index, bool):
            raise ValueError(f"{cell} row {line_number}: invalid row_index")
        if row_index in test_rows:
            raise ValueError(
                f"{cell}: duplicate test row_index {row_index} "
                "(pairing identity is row_index within the test split)"
            )
        if row.get("condition") != test:
            raise ValueError(
                f"{cell} test row_index {row_index}: condition mismatch: "
                f"expected {test!r}, found {row.get('condition')!r}"
            )
        for field in CONTRACTS.values():
            if not isinstance(row.get(field), bool):
                raise ValueError(
                    f"{cell} test row_index {row_index}: {field} must be a "
                    f"boolean, found {row.get(field)!r}"
                )
        decoding = row.get("decoding")
        greedy = decoding.get("greedy") if isinstance(decoding, dict) else None
        if not isinstance(greedy, dict):
            raise ValueError(
                f"{cell} test row_index {row_index}: missing decoding.greedy"
            )
        temperature = greedy.get("temperature")
        if (
            not isinstance(temperature, (int, float))
            or isinstance(temperature, bool)
            or float(temperature) != 0.0
        ):
            raise ValueError(
                f"{cell} test row_index {row_index}: greedy temperature must "
                f"be 0, found {temperature!r}"
            )
        if greedy.get("n") != 1 or isinstance(greedy.get("n"), bool):
            raise ValueError(
                f"{cell} test row_index {row_index}: greedy n must be 1, "
                f"found {greedy.get('n')!r}"
            )
        ground_truth = row.get("ground_truth")
        problem = row.get("problem")
        image_sha = row.get("image_sha256")
        if not isinstance(ground_truth, str) or not isinstance(problem, str):
            raise ValueError(
                f"{cell} test row_index {row_index}: ground_truth and problem "
                "must be strings"
            )
        if not isinstance(image_sha, list) or not all(
            isinstance(entry, str) for entry in image_sha
        ):
            raise ValueError(
                f"{cell} test row_index {row_index}: image_sha256 must be a "
                "list of strings"
            )
        observed = {field: row.get(field) for field in CONSISTENT_ROW_FIELDS}
        for field, value in observed.items():
            if not isinstance(value, str) or not value:
                raise ValueError(
                    f"{cell} test row_index {row_index}: missing or invalid "
                    f"{field}"
                )
        observed["decoding_seed"] = (
            decoding.get("seed") if isinstance(decoding, dict) else None
        )
        if consistent is None:
            consistent = observed
            schema_version = row.get("schema_version")
        elif observed != consistent:
            differing = sorted(
                field for field in observed if observed[field] != consistent[field]
            )
            raise ValueError(
                f"{cell} test row_index {row_index}: row-level contract "
                f"fields vary within the cell: {differing}"
            )
        test_rows[row_index] = row

    if consistent is None:
        raise ValueError(f"{cell}: no test rows found in {per_item_path}")
    if (
        consistent["source_manifest_sha256"] == REGISTERED_SOURCE_MANIFEST_SHA256
        and expected_test_rows != REGISTERED_TEST_ROWS
    ):
        raise ValueError(
            f"{cell}: the registered corpus (source_manifest_sha256 "
            f"{REGISTERED_SOURCE_MANIFEST_SHA256}) requires exactly "
            f"{REGISTERED_TEST_ROWS} test rows; the --expected-test-rows "
            "override is refused on registered data"
        )
    if len(test_rows) != expected_test_rows:
        raise ValueError(
            f"{cell}: expected {expected_test_rows} test rows, found "
            f"{len(test_rows)}"
        )
    return {
        "cell": cell,
        "model": model,
        "test": test,
        "run_dir": run_dir,
        "run_id": str(manifest.get("run_id") or run_dir.name),
        "manifest": manifest,
        "manifest_sha256": _sha256(manifest_path),
        "per_item_sha256": _sha256(per_item_path),
        "rows": test_rows,
        "train_row_count": train_row_count,
        "consistent": consistent,
        "schema_version_rows": schema_version,
    }


def readiness_gate(cells_data: dict[str, dict[str, Any]]) -> None:
    failures: list[str] = []
    for cell, data in cells_data.items():
        status = data["manifest"].get("status")
        if status != "complete":
            failures.append(
                f"{cell}: run_manifest status is {status!r}, not 'complete' "
                f"({data['run_id']})"
            )
        condition = data["manifest"].get("condition")
        if condition != data["test"]:
            failures.append(
                f"{cell}: run_manifest condition is {condition!r}, expected "
                f"{data['test']!r}"
            )
    if failures:
        raise ValueError(
            "readiness gate failed; refusing to compute any estimand:\n- "
            + "\n- ".join(failures)
        )


def row_field_consistency_gate(
    cells_data: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    cells = list(cells_data)
    reference_cell = cells[0]
    reference = cells_data[reference_cell]["consistent"]
    failures: list[str] = []
    for cell in cells[1:]:
        observed = cells_data[cell]["consistent"]
        if observed != reference:
            differing = sorted(
                field for field in observed if observed[field] != reference[field]
            )
            failures.append(
                f"{cell} vs {reference_cell}: row-level contract fields "
                f"differ: {differing}"
            )
    if failures:
        raise ValueError(
            "row-field consistency gate failed; the six cells must share one "
            "locked evaluation contract:\n- " + "\n- ".join(failures)
        )
    return dict(reference)


def registered_enforcement(consistent: dict[str, Any]) -> None:
    expectations = (
        ("prompt_contract_sha256", REGISTERED_PROMPT_CONTRACT_SHA256),
        ("format_prompt_sha256", REGISTERED_FORMAT_PROMPT_SHA256),
        ("train_filter_sha256", REGISTERED_TRAIN_FILTER_SHA256),
        ("decoding_seed", REGISTERED_DECODING_SEED),
    )
    failures = [
        f"{field}: expected {expected!r}, found {consistent.get(field)!r}"
        for field, expected in expectations
        if consistent.get(field) != expected
    ]
    if failures:
        raise ValueError(
            "registered-corpus enforcement failed; the registered corpus "
            "requires the registered evaluation contract:\n- "
            + "\n- ".join(failures)
        )


def _content_key(row: dict[str, Any]) -> str:
    return json.dumps(
        [row["ground_truth"], row["problem"], row["image_sha256"]],
        sort_keys=True,
    )


def item_identity_gate(cells_data: dict[str, dict[str, Any]]) -> None:
    cells = list(cells_data)
    reference_cell = cells[0]
    reference_keys = set(cells_data[reference_cell]["rows"])
    failures: list[str] = []
    for cell in cells[1:]:
        observed = set(cells_data[cell]["rows"])
        missing = sorted(reference_keys - observed)
        extra = sorted(observed - reference_keys)
        if missing or extra:
            failures.append(
                f"{cell} vs {reference_cell}: {len(missing)} test items "
                f"missing (examples {missing[:3]}), {len(extra)} extra "
                f"(examples {extra[:3]})"
            )
    if failures:
        raise ValueError(
            "item-identity gate failed; the six cells must cover the "
            "identical test item set and items are never silently "
            "dropped:\n- " + "\n- ".join(failures)
        )
    content_failures: list[str] = []
    for row_index in sorted(reference_keys):
        reference_content = _content_key(cells_data[reference_cell]["rows"][row_index])
        for cell in cells[1:]:
            if _content_key(cells_data[cell]["rows"][row_index]) != reference_content:
                content_failures.append(
                    f"row_index {row_index}: (ground_truth, problem, "
                    f"image_sha256) differs between {reference_cell} and {cell}"
                )
                break
        if len(content_failures) >= 3:
            break
    if content_failures:
        raise ValueError(
            "content-identity gate failed; row_index must name the same item "
            "in every cell:\n- " + "\n- ".join(content_failures)
        )


def model_identity_gate(
    cells_data: dict[str, dict[str, Any]], *, registered: bool
) -> None:
    failures: list[str] = []
    revision_of: dict[str, str] = {}
    for model in MODELS:
        revisions = {
            str(data["manifest"].get("model_revision"))
            for data in cells_data.values()
            if data["model"] == model
        }
        if not revisions:
            continue
        if len(revisions) != 1:
            failures.append(
                f"{model}: model_revision differs between its two cells: "
                f"{sorted(revisions)}"
            )
            continue
        revision_of[model] = next(iter(revisions))
    models = sorted(revision_of)
    for left_index, left in enumerate(models):
        for right in models[left_index + 1:]:
            if revision_of[left] == revision_of[right]:
                failures.append(
                    f"{left} and {right} share model_revision "
                    f"{revision_of[left]!r}; the three models must be distinct"
                )
    if registered:
        if "base" in revision_of and revision_of["base"] != REGISTERED_BASE_MODEL_PATH:
            failures.append(
                f"base: model_revision {revision_of['base']!r} is not the "
                f"registered base path {REGISTERED_BASE_MODEL_PATH!r}"
            )
        for model, marker in ARM_MODEL_MARKERS.items():
            if model in revision_of and marker not in revision_of[model]:
                failures.append(
                    f"{model}: model_revision {revision_of[model]!r} does not "
                    f"name the registered arm ({marker!r})"
                )
    if failures:
        raise ValueError(
            "model-identity gate failed:\n- " + "\n- ".join(failures)
        )


# --------------------------------------------------------------------------
# Estimands (full mode only; per contract; item-paired bootstrap)
# --------------------------------------------------------------------------

def _tagged(summary: dict[str, Any], label: str) -> dict[str, Any]:
    summary["seed_tag"] = SEED_SCOPE_TAG
    summary["seed_label"] = label
    return summary


def _contract_estimands(
    cells_data: dict[str, dict[str, Any]],
    *,
    contract: str,
    field: str,
    draws: int,
    base_seed: int,
) -> dict[str, Any]:
    order = sorted(cells_data["base:real"]["rows"])
    acc = {
        cell: [
            1.0 if cells_data[cell]["rows"][row_index][field] else 0.0
            for row_index in order
        ]
        for cell in CELLS
    }

    def _diff(minuend: str, subtrahend: str) -> list[float]:
        return [
            left - right for left, right in zip(acc[minuend], acc[subtrahend])
        ]

    cell_accuracy = {
        cell: _tagged(
            mean_with_paired_bootstrap(
                acc[cell],
                draws=draws,
                seed=deterministic_seed(base_seed, f"{contract}:cell_acc:{cell}"),
            ),
            f"{contract}:cell_acc:{cell}",
        )
        for cell in CELLS
    }

    matched_contrib = {
        "a1_real": _diff("a1_real:real", "base:real"),
        "a2_gray": _diff("a2_gray:gray", "base:gray"),
    }
    matched_definitions = {
        "a1_real": "Acc(A1, test real) - Acc(base, test real)",
        "a2_gray": "Acc(A2, test gray) - Acc(base, test gray)",
    }
    matched_gain: dict[str, Any] = {}
    for model in ("a1_real", "a2_gray"):
        summary = _tagged(
            mean_with_paired_bootstrap(
                matched_contrib[model],
                draws=draws,
                seed=deterministic_seed(
                    base_seed, f"{contract}:matched_gain:{model}"
                ),
            ),
            f"{contract}:matched_gain:{model}",
        )
        summary["definition"] = matched_definitions[model]
        matched_gain[model] = summary

    crossed_contrib = _diff("a2_gray:real", "base:real")
    crossed_summary = _tagged(
        mean_with_paired_bootstrap(
            crossed_contrib,
            draws=draws,
            seed=deterministic_seed(base_seed, f"{contract}:crossed_gain:a2_gray"),
        ),
        f"{contract}:crossed_gain:a2_gray",
    )
    crossed_summary["definition"] = "Acc(A2, test real) - Acc(base, test real)"

    descriptive_summary = _tagged(
        mean_with_paired_bootstrap(
            _diff("a1_real:gray", "base:gray"),
            draws=draws,
            seed=deterministic_seed(
                base_seed, f"{contract}:descriptive_crossed_diff:a1_real"
            ),
        ),
        f"{contract}:descriptive_crossed_diff:a1_real",
    )
    descriptive_summary["definition"] = (
        "Acc(A1, test gray) - Acc(base, test gray)"
    )
    descriptive = {
        "label": "descriptive",
        "role": (
            "the A1 crossed cell (A1 tested gray) is reported descriptively "
            "per the registered readout; it enters no registered gain or "
            "recovery estimand"
        ),
        "crossed_difference": descriptive_summary,
    }

    denominator = matched_gain["a1_real"]
    stable = (
        denominator["estimate"] > 0
        and denominator["estimate"] >= 2 * denominator["paired_se"]
    )
    trainshare: dict[str, Any] = {
        "rule": STABILITY_RULE,
        "numerator_definition": "crossed gain A2-gray (test real)",
        "denominator": {
            "definition": "matched gain A1 (test real)",
            "estimate": denominator["estimate"],
            "paired_se": denominator["paired_se"],
            "stable": bool(stable),
        },
        "seed_tag": SEED_SCOPE_TAG,
    }
    if stable:
        ratio = paired_ratio(
            crossed_contrib,
            matched_contrib["a1_real"],
            draws=draws,
            seed=deterministic_seed(base_seed, f"{contract}:trainshare:a2_gray"),
        )
        ratio["seed_label"] = f"{contract}:trainshare:a2_gray"
        trainshare["status"] = "stable"
        trainshare["ratio"] = ratio
    else:
        trainshare["status"] = "undefined-unstable-denominator"
        trainshare["exclusion"] = (
            "crossed recovery is excluded; the ratio is not computed"
        )

    return {
        "field": field,
        "seed_tag": SEED_SCOPE_TAG,
        "cell_accuracy": cell_accuracy,
        "matched_gain": matched_gain,
        "crossed_gain": {"a2_gray": crossed_summary},
        "a1_tested_gray_descriptive": descriptive,
        "crossed_recovery_trainshare": {"a2_gray": trainshare},
    }


# --------------------------------------------------------------------------
# Payload assembly
# --------------------------------------------------------------------------

def _provenance(
    cells_data: dict[str, dict[str, Any]],
    consistent: dict[str, Any],
    *,
    root: Path,
    draws: int,
    base_seed: int,
) -> dict[str, Any]:
    cell_block: dict[str, Any] = {}
    for cell, data in cells_data.items():
        manifest = data["manifest"]
        cell_block[cell] = {
            "run_dir": str(data["run_dir"].relative_to(root)),
            "run_id": data["run_id"],
            "job_type": manifest.get("job_type"),
            "node": manifest.get("node"),
            "model_revision": manifest.get("model_revision"),
            "eval_git_hash": manifest.get("git_hash"),
            "config_hash": manifest.get("config_hash"),
            "run_manifest_sha256": data["manifest_sha256"],
            "per_item_sha256": data["per_item_sha256"],
            "test_row_count": len(data["rows"]),
            "train_row_count": data["train_row_count"],
            "per_item_schema_version": data["schema_version_rows"],
        }
    return {
        "cells": cell_block,
        "shared_row_contract": consistent,
        "analysis_git_head": _git_head(root),
        "bootstrap": {
            "draws": draws,
            "seed": base_seed,
            "stream_mechanism": (
                "deterministic statistic/cell labels hashed into independent "
                "streams via src.analysis.pilot_fourarm.deterministic_seed"
            ),
        },
        "registered_documents": list(REGISTERED_DOCUMENTS),
        "train_rows_note": (
            "split == 'train' rows are never used in any estimand and are "
            "counted here only; the pairing identity is row_index within the "
            "test split"
        ),
    }


def build_payload(args: argparse.Namespace, root: Path) -> dict[str, Any]:
    provided = args.cells
    cells_data: dict[str, dict[str, Any]] = {}
    for cell in CELLS:
        if cell in provided:
            cells_data[cell] = load_cell(
                root,
                cell,
                provided[cell],
                expected_test_rows=args.expected_test_rows,
            )
    readiness_gate(cells_data)
    consistent = row_field_consistency_gate(cells_data)
    registered = (
        consistent["source_manifest_sha256"] == REGISTERED_SOURCE_MANIFEST_SHA256
    )
    if registered:
        registered_enforcement(consistent)
    item_identity_gate(cells_data)
    model_identity_gate(cells_data, registered=registered)

    draws = int(args.bootstrap_draws)
    base_seed = int(args.bootstrap_seed)
    checks: dict[str, Any] = {
        "manifests_complete": True,
        "conditions_match_cells": True,
        "test_rows_per_cell": {
            cell: len(data["rows"]) for cell, data in cells_data.items()
        },
        "expected_test_rows": int(args.expected_test_rows),
        "item_identity_exact": True,
        "content_identity_exact": True,
        "model_identity_verified": True,
        "contract_fields_boolean": True,
        "contracts_never_merged": True,
        "greedy_temperature_zero_n1": True,
        "row_field_consistency_across_cells": True,
        "source_manifest_sha256_registered": registered,
        "prompt_contract_sha256_registered": (
            consistent["prompt_contract_sha256"]
            == REGISTERED_PROMPT_CONTRACT_SHA256
        ),
        "format_prompt_sha256_registered": (
            consistent["format_prompt_sha256"] == REGISTERED_FORMAT_PROMPT_SHA256
        ),
        "train_filter_sha256_registered": (
            consistent["train_filter_sha256"] == REGISTERED_TRAIN_FILTER_SHA256
        ),
        "decoding_seed_registered_20260710": (
            consistent["decoding_seed"] == REGISTERED_DECODING_SEED
        ),
        "bootstrap_draws_registered_5000": draws == REGISTERED_BOOTSTRAP_DRAWS,
        "bootstrap_seed_registered_20260730": (
            base_seed == REGISTERED_BOOTSTRAP_SEED
        ),
    }

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "partial-verify-only" if args.partial else "complete",
        "seed_scope": {
            "tag": SEED_SCOPE_TAG,
            "statement": SEED_SCOPE_STATEMENT,
        },
        "contract_policy": CONTRACT_POLICY,
        "bootstrap": {
            "draws": draws,
            "seed": base_seed,
            "registered_draws": REGISTERED_BOOTSTRAP_DRAWS,
            "registered_seed": REGISTERED_BOOTSTRAP_SEED,
            "unit": (
                "item-paired bootstrap over the evaluation items, preserving "
                "item identity across all six cells; percentile 95% intervals"
            ),
        },
        "checks": checks,
    }
    if args.partial:
        checks["partial_refuses_all_estimands"] = True
        payload["partial_mode"] = {
            "verifies": [
                "manifest completeness and cell conditions",
                "test-split extraction and row counts",
                "item and content identity across the provided cells",
                "model identity",
                "row-level contract-field consistency and registered hashes",
                "scoring-contract fields present and boolean",
            ],
            "refused_estimands": list(REFUSED_IN_PARTIAL),
            "reason": (
                "not all six cells are bound; per the registered inspection "
                "discipline no accuracy or performance value is computed or "
                "emitted before both arms complete "
                "(docs/registered_c5_7b_access_pair_v1.md)"
            ),
        }
    else:
        artifact_dir = _resolve(root, args.artifact_dir)
        if artifact_dir.exists():
            raise FileExistsError(
                f"refusing to overwrite artifact directory: {artifact_dir}"
            )
        artifact_dir.mkdir(parents=True)
        payload["estimands"] = {
            contract: _contract_estimands(
                cells_data,
                contract=contract,
                field=field,
                draws=draws,
                base_seed=base_seed,
            )
            for contract, field in CONTRACTS.items()
        }
        payload["cross_scale_anchor"] = CROSS_SCALE_ANCHOR
        joined_path = artifact_dir / "c5_joined_items.jsonl"
        _write_text(
            joined_path,
            "".join(
                json.dumps(
                    {
                        "cell": cell,
                        "model": cells_data[cell]["model"],
                        "test": cells_data[cell]["test"],
                        "row_index": row_index,
                        "greedy_canonical_correct": (
                            cells_data[cell]["rows"][row_index][
                                "greedy_canonical_correct"
                            ]
                        ),
                        "greedy_acc_strict": (
                            cells_data[cell]["rows"][row_index]["greedy_acc_strict"]
                        ),
                    },
                    sort_keys=True,
                )
                + "\n"
                for cell in CELLS
                for row_index in sorted(cells_data[cell]["rows"])
            ),
        )
        payload["joined_items_artifact"] = str(joined_path.relative_to(root))
        payload["joined_items_sha256"] = _sha256(joined_path)
    payload["provenance"] = _provenance(
        cells_data, consistent, root=root, draws=draws, base_seed=base_seed
    )
    return payload


# --------------------------------------------------------------------------
# Rendering (numbers, checks, provenance only)
# --------------------------------------------------------------------------

def _fmt(value: float | None) -> str:
    return "NA" if value is None else f"{value:.4f}"


def _fmt_ci(summary: dict[str, Any] | None) -> str:
    if summary is None or summary.get("estimate") is None:
        return "NA"
    interval = summary.get("ci95")
    if interval is None:
        return f"{summary['estimate']:.4f} [NA]"
    return f"{summary['estimate']:.4f} [{interval[0]:.4f}, {interval[1]:.4f}]"


def _checks_lines(checks: dict[str, Any]) -> list[str]:
    lines = ["| Check | Value |", "|---|---|"]
    for key in sorted(checks):
        value = checks[key]
        if isinstance(value, dict):
            shown = ", ".join(f"{k}={v}" for k, v in sorted(value.items()))
        elif isinstance(value, bool):
            shown = str(value).lower()
        else:
            shown = str(value)
        lines.append(f"| {key} | {shown} |")
    return lines


def render_markdown(payload: dict[str, Any], json_relpath: str) -> str:
    partial = payload["status"] == "partial-verify-only"
    lines = [
        "# C5 R4 Readout V1 (7B access pair)"
        + (" - PARTIAL (verify-only)" if partial else ""),
        "",
        f"Status: `{payload['status']}`.",
        "",
        "Scope:",
        f"- {payload['seed_scope']['statement']}",
        f"- {payload['contract_policy']}",
        "- This report contains numbers, checks, and provenance only; "
        "interpretation is reserved to the PIs.",
        "",
        f"Machine artifact: `{json_relpath}`.",
        "",
    ]
    if partial:
        lines.extend(
            [
                "## PARTIAL MODE (verify-only)",
                "",
                "- This output verifies schema, pairing, manifests, and "
                "registered hashes only; it is NOT the registered R4 result.",
                "- No accuracy or performance value appears in this output "
                "(registered inspection discipline: no evaluation performance "
                "value is inspected before both arms complete).",
                "- Refused estimands: "
                + ", ".join(payload["partial_mode"]["refused_estimands"])
                + ".",
                "",
            ]
        )
    lines.extend(["## Checks", ""])
    lines.extend(_checks_lines(payload["checks"]))
    lines.append("")
    if not partial:
        for contract, field in CONTRACTS.items():
            block = payload["estimands"][contract]
            lines.extend(
                [
                    f"## Contract: {contract} (`{field}`) - {SEED_SCOPE_TAG}",
                    "",
                    f"### Cell accuracy ({SEED_SCOPE_TAG})",
                    "",
                    "| Model | Test | n | Acc (95% CI) |",
                    "|---|---|---:|---:|",
                ]
            )
            for cell in CELLS:
                model, _, test = cell.partition(":")
                summary = block["cell_accuracy"][cell]
                lines.append(
                    f"| {DISPLAY_NAMES[model]} | {test} | {summary['n']} | "
                    f"{_fmt_ci(summary)} |"
                )
            lines.extend(
                [
                    "",
                    f"### Gains ({SEED_SCOPE_TAG})",
                    "",
                    "| Estimand | Definition | Estimate (95% CI) |",
                    "|---|---|---:|",
                ]
            )
            for label, summary in (
                ("Matched gain A1", block["matched_gain"]["a1_real"]),
                ("Matched gain A2", block["matched_gain"]["a2_gray"]),
                ("Crossed gain A2", block["crossed_gain"]["a2_gray"]),
                (
                    "A1 tested gray (descriptive)",
                    block["a1_tested_gray_descriptive"]["crossed_difference"],
                ),
            ):
                lines.append(
                    f"| {label} | {summary['definition']} | {_fmt_ci(summary)} |"
                )
            trainshare = block["crossed_recovery_trainshare"]["a2_gray"]
            denominator = trainshare["denominator"]
            lines.extend(
                [
                    "",
                    f"### Crossed recovery TrainShare A2-gray ({SEED_SCOPE_TAG})",
                    "",
                    f"- Rule: {trainshare['rule']}.",
                    f"- Denominator ({denominator['definition']}): estimate "
                    f"{_fmt(denominator['estimate'])}, paired SE "
                    f"{_fmt(denominator['paired_se'])}, stable "
                    f"`{str(denominator['stable']).lower()}`.",
                    f"- Status: `{trainshare['status']}`.",
                ]
            )
            if trainshare["status"] == "stable":
                ratio = trainshare["ratio"]
                lines.append(
                    f"- TrainShare: {_fmt_ci(ratio)} "
                    f"(retained bootstrap draws "
                    f"{ratio['retained_bootstrap_draws']}/"
                    f"{ratio['bootstrap_draws']})."
                )
            else:
                lines.append(f"- {trainshare['exclusion']}.")
            lines.append("")
        anchor = payload["cross_scale_anchor"]
        pilot = anchor["pilot_pooled_crossed_trainshare_a2_gray"]
        lines.extend(
            [
                "## Cross-scale descriptive anchor",
                "",
                f"- {anchor['label']}.",
                f"- 3B pilot pooled crossed TrainShare A2-gray: "
                f"{pilot['estimate']:.3f} [{pilot['ci95'][0]:.3f}, "
                f"{pilot['ci95'][1]:.3f}] (`{pilot['source']}`).",
                f"- {anchor['comparison_policy']}.",
                "",
            ]
        )
    provenance = payload["provenance"]
    lines.extend(
        [
            "## Provenance",
            "",
            f"- Analysis git head: `{provenance['analysis_git_head']}`.",
            f"- Bootstrap: {provenance['bootstrap']['draws']} draws, seed "
            f"{provenance['bootstrap']['seed']}; "
            f"{provenance['bootstrap']['stream_mechanism']}.",
            f"- {provenance['train_rows_note']}.",
            "- Registered documents: "
            + ", ".join(f"`{doc}`" for doc in provenance["registered_documents"])
            + ".",
            "",
            "| Cell | Run dir | Test rows | Train rows | per_item sha256 |",
            "|---|---|---:|---:|---|",
        ]
    )
    for cell in CELLS:
        if cell not in provenance["cells"]:
            continue
        row = provenance["cells"][cell]
        lines.append(
            f"| {cell} | `{row['run_dir']}` | {row['test_row_count']} | "
            f"{row['train_row_count']} | `{row['per_item_sha256']}` |"
        )
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _parse_cells(values: list[str] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values or []:
        if "=" not in value:
            raise SystemExit(f"--cell expects MODEL:TEST=RUN_DIR, got {value!r}")
        key, _, run_dir = value.partition("=")
        model, _, test = key.partition(":")
        if model not in MODELS or test not in TESTS:
            raise SystemExit(
                f"--cell: unknown cell {key!r}; registered cells are {CELLS}"
            )
        if key in result:
            raise SystemExit(f"--cell: duplicate cell {key!r}")
        if not run_dir:
            raise SystemExit(f"--cell: empty run dir for cell {key!r}")
        result[key] = run_dir
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--cell",
        action="append",
        metavar="MODEL:TEST=RUN_DIR",
        help=(
            "evaluation run directory for one cell, e.g. "
            "base:real=experiments/runs/... (repeat; six cells in full mode)"
        ),
    )
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--markdown-output", required=True)
    parser.add_argument(
        "--artifact-dir",
        default=None,
        help="directory for the joined-items artifact (full mode only)",
    )
    parser.add_argument(
        "--partial",
        action="store_true",
        help=(
            "verify-only mode: validates schema/pairing/manifests/hashes on "
            "the provided cells (both base cells required) and refuses every "
            "estimand; emits no accuracy or performance value"
        ),
    )
    parser.add_argument(
        "--bootstrap-draws", type=int, default=REGISTERED_BOOTSTRAP_DRAWS
    )
    parser.add_argument(
        "--bootstrap-seed", type=int, default=REGISTERED_BOOTSTRAP_SEED
    )
    parser.add_argument(
        "--expected-test-rows",
        type=int,
        default=REGISTERED_TEST_ROWS,
        help=(
            "test rows per cell (override exists only for synthetic "
            "fixtures; refused on the registered corpus)"
        ),
    )
    args = parser.parse_args()

    args.cells = _parse_cells(args.cell)
    if args.partial:
        if args.artifact_dir is not None:
            parser.error("--partial forbids --artifact-dir")
        missing_base = [cell for cell in BASE_CELLS if cell not in args.cells]
        if missing_base:
            parser.error(
                f"--partial requires both base cells; missing: {missing_base}"
            )
    else:
        missing = [cell for cell in CELLS if cell not in args.cells]
        if missing:
            parser.error(
                f"full mode requires all six cells; missing: {missing} "
                "(pass --partial for the verify-only mode)"
            )
        if args.artifact_dir is None:
            parser.error("--artifact-dir is required in full mode")
    if args.bootstrap_draws < 100:
        parser.error("--bootstrap-draws must be at least 100")

    root = args.root.resolve()
    json_output = _resolve(root, args.json_output)
    markdown_output = _resolve(root, args.markdown_output)
    if json_output.exists() or markdown_output.exists():
        raise FileExistsError("refusing to overwrite R4 readout artifacts")

    payload = build_payload(args, root)
    markdown = render_markdown(payload, str(json_output.relative_to(root)))
    _write_text(json_output, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    _write_text(markdown_output, markdown)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "json": str(json_output.relative_to(root)),
                "markdown": str(markdown_output.relative_to(root)),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
