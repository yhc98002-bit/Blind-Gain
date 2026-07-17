#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from scripts.run_support_sharpening_followup import (
    ARMS,
    SCHEMA_VERSION as DRAW_SCHEMA_VERSION,
    read_jsonl,
    sha256,
    validate_execution_config,
)
from src.analysis.support_sharpening import (
    registered_followup_schedule,
    registered_sampling_kwargs,
    summarize_resampling_draws,
)
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT
from src.rewards.answer_reward import PARSER_VERSION
from src.rewards.pilot_reward import PILOT_REWARD_VERSION


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "blind-gains.support-sharpening-seed1-readout.v1"
DISPLAY_NAMES = {
    "a1_real": "A1 real",
    "a2_gray": "A2 gray",
    "a2b_noimage": "A2b no-image",
    "a3_caption": "A3 caption",
}


def _write_new(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f".{path.name}.partial.{os.getpid()}")
    partial.write_text(content, encoding="utf-8")
    os.replace(partial, path)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _candidate_rows(config: dict[str, Any], arm: str) -> list[dict[str, Any]]:
    record = config["arms"][arm]
    path = ROOT / record["candidate_path"]
    if not path.is_file() or sha256(path) != record["candidate_sha256"]:
        raise ValueError(f"candidate hash mismatch for {arm}")
    rows = sorted(read_jsonl(path), key=lambda row: (row["split"], row["row_index"]))
    if len(rows) != record["candidate_count"]:
        raise ValueError(f"candidate count mismatch for {arm}")
    return rows


def _validate_draw_contract(row: dict[str, Any], arm: str, condition: str) -> None:
    draw_index = row.get("draw_index")
    checks = {
        "schema": row.get("schema_version") == DRAW_SCHEMA_VERSION,
        "arm": row.get("arm") == arm,
        "condition": row.get("condition") == condition,
        "draw_index": isinstance(draw_index, int)
        and not isinstance(draw_index, bool)
        and 16 <= draw_index < 80,
        "decoding": isinstance(draw_index, int)
        and not isinstance(draw_index, bool)
        and row.get("decoding") == registered_sampling_kwargs(draw_index),
        "response": isinstance(row.get("response"), str),
        "outcome": isinstance(row.get("pilot_accuracy_correct"), bool),
        "parser": row.get("parser_version") == PARSER_VERSION,
        "reward": row.get("pilot_reward_version") == PILOT_REWARD_VERSION,
        "prompt": row.get("prompt_contract_sha256")
        == DEFAULT_PROMPT_CONTRACT.sha256,
        "duplicates_retained": row.get("duplicate_text_responses_retained") is True,
    }
    if not all(checks.values()):
        raise ValueError(f"M10 draw contract mismatch for {arm}: {checks}")


def _validate_run(
    config: dict[str, Any], config_path: Path, arm: str, run_dir: Path
) -> tuple[dict[str, Any], Path]:
    manifest_path = run_dir / "run_manifest.json"
    manifest = _load(manifest_path)
    checks = {
        "status": manifest.get("status") == "complete",
        "exit": manifest.get("exit_code") == 0,
        "artifacts": manifest.get("artifacts_exist") is True,
        "job": manifest.get("job_type") == "m10_support_sharpening_followup",
        "arm": manifest.get("arm") == arm,
        "condition": manifest.get("condition") == config["arms"][arm]["condition"],
        "config_path": manifest.get("config_path")
        == str(config_path.relative_to(ROOT)),
        "config_hash": manifest.get("config_hash") == sha256(config_path),
        "candidate_count": manifest.get("candidate_count")
        == config["arms"][arm]["candidate_count"],
        "expected_rows": manifest.get("expected_row_count")
        == config["arms"][arm]["candidate_count"] * 64,
        "draw_seeds": manifest.get("draw_seeds")
        == {
            "first": 20260732,
            "last": 20260795,
            "count": 64,
            "formula": "20260716 + draw_index",
        },
        "decoding": manifest.get("decoding")
        == {"temperature": 1.0, "top_p": 1.0, "n_per_call": 1, "max_tokens": 2048},
    }
    if not all(checks.values()):
        raise ValueError(f"M10 run manifest does not pass for {arm}: {checks}")
    output = run_dir / "draws.jsonl"
    registered = {(ROOT / path).resolve() for path in manifest.get("expected_artifacts", [])}
    if output.resolve() not in registered or not output.is_file():
        raise ValueError(f"M10 output is absent or unregistered for {arm}")
    return manifest, output


