#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_outputs(config_path: Path, work_dir: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    model_names = sorted(config.get("model", {}))
    dataset_names = sorted(config.get("data", {}))
    if not model_names or not dataset_names:
        raise ValueError("VLMEvalKit config must define at least one model and dataset")

    artifacts: list[dict[str, Any]] = []
    score_artifacts: list[dict[str, Any]] = []
    missing: list[str] = []
    for model_name in model_names:
        model_dir = work_dir / model_name
        for dataset_name in dataset_names:
            pattern = f"{model_name}_{dataset_name}*.xlsx"
            candidates = sorted(path for path in model_dir.glob(pattern) if path.is_file() and path.stat().st_size > 0)
            if not candidates:
                missing.append(f"{model_name}/{pattern}")
                continue
            for path in candidates:
                artifacts.append(
                    {
                        "model": model_name,
                        "dataset": dataset_name,
                        "path": str(path),
                        "bytes": path.stat().st_size,
                        "sha256": _sha256(path),
                    }
                )
            score_pattern = f"{model_name}_{dataset_name}*_acc.csv"
            score_candidates = sorted(
                path for path in model_dir.glob(score_pattern) if path.is_file() and path.stat().st_size > 0
            )
            if not score_candidates:
                missing.append(f"{model_name}/{score_pattern}")
                continue
            for path in score_candidates:
                score_artifacts.append(
                    {
                        "model": model_name,
                        "dataset": dataset_name,
                        "path": str(path),
                        "bytes": path.stat().st_size,
                        "sha256": _sha256(path),
                    }
                )

    if missing:
        raise FileNotFoundError("missing VLMEvalKit inference artifacts: " + ", ".join(missing))
    return {
        "status": "pass",
        "config": str(config_path),
        "work_dir": str(work_dir),
        "models": model_names,
        "datasets": dataset_names,
        "artifacts": artifacts,
        "score_artifacts": score_artifacts,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = validate_outputs(args.config, args.work_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "artifact_count": len(payload["artifacts"])}))


if __name__ == "__main__":
    main()
