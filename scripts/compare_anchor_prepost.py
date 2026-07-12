#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from src.analysis.blind_solvability import bootstrap_mean_ci


SCHEMA_VERSION = "blind-gains.anchor-prepost.v1"
BOOLEAN_METRICS: dict[str, str] = {
    "pilot_accuracy": "greedy_correct",
    "canonical_accuracy": "greedy_canonical_correct",
    "contract_valid": "greedy_contract_valid",
    "strict_accuracy": "greedy_acc_strict",
}
CONTINUOUS_METRICS: dict[str, str] = {
    "sampled_pilot_accuracy": "p_sample",
    "sampled_training_reward": "mean_sampled_training_reward",
    "sampled_format_reward": "mean_sampled_format_reward",
}
ITEM_FIELDS = ("problem", "ground_truth", "image_sha256", "qid", "source_metadata")
MANIFEST_LOCK_FIELDS = (
    "condition",
    "data_manifest",
    "data_manifest_hash",
    "source_manifest_sha256",
    "train_filter_ids",
    "train_filter_sha256",
    "format_prompt_sha256",
    "prompt_contract_sha256",
    "parser_version",
    "pilot_reward_version",
    "scoring_mode",
    "decoding",
    "sample_count",
    "sample_temperature",
    "group_size",
    "max_tokens",
    "format_weight",
    "symbolic_grader_guard_version",
    "symbolic_grader_timeout_seconds",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise ValueError(f"blank JSONL row at {path}:{line_number}")
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"non-object JSONL row at {path}:{line_number}")
            rows.append(row)
    return rows


def _identity(row: dict[str, Any]) -> tuple[str, int]:
    return str(row["split"]), int(row["row_index"])


def _index_rows(rows: list[dict[str, Any]], label: str) -> dict[tuple[str, int], dict[str, Any]]:
    indexed: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows:
        key = _identity(row)
        if key in indexed:
            raise ValueError(f"duplicate {label} row identity: {key}")
        indexed[key] = row
    return indexed


def _row_value(row: dict[str, Any], field: str, converter: Callable[[Any], float]) -> float:
    if field not in row:
        raise ValueError(f"row lacks required metric field: {field}")
    return converter(row[field])


def _metric_summary(
    before_rows: list[dict[str, Any]],
    after_rows: list[dict[str, Any]],
    field: str,
    *,
    converter: Callable[[Any], float],
    seed: int,
    draws: int,
) -> dict[str, Any]:
    before = [_row_value(row, field, converter) for row in before_rows]
    after = [_row_value(row, field, converter) for row in after_rows]
    delta = [right - left for left, right in zip(before, after)]
    interval = bootstrap_mean_ci(delta, seed=seed, draws=draws)
    return {
        "before": sum(before) / len(before),
        "after": sum(after) / len(after),
        "delta": interval["mean"],
        "delta_ci_low": interval["ci_low"],
        "delta_ci_high": interval["ci_high"],
    }


def _transitions(before_rows: list[dict[str, Any]], after_rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"both_correct": 0, "before_only": 0, "after_only": 0, "neither_correct": 0}
    for before, after in zip(before_rows, after_rows):
        left = bool(before["greedy_correct"])
        right = bool(after["greedy_correct"])
        key = (
            "both_correct"
            if left and right
            else "before_only"
            if left
            else "after_only"
            if right
            else "neither_correct"
        )
        counts[key] += 1
    return counts