def build_readout(
    config: dict[str, Any], config_path: Path, run_dirs: dict[str, Path]
) -> dict[str, Any]:
    validate_execution_config(config, ROOT)
    if tuple(run_dirs) != ARMS:
        raise ValueError("M10 finalizer requires exactly all four registered arms")
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "complete",
        "scientific_gate_decision": None,
        "registered_language": [
            "mass sharpening within observed support",
            "not observed in the base K-sample set",
        ],
        "causal_capability_claim_permitted": False,
        "arms": {},
        "source_runs": {},
    }
    for arm in ARMS:
        manifest, output = _validate_run(config, config_path, arm, run_dirs[arm])
        candidates = _candidate_rows(config, arm)
        candidate_by_fingerprint = {
            row["source_item_fingerprint"]: row for row in candidates
        }
        if len(candidate_by_fingerprint) != len(candidates):
            raise ValueError(f"duplicate candidate fingerprint for {arm}")
        draws = read_jsonl(output)
        if len(draws) != len(candidates) * 64:
            raise ValueError(f"M10 draw count mismatch for {arm}")
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in draws:
            _validate_draw_contract(
                row, arm, str(config["arms"][arm]["condition"])
            )
            grouped[str(row.get("source_item_fingerprint"))].append(row)
        if set(grouped) != set(candidate_by_fingerprint):
            raise ValueError(f"M10 candidate/draw identity mismatch for {arm}")
        summaries = []
        for fingerprint, candidate in candidate_by_fingerprint.items():
            ordered = sorted(grouped[fingerprint], key=lambda row: row["draw_index"])
            if any(
                row.get("split") != candidate["split"]
                or row.get("row_index") != candidate["row_index"]
                for row in ordered
            ):
                raise ValueError(f"M10 candidate row identity mismatch for {arm}")
            summary = summarize_resampling_draws(candidate, ordered)
            summary["jeffreys_ci95"] = [
                summary["jeffreys_ci95_low"],
                summary["jeffreys_ci95_high"],
            ]
            summaries.append(summary)
        summaries.sort(key=lambda row: (row["split"], row["row_index"]))
        classes = Counter(row["classification"] for row in summaries)
        extra_counts = Counter(row["extra_correct_count"] for row in summaries)
        payload["arms"][arm] = {
            "condition": config["arms"][arm]["condition"],
            "candidate_count": len(candidates),
            "draw_count": len(draws),
            "class_counts": dict(sorted(classes.items())),
            "extra_correct_count_distribution": {
                str(key): value for key, value in sorted(extra_counts.items())
            },
            "items": summaries,
        }
        payload["source_runs"][arm] = {
            "run_dir": str(run_dirs[arm].relative_to(ROOT)),
            "run_manifest_sha256": sha256(run_dirs[arm] / "run_manifest.json"),
            "draw_output_sha256": sha256(output),
            "node": manifest["node"],
            "gpu_ids": manifest["gpu_ids"],
        }
    payload["checks"] = {
        "arm_count": len(payload["arms"]),
        "candidate_counts": {
            arm: payload["arms"][arm]["candidate_count"] for arm in ARMS
        },
        "every_candidate_has_64_registered_draws": all(
            arm_payload["draw_count"] == arm_payload["candidate_count"] * 64
            for arm_payload in payload["arms"].values()
        ),
        "draw_indices_exact": True,
        "draw_seeds_exact_and_distinct": len(
            {row["seed"] for row in registered_followup_schedule()}
        )
        == 64,
        "duplicate_text_not_deduplicated": True,
        "causal_language_locked": True,
    }
    return payload


def render_markdown(payload: dict[str, Any], machine_path: Path) -> str:
    lines = [
        "# Seed-1 M10 Support-Sharpening Follow-Up V1",
        "",
        "Status:",
        "- Four-arm frozen-base follow-up complete under the registered 64-seed rule.",
        "- This is a support-sharpening readout, not a claim that RL created or taught a capability.",
        "- No scientific gate decision is made.",
        "",
        "Evidence:",
        f"- Machine artifact: `{machine_path}`.",
        "- Draw indices `16..79`; seeds `20260732..20260795`; one `n=1` output row per item and seed.",
        "- Duplicate text responses were retained as distinct registered draws.",
        "",
        "| Arm | Candidates | Follow-up draws | High-confidence support-expansion candidates | Observed in support-sharpening samples |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for arm in ARMS:
        record = payload["arms"][arm]
        classes = record["class_counts"]
        lines.append(
            f"| {DISPLAY_NAMES[arm]} | {record['candidate_count']} | {record['draw_count']} | "
            f"{classes.get('high-confidence support-expansion candidate', 0)} | "
            f"{classes.get('observed in support-sharpening samples', 0)} |"
        )
    lines.extend(
        [
            "",
            "Interpretation lock:",
            "- Zero successes in 80 is `not observed in the base K-sample set` and carries the per-item Jeffreys 95% interval in the machine artifact.",
            "- Any success in the new draws is `mass sharpening within observed support`.",
            "",
            "Problems:",
            "- Item-level sampling uncertainty does not measure run-to-run RL variance.",
            "",
            "Decision:",
            "- None. These classifications are folded into the seed-1 readout under the registered non-causal language.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    for arm in ARMS:
        parser.add_argument(f"--{arm.replace('_', '-')}-run", type=Path, required=True)
    parser.add_argument(
        "--output-json", type=Path, default=Path("reports/support_sharpening_seed1_v1.json")
    )
    parser.add_argument(
        "--output-md", type=Path, default=Path("reports/support_sharpening_seed1_v1.md")
    )
    args = parser.parse_args()
    config = _load(args.config)
    run_dirs = {
        arm: getattr(args, f"{arm}_run").resolve()
        for arm in ARMS
    }
    payload = build_readout(config, args.config.resolve(), run_dirs)
    payload["config"] = {
        "path": str(args.config.resolve().relative_to(ROOT)),
        "sha256": sha256(args.config),
    }
    output_json = args.output_json.resolve()
    output_md = args.output_md.resolve()
    _write_new(output_json, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    try:
        _write_new(output_md, render_markdown(payload, output_json.relative_to(ROOT)))
    except Exception:
        output_json.unlink(missing_ok=True)
        raise


if __name__ == "__main__":
    main()
