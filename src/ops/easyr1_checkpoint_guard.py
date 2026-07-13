from __future__ import annotations

import datetime as dt
import functools
import json
import os
import time
from pathlib import Path
from typing import Callable, Mapping

from src.ops.storage_guard import (
    DEFAULT_SCRATCH_FLOOR_BYTES,
    DEFAULT_SHARED_FLOOR_BYTES,
    DEFAULT_SHARED_QUOTA_BYTES,
    GuardResult,
    StorageGuardRefusal,
    allocated_bytes_from_snapshot,
    append_guard_log,
    check_storage,
    disk_free_bytes,
    filesystem_type,
)


DEFAULT_SHARED_QUOTA_ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289")
DEFAULT_SHARED_USAGE_SNAPSHOT = (
    Path(__file__).resolve().parents[2] / "reports" / "storage_usage_snapshot.json"
)


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _probe_refusal(
    *,
    tier: str,
    path: Path,
    global_step: int,
    required_bytes: int,
    shared_quota_bytes: int,
    shared_floor_bytes: int,
    scratch_floor_bytes: int,
    error: Exception,
) -> GuardResult:
    return GuardResult(
        schema_version=1,
        event="storage_guard",
        checked_at_utc=_utc_now(),
        status="refused",
        tier=tier,  # type: ignore[arg-type]
        operation=f"easyr1_checkpoint_save_step_{global_step}",
        path=str(path),
        required_bytes=required_bytes,
        capacity_bytes=shared_quota_bytes if tier == "S" else None,
        used_bytes=None,
        free_bytes_before=0,
        free_bytes_after=0,
        floor_bytes=shared_floor_bytes if tier == "S" else scratch_floor_bytes,
        filesystem_type=None,
        reason=(
            "storage probe unavailable; checkpoint save refused: "
            f"{type(error).__name__}: {error}"
        ),
    )


def _snapshot_usage_probe(environment: Mapping[str, str]) -> Callable[[Path], int]:
    snapshot = Path(
        environment.get(
            "BLIND_GAINS_SHARED_USAGE_SNAPSHOT", str(DEFAULT_SHARED_USAGE_SNAPSHOT)
        )
    )
    try:
        max_age_seconds = int(
            environment.get(
                "BLIND_GAINS_SHARED_USAGE_SNAPSHOT_MAX_AGE_SECONDS", str(6 * 60 * 60)
            )
        )
    except ValueError as error:
        raise ValueError(
            "BLIND_GAINS_SHARED_USAGE_SNAPSHOT_MAX_AGE_SECONDS must be an integer"
        ) from error
    if max_age_seconds < 0:
        raise ValueError(
            "BLIND_GAINS_SHARED_USAGE_SNAPSHOT_MAX_AGE_SECONDS must be nonnegative"
        )
    return functools.partial(
        allocated_bytes_from_snapshot,
        snapshot,
        max_age_seconds=max_age_seconds,
    )