def compare_runs(
    before_run: Path,
    after_run: Path,
    *,
    bootstrap_draws: int = 2000,
    seed: int = 20260712,
) -> dict[str, Any]:
    before_manifest_path = before_run / "run_manifest.json"
    after_manifest_path = after_run / "run_manifest.json"
    before_output = before_run / "per_item.jsonl"
    after_output = after_run / "per_item.jsonl"
    before_manifest = _read_json(before_manifest_path)
    after_manifest = _read_json(after_manifest_path)
    before_rows = _read_jsonl(before_output)
    after_rows = _read_jsonl(after_output)
    before_index = _index_rows(before_rows, "before")
    after_index = _index_rows(after_rows, "after")

    before_keys = set(before_index)
    after_keys = set(after_index)
    common_keys = sorted(before_keys & after_keys)
    item_mismatches = [
        key
        for key in common_keys
        if any(before_index[key].get(field) != after_index[key].get(field) for field in ITEM_FIELDS)
    ]
    manifest_drift = {
        field: {"before": before_manifest.get(field), "after": after_manifest.get(field)}
        for field in MANIFEST_LOCK_FIELDS
        if before_manifest.get(field) != after_manifest.get(field)
    }
    checks = {
        "run_manifests_complete": all(
            manifest.get("status") == "complete" and manifest.get("exit_code") == 0
            for manifest in (before_manifest, after_manifest)
        ),
        "guarded_rescore_contract": all(
            manifest.get("job_type") == "l7_blind_solvability_geo3k_v2_guarded_rescore"
            and manifest.get("guarded_rescore_version") == "l7-guarded-rescore-v1"
            for manifest in (before_manifest, after_manifest)
        ),
        "real_condition": before_manifest.get("condition") == after_manifest.get("condition") == "real",
        "manifest_contract_identical": not manifest_drift,
        "manifest_output_hashes_match": (
            before_manifest.get("output_sha256") == _sha256(before_output)
            and after_manifest.get("output_sha256") == _sha256(after_output)
        ),
        "row_identity_sets_identical": before_keys == after_keys and bool(before_keys),
        "item_content_identical": not item_mismatches and before_keys == after_keys,
        "expected_splits_present": {key[0] for key in before_keys} == {"train", "test"},
        "model_revisions_differ": before_manifest.get("model_revision")
        != after_manifest.get("model_revision"),
    }
    if not all(checks.values()):
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "fail",
            "checks": checks,
            "manifest_drift": manifest_drift,
            "before_only_identities": [list(key) for key in sorted(before_keys - after_keys)],
            "after_only_identities": [list(key) for key in sorted(after_keys - before_keys)],
            "item_content_mismatches": [list(key) for key in item_mismatches],
        }

    split_results: dict[str, Any] = {}
    metric_specs = {
        **{name: (field, lambda value: float(bool(value))) for name, field in BOOLEAN_METRICS.items()},
        **{name: (field, float) for name, field in CONTINUOUS_METRICS.items()},
    }
    for split_offset, split in enumerate(("train", "test")):
        keys = [key for key in common_keys if key[0] == split]
        before_split = [before_index[key] for key in keys]
        after_split = [after_index[key] for key in keys]
        metrics = {
            name: _metric_summary(
                before_split,
                after_split,
                field,
                converter=converter,
                seed=seed + split_offset * 100 + metric_offset,
                draws=bootstrap_draws,
            )
            for metric_offset, (name, (field, converter)) in enumerate(metric_specs.items())
        }
        split_results[split] = {
            "n": len(keys),
            "metrics": metrics,
            "pilot_accuracy_transitions": _transitions(before_split, after_split),
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "pass",
        "scope": "engineering-anchor evaluation; not a published-reproduction or PI gate verdict",
        "checks": checks,
        "bootstrap": {
            "unit": "paired item",
            "draws": bootstrap_draws,
            "seed": seed,
            "interval": 0.95,
            "run_to_run_variance_covered": False,
        },
        "before": {
            "run": str(before_run),
            "model_revision": before_manifest["model_revision"],
            "manifest_sha256": _sha256(before_manifest_path),
            "output_sha256": _sha256(before_output),
        },
        "after": {
            "run": str(after_run),
            "model_revision": after_manifest["model_revision"],
            "manifest_sha256": _sha256(after_manifest_path),
            "output_sha256": _sha256(after_output),
        },
        "locked_contract": {field: before_manifest.get(field) for field in MANIFEST_LOCK_FIELDS},
        "splits": split_results,
        "known_limitations": [
            "The step-100 checkpoint was optimized with the anchor's native EasyR1 r1v reward; pilot-reward-v1 and canonical-v2 are evaluation contracts only.",
            "The EasyR1 file logger was truncated on resume, so a continuous native-reward/KL curve for steps 1-80 is unavailable.",
            "Paired item-bootstrap intervals quantify evaluation-item uncertainty, not run-to-run RL variance.",
        ],
    }


