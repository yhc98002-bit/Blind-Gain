#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import functools
import hashlib
import json
import os
import re
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SHARED_QUOTA_ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289")
CURRENT_USAGE_SNAPSHOT = ROOT / "reports" / "storage_usage_snapshot.json"
RAW_RE = re.compile(r"^(model|optim)_world_size_(\d+)_rank_(\d+)\.pt$")


@dataclass(frozen=True)
class RawSignature:
    world_size: int
    files: tuple[tuple[str, int, int], ...]


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def raw_signature(actor_dir: Path) -> RawSignature | None:
    families: dict[str, tuple[int, set[int]]] = {}
    records: list[tuple[str, int, int]] = []
    for path in sorted(actor_dir.glob("*_world_size_*_rank_*.pt")):
        match = RAW_RE.fullmatch(path.name)
        if not match:
            continue
        family, world_text, rank_text = match.groups()
        world_size = int(world_text)
        rank = int(rank_text)
        if family not in families:
            families[family] = (world_size, set())
        registered_world, ranks = families[family]
        if registered_world != world_size or rank in ranks:
            return None
        ranks.add(rank)
        try:
            stat = path.stat()
        except OSError:
            return None
        if stat.st_size <= 0:
            return None
        records.append((path.name, stat.st_size, stat.st_mtime_ns))
    if set(families) != {"model", "optim"}:
        return None
    model_world, model_ranks = families["model"]
    optim_world, optim_ranks = families["optim"]
    expected = set(range(model_world))
    if model_world != optim_world or model_ranks != expected or optim_ranks != expected:
        return None
    return RawSignature(world_size=model_world, files=tuple(records))


def tracker_reached(run_root: Path, step: int) -> bool:
    tracker = run_root / "checkpoint_tracker.json"
    if not tracker.is_file():
        return False
    try:
        payload = json.loads(tracker.read_text(encoding="utf-8"))
        return int(payload.get("last_global_step", -1)) >= step
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return False


def valid_relocation_marker(actor_dir: Path, name: str) -> bool:
    marker = actor_dir / name
    if not marker.is_file():
        return False
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    expected = {
        "RAW_STATE_RELOCATED.json": "raw_training_state_relocated_due_to_shared_quota",
        "MERGED_CHECKPOINT_RELOCATED.json": "merged_checkpoint_relocated",
    }
    return payload.get("status") == expected[name] and Path(str(payload.get("archive_path", ""))).exists()


def wait_for_stable_checkpoint(run_root: Path, step: int, poll_seconds: int) -> Path:
    actor_dir = run_root / f"global_step_{step}" / "actor"
    previous: RawSignature | None = None
    while True:
        if tracker_reached(run_root, step) and valid_relocation_marker(
            actor_dir, "RAW_STATE_RELOCATED.json"
        ):
            return actor_dir
        current = raw_signature(actor_dir) if tracker_reached(run_root, step) else None
        if current is not None and current == previous:
            return actor_dir
        previous = current
        time.sleep(poll_seconds)


def merged_checkpoint_complete(huggingface_dir: Path) -> bool:
    index_path = huggingface_dir / "model.safetensors.index.json"
    if not index_path.is_file():
        return False
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    weight_map = payload.get("weight_map")
    if not isinstance(weight_map, dict) or not weight_map:
        return False
    names = set(weight_map.values())
    if any(not isinstance(name, str) or Path(name).name != name for name in names):
        return False
    return all((huggingface_dir / name).is_file() for name in names)


