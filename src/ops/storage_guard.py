from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Literal


GIB = 1024**3
DEFAULT_SHARED_QUOTA_BYTES = 500 * GIB
DEFAULT_SHARED_FLOOR_BYTES = 20 * GIB
DEFAULT_SCRATCH_FLOOR_BYTES = 40 * GIB
MEMORY_FILESYSTEMS = frozenset({"tmpfs", "ramfs"})

Tier = Literal["S", "T"]


@dataclass(frozen=True)
class GuardResult:
    schema_version: int
    event: str
    checked_at_utc: str
    status: Literal["pass", "refused"]
    tier: Tier
    operation: str
    path: str
    required_bytes: int
    capacity_bytes: int | None
    used_bytes: int | None
    free_bytes_before: int
    free_bytes_after: int
    floor_bytes: int
    filesystem_type: str | None
    reason: str

    @property
    def allowed(self) -> bool:
        return self.status == "pass"


class StorageGuardRefusal(RuntimeError):
    def __init__(self, result: GuardResult):
        self.result = result
        super().__init__(result.reason)


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def nearest_existing_path(path: Path) -> Path:
    candidate = path.expanduser().absolute()
    while not candidate.exists():
        parent = candidate.parent
        if parent == candidate:
            raise FileNotFoundError(f"no existing ancestor for storage path: {path}")
        candidate = parent
    return candidate