def _format_metric(name: str, metric: dict[str, Any]) -> str:
    return (
        f"| {name} | {metric['before']:.4f} | {metric['after']:.4f} | "
        f"{metric['delta']:+.4f} | [{metric['delta_ci_low']:+.4f}, "
        f"{metric['delta_ci_high']:+.4f}] |"
    )


def render_markdown(payload: dict[str, Any], machine_output: Path) -> str:
    if payload.get("status") != "pass":
        raise ValueError("refusing to render a report from a failed comparison audit")
    lines = [
        "# Geometry3K Anchor Step-100 Pre/Post Evaluation V1",
        "",
        "Status:",
        "- Complete as a hash-pinned engineering-anchor evaluation; this is not a published-reproduction or PI gate verdict.",
        f"- Machine artifact: `{machine_output}`.",
        "",
        "Evidence:",
        f"- Base run: `{payload['before']['run']}`.",
        f"- Step-100 run: `{payload['after']['run']}`.",
        f"- Base/step-100 output SHA256: `{payload['before']['output_sha256']}` / `{payload['after']['output_sha256']}`.",
        "- Every manifest lock, output hash, item identity, problem, answer, image hash, parser, prompt, and decoding check passed.",
        "- Intervals are 2,000-draw paired item-bootstrap 95% intervals; they do not estimate run-to-run RL variance.",
    ]
    labels = {
        "pilot_accuracy": "Greedy pilot accuracy",
        "canonical_accuracy": "Greedy canonical accuracy",
        "contract_valid": "Greedy contract valid",
        "strict_accuracy": "Greedy strict accuracy",
        "sampled_pilot_accuracy": "Sampled pilot accuracy",
        "sampled_training_reward": "Sampled training reward",
        "sampled_format_reward": "Sampled format reward",
    }
    for split in ("test", "train"):
        result = payload["splits"][split]
        lines.extend(
            [
                "",
                f"{split.title()} split (`n={result['n']}`):",
                "",
                "| Metric | Base | Step 100 | Paired delta | 95% CI |",
                "| --- | ---: | ---: | ---: | ---: |",
                *[
                    _format_metric(labels[name], result["metrics"][name])
                    for name in labels
                ],
                "",
                f"Pilot-accuracy transitions: `{result['pilot_accuracy_transitions']}`.",
            ]
        )
    lines.extend(
        [
            "",
            "Problems:",
            "- The checkpoint was trained with the anchor's native EasyR1 `r1v` reward. Pilot-reward-v1 and canonical-v2 are used here only for a locked comparison.",
            "- EasyR1 truncated the structured metric file when the anchor resumed; steps 1-80 of the native reward/KL curve cannot be reconstructed from that file.",
            "- Geometry3K is both the anchor training source and evaluation family. The untouched test split avoids direct row reuse but does not establish external transfer.",
            "",
            "Decision:",
            "- Treat this as the missing deterministic pre/post engineering-anchor evaluation, not as a published-recipe reproduction claim.",
            "- Use gray/noise step-100 evaluations to test whether the observed post-training gain still depends on image information.",
            "",
            "Next actions:",
            "- Run step-100 gray and noise ablations after the corrected L3 reward smoke closes its fail-closed dependency.",
            "- Keep the four-arm pilot launch blocked until the final L12 preregistration has the required human audit and both PI approvals.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before-run", type=Path, required=True)
    parser.add_argument("--after-run", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--bootstrap-draws", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260712)
    args = parser.parse_args()
    for output in (args.output_json, args.output_md):
        if output.exists():
            raise FileExistsError(f"refusing to overwrite comparison output: {output}")
    payload = compare_runs(
        args.before_run,
        args.after_run,
        bootstrap_draws=args.bootstrap_draws,
        seed=args.seed,
    )
    if payload.get("status") != "pass":
        raise RuntimeError(json.dumps(payload, sort_keys=True))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(payload, args.output_json), encoding="utf-8")
    print(args.output_md)


if __name__ == "__main__":
    main()
