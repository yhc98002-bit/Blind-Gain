#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import time
from pathlib import Path
from typing import Any


ARTIFACT_LAYOUTS = {
    "fliptrack_v02_image_evaluation": (
        "shards/shard_{index}.jsonl",
        "metrics/shard_{index}.json",
    ),
    "fliptrack_question_blind_caption_generation": (
        "shards/captions_shard_{index}.jsonl",
    ),
    "fliptrack_v02_caption_only_qa": (
        "shards/caption_qa_shard_{index}.jsonl",
        "metrics/shard_{index}.json",
    ),
}


def _validate_json(path: Path) -> None:
    json.loads(path.read_text(encoding="utf-8"))


def _validate_jsonl(path: Path) -> None:
    rows = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                json.loads(line)
                rows += 1
    if rows == 0:
        raise ValueError(f"empty JSONL artifact: {path}")


def expected_artifacts(manifest_path: Path, payload: dict[str, Any]) -> list[Path]:
    try:
        patterns = ARTIFACT_LAYOUTS[payload["job_type"]]
    except KeyError as error:
        raise ValueError(f"unsupported sharded job type: {payload.get('job_type')}") from error
    count = int(payload["expected_shards"])
    if count <= 0:
        raise ValueError("expected_shards must be positive")
    return [manifest_path.parent / pattern.format(index=index) for index in range(count) for pattern in patterns]


def inspect_artifacts(manifest_path: Path, payload: dict[str, Any]) -> tuple[list[Path], list[str]]:
    artifacts = expected_artifacts(manifest_path, payload)
    problems: list[str] = []
    for path in artifacts:
        if not path.is_file() or path.stat().st_size == 0:
            problems.append(f"missing_or_empty:{path.relative_to(manifest_path.parent)}")
            continue
        try:
            _validate_jsonl(path) if path.suffix == ".jsonl" else _validate_json(path)
        except (json.JSONDecodeError, ValueError) as error:
            problems.append(f"invalid:{path.relative_to(manifest_path.parent)}:{error}")
    return artifacts, problems


def artifact_digest(run_dir: Path, artifacts: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(artifacts, key=lambda item: item.relative_to(run_dir).as_posix()):
        relative = path.relative_to(run_dir).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def finalize_if_complete(manifest_path: Path, now: dt.datetime | None = None) -> bool:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts, problems = inspect_artifacts(manifest_path, payload)
    if problems:
        return False
    timestamp = now or dt.datetime.now(dt.timezone.utc)
    payload.update(
        {
            "end_time_utc": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "complete",
            "artifacts_exist": True,
            "artifact_count": len(artifacts),
            "artifact_sha256": artifact_digest(manifest_path.parent, artifacts),
            "expected_artifacts": [str(path.relative_to(manifest_path.parent)) for path in artifacts],
        }
    )
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return True


def mark_timeout(manifest_path: Path) -> None:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    _, problems = inspect_artifacts(manifest_path, payload)
    payload.update(
        {
            "end_time_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "fail",
            "artifacts_exist": False,
            "finalizer_error": "timeout waiting for sharded artifacts",
            "artifact_problems": problems,
        }
    )
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=30.0)
    parser.add_argument("--timeout-seconds", type=float, default=86400.0)
    args = parser.parse_args()
    manifest_path = Path(args.manifest)
    deadline = time.monotonic() + args.timeout_seconds
    while True:
        if finalize_if_complete(manifest_path):
            print(f"finalized={manifest_path}")
            return
        if not args.wait:
            raise SystemExit("sharded artifacts are not complete")
        if time.monotonic() >= deadline:
            mark_timeout(manifest_path)
            raise SystemExit("timed out waiting for sharded artifacts")
        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    main()
