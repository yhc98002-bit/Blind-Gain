from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Mapping

from src.ops.storage_guard import (
    DEFAULT_SCRATCH_FLOOR_BYTES,
    DEFAULT_SHARED_FLOOR_BYTES,
    DEFAULT_SHARED_QUOTA_BYTES,
    GuardResult,
    StorageGuardRefusal,
    allocated_bytes,
    append_guard_log,
    check_storage,
    disk_free_bytes,
    filesystem_type,
)


DEFAULT_SHARED_QUOTA_ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289")


def guard_easyr1_checkpoint_save(
    checkpoint_root: str | Path,
    global_step: int,
    *,
    environment: Mapping[str, str] | None = None,
    usage_probe: Callable[[Path], int] = allocated_bytes,
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

    path = Path(checkpoint_root) / f"global_step_{global_step}"
    result = check_storage(
        tier=tier,
        path=path,
        operation=f"easyr1_checkpoint_save_step_{global_step}",
        required_bytes=required_bytes,
        shared_quota_root=Path(env.get("BLIND_GAINS_SHARED_QUOTA_ROOT", DEFAULT_SHARED_QUOTA_ROOT)),
        shared_quota_bytes=int(env.get("BLIND_GAINS_SHARED_QUOTA_BYTES", DEFAULT_SHARED_QUOTA_BYTES)),
        shared_floor_bytes=int(env.get("BLIND_GAINS_SHARED_FLOOR_BYTES", DEFAULT_SHARED_FLOOR_BYTES)),
        scratch_floor_bytes=int(env.get("BLIND_GAINS_SCRATCH_FLOOR_BYTES", DEFAULT_SCRATCH_FLOOR_BYTES)),
        usage_probe=usage_probe,
        free_probe=free_probe,
        filesystem_probe=filesystem_probe,
        reject_memory_filesystem=env.get("BLIND_GAINS_ALLOW_MEMORY_SCRATCH") != "1",
    )
    log_path = Path(env.get("BLIND_GAINS_STORAGE_GUARD_LOG", "logs/storage_guard.jsonl"))
    append_guard_log(log_path, result)
    if not result.allowed:
        raise StorageGuardRefusal(result)
    return result

