#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from src.analysis.blind_solvability import bootstrap_mean_ci, real_blind_quadrants
from src.eval.blind_solvability import (
    CONDITIONS,
    PILOT_ROW_SCHEMA_VERSION,
    PILOT_SCORING_MODE,
    load_geometry_rows,
    load_train_filter_ids,
    score_item_pilot,
)
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT, load_prompt_contract_from_run_manifest
from src.rewards.answer_reward import PARSER_VERSION
from src.rewards.pilot_reward import PILOT_REWARD_VERSION


SCORE_FIELDS = (
    "scoring_mode",
    "pilot_reward_version",
    "format_weight",
    "p_greedy",
    "greedy_correct",
    "greedy_training_reward",
    "greedy_format_reward",
    "greedy_native_r1v_shadow_reward",
    "greedy_canonical_correct",
    "greedy_reward_disagreement_reason",
    "greedy_extracted_answer",
    "greedy_extractor_valid",
    "greedy_contract_valid",
    "greedy_format_valid",
    "greedy_acc_strict",
    "sampled_extractor_valid",
    "sampled_contract_valid",
    "sampled_training_rewards",
    "sampled_format_rewards",
    "sampled_native_r1v_shadow_rewards",
    "sampled_canonical_rewards",
    "sampled_reward_disagreement_reasons",
    "parser_version",
    "prompt_contract_id",
    "prompt_contract_sha256",
    "sample_count",
    "sample_correct_count",
    "sample_correct",
    "p_sample",
    "p_i_jeffreys",
    "q_i",
    "pass_at_g",
    "pass_at_k16",
    "variance_proxy",
    "mean_sampled_training_reward",
    "mean_sampled_format_reward",
    "canonical_sample_correct_count",
    "canonical_p_sample",
    "sampled_canonical_correct",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if any(not line.strip() for line in lines):
        raise ValueError(f"blank JSONL row in {path}")
    return [json.loads(line) for line in lines]


def _parse_runs(values: list[str]) -> dict[str, Path]:
    runs: dict[str, Path] = {}
    for value in values:
        condition, separator, path = value.partition("=")
        if not separator or condition not in CONDITIONS or condition in runs:
            raise ValueError(f"invalid condition=run mapping: {value}")
        runs[condition] = Path(path)
    if set(runs) != set(CONDITIONS):
        raise ValueError(f"expected all five conditions, found {sorted(runs)}")
    return runs


def _equal(actual: Any, expected: Any) -> bool:
    if isinstance(expected, float):
        return isinstance(actual, (float, int)) and math.isclose(
            float(actual), expected, rel_tol=1e-12, abs_tol=1e-12
        )
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(
            _equal(left, right) for left, right in zip(actual, expected)
        )
    return actual == expected


def _identity(row: dict[str, Any]) -> tuple[str, int]:
    return str(row["split"]), int(row["row_index"])


def _item_contract(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "problem": row.get("problem"),
        "ground_truth": row.get("ground_truth"),
        "image_sha256": row.get("image_sha256"),
        "qid": row.get("qid"),
        "source_metadata": row.get("source_metadata"),
    }


def _expected_decoding(seed: int) -> dict[str, Any]:
    return {
        "greedy": {"temperature": 0.0, "top_p": 1.0, "n": 1},
        "sampled": {"temperature": 1.0, "top_p": 1.0, "n": 16},
        "max_tokens": 2048,
        "seed": seed,
    }


def _check_manifest_contract(manifest: dict[str, Any], condition: str) -> bool:
    try:
        seed = int(manifest.get("seed", -1))
    except (TypeError, ValueError):
        return False
    return bool(
        manifest.get("status") == "complete"
        and manifest.get("condition") == condition
        and manifest.get("job_type") == "l7_blind_solvability_geo3k_v2"
        and manifest.get("scoring_mode") == PILOT_SCORING_MODE
        and manifest.get("pilot_reward_version") == PILOT_REWARD_VERSION
        and manifest.get("parser_version") == PARSER_VERSION
        and manifest.get("prompt_contract_sha256") == DEFAULT_PROMPT_CONTRACT.sha256
        and manifest.get("sample_count") == 16
        and manifest.get("sample_temperature") == 1.0
        and manifest.get("group_size") == 5
        and manifest.get("max_tokens") == 2048
        and manifest.get("format_weight") == 0.5
        and isinstance(manifest.get("source_manifest_sha256"), str)
        and len(manifest["source_manifest_sha256"]) == 64
        and isinstance(manifest.get("train_filter_sha256"), str)
        and len(manifest["train_filter_sha256"]) == 64
        and manifest.get("decoding") == _expected_decoding(seed)
    )


def audit_runs(run_dirs: dict[str, Path]) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    manifests: dict[str, dict[str, Any]] = {}
    rows_by_condition: dict[str, list[dict[str, Any]]] = {}
    output_hashes: dict[str, str] = {}
    mismatch_counts: dict[str, int] = {}
    mismatch_fields: Counter[str] = Counter()
    manifest_checks: dict[str, bool] = {}
    row_contract_checks: dict[str, bool] = {}
    identity_unique_checks: dict[str, bool] = {}
    decoding_checks: dict[str, bool] = {}
    source_paths: set[str] = set()
    filter_paths: set[str] = set()
    filter_hashes: set[str] = set()
    source_hashes: set[str] = set()

    for condition in CONDITIONS:
        run_dir = run_dirs[condition]
        manifest_path = run_dir / "run_manifest.json"
        output_path = run_dir / "per_item.jsonl"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        rows = _read_jsonl(output_path)
        manifests[condition] = manifest
        rows_by_condition[condition] = rows
        output_hashes[condition] = _sha256(output_path)
        manifest_checks[condition] = _check_manifest_contract(manifest, condition)
        source_paths.add(str(manifest.get("data_manifest")))
        filter_paths.add(str(manifest.get("train_filter_ids")))
        filter_hashes.add(str(manifest.get("train_filter_sha256")))
        source_hashes.add(str(manifest.get("source_manifest_sha256")))

        try:
            prompt_contract = load_prompt_contract_from_run_manifest(manifest_path)
        except Exception:
            prompt_contract = DEFAULT_PROMPT_CONTRACT
            manifest_checks[condition] = False
        seen: set[tuple[str, int]] = set()
        row_contract_ok = True
        decoding_ok = True
        mismatched_rows = 0
        for row in rows:
            try:
                key = _identity(row)
            except Exception:
                row_contract_ok = False
                mismatched_rows += 1
                continue
            if key in seen:
                identity_unique_checks[condition] = False
            seen.add(key)
            try:
                expected_decoding = _expected_decoding(int(manifest.get("seed", -1)))
            except (TypeError, ValueError):
                expected_decoding = None
            if row.get("decoding") != expected_decoding:
                decoding_ok = False
            fixed_contract = bool(
                row.get("schema_version") == PILOT_ROW_SCHEMA_VERSION
                and row.get("condition") == condition
                and row.get("source_manifest_sha256") == manifest.get("source_manifest_sha256")
                and row.get("train_filter_sha256") == manifest.get("train_filter_sha256")
                and row.get("prompt_contract_sha256") == DEFAULT_PROMPT_CONTRACT.sha256
                and row.get("parser_version") == PARSER_VERSION
                and row.get("pilot_reward_version") == PILOT_REWARD_VERSION
                and row.get("scoring_mode") == PILOT_SCORING_MODE
            )
            sampled = row.get("sampled_responses")
            if not fixed_contract or not isinstance(sampled, list) or len(sampled) != 16:
                row_contract_ok = False
                mismatched_rows += 1
                continue
            recomputed = score_item_pilot(
                str(row.get("ground_truth", "")),
                str(row.get("greedy_response", "")),
                [str(response) for response in sampled],
                group_size=5,
                prompt_contract=prompt_contract,
                format_weight=0.5,
            )
            row_mismatch = False
            for field in SCORE_FIELDS:
                if field not in row or not _equal(row.get(field), recomputed[field]):
                    mismatch_fields[field] += 1
                    row_mismatch = True
            if row_mismatch:
                mismatched_rows += 1
        identity_unique_checks.setdefault(condition, len(seen) == len(rows))
        row_contract_checks[condition] = row_contract_ok
        decoding_checks[condition] = decoding_ok
        mismatch_counts[condition] = mismatched_rows

    source_selection_exact = False
    expected_rows: list[dict[str, Any]] = []
    if len(source_paths) == len(source_hashes) == len(filter_paths) == len(filter_hashes) == 1:
        source_path = Path(next(iter(source_paths)))
        filter_path = Path(next(iter(filter_paths)))
        try:
            filter_ids = load_train_filter_ids(filter_path)
            expected_rows = load_geometry_rows(
                source_path,
                ("train", "test"),
                train_filter_ids=filter_ids,
            )
            source_selection_exact = bool(
                _sha256(source_path) == next(iter(source_hashes))
                and _sha256(filter_path) == next(iter(filter_hashes))
            )
        except Exception:
            source_selection_exact = False

    expected_contracts = {
        (str(row["split"]), int(row["row_index"])): {
            "problem": row.get("problem"),
            "ground_truth": row.get("answer"),
            "image_sha256": [image["sha256"] for image in row.get("images", [])],
            "qid": row.get("qid"),
            "source_metadata": row.get("metadata"),
        }
        for row in expected_rows
    }
    expected_keys = set(expected_contracts)
    condition_keys = {
        condition: {_identity(row) for row in rows if "split" in row and "row_index" in row}
        for condition, rows in rows_by_condition.items()
    }
    identity_equal = all(keys == expected_keys for keys in condition_keys.values())
    item_contract_equal = bool(expected_contracts)
    if item_contract_equal:
        try:
            item_contract_equal = all(
                all(_item_contract(row) == expected_contracts.get(_identity(row)) for row in rows)
                for rows in rows_by_condition.values()
            )
        except (KeyError, TypeError, ValueError):
            item_contract_equal = False
    row_counts = {condition: len(rows) for condition, rows in rows_by_condition.items()}
    split_counts = Counter(str(row["split"]) for row in expected_rows)

    checks = {
        "all_run_manifests_complete_and_registered": all(manifest_checks.values()),
        "source_and_filter_contract_shared": len(source_paths)
        == len(source_hashes)
        == len(filter_paths)
        == len(filter_hashes)
        == 1,
        "source_selection_exact": source_selection_exact,
        "row_counts_match_filtered_train_plus_untouched_test": all(
            count == len(expected_rows) for count in row_counts.values()
        ) and bool(expected_rows),
        "row_identity_unique": all(identity_unique_checks.values()),
        "row_identity_equal_across_conditions": identity_equal,
        "scientific_item_contract_equal": item_contract_equal,
        "row_version_contract_valid": all(row_contract_checks.values()),
        "decoding_parameters_locked": all(decoding_checks.values()),
        "prompt_parser_reward_versions_locked": all(manifest_checks.values())
        and all(row_contract_checks.values()),
        "recomputed_scores_match": sum(mismatch_counts.values()) == 0,
        "output_hashes_recorded": len(output_hashes) == len(CONDITIONS)
        and all(len(value) == 64 for value in output_hashes.values()),
    }
    status = "pass" if all(checks.values()) else "fail"
    audit = {
        "schema_version": "blind-gains.blind-solvability-audit.v2",
        "status": status,
        "checks": checks,
        "conditions": list(CONDITIONS),
        "row_counts": row_counts,
        "expected_row_count": len(expected_rows),
        "expected_split_counts": dict(sorted(split_counts.items())),
        "row_identity_duplicate_checks": identity_unique_checks,
        "decoding_parameters": _expected_decoding(20260710),
        "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
        "parser_version": PARSER_VERSION,
        "pilot_reward_version": PILOT_REWARD_VERSION,
        "scoring_mode": PILOT_SCORING_MODE,
        "recomputed_score_mismatch_count": sum(mismatch_counts.values()),
        "recomputed_score_mismatch_rows_by_condition": mismatch_counts,
        "recomputed_score_mismatch_fields": dict(sorted(mismatch_fields.items())),
        "per_item_output_sha256": output_hashes,
        "run_manifest_sha256": {
            condition: _sha256(run_dirs[condition] / "run_manifest.json") for condition in CONDITIONS
        },
        "runs": {condition: str(run_dirs[condition]) for condition in CONDITIONS},
    }
    return audit, rows_by_condition


def _p_bands(rows: list[dict[str, Any]], seed: int) -> dict[str, dict[str, float]]:
    tests = {
        "[0,0.2)": lambda p: p < 0.2,
        "[0.2,0.4)": lambda p: 0.2 <= p < 0.4,
        "[0.4,0.6)": lambda p: 0.4 <= p < 0.6,
        "[0.6,0.8)": lambda p: 0.6 <= p < 0.8,
        "[0.8,1]": lambda p: p >= 0.8,
    }
    return {
        name: bootstrap_mean_ci(
            (float(test(float(row["p_i_jeffreys"]))) for row in rows),
            seed=seed + offset,
        )
        for offset, (name, test) in enumerate(tests.items())
    }


def _summarize_condition(rows: list[dict[str, Any]], seed: int) -> dict[str, Any]:
    if not rows:
        raise ValueError("cannot summarize an empty condition/split")
    fields = (
        "p_greedy",
        "greedy_canonical_correct",
        "greedy_training_reward",
        "greedy_format_reward",
        "p_sample",
        "p_i_jeffreys",
        "q_i",
        "mean_sampled_training_reward",
        "mean_sampled_format_reward",
        "canonical_p_sample",
    )
    q_values = np.asarray([float(row["q_i"]) for row in rows], dtype=np.float64)
    return {
        "n": len(rows),
        "metrics": {
            field: bootstrap_mean_ci((float(row[field]) for row in rows), seed=seed + offset)
            for offset, field in enumerate(fields)
        },
        "p_i_bands": _p_bands(rows, seed + 100),
        "q_i_distribution": {
            "min": float(q_values.min()),
            "q25": float(np.quantile(q_values, 0.25)),
            "median": float(np.quantile(q_values, 0.5)),
            "q75": float(np.quantile(q_values, 0.75)),
            "max": float(q_values.max()),
        },
        "reward_disagreement_rate": bootstrap_mean_ci(
            (
                float(
                    row["greedy_reward_disagreement_reason"] != "none"
                    or any(reason != "none" for reason in row["sampled_reward_disagreement_reasons"])
                )
                for row in rows
            ),
            seed=seed + 200,
        ),
    }


def build_summary(
    rows_by_condition: dict[str, list[dict[str, Any]]],
    audit: dict[str, Any],
    *,
    seed: int = 20260710,
) -> dict[str, Any]:
    if audit.get("status") != "pass":
        raise ValueError("refusing to summarize L7 outputs before the audit passes")
    splits = ("train", "test")
    aggregates = {
        condition: {
            "all": _summarize_condition(rows, seed + condition_index * 1000),
            **{
                split: _summarize_condition(
                    [row for row in rows if row["split"] == split],
                    seed + condition_index * 1000 + split_index * 100,
                )
                for split_index, split in enumerate(splits, start=1)
            },
        }
        for condition_index, (condition, rows) in enumerate(rows_by_condition.items())
    }
    quadrants = {
        condition: {
            split: real_blind_quadrants(
                [row for row in rows_by_condition["real"] if split == "all" or row["split"] == split],
                [row for row in rows_by_condition[condition] if split == "all" or row["split"] == split],
            )
            for split in ("all", *splits)
        }
        for condition in CONDITIONS
        if condition != "real"
    }
    return {
        "schema_version": "blind-gains.blind-solvability-summary.v5",
        "report_version": "geo3k-v2",
        "status": "complete",
        "dataset_name": "Geometry3K filtered-train plus untouched-test",
        "n_items": audit["expected_row_count"],
        "split_counts": audit["expected_split_counts"],
        "evaluation_contract": {
            "max_tokens": 2048,
            "sample_count": 16,
            "sample_temperature": 1.0,
            "group_size": 5,
            "format_weight": 0.5,
            "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
            "parser_version": PARSER_VERSION,
            "pilot_reward_version": PILOT_REWARD_VERSION,
            "scoring_mode": PILOT_SCORING_MODE,
        },
        "audit": audit,
        "aggregates": aggregates,
        "real_blind_greedy_quadrants": quadrants,
    }


def _metric_cell(summary: dict[str, Any], condition: str, split: str, field: str) -> str:
    metric = summary["aggregates"][condition][split]["metrics"][field]
    return f"{metric['mean']:.4f} [{metric['ci_low']:.4f}, {metric['ci_high']:.4f}]"


def render_summary(summary: dict[str, Any], audit_json: Path) -> str:
    lines = [
        "# Geometry3K Blind-Solvability Audit V2",
        "",
        "Status:",
        "- Complete for the frozen filtered train corpus and untouched test split under all five conditions.",
        "- This v2 uses 2,048-token outputs, the exact pilot-reward-v1 scorer, canonical-v2 comparison scoring, and Jeffreys-smoothed p_i. The retained v1 tables used 512 tokens and the canonical-v1 scorer.",
        f"- Machine status JSON: `{audit_json}` (`status=pass`).",
        "",
        "Evidence:",
        f"- Items: {summary['n_items']} ({summary['split_counts']}).",
        f"- Prompt contract SHA256: `{summary['evaluation_contract']['prompt_contract_sha256']}`.",
        "- Sampling: n=16, temperature=1.0, G=5; greedy decoding uses temperature=0, top_p=1.0, n=1.",
        "",
        "Primary pilot-reward and canonical-v2 results:",
        "| Condition | Split | Pilot greedy accuracy | Canonical greedy accuracy | Mean p_i | Mean q_i | Mean pilot reward | Format rate |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for condition in CONDITIONS:
        for split in ("all", "train", "test"):
            lines.append(
                f"| {condition} | {split} | {_metric_cell(summary, condition, split, 'p_greedy')} | "
                f"{_metric_cell(summary, condition, split, 'greedy_canonical_correct')} | "
                f"{_metric_cell(summary, condition, split, 'p_i_jeffreys')} | "
                f"{_metric_cell(summary, condition, split, 'q_i')} | "
                f"{_metric_cell(summary, condition, split, 'mean_sampled_training_reward')} | "
                f"{_metric_cell(summary, condition, split, 'mean_sampled_format_reward')} |"
            )
    lines.extend(
        [
            "",
            "Jeffreys p_i bands (all items):",
            "| Condition | [0,0.2) | [0.2,0.4) | [0.4,0.6) | [0.6,0.8) | [0.8,1] |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for condition in CONDITIONS:
        bands = summary["aggregates"][condition]["all"]["p_i_bands"]
        cells = [f"{bands[name]['mean']:.4f}" for name in ("[0,0.2)", "[0.2,0.4)", "[0.4,0.6)", "[0.6,0.8)", "[0.8,1]")]
        lines.append(f"| {condition} | " + " | ".join(cells) + " |")
    lines.extend(
        [
            "",
            "q_i distributions (all items):",
            "| Condition | Min | Q25 | Median | Q75 | Max |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for condition in CONDITIONS:
        values = summary["aggregates"][condition]["all"]["q_i_distribution"]
        lines.append(
            f"| {condition} | {values['min']:.4f} | {values['q25']:.4f} | "
            f"{values['median']:.4f} | {values['q75']:.4f} | {values['max']:.4f} |"
        )
    lines.extend(
        [
            "",
            "Greedy real-vs-blind quadrants:",
            "| Blind condition | Split | Both | Real only | Blind only | Neither |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for condition, split_values in summary["real_blind_greedy_quadrants"].items():
        for split, counts in split_values.items():
            lines.append(
                f"| {condition} | {split} | {counts['both_correct']} | {counts['real_only']} | "
                f"{counts['blind_only']} | {counts['neither_correct']} |"
            )
    lines.extend(
        [
            "",
            "Problems:",
            "- These are base-model corpus measurements, not pilot-arm outcomes.",
            "- Item-bootstrap intervals quantify item uncertainty; they do not estimate run-to-run RL variance.",
            "",
            "Decision:",
            "- No gate decision is made here. These frozen q_i values are inputs to PI-reviewed preregistration.",
            "",
            "Next actions:",
            "- Fill the preregistration's computed q_i fields and submit the frozen document for PI review after the separate human R19 audit is recorded.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_audit(audit: dict[str, Any], audit_json: Path) -> str:
    lines = [
        "# Geometry3K Blind-Solvability V2 Independent Audit",
        "",
        "Status:",
        f"- Machine audit status: `{audit['status']}`.",
        f"- Machine status JSON: `{audit_json}`.",
        "",
        "Evidence:",
    ]
    for name, passed in audit["checks"].items():
        lines.append(f"- `{name}`: `{str(passed).lower()}`.")
    lines.extend(
        [
            f"- Row counts: `{audit['row_counts']}`; expected `{audit['expected_row_count']}` per condition.",
            f"- Recomputed score mismatches: `{audit['recomputed_score_mismatch_count']}`.",
            f"- Decoding: `{audit['decoding_parameters']}`.",
            "",
            "Problems:",
            "- A failed sub-check makes the logical-AND audit status fail; no exception is waived in this artifact.",
            "",
            "Decision:",
            "- This is a measurement-integrity audit only. It does not declare L7 or any PI gate passed.",
            "",
            "Next actions:",
            "- Use the audited outputs only when machine status is pass and the ledger has the named report.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="append", required=True, help="condition=run_directory")
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--audit-json-output", type=Path, required=True)
    parser.add_argument("--audit-markdown-output", type=Path, required=True)
    args = parser.parse_args()
    outputs = (
        args.json_output,
        args.markdown_output,
        args.audit_json_output,
        args.audit_markdown_output,
    )
    if any(path.exists() for path in outputs):
        raise FileExistsError("refusing to overwrite an L7 v2 summary or audit artifact")
    for path in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)

    audit, rows_by_condition = audit_runs(_parse_runs(args.run))
    args.audit_json_output.write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    args.audit_markdown_output.write_text(
        render_audit(audit, args.audit_json_output), encoding="utf-8"
    )
    if audit["status"] != "pass":
        raise SystemExit(1)
    summary = build_summary(rows_by_condition, audit)
    args.json_output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    args.markdown_output.write_text(
        render_summary(summary, args.audit_json_output), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
