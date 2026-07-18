#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT
from src.eval.nonqwen_adapters import nonqwen_runtime_metadata_valid
from src.eval.visual_evidence_ranking import HUMAN_TEMPLATE_LABELS
from src.rewards.answer_reward import PARSER_VERSION


BACKENDS = ("internvl3", "gemma3")
CONDITIONS = ("real", "none", "caption")
DATASETS = ("r19", "r20")
EXPECTED_FLIPTRACK_KEYS = {
    (backend, dataset, condition)
    for backend in BACKENDS
    for dataset in DATASETS
    for condition in CONDITIONS
}
EXPECTED_BLIND_KEYS = {
    (backend, condition) for backend in BACKENDS for condition in CONDITIONS
}
MODEL_DIRECTORY_BACKENDS = {
    "internvl3-9b": "internvl3",
    "gemma-3-12b-it": "gemma3",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _validate_completed_metric_run(path: Path, expected_job_type: str) -> dict[str, Any]:
    manifest_path = path.parent / "run_manifest.json"
    if not manifest_path.is_file():
        raise ValueError(f"metric lacks sibling run manifest: {path}")
    manifest = _load_json(manifest_path)
    if manifest.get("status") != "complete" or manifest.get("job_type") != expected_job_type:
        raise ValueError(f"metric run is not a completed {expected_job_type}: {path}")
    expected = {Path(str(value)).resolve() for value in manifest.get("expected_artifacts", [])}
    if path.resolve() not in expected:
        raise ValueError(f"metric is not registered as an expected artifact: {path}")
    return manifest


def build_payload(
    fliptrack_paths: Iterable[Path],
    blind_paths: Iterable[Path],
    stage_paths: Iterable[Path],
) -> dict[str, Any]:
    errors: list[str] = []
    stage_evidence = []
    staged_placements: set[tuple[str, str]] = set()
    for path in stage_paths:
        manifest = _load_json(path)
        destination_name = Path(str(manifest.get("destination", ""))).name.lower()
        backend = MODEL_DIRECTORY_BACKENDS.get(destination_name)
        node = str(manifest.get("node", ""))
        valid = (
            manifest.get("status") == "complete"
            and manifest.get("job_type") == "m11_ephemeral_model_stage"
            and str(manifest.get("destination", "")).startswith(
                "/dev/shm/blind-gains/models/"
            )
            and isinstance(manifest.get("data_manifest_hash"), str)
            and len(manifest["data_manifest_hash"]) == 64
            and backend in BACKENDS
            and node in {"an12", "an29"}
        )
        if not valid:
            errors.append(f"invalid model-stage manifest: {path}")
        else:
            staged_placements.add((str(backend), node))
        stage_evidence.append(
            {
                "path": str(path),
                "sha256": _sha256(path),
                "destination": manifest.get("destination"),
                "backend": backend,
                "node": node,
                "valid": valid,
            }
        )

    fliptrack: dict[tuple[str, str, str], dict[str, Any]] = {}
    required_stage_placements: set[tuple[str, str]] = set()
    for path in fliptrack_paths:
        metric = _load_json(path)
        try:
            manifest = _validate_completed_metric_run(
                path, "m11_nonqwen_fliptrack_evaluation"
            )
        except ValueError as error:
            errors.append(str(error))
            manifest = {}
        key = (
            str(metric.get("backend")),
            str(metric.get("dataset_id")),
            str(metric.get("condition")),
        )
        if key in fliptrack:
            errors.append(f"duplicate FlipTrack cell: {key}")
        checks = {
            "row_count": metric.get("row_count") == 1200,
            "pair_count": metric.get("n_pairs") == 1200.0,
            "parser": metric.get("parser_version") == PARSER_VERSION,
            "prompt": metric.get("prompt_contract_sha256")
            == DEFAULT_PROMPT_CONTRACT.sha256,
            "decoding": metric.get("decoding")
            == {"temperature": 0.0, "top_p": 1.0, "n": 1, "max_new_tokens": 384},
            "templates": isinstance(metric.get("per_template"), dict)
            and bool(metric["per_template"]),
            "runtime": nonqwen_runtime_metadata_valid(metric.get("runtime"), key[0]),
            "run_key": (
                manifest.get("model_backend"),
                manifest.get("dataset_id"),
                manifest.get("condition"),
            )
            == key,
        }
        if not all(checks.values()):
            errors.append(f"invalid FlipTrack cell {key}: {checks}")
        if manifest:
            required_stage_placements.add(
                (str(manifest.get("model_backend")), str(manifest.get("node")))
            )
        fliptrack[key] = {
            "path": str(path),
            "sha256": _sha256(path),
            "checks": checks,
            "metrics": metric,
        }

    blind: dict[tuple[str, str], dict[str, Any]] = {}
    for path in blind_paths:
        metric = _load_json(path)
        try:
            manifest = _validate_completed_metric_run(
                path, "m11_nonqwen_blind_sample_evaluation"
            )
        except ValueError as error:
            errors.append(str(error))
            manifest = {}
        key = (str(metric.get("backend")), str(metric.get("condition")))
        if key in blind:
            errors.append(f"duplicate blind-sample cell: {key}")
        checks = {
            "row_count": metric.get("n_rows") == 4096,
            "parser": metric.get("parser_version") == PARSER_VERSION,
            "prompt": metric.get("prompt_contract_sha256")
            == DEFAULT_PROMPT_CONTRACT.sha256,
            "decoding": metric.get("decoding")
            == {"temperature": 0.0, "top_p": 1.0, "n": 1, "max_new_tokens": 2048},
            "strata": isinstance(metric.get("per_source_category"), dict)
            and bool(metric["per_source_category"]),
            "runtime": nonqwen_runtime_metadata_valid(metric.get("runtime"), key[0]),
            "run_key": (manifest.get("model_backend"), manifest.get("condition"))
            == key,
        }
        if not all(checks.values()):
            errors.append(f"invalid blind-sample cell {key}: {checks}")
        if manifest:
            required_stage_placements.add(
                (str(manifest.get("model_backend")), str(manifest.get("node")))
            )
        blind[key] = {
            "path": str(path),
            "sha256": _sha256(path),
            "checks": checks,
            "metrics": metric,
        }

    if set(fliptrack) != EXPECTED_FLIPTRACK_KEYS:
        errors.append(
            "FlipTrack matrix mismatch: "
            f"missing={sorted(EXPECTED_FLIPTRACK_KEYS - set(fliptrack))}, "
            f"extra={sorted(set(fliptrack) - EXPECTED_FLIPTRACK_KEYS)}"
        )
    if set(blind) != EXPECTED_BLIND_KEYS:
        errors.append(
            "blind-sample matrix mismatch: "
            f"missing={sorted(EXPECTED_BLIND_KEYS - set(blind))}, "
            f"extra={sorted(set(blind) - EXPECTED_BLIND_KEYS)}"
        )
    missing_stage_placements = sorted(required_stage_placements - staged_placements)
    if missing_stage_placements:
        errors.append(
            f"model-stage placement coverage missing: {missing_stage_placements}"
        )
    checks = {
        "both_model_backends_staged": {
            str(record["backend"])
            for record in stage_evidence
            if record["valid"]
        }
        == set(BACKENDS),
        "all_run_placements_have_verified_stage": not missing_stage_placements
        and bool(required_stage_placements)
        and all(record["valid"] for record in stage_evidence),
        "complete_fliptrack_2x2x3_matrix": set(fliptrack) == EXPECTED_FLIPTRACK_KEYS,
        "all_fliptrack_cells_audited": len(fliptrack) == 12
        and all(all(record["checks"].values()) for record in fliptrack.values()),
        "complete_blind_sample_2x3_matrix": set(blind) == EXPECTED_BLIND_KEYS,
        "all_blind_sample_cells_audited": len(blind) == 6
        and all(all(record["checks"].values()) for record in blind.values()),
    }
    return {
        "schema_version": "blind-gains.generalization-audits.v1",
        "status": "pass" if all(checks.values()) and not errors else "fail",
        "checks": checks,
        "model_stages": stage_evidence,
        "fliptrack": {"|".join(key): value for key, value in sorted(fliptrack.items())},
        "blind_sample": {"|".join(key): value for key, value in sorted(blind.items())},
        "errors": errors,
    }


def _format(value: Any) -> str:
    return "NA" if value is None else f"{float(value):.4f}"


def render_markdown(payload: dict[str, Any], machine_path: Path) -> str:
    flip_rows = []
    for key, record in payload["fliptrack"].items():
        backend, dataset, condition = key.split("|")
        metric = record["metrics"]
        templates = ", ".join(
            f"{HUMAN_TEMPLATE_LABELS.get(name, name)}={_format(values.get('pair_accuracy'))}"
            for name, values in sorted(metric["per_template"].items())
        )
        flip_rows.append(
            f"| {backend} | {dataset.upper()} | {condition} | {_format(metric.get('pair_accuracy'))} "
            f"| [{_format(metric.get('pair_accuracy_ci95_low'))}, {_format(metric.get('pair_accuracy_ci95_high'))}] "
            f"| {_format(metric.get('collapse_rate'))} | {templates} |"
        )
    blind_rows = []
    for key, record in payload["blind_sample"].items():
        backend, condition = key.split("|")
        metric = record["metrics"]
        blind_rows.append(
            f"| {backend} | {condition} | {_format(metric.get('acc_final'))} "
            f"| [{_format(metric.get('acc_final_ci95_low'))}, {_format(metric.get('acc_final_ci95_high'))}] "
            f"| {_format(metric.get('acc_strict'))} | {_format(metric.get('contract_valid_rate'))} |"
        )
    check_rows = [
        f"| `{name}` | `{str(value).lower()}` |" for name, value in payload["checks"].items()
    ]
    return "\n".join(
        [
            "# Generalization Audits V2",
            "",
            "Status:",
            f"- M11 evidence conjunction: `{payload['status']}`.",
            "- These are inference-only audits; they do not establish a training-effect claim.",
            "- Caption results measure caption-mediated accessibility using fixed 3B question-blind captions.",
            "- Human-facing chart label: `cued chart point-value reading`; internal template IDs remain only in the machine artifact for compatibility.",
            "",
            "Checks:",
            "| Check | Result |",
            "| --- | --- |",
            *check_rows,
            "",
            "FlipTrack:",
            "| Backend | Split | Condition | Pair accuracy | 95% item-bootstrap CI | Collapse | Per-template pair accuracy |",
            "| --- | --- | --- | ---: | --- | ---: | --- |",
            *flip_rows,
            "",
            "ViRL39K Blind-Solvability Sample:",
            "| Backend | Condition | Acc_final | 95% item-bootstrap CI | Acc_strict | Contract-valid rate |",
            "| --- | --- | ---: | --- | ---: | ---: |",
            *blind_rows,
            "",
            "Evidence:",
            f"- Machine artifact: `{machine_path}`.",
            "- Every cell links its immutable metric path and SHA256 in the machine artifact.",
            "- Decoding is greedy with temperature 0, top-p 1, n=1; prompt and parser versions are fixed.",
            "",
            "Decision:",
            "- Report the two model families separately; no architecture-pooled estimate is computed.",
            "- Source/category and template strata are preserved in the machine artifact.",
        ]
    ) + "\n"


def _atomic_write(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite generalization audit: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fliptrack-metrics", type=Path, nargs="+", required=True)
    parser.add_argument("--blind-metrics", type=Path, nargs="+", required=True)
    parser.add_argument("--model-stage-manifests", type=Path, nargs="+", required=True)
    parser.add_argument("--machine-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    payload = build_payload(
        args.fliptrack_metrics, args.blind_metrics, args.model_stage_manifests
    )
    _atomic_write(
        args.machine_output,
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write(
        args.markdown_output,
        render_markdown(payload, args.machine_output),
    )
    print(json.dumps({"status": payload["status"], "errors": payload["errors"]}))
    raise SystemExit(0 if payload["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
