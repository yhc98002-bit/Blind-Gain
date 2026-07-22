#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

from scripts.watch_anchor_checkpoints import (
    CODE_BUNDLE_PATHS,
    code_bundle_hash,
    process_step,
    refresh_usage_snapshot_if_needed,
    relocate_merged,
    require_code_bundle,
    valid_evaluation_marker,
)


ROOT = Path(__file__).resolve().parents[1]
PILOT_STEPS = (20, 40, 60, 80, 100)
PILOT_CODE_BUNDLE_PATHS = (*CODE_BUNDLE_PATHS, ROOT / "scripts/watch_pilot_checkpoints.py")
GEO3K_MARKER_SCHEMA_VERSION = "blind-gains.pilot-followup-geo3k-eval-marker.v1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def valid_geo3k_evaluation_marker(
    marker: Path,
    *,
    step: int,
    actor_dir: Path,
    root: Path = ROOT,
) -> bool:
    if not marker.is_file():
        return False
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    index = actor_dir / "huggingface" / "model.safetensors.index.json"
    if not index.is_file():
        return False
    evaluation_run = root / str(payload.get("evaluation_run", ""))
    audit_run = root / str(payload.get("audit_run", ""))
    evaluation_manifest = evaluation_run / "run_manifest.json"
    audit = audit_run / "audit.json"
    if not evaluation_manifest.is_file() or not audit.is_file():
        return False
    return bool(
        payload.get("schema_version") == GEO3K_MARKER_SCHEMA_VERSION
        and payload.get("status") == "complete"
        and payload.get("global_step") == step
        and Path(str(payload.get("checkpoint_path", ""))).resolve()
        == (actor_dir / "huggingface").resolve()
        and payload.get("checkpoint_index_sha256") == _sha256(index)
        and payload.get("row_count") == 601
        and payload.get("performance_values_opened") is False
        and isinstance(payload.get("evaluation_run"), str)
        and bool(payload["evaluation_run"])
        and payload.get("evaluation_manifest_sha256")
        == _sha256(evaluation_manifest)
        and isinstance(payload.get("evaluation_output_sha256"), str)
        and len(payload["evaluation_output_sha256"]) == 64
        and isinstance(payload.get("audit_run"), str)
        and bool(payload["audit_run"])
        and isinstance(payload.get("audit_sha256"), str)
        and len(payload["audit_sha256"]) == 64
        and payload["audit_sha256"] == _sha256(audit)
    )


def pilot_evaluation_barriers_ready(
    r19_marker: Path,
    geo3k_marker: Path,
    *,
    step: int,
    actor_dir: Path,
    root: Path = ROOT,
) -> bool:
    return valid_evaluation_marker(
        r19_marker, step=step, actor_dir=actor_dir
    ) and valid_geo3k_evaluation_marker(
        geo3k_marker, step=step, actor_dir=actor_dir, root=root
    )


def wait_for_pilot_evaluation_markers(
    r19_marker: Path,
    geo3k_marker: Path,
    *,
    step: int,
    actor_dir: Path,
    poll_seconds: int = 60,
) -> None:
    while not pilot_evaluation_barriers_ready(
        r19_marker,
        geo3k_marker,
        step=step,
        actor_dir=actor_dir,
    ):
        time.sleep(poll_seconds)


def pilot_code_bundle_hash() -> str:
    return code_bundle_hash(PILOT_CODE_BUNDLE_PATHS)


def relocation_plan() -> dict[int, str]:
    return {
        20: "relocate_after_merge",
        40: "relocate_after_merge",
        60: "relocate_after_registered_evaluation",
        80: "relocate_after_merge",
        100: "retain_final_on_shared",
    }


def execution_plan() -> tuple[tuple[int, str], ...]:
    """Keep the evaluated step on shared without blocking later raw retention."""
    return (
        (20, "relocate_after_merge"),
        (40, "relocate_after_merge"),
        (60, "retain_for_registered_evaluation"),
        (80, "relocate_after_merge"),
        (100, "retain_final_on_shared"),
        (60, "relocate_after_registered_evaluation"),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--node", choices=("an12", "an29"), required=True)
    parser.add_argument("--run-label", required=True)
    parser.add_argument("--step60-evaluation-marker", type=Path, required=True)
    parser.add_argument("--step60-geo3k-marker", type=Path, required=True)
    parser.add_argument("--expected-code-hash", required=True)
    args = parser.parse_args()
    require_code_bundle(args.expected_code_hash, PILOT_CODE_BUNDLE_PATHS)
    for step, action in execution_plan():
        if action == "relocate_after_registered_evaluation":
            actor_dir = args.run_root / f"global_step_{step}" / "actor"
            wait_for_pilot_evaluation_markers(
                args.step60_evaluation_marker,
                args.step60_geo3k_marker,
                step=step,
                actor_dir=actor_dir,
            )
            require_code_bundle(args.expected_code_hash, PILOT_CODE_BUNDLE_PATHS)
            relocate_merged(
                actor_dir,
                args.archive_root,
                step,
                scope="pilot",
                run_label=args.run_label,
            )
            refresh_usage_snapshot_if_needed(
                step,
                "post_evaluation_relocation",
                scope="pilot",
            )
            continue
        process_step(
            run_root=args.run_root,
            archive_root=args.archive_root,
            anchor_manifest=args.run_manifest,
            step=step,
            node=args.node,
            relocate_merged_output=action == "relocate_after_merge",
            expected_code_hash=args.expected_code_hash,
            scope="pilot",
            run_label=args.run_label,
            retention_report=ROOT / "reports/pilot_raw_checkpoint_retention.md",
            evaluation_marker=None,
            code_bundle_paths=PILOT_CODE_BUNDLE_PATHS,
        )


if __name__ == "__main__":
    main()
