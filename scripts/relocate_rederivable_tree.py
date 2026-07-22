#!/usr/bin/env python3
from __future__ import annotations

import argparse
import functools
import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ops.storage_guard import (
    DEFAULT_SHARED_FLOOR_BYTES,
    DEFAULT_SHARED_QUOTA_BYTES,
    Tier,
    allocated_bytes_from_snapshot,
    check_storage,
)


SCRATCH_FLOOR_BYTES = 40 * 1024**3
SHARED_QUOTA_ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289")
SHARED_USAGE_SNAPSHOT = (
    Path(__file__).resolve().parents[1] / "reports/storage_usage_snapshot.json"
)
ARTIFACT_CLASSES = frozenset({"rederivable", "persistent_training_state"})


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory_tree(root: Path) -> list[dict[str, Any]]:
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"source must be a real directory: {root}")
    records: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"source contains a symlink: {path}")
        if not path.is_file():
            continue
        stat = path.stat()
        records.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size_bytes": stat.st_size,
                "sha256": _sha256(path),
            }
        )
    return records


def validate_embedded_checksum_manifests(
    root: Path, inventory: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    by_path = {record["path"]: record for record in inventory}
    validated: list[dict[str, Any]] = []
    for manifest in sorted(root.rglob("*.source.sha256")):
        if manifest.is_symlink() or not manifest.is_file():
            raise ValueError(f"invalid embedded checksum manifest: {manifest}")
        targets: list[str] = []
        for line_number, line in enumerate(
            manifest.read_text(encoding="utf-8").splitlines(), 1
        ):
            digest, separator, raw_name = line.partition("  ")
            if separator != "  " or len(digest) != 64:
                raise ValueError(
                    f"malformed embedded checksum line {line_number}: {manifest}"
                )
            try:
                int(digest, 16)
            except ValueError as error:
                raise ValueError(
                    f"invalid embedded SHA256 line {line_number}: {manifest}"
                ) from error
            relative_name = Path(raw_name.removeprefix("./"))
            if (
                relative_name.is_absolute()
                or ".." in relative_name.parts
                or relative_name == Path(".")
            ):
                raise ValueError(
                    f"unsafe embedded checksum path line {line_number}: {manifest}"
                )
            target = (manifest.parent / relative_name).relative_to(root).as_posix()
            record = by_path.get(target)
            if record is None or record["sha256"] != digest:
                raise RuntimeError(
                    f"embedded checksum does not match inventoried source: {target}"
                )
            targets.append(target)
        if not targets:
            raise ValueError(f"empty embedded checksum manifest: {manifest}")
        validated.append(
            {
                "path": manifest.relative_to(root).as_posix(),
                "sha256": by_path[manifest.relative_to(root).as_posix()]["sha256"],
                "target_count": len(targets),
                "all_targets_match": True,
            }
        )
    return validated


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite JSON artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _read_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def prepare_relocation_plan(
    *,
    source: Path,
    destination: Path,
    plan_path: Path,
    operation: str,
    artifact_class: str,
) -> dict[str, Any]:
    if artifact_class not in ARTIFACT_CLASSES:
        raise ValueError(f"unsupported artifact class: {artifact_class}")
    source = source.resolve()
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"destination already exists: {destination}")
    inventory = inventory_tree(source)
    embedded_checksums = validate_embedded_checksum_manifests(source, inventory)
    if artifact_class == "persistent_training_state" and not embedded_checksums:
        raise ValueError("persistent training state has no embedded checksum manifest")
    payload = {
        "schema_version": "blind-gains.relocation-plan.v1",
        "status": "validated_not_executed",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "operation": operation,
        "artifact_class": artifact_class,
        "source": str(source),
        "destination": str(destination),
        "total_bytes": sum(record["size_bytes"] for record in inventory),
        "file_count": len(inventory),
        "files": inventory,
        "embedded_checksum_manifests": embedded_checksums,
    }
    _atomic_json(plan_path, payload)
    return payload