def allocated_bytes(root: Path, *, timeout_seconds: int = 600) -> int:
    """Return allocated bytes; unlike df, this reflects this quota subtree only."""
    completed = subprocess.run(
        ["du", "-sx", "--block-size=1", str(root)],
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    first_field = completed.stdout.strip().split(maxsplit=1)[0]
    try:
        value = int(first_field)
    except ValueError as error:
        raise RuntimeError(f"could not parse allocated-byte probe: {completed.stdout!r}") from error
    if value < 0:
        raise RuntimeError(f"allocated-byte probe returned a negative value: {value}")
    return value


def allocated_bytes_from_snapshot(
    snapshot_path: Path,
    quota_root: Path,
    *,
    max_age_seconds: int = 6 * 60 * 60,
    now: dt.datetime | None = None,
) -> int:
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if payload.get("status") != "pass":
        raise RuntimeError(f"storage usage snapshot is not pass: {snapshot_path}")
    recorded_root = Path(str(payload.get("quota_root", ""))).resolve()
    if recorded_root != quota_root.resolve():
        raise RuntimeError(
            f"storage usage snapshot root mismatch: expected {quota_root}, found {recorded_root}"
        )
    measured_text = payload.get("measured_at_utc")
    if not isinstance(measured_text, str):
        raise RuntimeError("storage usage snapshot has no measured_at_utc")
    try:
        measured = dt.datetime.fromisoformat(measured_text.replace("Z", "+00:00"))
    except ValueError as error:
        raise RuntimeError("storage usage snapshot timestamp is invalid") from error
    if measured.tzinfo is None:
        raise RuntimeError("storage usage snapshot timestamp has no timezone")
    if max_age_seconds < 0:
        raise ValueError("max_age_seconds must be nonnegative")
    current = now or dt.datetime.now(dt.timezone.utc)
    age_seconds = (current - measured).total_seconds()
    if age_seconds < 0 or age_seconds > max_age_seconds:
        raise RuntimeError(
            f"storage usage snapshot is stale or future-dated: age_seconds={age_seconds:.1f}"
        )
    used_bytes = payload.get("used_bytes")
    if not isinstance(used_bytes, int) or used_bytes < 0:
        raise RuntimeError("storage usage snapshot used_bytes is invalid")
    return used_bytes


def disk_free_bytes(path: Path) -> int:
    return shutil.disk_usage(nearest_existing_path(path)).free


def filesystem_type(path: Path) -> str:
    completed = subprocess.run(
        ["findmnt", "-T", str(nearest_existing_path(path)), "-n", "-o", "FSTYPE"],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip().splitlines()[0]


def evaluate_shared_guard(
    *,
    path: Path,
    operation: str,
    required_bytes: int,
    used_bytes: int,
    quota_bytes: int = DEFAULT_SHARED_QUOTA_BYTES,
    floor_bytes: int = DEFAULT_SHARED_FLOOR_BYTES,
    checked_at_utc: str | None = None,
) -> GuardResult:
    _validate_inputs(required_bytes, used_bytes, quota_bytes, floor_bytes)
    before = quota_bytes - used_bytes
    after = before - required_bytes
    allowed = after >= floor_bytes
    reason = (
        "shared quota headroom remains at or above the configured floor"
        if allowed
        else "shared write would leave less than the configured quota headroom"
    )
    return GuardResult(
        schema_version=1,
        event="storage_guard",
        checked_at_utc=checked_at_utc or _utc_now(),
        status="pass" if allowed else "refused",
        tier="S",
        operation=operation,
        path=str(path),
        required_bytes=required_bytes,
        capacity_bytes=quota_bytes,
        used_bytes=used_bytes,
        free_bytes_before=before,
        free_bytes_after=after,
        floor_bytes=floor_bytes,
        filesystem_type=None,
        reason=reason,
    )


def evaluate_scratch_guard(
    *,
    path: Path,
    operation: str,
    required_bytes: int,
    free_bytes: int,
    floor_bytes: int = DEFAULT_SCRATCH_FLOOR_BYTES,
    fs_type: str | None = None,
    reject_memory_filesystem: bool = True,
    checked_at_utc: str | None = None,
) -> GuardResult:
    if free_bytes < 0:
        raise ValueError("free_bytes must be nonnegative")
    _validate_inputs(required_bytes, 0, max(free_bytes, 0), floor_bytes)
    after = free_bytes - required_bytes
    memory_backed = reject_memory_filesystem and fs_type in MEMORY_FILESYSTEMS
    enough_space = after >= floor_bytes
    allowed = enough_space and not memory_backed
    if memory_backed:
        reason = "scratch target is memory-backed and cannot hold process-survival artifacts"
    elif not enough_space:
        reason = "scratch write would leave less than the configured free-space floor"
    else:
        reason = "scratch free space remains at or above the configured floor"
    return GuardResult(
        schema_version=1,
        event="storage_guard",
        checked_at_utc=checked_at_utc or _utc_now(),
        status="pass" if allowed else "refused",
        tier="T",
        operation=operation,
        path=str(path),
        required_bytes=required_bytes,
        capacity_bytes=None,
        used_bytes=None,
        free_bytes_before=free_bytes,
        free_bytes_after=after,
        floor_bytes=floor_bytes,
        filesystem_type=fs_type,
        reason=reason,
    )


def check_storage(
    *,
    tier: Tier,
    path: Path,
    operation: str,
    required_bytes: int,
    shared_quota_root: Path | None = None,
    shared_quota_bytes: int = DEFAULT_SHARED_QUOTA_BYTES,
    shared_floor_bytes: int = DEFAULT_SHARED_FLOOR_BYTES,
    scratch_floor_bytes: int = DEFAULT_SCRATCH_FLOOR_BYTES,
    usage_probe: Callable[[Path], int] = allocated_bytes,
    free_probe: Callable[[Path], int] = disk_free_bytes,
    filesystem_probe: Callable[[Path], str] = filesystem_type,
    reject_memory_filesystem: bool = True,
) -> GuardResult:
    if tier == "S":
        if shared_quota_root is None:
            raise ValueError("shared_quota_root is required for Tier S")
        used = usage_probe(shared_quota_root)
        return evaluate_shared_guard(
            path=path,
            operation=operation,
            required_bytes=required_bytes,
            used_bytes=used,
            quota_bytes=shared_quota_bytes,
            floor_bytes=shared_floor_bytes,
        )
    if tier == "T":
        return evaluate_scratch_guard(
            path=path,
            operation=operation,
            required_bytes=required_bytes,
            free_bytes=free_probe(path),
            floor_bytes=scratch_floor_bytes,
            fs_type=filesystem_probe(path),
            reject_memory_filesystem=reject_memory_filesystem,
        )
    raise ValueError(f"unsupported storage tier: {tier}")


def append_guard_log(path: Path, result: GuardResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(asdict(result), sort_keys=True) + "\n"
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o664)
    try:
        os.write(descriptor, line.encode("utf-8"))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def require_storage(**kwargs: object) -> GuardResult:
    result = check_storage(**kwargs)  # type: ignore[arg-type]
    if not result.allowed:
        raise StorageGuardRefusal(result)
    return result


def _validate_inputs(required_bytes: int, used_bytes: int, capacity_bytes: int, floor_bytes: int) -> None:
    values = {
        "required_bytes": required_bytes,
        "used_bytes": used_bytes,
        "capacity_bytes": capacity_bytes,
        "floor_bytes": floor_bytes,
    }
    negative = [name for name, value in values.items() if value < 0]
    if negative:
        raise ValueError(f"storage values must be nonnegative: {', '.join(negative)}")