def guard_easyr1_checkpoint_save(
    checkpoint_root: str | Path,
    global_step: int,
    *,
    environment: Mapping[str, str] | None = None,
    usage_probe: Callable[[Path], int] | None = None,
    free_probe: Callable[[Path], int] = disk_free_bytes,
    filesystem_probe: Callable[[Path], str] = filesystem_type,
) -> GuardResult | None:
    env = os.environ if environment is None else environment
    if env.get("BLIND_GAINS_STORAGE_GUARD_ENABLED") != "1":
        return None

    tier = env.get("BLIND_GAINS_CHECKPOINT_TIER")
    if tier not in {"S", "T"}:
        raise ValueError("BLIND_GAINS_CHECKPOINT_TIER must be S or T when the guard is enabled")
    required_text = env.get("BLIND_GAINS_CHECKPOINT_REQUIRED_BYTES")
    if required_text is None:
        raise ValueError("BLIND_GAINS_CHECKPOINT_REQUIRED_BYTES is required when the guard is enabled")
    try:
        required_bytes = int(required_text)
    except ValueError as error:
        raise ValueError("BLIND_GAINS_CHECKPOINT_REQUIRED_BYTES must be an integer") from error
    if required_bytes <= 0:
        raise ValueError("BLIND_GAINS_CHECKPOINT_REQUIRED_BYTES must be positive")

    shared_quota_bytes = int(
        env.get("BLIND_GAINS_SHARED_QUOTA_BYTES", DEFAULT_SHARED_QUOTA_BYTES)
    )
    shared_floor_bytes = int(
        env.get("BLIND_GAINS_SHARED_FLOOR_BYTES", DEFAULT_SHARED_FLOOR_BYTES)
    )
    scratch_floor_bytes = int(
        env.get("BLIND_GAINS_SCRATCH_FLOOR_BYTES", DEFAULT_SCRATCH_FLOOR_BYTES)
    )
    path = Path(checkpoint_root) / f"global_step_{global_step}"
    effective_usage_probe = usage_probe or _snapshot_usage_probe(env)
    log_path = Path(env.get("BLIND_GAINS_STORAGE_GUARD_LOG", "logs/storage_guard.jsonl"))
    try:
        result = check_storage(
            tier=tier,
            path=path,
            operation=f"easyr1_checkpoint_save_step_{global_step}",
            required_bytes=required_bytes,
            shared_quota_root=Path(
                env.get("BLIND_GAINS_SHARED_QUOTA_ROOT", DEFAULT_SHARED_QUOTA_ROOT)
            ),
            shared_quota_bytes=shared_quota_bytes,
            shared_floor_bytes=shared_floor_bytes,
            scratch_floor_bytes=scratch_floor_bytes,
            usage_probe=effective_usage_probe,
            free_probe=free_probe,
            filesystem_probe=filesystem_probe,
            reject_memory_filesystem=env.get("BLIND_GAINS_ALLOW_MEMORY_SCRATCH")
            != "1",
        )
    except (OSError, RuntimeError, json.JSONDecodeError) as error:
        result = _probe_refusal(
            tier=tier,
            path=path,
            global_step=global_step,
            required_bytes=required_bytes,
            shared_quota_bytes=shared_quota_bytes,
            shared_floor_bytes=shared_floor_bytes,
            scratch_floor_bytes=scratch_floor_bytes,
            error=error,
        )
    append_guard_log(log_path, result)
    if not result.allowed:
        raise StorageGuardRefusal(result)
    return result


def wait_for_easyr1_checkpoint_storage(
    checkpoint_root: str | Path,
    global_step: int,
    *,
    environment: Mapping[str, str] | None = None,
    usage_probe: Callable[[Path], int] | None = None,
    free_probe: Callable[[Path], int] = disk_free_bytes,
    filesystem_probe: Callable[[Path], str] = filesystem_type,
    sleep: Callable[[float], None] = time.sleep,
) -> GuardResult | None:
    """Wait for quota headroom instead of terminating a pilot at a save boundary."""
    env = os.environ if environment is None else environment
    retry_text = env.get("BLIND_GAINS_STORAGE_GUARD_RETRY_SECONDS", "300")
    attempts_text = env.get("BLIND_GAINS_STORAGE_GUARD_MAX_ATTEMPTS", "0")
    try:
        retry_seconds = float(retry_text)
        max_attempts = int(attempts_text)
    except ValueError as error:
        raise ValueError("storage guard retry settings must be numeric") from error
    if retry_seconds < 0 or max_attempts < 0:
        raise ValueError("storage guard retry settings must be nonnegative")

    attempt = 0
    while True:
        attempt += 1
        try:
            return guard_easyr1_checkpoint_save(
                checkpoint_root,
                global_step,
                environment=env,
                usage_probe=usage_probe,
                free_probe=free_probe,
                filesystem_probe=filesystem_probe,
            )
        except StorageGuardRefusal:
            if max_attempts and attempt >= max_attempts:
                raise
            sleep(retry_seconds)