def validate_relocation_plan(
    *,
    plan_path: Path,
    source: Path,
    destination: Path,
    operation: str,
    artifact_class: str,
    observed_inventory: list[dict[str, Any]],
) -> dict[str, Any]:
    plan = _read_object(plan_path)
    checks = {
        "schema": plan.get("schema_version") == "blind-gains.relocation-plan.v1",
        "status": plan.get("status") == "validated_not_executed",
        "source": Path(str(plan.get("source", ""))).resolve() == source,
        "destination": Path(str(plan.get("destination", ""))).absolute() == destination,
        "operation": plan.get("operation") == operation,
        "artifact_class": plan.get("artifact_class") == artifact_class,
        "file_count": plan.get("file_count") == len(observed_inventory),
        "total_bytes": plan.get("total_bytes")
        == sum(record["size_bytes"] for record in observed_inventory),
        "inventory": plan.get("files") == observed_inventory,
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise RuntimeError(
            "source/destination differs from the immutable relocation plan: "
            + ", ".join(failed)
        )
    return {
        "path": str(plan_path),
        "sha256": _sha256(plan_path),
        "checks": checks,
    }


def relocate_tree(
    *,
    source: Path,
    destination: Path,
    manifest_path: Path,
    operation: str,
    destination_tier: Tier,
    artifact_class: str = "rederivable",
    expected_plan_path: Path | None = None,
    shared_quota_root: Path = SHARED_QUOTA_ROOT,
    shared_usage_snapshot: Path = SHARED_USAGE_SNAPSHOT,
) -> dict[str, Any]:
    if artifact_class not in ARTIFACT_CLASSES:
        raise ValueError(f"unsupported artifact class: {artifact_class}")
    source = source.resolve()
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"destination already exists: {destination}")
    if manifest_path.exists():
        raise FileExistsError(f"manifest already exists: {manifest_path}")

    source_inventory = inventory_tree(source)
    source_bytes = sum(record["size_bytes"] for record in source_inventory)
    plan_evidence = None
    if expected_plan_path is not None:
        plan_evidence = validate_relocation_plan(
            plan_path=expected_plan_path,
            source=source,
            destination=destination,
            operation=operation,
            artifact_class=artifact_class,
            observed_inventory=source_inventory,
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    guard_arguments: dict[str, Any] = {
        "tier": destination_tier,
        "path": destination.parent,
        "operation": operation,
        "required_bytes": source_bytes,
    }
    if destination_tier == "S":
        guard_arguments.update(
            shared_quota_root=shared_quota_root,
            shared_quota_bytes=DEFAULT_SHARED_QUOTA_BYTES,
            shared_floor_bytes=DEFAULT_SHARED_FLOOR_BYTES,
            usage_probe=functools.partial(
                allocated_bytes_from_snapshot,
                shared_usage_snapshot,
                max_age_seconds=6 * 60 * 60,
            ),
        )
    else:
        guard_arguments["scratch_floor_bytes"] = SCRATCH_FLOOR_BYTES
    guard = check_storage(**guard_arguments)
    if not guard.allowed:
        raise RuntimeError(f"storage_guard refused relocation: {guard.reason}")

    partial = Path(
        tempfile.mkdtemp(
            prefix=f".{destination.name}.partial.", dir=str(destination.parent)
        )
    )
    published = False
    try:
        shutil.copytree(source, partial, dirs_exist_ok=True, copy_function=shutil.copy2)
        copied_inventory = inventory_tree(partial)
        if copied_inventory != source_inventory:
            raise RuntimeError("copied tree differs from source inventory")
        if inventory_tree(source) != source_inventory:
            raise RuntimeError("source changed while relocation was in progress")
        os.replace(partial, destination)
        published = True

        shutil.rmtree(source)
        source.symlink_to(destination, target_is_directory=True)
        payload = {
            "schema_version": (
                "blind-gains.persistent-preservation-relocation.v1"
                if artifact_class == "persistent_training_state"
                else "blind-gains.rederivable-relocation.v1"
            ),
            "status": "relocated",
            "operation": operation,
            "artifact_class": artifact_class,
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "source": str(source),
            "destination": str(destination),
            "source_replaced_by_symlink": True,
            "total_bytes": source_bytes,
            "file_count": len(source_inventory),
            "files": source_inventory,
            "storage_guard": asdict(guard),
            "preflight_plan": plan_evidence,
        }
        _atomic_json(manifest_path, payload)
        return payload
    finally:
        if not published and partial.exists():
            shutil.rmtree(partial)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--prepare-plan", type=Path)
    parser.add_argument("--expected-plan", type=Path)
    parser.add_argument("--operation", required=True)
    parser.add_argument("--artifact-class", choices=tuple(sorted(ARTIFACT_CLASSES)), default="rederivable")
    parser.add_argument("--destination-tier", choices=("S", "T"))
    parser.add_argument("--shared-quota-root", type=Path, default=SHARED_QUOTA_ROOT)
    parser.add_argument(
        "--shared-usage-snapshot", type=Path, default=SHARED_USAGE_SNAPSHOT
    )
    args = parser.parse_args()
    if args.prepare_plan is not None:
        if args.manifest is not None or args.destination_tier is not None or args.expected_plan is not None:
            parser.error("--prepare-plan cannot be combined with execute-only arguments")
        payload = prepare_relocation_plan(
            source=args.source,
            destination=args.destination,
            plan_path=args.prepare_plan,
            operation=args.operation,
            artifact_class=args.artifact_class,
        )
        print(json.dumps(payload, sort_keys=True))
        return
    if args.manifest is None or args.destination_tier is None:
        parser.error("execution requires --manifest and --destination-tier")
    payload = relocate_tree(
        source=args.source,
        destination=args.destination,
        manifest_path=args.manifest,
        operation=args.operation,
        destination_tier=args.destination_tier,
        artifact_class=args.artifact_class,
        expected_plan_path=args.expected_plan,
        shared_quota_root=args.shared_quota_root,
        shared_usage_snapshot=args.shared_usage_snapshot,
    )
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