def _git_hash() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def run_subjob(
    *,
    tag: str,
    job_type: str,
    node: str,
    command: str,
    data_manifest: str,
    data_manifest_hash: str | None,
    expected_artifacts: list[str],
    seed: int = 1,
) -> Path:
    run_id = f"{tag}_{_stamp()}"
    run_dir = ROOT / "experiments" / "runs" / run_id
    run_dir.mkdir(parents=True)
    log_path = run_dir / "logs" / f"{node}.log"
    log_path.parent.mkdir()
    manifest_path = run_dir / "run_manifest.json"
    config_hash = hashlib.sha256(command.encode("utf-8")).hexdigest()
    payload: dict[str, Any] = {
        "run_id": run_id,
        "job_type": job_type,
        "node": node,
        "gpu_allocation": [],
        "git_hash": _git_hash(),
        "config_hash": config_hash,
        "data_manifest": data_manifest,
        "data_manifest_hash": data_manifest_hash,
        "seed": seed,
        "command": command,
        "start_time_utc": _utc_now(),
        "end_time_utc": None,
        "status": "running",
        "expected_artifacts": expected_artifacts,
        "deviations": [],
    }
    _atomic_json(manifest_path, payload)
    with log_path.open("ab", buffering=0) as log:
        result = subprocess.run(
            command,
            cwd=ROOT,
            shell=True,
            executable="/bin/bash",
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    artifacts_exist = all(Path(path).exists() for path in expected_artifacts)
    payload.update(
        {
            "end_time_utc": _utc_now(),
            "exit_code": result.returncode,
            "artifacts_exist": artifacts_exist,
            "status": "complete" if result.returncode == 0 and artifacts_exist else "failed",
        }
    )
    _atomic_json(manifest_path, payload)
    if payload["status"] != "complete":
        raise RuntimeError(f"anchor checkpoint subjob failed: {run_dir}")
    return run_dir


def refresh_usage_snapshot(step: int, phase: str) -> Path:
    stamp = _stamp()
    versioned = ROOT / "reports" / f"storage_usage_snapshot_{stamp}.json"
    command = " && ".join(
        [
            shlex.join(
                [
                    str(ROOT / ".venv" / "bin" / "python"),
                    str(ROOT / "scripts" / "measure_storage_usage.py"),
                    "--output",
                    str(versioned),
                ]
            ),
            shlex.join(["cp", str(versioned), str(CURRENT_USAGE_SNAPSHOT)]),
        ]
    )
    return run_subjob(
        tag=f"storage_usage_anchor_step{step}_{phase}",
        job_type="anchor_storage_usage_refresh",
        node="login",
        command=command,
        data_manifest=str(SHARED_QUOTA_ROOT),
        data_manifest_hash=None,
        expected_artifacts=[str(versioned), str(CURRENT_USAGE_SNAPSHOT)],
    )


def guard_merge(actor_dir: Path, step: int) -> None:
    from src.ops.storage_guard import (
        StorageGuardRefusal,
        allocated_bytes_from_snapshot,
        append_guard_log,
        check_storage,
    )

    signature = raw_signature(actor_dir)
    if signature is None:
        raise RuntimeError(f"raw checkpoint became incomplete before merge: {actor_dir}")
    required_bytes = sum(size for name, size, _ in signature.files if name.startswith("model_"))
    result = check_storage(
        tier="S",
        path=actor_dir / "huggingface",
        operation=f"anchor_checkpoint_merge_step_{step}",
        required_bytes=required_bytes,
        shared_quota_root=SHARED_QUOTA_ROOT,
        usage_probe=functools.partial(
            allocated_bytes_from_snapshot,
            CURRENT_USAGE_SNAPSHOT,
            max_age_seconds=6 * 60 * 60,
        ),
    )
    append_guard_log(ROOT / "logs" / "storage_guard.jsonl", result)
    if not result.allowed:
        raise StorageGuardRefusal(result)


def merge_checkpoint(actor_dir: Path, step: int, node: str) -> Path | None:
    huggingface = actor_dir / "huggingface"
    if valid_relocation_marker(actor_dir, "MERGED_CHECKPOINT_RELOCATED.json"):
        return None
    if merged_checkpoint_complete(huggingface):
        return None
    if any(huggingface.glob("*.safetensors")):
        raise RuntimeError(f"partial merged checkpoint requires manual audit: {huggingface}")
    guard_merge(actor_dir, step)
    relative_actor = actor_dir.relative_to(ROOT)
    remote = " && ".join(
        [
            f"cd {shlex.quote(str(ROOT))}",
            " ".join(
                [
                    f"PYTHONPATH={shlex.quote(str(ROOT / 'artifacts/repos/EasyR1'))}",
                    "TRANSFORMERS_OFFLINE=1",
                    f"HF_HOME={shlex.quote(str(ROOT / 'artifacts/hf_home'))}",
                    shlex.quote(str(ROOT / ".venv/bin/python")),
                    "scripts/model_merger_no_deepspeed.py",
                    "--local_dir",
                    shlex.quote(str(relative_actor)),
                ]
            ),
        ]
    )
    command = shlex.join(["ssh", node, remote])
    signature = raw_signature(actor_dir)
    if signature is None:
        raise RuntimeError(f"raw checkpoint disappeared before merge launch: {actor_dir}")
    raw_hash = hashlib.sha256()
    for name, _, _ in signature.files:
        if name.startswith("model_"):
            raw_hash.update(f"{_sha256(actor_dir / name)}  {name}\n".encode("ascii"))
    if raw_signature(actor_dir) != signature:
        raise RuntimeError(f"raw checkpoint changed while hashing merge inputs: {actor_dir}")
    return run_subjob(
        tag=f"easyr1_checkpoint_merge_anchor_a0_step{step}_{node}",
        job_type="anchor_checkpoint_merge",
        node=node,
        command=command,
        data_manifest=str(actor_dir),
        data_manifest_hash=raw_hash.hexdigest(),
        expected_artifacts=[str(huggingface / "model.safetensors.index.json")],
    )


def relocate_raw(
    *,
    actor_dir: Path,
    archive_root: Path,
    anchor_manifest: Path,
    step: int,
) -> Path | None:
    marker = actor_dir / "RAW_STATE_RELOCATED.json"
    if valid_relocation_marker(actor_dir, marker.name):
        return None
    archive_dir = archive_root / f"global_step_{step}" / "actor"
    command = shlex.join(
        [
            str(ROOT / ".venv/bin/python"),
            str(ROOT / "scripts/relocate_easyr1_raw_checkpoint.py"),
            "--actor-dir",
            str(actor_dir),
            "--archive-dir",
            str(archive_dir),
            "--run-archive-root",
            str(archive_root),
            "--run-manifest",
            str(anchor_manifest),
            "--retention-report",
            str(ROOT / "reports/raw_checkpoint_retention.md"),
            "--guard-log",
            str(ROOT / "logs/storage_guard.jsonl"),
        ]
    )
    index = actor_dir / "huggingface/model.safetensors.index.json"
    return run_subjob(
        tag=f"easyr1_raw_relocation_anchor_a0_step{step}_login",
        job_type="anchor_raw_checkpoint_relocation",
        node="login",
        command=command,
        data_manifest=str(actor_dir),
        data_manifest_hash=_sha256(index),
        expected_artifacts=[str(archive_dir / "raw_training_state.source.sha256"), str(marker)],
    )


def relocate_merged(actor_dir: Path, archive_root: Path, step: int) -> Path | None:
    marker = actor_dir / "MERGED_CHECKPOINT_RELOCATED.json"
    if valid_relocation_marker(actor_dir, marker.name):
        return None
    source = actor_dir / "huggingface"
    archive = archive_root / f"global_step_{step}" / "actor" / "huggingface"
    command = shlex.join(
        [
            str(ROOT / ".venv/bin/python"),
            str(ROOT / "scripts/relocate_merged_checkpoint.py"),
            "--source-dir",
            str(source),
            "--archive-dir",
            str(archive),
            "--guard-log",
            str(ROOT / "logs/storage_guard.jsonl"),
        ]
    )
    index = source / "model.safetensors.index.json"
    return run_subjob(
        tag=f"easyr1_merged_relocation_anchor_a0_step{step}_login",
        job_type="anchor_merged_checkpoint_relocation",
        node="login",
        command=command,
        data_manifest=str(source),
        data_manifest_hash=_sha256(index),
        expected_artifacts=[str(archive / "merged_checkpoint.source.sha256"), str(marker)],
    )


def process_step(
    *,
    run_root: Path,
    archive_root: Path,
    anchor_manifest: Path,
    step: int,
    node: str,
    relocate_merged_output: bool,
) -> None:
    actor_dir = wait_for_stable_checkpoint(run_root, step, poll_seconds=60)
    refresh_usage_snapshot(step, "premerge")
    merge_checkpoint(actor_dir, step, node)
    refresh_usage_snapshot(step, "postmerge")
    relocate_raw(
        actor_dir=actor_dir,
        archive_root=archive_root,
        anchor_manifest=anchor_manifest,
        step=step,
    )
    if relocate_merged_output:
        relocate_merged(actor_dir, archive_root, step)
    refresh_usage_snapshot(step, "postrelocation")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--anchor-manifest", type=Path, required=True)
    parser.add_argument("--node", default="an12")
    args = parser.parse_args()
    process_step(
        run_root=args.run_root,
        archive_root=args.archive_root,
        anchor_manifest=args.anchor_manifest,
        step=80,
        node=args.node,
        relocate_merged_output=True,
    )
    process_step(
        run_root=args.run_root,
        archive_root=args.archive_root,
        anchor_manifest=args.anchor_manifest,
        step=100,
        node=args.node,
        relocate_merged_output=False,
    )


if __name__ == "__main__":
    main()
