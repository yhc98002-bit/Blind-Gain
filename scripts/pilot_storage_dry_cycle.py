#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import functools
import hashlib
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.relocate_easyr1_raw_checkpoint import relocate_raw_checkpoint  # noqa: E402
from scripts.relocate_merged_checkpoint import relocate_merged_checkpoint  # noqa: E402
from src.ops.storage_guard import (  # noqa: E402
    DEFAULT_SHARED_QUOTA_BYTES,
    allocated_bytes_from_snapshot,
    append_guard_log,
    check_storage,
)


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _assert_child(path: Path, parent: Path, label: str) -> None:
    if not path.resolve().is_relative_to(parent.resolve()):
        raise ValueError(f"{label} must be under {parent}: {path}")


def _write_synthetic_easy_r1_checkpoint(actor_dir: Path) -> dict[str, str]:
    if actor_dir.exists():
        raise FileExistsError(f"refusing to overwrite dry checkpoint: {actor_dir}")
    huggingface = actor_dir / "huggingface"
    huggingface.mkdir(parents=True)
    payloads = {
        actor_dir / "model_world_size_1_rank_0.pt": b"blind-gains-l0-model-state-v1\n",
        actor_dir / "optim_world_size_1_rank_0.pt": b"blind-gains-l0-optimizer-state-v1\n",
        huggingface / "model-00001-of-00001.safetensors": b"blind-gains-l0-merged-state-v1\n",
    }
    for path, content in payloads.items():
        path.write_bytes(content)
    index = {
        "metadata": {"format": "synthetic-storage-cycle"},
        "weight_map": {"dry.weight": "model-00001-of-00001.safetensors"},
    }
    (huggingface / "model.safetensors.index.json").write_text(
        json.dumps(index, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        str(path.relative_to(actor_dir)): _sha256(path)
        for path in sorted(actor_dir.rglob("*"))
        if path.is_file()
    }


def run_cycle(
    *,
    shared_checkpoint_root: Path,
    archive_root: Path,
    run_manifest: Path,
    result_path: Path,
    usage_snapshot: Path,
    quota_root: Path,
    guard_log: Path,
    approved_shared_root: Path,
    approved_archive_root: Path,
    quota_bytes: int = DEFAULT_SHARED_QUOTA_BYTES,
) -> dict[str, Any]:
    _assert_child(shared_checkpoint_root, approved_shared_root, "shared checkpoint root")
    _assert_child(archive_root, approved_archive_root, "archive root")
    if not run_manifest.is_file():
        raise FileNotFoundError(f"run manifest is missing: {run_manifest}")
    if result_path.exists() or shared_checkpoint_root.exists() or archive_root.exists():
        raise FileExistsError("dry-cycle outputs are immutable and already exist")

    step_dir = shared_checkpoint_root / "global_step_1"
    actor_dir = step_dir / "actor"
    guard = check_storage(
        tier="S",
        path=actor_dir,
        operation="pilot_l0_dry_checkpoint_save",
        required_bytes=4 * 1024 * 1024,
        shared_quota_root=quota_root,
        shared_quota_bytes=quota_bytes,
        usage_probe=functools.partial(
            allocated_bytes_from_snapshot,
            usage_snapshot,
            max_age_seconds=6 * 60 * 60,
        ),
    )
    append_guard_log(guard_log, guard)
    if not guard.allowed:
        raise RuntimeError(guard.reason)

    source_hashes = _write_synthetic_easy_r1_checkpoint(actor_dir)
    raw_archive = archive_root / "global_step_1" / "actor"
    raw_result = relocate_raw_checkpoint(
        actor_dir,
        raw_archive,
        run_archive_root=archive_root,
        run_manifest=run_manifest,
        retention_report=ROOT / "reports" / "pilot_raw_checkpoint_retention.md",
        guard_log=guard_log,
    )
    merged_archive = raw_archive / "huggingface"
    merged_result = relocate_merged_checkpoint(
        actor_dir / "huggingface",
        merged_archive,
        guard_log=guard_log,
    )

    archived_hashes = {
        str(path.relative_to(raw_archive)): _sha256(path)
        for path in sorted(raw_archive.rglob("*"))
        if path.is_file() and not path.name.endswith(".sha256")
    }
    expected_hashes = {
        name: digest
        for name, digest in source_hashes.items()
        if name.startswith("model_world_size_") or name.startswith("optim_world_size_")
    }
    expected_hashes.update(
        {
            f"huggingface/{name.removeprefix('huggingface/')}": digest
            for name, digest in source_hashes.items()
            if name.startswith("huggingface/")
        }
    )
    checks = {
        "shared_guard_passed": guard.allowed,
        "raw_source_swept": not any(actor_dir.glob("*_world_size_*_rank_*.pt")),
        "merged_source_swept": not (actor_dir / "huggingface").exists(),
        "raw_marker_persisted": (actor_dir / "RAW_STATE_RELOCATED.json").is_file(),
        "merged_marker_persisted": (actor_dir / "MERGED_CHECKPOINT_RELOCATED.json").is_file(),
        "raw_archive_manifest_present": (raw_archive / "raw_training_state.source.sha256").is_file(),
        "merged_archive_manifest_present": (
            merged_archive / "merged_checkpoint.source.sha256"
        ).is_file(),
        "archive_readback_hashes_match": all(
            archived_hashes.get(name) == digest for name, digest in expected_hashes.items()
        ),
        "all_source_payloads_read_back": set(expected_hashes).issubset(archived_hashes),
    }
    payload = {
        "schema_version": 1,
        "status": "pass" if all(checks.values()) else "fail",
        "completed_at_utc": _utc_now(),
        "shared_checkpoint_root": str(shared_checkpoint_root),
        "archive_root": str(archive_root),
        "checks": checks,
        "source_hashes": source_hashes,
        "archived_payload_hashes": archived_hashes,
        "raw_relocation": raw_result,
        "merged_relocation": merged_result,
        "shared_save_guard": asdict(guard),
    }
    _atomic_json(result_path, payload)
    if payload["status"] != "pass":
        raise RuntimeError(f"pilot storage dry cycle failed: {checks}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shared-checkpoint-root", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument(
        "--usage-snapshot",
        type=Path,
        default=ROOT / "reports" / "storage_usage_snapshot.json",
    )
    parser.add_argument(
        "--quota-root",
        type=Path,
        default=Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289"),
    )
    parser.add_argument("--guard-log", type=Path, default=ROOT / "logs" / "storage_guard.jsonl")
    parser.add_argument(
        "--approved-shared-root",
        type=Path,
        default=ROOT / "checkpoints" / "pilot",
    )
    parser.add_argument(
        "--approved-archive-root",
        type=Path,
        default=Path("/tmp/blindgain_checkpoint_archive/pilot"),
    )
    args = parser.parse_args()
    payload = run_cycle(
        shared_checkpoint_root=args.shared_checkpoint_root,
        archive_root=args.archive_root,
        run_manifest=args.run_manifest,
        result_path=args.result,
        usage_snapshot=args.usage_snapshot,
        quota_root=args.quota_root,
        guard_log=args.guard_log,
        approved_shared_root=args.approved_shared_root,
        approved_archive_root=args.approved_archive_root,
    )
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
