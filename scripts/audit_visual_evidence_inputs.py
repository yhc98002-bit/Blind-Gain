#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def audit_expected_file(path: Path, expected_sha256: str) -> dict[str, Any]:
    if not path.is_file():
        return {
            "path": str(path),
            "exists": False,
            "expected_sha256": expected_sha256,
            "observed_sha256": None,
            "matches": False,
            "bytes": None,
        }
    observed = sha256_file(path)
    return {
        "path": str(path),
        "exists": True,
        "expected_sha256": expected_sha256,
        "observed_sha256": observed,
        "matches": observed == expected_sha256,
        "bytes": path.stat().st_size,
    }


def audit_model(model_key: str, spec: dict[str, Any]) -> dict[str, Any]:
    model_path = _resolve(str(spec["path"]))
    index_path = model_path / "model.safetensors.index.json"
    index_audit = audit_expected_file(index_path, str(spec["model_index_sha256"]))
    if not index_audit["matches"]:
        return {
            "model_key": model_key,
            "path": str(model_path),
            "status": "fail",
            "index": index_audit,
            "shards": [],
        }
    index = json.loads(index_path.read_text(encoding="utf-8"))
    weight_map = index.get("weight_map")
    if not isinstance(weight_map, dict) or not weight_map:
        raise ValueError(f"model index has no weight map: {index_path}")
    shard_names = sorted(set(weight_map.values()))
    if any(
        not isinstance(name, str)
        or Path(name).name != name
        or not name.endswith(".safetensors")
        for name in shard_names
    ):
        raise ValueError(f"model index contains an unsafe shard name: {index_path}")
    shards = []
    for name in shard_names:
        path = model_path / name
        shards.append(
            {
                "name": name,
                "exists": path.is_file(),
                "bytes": path.stat().st_size if path.is_file() else None,
                "sha256": sha256_file(path) if path.is_file() else None,
            }
        )
    inventory_payload = [
        {"name": item["name"], "bytes": item["bytes"], "sha256": item["sha256"]}
        for item in shards
    ]
    inventory_hash = hashlib.sha256(
        json.dumps(inventory_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    status = "pass" if all(item["exists"] and item["bytes"] for item in shards) else "fail"
    return {
        "model_key": model_key,
        "path": str(model_path),
        "status": status,
        "index": index_audit,
        "shard_count": len(shards),
        "weight_bytes": sum(int(item["bytes"] or 0) for item in shards),
        "shard_inventory_sha256": inventory_hash,
        "shards": shards,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    config_path = _resolve(args.config)
    output = _resolve(args.output)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite input-integrity audit: {output}")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    registry_path = _resolve(str(config["candidate_registry"]["path"]))
    registry_audit = audit_expected_file(
        registry_path, str(config["candidate_registry"]["sha256"])
    )
    rows = [
        json.loads(line)
        for line in registry_path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    image_audits: dict[str, dict[str, Any]] = {}
    path_escape_count = 0
    release_root = (ROOT / "data/fliptrack_v02r19_artifact_expanded").resolve()
    for row in rows:
        for side in ("a", "b"):
            path = _resolve(str(row[f"image_{side}_path"])).resolve()
            try:
                path.relative_to(release_root)
            except ValueError:
                path_escape_count += 1
            expected = str(row[f"image_{side}_sha256"])
            key = str(path)
            prior = image_audits.get(key)
            if prior is not None and prior["expected_sha256"] != expected:
                raise ValueError(f"one image path has conflicting expected hashes: {path}")
            image_audits[key] = audit_expected_file(path, expected)
    models = {
        key: audit_model(key, spec) for key, spec in sorted(config["models"].items())
    }
    checks = {
        "config_exists": config_path.is_file(),
        "candidate_registry_hash_exact": bool(registry_audit["matches"]),
        "pair_count_exact": len(rows) == int(config["candidate_registry"]["pair_count"]),
        "pair_ids_unique": len({str(row["pair_id"]) for row in rows}) == len(rows),
        "image_paths_inside_release": path_escape_count == 0,
        "all_image_hashes_exact": all(item["matches"] for item in image_audits.values()),
        "all_model_indexes_and_shards_present": all(
            model["status"] == "pass" for model in models.values()
        ),
    }
    result = {
        "schema_version": "blind-gains.visual-evidence-input-integrity.v1",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "config_path": str(config_path),
        "config_sha256": sha256_file(config_path),
        "candidate_registry": registry_audit,
        "pair_count": len(rows),
        "unique_image_count": len(image_audits),
        "image_bytes": sum(int(item["bytes"] or 0) for item in image_audits.values()),
        "image_hash_mismatch_count": sum(not item["matches"] for item in image_audits.values()),
        "path_escape_count": path_escape_count,
        "models": models,
        "performance_values_opened": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.{os.getpid()}.partial")
    temporary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, output)
    print(
        json.dumps(
            {
                "status": result["status"],
                "pair_count": result["pair_count"],
                "unique_image_count": result["unique_image_count"],
                "image_hash_mismatch_count": result["image_hash_mismatch_count"],
                "model_status": {key: model["status"] for key, model in models.items()},
                "performance_values_opened": False,
            },
            sort_keys=True,
        )
    )
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
