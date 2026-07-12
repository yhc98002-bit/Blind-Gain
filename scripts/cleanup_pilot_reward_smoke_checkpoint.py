#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite retention record: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _replace_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.retention.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _resolve_recorded_path(value: str, *, root: Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def validate_cleanup_contract(
    run_manifest_path: Path,
    audit_path: Path,
    *,
    root: Path = ROOT,
) -> tuple[dict[str, Any], Path]:
    manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    run_id = str(manifest.get("run_id", ""))
    expected_checkpoint = (root / "checkpoints" / "smoke" / run_id).resolve()
    checkpoint_path = _resolve_recorded_path(
        str(manifest.get("checkpoint_path", "")), root=root
    )
    audited_manifest = _resolve_recorded_path(str(audit.get("run_manifest", "")), root=root)
    existing_events = manifest.get("storage_retention_events", [])
    checks = {
        "run_complete": manifest.get("status") == "complete"
        and manifest.get("exit_code") == 0,
        "run_type_exact": manifest.get("job_type") == "l3_pilot_reward_plumbing_smoke",
        "run_id_matches_directory": run_id == run_manifest_path.parent.name,
        "checkpoint_namespace_exact": checkpoint_path == expected_checkpoint,
        "audit_v5_pass": audit.get("schema_version")
        == "blind-gains.pilot-reward-smoke-audit.v5"
        and audit.get("status") == "pass",
        "audit_targets_run_manifest": audited_manifest == run_manifest_path.resolve(),
        "placement_audit_pass": audit.get("placement_audit", {}).get("status") == "pass"
        and all(audit.get("placement_audit", {}).get("checks", {}).values()),
        "retention_event_absent": isinstance(existing_events, list)
        and not any(
            isinstance(item, dict)
            and item.get("checkpoint_path") == str(checkpoint_path)
            for item in existing_events
        ),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError(f"pilot smoke checkpoint cleanup contract failed: {failed}")
    if not checkpoint_path.is_dir():
        raise FileNotFoundError(f"pilot smoke checkpoint path is absent: {checkpoint_path}")
    step_dirs = sorted(path.name for path in checkpoint_path.glob("global_step_*") if path.is_dir())
    if step_dirs != ["global_step_5"]:
        raise ValueError(f"expected only global_step_5 in smoke checkpoint, found {step_dirs}")
    return manifest, checkpoint_path


def cleanup_checkpoint(
    run_manifest_path: Path,
    audit_path: Path,
    checksum_path: Path,
    predelete_record_path: Path,
    deletion_record_path: Path,
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    manifest, checkpoint_path = validate_cleanup_contract(
        run_manifest_path, audit_path, root=root
    )
    paths = sorted(checkpoint_path.rglob("*"))
    if any(path.is_symlink() for path in paths):
        raise ValueError("smoke checkpoint cleanup refuses symbolic links")
    files = [path for path in paths if path.is_file()]
    if not files:
        raise ValueError("smoke checkpoint contains no files")
    records = [
        {
            "file": str(path.relative_to(checkpoint_path)),
            "sha256": _sha256(path),
            "size_bytes": path.stat().st_size,
        }
        for path in files
    ]
    total_bytes = sum(record["size_bytes"] for record in records)
    checksum_text = "".join(
        f"{record['sha256']}  {record['file']}\n" for record in records
    )
    if checksum_path.exists():
        raise FileExistsError(f"refusing to overwrite checksum manifest: {checksum_path}")
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_checksum = checksum_path.with_name(
        f".{checksum_path.name}.partial.{os.getpid()}"
    )
    with temporary_checksum.open("x", encoding="ascii") as handle:
        handle.write(checksum_text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary_checksum, checksum_path)
    checksum_sha256 = _sha256(checksum_path)
    common = {
        "schema_version": "blind-gains.pilot-smoke-checkpoint-retention.v1",
        "run_id": manifest["run_id"],
        "checkpoint_path": str(checkpoint_path),
        "classification": "retention-expired",
        "reason": "Completed five-step plumbing smoke is not a registered pilot endpoint or resume source.",
        "size_bytes": total_bytes,
        "file_count": len(records),
        "checksum_manifest": str(checksum_path),
        "checksum_manifest_sha256": checksum_sha256,
        "files": records,
        "audit_path": str(audit_path),
        "audit_sha256": _sha256(audit_path),
    }
    _atomic_json(
        predelete_record_path,
        {
            **common,
            "status": "retention-expired-listed-before-deletion",
            "recorded_at_utc": dt.datetime.now(dt.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
        },
    )

    current_files = sorted(path for path in checkpoint_path.rglob("*") if path.is_file())
    current_names = [str(path.relative_to(checkpoint_path)) for path in current_files]
    if current_names != [record["file"] for record in records]:
        raise RuntimeError("smoke checkpoint file set changed after predelete listing")
    for path, record in zip(current_files, records):
        if path.stat().st_size != record["size_bytes"] or _sha256(path) != record["sha256"]:
            raise RuntimeError(f"smoke checkpoint changed before deletion: {path}")

    shutil.rmtree(checkpoint_path)
    if checkpoint_path.exists():
        raise RuntimeError(f"smoke checkpoint remains after deletion: {checkpoint_path}")
    deleted_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    deletion_payload = {
        **common,
        "status": "deleted",
        "deleted_at_utc": deleted_at,
        "path_absent_after_deletion": True,
    }
    _atomic_json(deletion_record_path, deletion_payload)

    event = {
        "event": "checkpoint_retention",
        "status": "retention-expired-deleted",
        "checkpoint_path": str(checkpoint_path),
        "size_bytes": total_bytes,
        "file_count": len(records),
        "checksum_manifest": str(checksum_path),
        "checksum_manifest_sha256": checksum_sha256,
        "predelete_record": str(predelete_record_path),
        "deletion_record": str(deletion_record_path),
        "recorded_at_utc": deleted_at,
    }
    events = manifest.setdefault("storage_retention_events", [])
    events.append(event)
    _replace_json(run_manifest_path, manifest)
    return deletion_payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--checksum-output", type=Path, required=True)
    parser.add_argument("--predelete-record", type=Path, required=True)
    parser.add_argument("--deletion-record", type=Path, required=True)
    args = parser.parse_args()
    payload = cleanup_checkpoint(
        args.run_manifest,
        args.audit,
        args.checksum_output,
        args.predelete_record,
        args.deletion_record,
    )
    print(json.dumps({"status": payload["status"], "bytes": payload["size_bytes"]}))


if __name__ == "__main__":
    main()
