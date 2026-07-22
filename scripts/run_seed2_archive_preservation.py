#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

from scripts.measure_storage_usage import measure
from scripts.relocate_rederivable_tree import (
    inventory_tree,
    prepare_relocation_plan,
    relocate_tree,
    validate_relocation_plan,
)
from src.ops.storage_guard import (
    DEFAULT_SHARED_FLOOR_BYTES,
    DEFAULT_SHARED_QUOTA_BYTES,
    evaluate_shared_guard,
)


ROOT = Path(__file__).resolve().parents[1]
SCRATCH_ROOT = Path("/tmp/blindgain_checkpoint_archive")
DESTINATION_ROOT = Path(
    "/XYFS02/HDD_POOL/paratera_xy/pxy1289/blindgain_archive/"
    "login_tmp_checkpoint_archive"
)
QUOTA_ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289")
OPERATION = "preserve_completed_seed2_training_state"
ENTRIES = (
    {
        "arm": "a1_real",
        "run_id": "mech_a1_real_seed2_an29_20260716T164827Z",
    },
    {
        "arm": "a3_caption",
        "run_id": "mech_a3_caption_seed2_an29_20260720T125144Z",
    },
)


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _atomic_update(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _entry_paths(entry: dict[str, str]) -> dict[str, Any]:
    run_id = entry["run_id"]
    return {
        **entry,
        "source": SCRATCH_ROOT / run_id,
        "destination": DESTINATION_ROOT / run_id,
        "training_manifest": ROOT / "experiments/runs" / run_id / "run_manifest.json",
    }


def validate_registered_sources() -> list[dict[str, Any]]:
    readout_path = ROOT / "reports/pilot_4arm_seed2_results_v1.json"
    readout = _read(readout_path)
    if (
        readout.get("status") != "complete"
        or readout.get("seed") != 2
        or readout.get("checks", {}).get("strict_gain_identity_all_arms") is not True
    ):
        raise RuntimeError("seed-2 unified readout is not complete and internally checked")
    registered: list[dict[str, Any]] = []
    for raw in ENTRIES:
        entry = _entry_paths(raw)
        source = entry["source"]
        destination = entry["destination"]
        if source.is_symlink() or not source.is_dir():
            raise ValueError(f"source is not one real archive directory: {source}")
        if source.resolve().parent != SCRATCH_ROOT.resolve(strict=True):
            raise ValueError(f"source is outside the exact scratch allowlist: {source}")
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(f"destination already exists: {destination}")
        if destination.parent.resolve(strict=True) != DESTINATION_ROOT.resolve(strict=True):
            raise ValueError(f"destination is outside the exact persistent allowlist: {destination}")

        manifest = _read(entry["training_manifest"])
        if (
            manifest.get("status") != "complete"
            or manifest.get("seed") != 2
            or manifest.get("arm") != entry["arm"]
            or manifest.get("run_id") != entry["run_id"]
        ):
            raise RuntimeError(f"training manifest identity is not complete: {entry['run_id']}")
        provenance = readout["provenance"]["training_manifests"][entry["arm"]]
        expected_path = entry["training_manifest"].relative_to(ROOT).as_posix()
        if provenance.get("path") != expected_path or provenance.get("sha256") != _sha256(
            entry["training_manifest"]
        ):
            raise RuntimeError(f"unified readout does not bind the training manifest: {entry['arm']}")
        registered.append(entry)
    return registered


def _write_usage_snapshot(path: Path) -> dict[str, Any]:
    payload = measure(QUOTA_ROOT, workers=4, timeout_seconds=7200)
    _atomic_update(path, payload)
    return payload


def prepare(run_dir: Path) -> dict[str, Any]:
    entries = validate_registered_sources()
    plans = []
    for entry in entries:
        plan_path = run_dir / "plans" / f"{entry['arm']}.json"
        payload = prepare_relocation_plan(
            source=entry["source"],
            destination=entry["destination"],
            plan_path=plan_path,
            operation=OPERATION,
            artifact_class="persistent_training_state",
        )
        plans.append(
            {
                "arm": entry["arm"],
                "run_id": entry["run_id"],
                "plan": str(plan_path),
                "plan_sha256": _sha256(plan_path),
                "file_count": payload["file_count"],
                "total_bytes": payload["total_bytes"],
                "embedded_checksum_manifests": len(
                    payload["embedded_checksum_manifests"]
                ),
            }
        )
    usage = _write_usage_snapshot(run_dir / "storage_usage_before.json")
    guard = evaluate_shared_guard(
        path=DESTINATION_ROOT,
        operation=OPERATION,
        required_bytes=sum(item["total_bytes"] for item in plans),
        used_bytes=int(usage["used_bytes"]),
        quota_bytes=DEFAULT_SHARED_QUOTA_BYTES,
        floor_bytes=DEFAULT_SHARED_FLOOR_BYTES,
    )
    if not guard.allowed:
        raise RuntimeError(f"combined Tier-S guard refused preservation plan: {guard.reason}")
    return {
        "schema_version": "blind-gains.seed2-archive-preservation.v1",
        "status": "validated_not_executed",
        "mode": "plan",
        "created_at_utc": _now(),
        "entries": plans,
        "total_files": sum(item["file_count"] for item in plans),
        "total_bytes": sum(item["total_bytes"] for item in plans),
        "combined_storage_guard": asdict(guard),
        "seed2_readout": "reports/pilot_4arm_seed2_results_v1.json",
        "deletion_authorized": False,
    }


def _prevalidate_all(
    entries: list[dict[str, Any]], plan_run_dir: Path
) -> list[dict[str, Any]]:
    validated = []
    for entry in entries:
        plan_path = plan_run_dir / "plans" / f"{entry['arm']}.json"
        inventory = inventory_tree(entry["source"])
        evidence = validate_relocation_plan(
            plan_path=plan_path,
            source=entry["source"].resolve(),
            destination=entry["destination"].absolute(),
            operation=OPERATION,
            artifact_class="persistent_training_state",
            observed_inventory=inventory,
        )
        validated.append(
            {
                **entry,
                "plan": plan_path,
                "plan_evidence": evidence,
                "file_count": len(inventory),
                "total_bytes": sum(record["size_bytes"] for record in inventory),
            }
        )
    return validated


def execute(run_dir: Path, plan_run_dir: Path) -> dict[str, Any]:
    plan_manifest = _read(plan_run_dir / "run_manifest.json")
    plan_result = _read(plan_run_dir / "operation_result.json")
    if (
        plan_manifest.get("status") != "complete"
        or plan_manifest.get("exit_code") != 0
        or plan_manifest.get("job_type") != "seed2_archive_preservation_plan"
        or plan_result.get("status") != "validated_not_executed"
        or plan_result.get("deletion_authorized") is not False
    ):
        raise RuntimeError("prior preservation plan run is not complete and fail-closed")

    entries = _prevalidate_all(validate_registered_sources(), plan_run_dir)
    usage = _write_usage_snapshot(run_dir / "storage_usage_before.json")
    total_bytes = sum(item["total_bytes"] for item in entries)
    guard = evaluate_shared_guard(
        path=DESTINATION_ROOT,
        operation=OPERATION,
        required_bytes=total_bytes,
        used_bytes=int(usage["used_bytes"]),
        quota_bytes=DEFAULT_SHARED_QUOTA_BYTES,
        floor_bytes=DEFAULT_SHARED_FLOOR_BYTES,
    )
    if not guard.allowed:
        raise RuntimeError(f"combined Tier-S guard refused preservation: {guard.reason}")

    result: dict[str, Any] = {
        "schema_version": "blind-gains.seed2-archive-preservation.v1",
        "status": "relocating",
        "mode": "execute",
        "started_at_utc": _now(),
        "plan_run": str(plan_run_dir),
        "plan_result_sha256": _sha256(plan_run_dir / "operation_result.json"),
        "combined_storage_guard": asdict(guard),
        "entries": [],
        "total_bytes": total_bytes,
        "deletion_scope": "source bytes only after a verified persistent copy",
    }
    result_path = run_dir / "operation_result.json"
    _atomic_update(result_path, result)
    for index, entry in enumerate(entries):
        usage_path = run_dir / f"storage_usage_before_{entry['arm']}.json"
        _write_usage_snapshot(usage_path)
        relocation_manifest = run_dir / "relocations" / f"{entry['arm']}.json"
        relocated = relocate_tree(
            source=entry["source"],
            destination=entry["destination"],
            manifest_path=relocation_manifest,
            operation=OPERATION,
            destination_tier="S",
            artifact_class="persistent_training_state",
            expected_plan_path=entry["plan"],
            shared_quota_root=QUOTA_ROOT,
            shared_usage_snapshot=usage_path,
        )
        result["entries"].append(
            {
                "arm": entry["arm"],
                "run_id": entry["run_id"],
                "relocation_manifest": str(relocation_manifest),
                "relocation_manifest_sha256": _sha256(relocation_manifest),
                "file_count": relocated["file_count"],
                "total_bytes": relocated["total_bytes"],
                "source_is_symlink": entry["source"].is_symlink(),
                "source_resolves_to_destination": entry["source"].resolve()
                == entry["destination"].resolve(),
            }
        )
        result["completed_entries"] = index + 1
        _atomic_update(result_path, result)
    usage_after = _write_usage_snapshot(run_dir / "storage_usage_after.json")
    result.update(
        {
            "status": "complete",
            "completed_at_utc": _now(),
            "storage_usage_after": usage_after,
            "all_sources_are_verified_symlinks": all(
                item["source_is_symlink"] and item["source_resolves_to_destination"]
                for item in result["entries"]
            ),
        }
    )
    _atomic_update(result_path, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("plan", "execute"), required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--plan-run-dir", type=Path)
    args = parser.parse_args()
    if args.mode == "plan":
        if args.plan_run_dir is not None:
            parser.error("plan mode does not accept --plan-run-dir")
        payload = prepare(args.run_dir)
        _atomic_update(args.run_dir / "operation_result.json", payload)
    else:
        if args.plan_run_dir is None:
            parser.error("execute mode requires --plan-run-dir")
        payload = execute(args.run_dir, args.plan_run_dir)
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
