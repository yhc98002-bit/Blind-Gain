#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs/eval/seed1_visual_evidence_ranking_v1.json"
CONFIG = DEFAULT_CONFIG


def matrix_cells() -> list[dict[str, str]]:
    return [
        {"model_key": model, "condition": condition}
        for model in ("base", "a1_step60", "a1_step100")
        for condition in ("real", "no_image", "gray")
    ]


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def _atomic(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.partial")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _gpu_is_free(node: str, gpu: int) -> bool:
    result = subprocess.run(
        [
            "ssh",
            node,
            f"nvidia-smi -i {gpu} --query-compute-apps=pid --format=csv,noheader,nounits",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"GPU query failed for {node}:{gpu}: {result.stderr.strip()}")
    return not result.stdout.strip()


def _remote_pid_alive(node: str, pid_path: Path) -> bool:
    if not pid_path.is_file():
        return False
    try:
        pid = int(pid_path.read_text(encoding="utf-8").strip())
    except ValueError:
        return False
    result = subprocess.run(
        ["ssh", node, f"kill -0 {pid}"],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _finish_queue(manifest_path: Path, status: str, exit_code: int) -> None:
    manifest = _read(manifest_path)
    manifest.update({"status": status, "exit_code": exit_code, "end_time_utc": _now()})
    _atomic(manifest_path, manifest)


def run(
    queue_dir: Path,
    node: str,
    gpu_ids: list[int],
    poll_seconds: int,
    resume: bool = False,
) -> int:
    queue_dir.mkdir(parents=True, exist_ok=True)
    state_path = queue_dir / "state.json"
    manifest_path = queue_dir / "run_manifest.json"
    config = _read(CONFIG)
    queue_tag = queue_dir.name
    if resume:
        if not state_path.is_file() or not manifest_path.is_file():
            raise FileNotFoundError("resume requires existing queue state and manifest")
        state = _read(state_path)
        manifest = _read(manifest_path)
        if state.get("status") != "running" or manifest.get("status") != "running":
            raise ValueError("only a running queue may be resumed")
        if manifest.get("node") != node or manifest.get("gpu_ids") != gpu_ids:
            raise ValueError("resume placement differs from the immutable queue manifest")
        if manifest.get("config_hash") != _sha256(CONFIG):
            raise ValueError("resume config hash mismatch")
        if manifest.get("data_manifest_hash") != config["candidate_registry"]["sha256"]:
            raise ValueError("resume data hash mismatch")
        event = {
            "time_utc": _now(),
            "git_hash": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "command": "explicit --resume",
        }
        state.setdefault("resume_events", []).append(event)
        manifest.setdefault("resume_events", []).append(event)
        _atomic(state_path, state)
        _atomic(manifest_path, manifest)
    else:
        if state_path.exists() or manifest_path.exists():
            raise FileExistsError("queue state already exists; use explicit --resume")
        state = {
            "schema_version": "blind-gains.visual-evidence-ranking-queue-state.v1",
            "status": "running",
            "pending": matrix_cells(),
            "active": {},
            "complete": [],
            "failed": [],
            "resume_events": [],
            "performance_values_opened": False,
            "last_update_utc": _now(),
        }
        manifest = {
            "schema_version": "blind-gains.visual-evidence-ranking-queue-run.v1",
            "run_id": queue_tag,
            "job_type": "post_seed1_visual_evidence_ranking_queue",
            "status": "running",
            "node": node,
            "gpu_ids": gpu_ids,
            "tensor_parallel_width": 1,
            "replica_count": len(gpu_ids),
            "placement_justification": "Up to four independent TP1 3B ranking cells occupy disjoint free GPUs on one node; no cell is split across nodes.",
            "git_hash": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "config_path": str(CONFIG.relative_to(ROOT)),
            "config_hash": _sha256(CONFIG),
            "data_manifest": config["candidate_registry"]["path"],
            "data_manifest_hash": config["candidate_registry"]["sha256"],
            "seed": 0,
            "command": f"scripts/run_visual_evidence_ranking_queue.py --queue-dir {queue_dir} --node {node} --gpu-ids {' '.join(map(str, gpu_ids))} --poll-seconds {poll_seconds}",
            "start_time_utc": _now(),
            "end_time_utc": None,
            "exit_code": None,
            "resume_events": [],
            "expected_artifacts": [str(state_path), str(queue_dir / "matrix_runs.json")],
            "performance_values_opened": False,
        }
        _atomic(state_path, state)
        _atomic(manifest_path, manifest)

    while state["pending"] or state["active"]:
        for gpu_text, active in list(state["active"].items()):
            child_manifest_path = ROOT / active["run_dir"] / "run_manifest.json"
            if not child_manifest_path.is_file():
                continue
            child = _read(child_manifest_path)
            if child.get("status") == "complete" and child.get("exit_code") == 0:
                state["complete"].append(active)
                del state["active"][gpu_text]
            elif child.get("status") in {"failed", "fail", "error", "cancelled", "canceled"}:
                state["failed"].append({**active, "child_status": child.get("status")})
                del state["active"][gpu_text]
            elif child.get("status") == "running" and not _remote_pid_alive(
                node, ROOT / active["run_dir"] / "process.pid"
            ):
                state["failed"].append(
                    {**active, "child_status": "running_manifest_without_live_worker"}
                )
                del state["active"][gpu_text]

        if state["failed"]:
            state.update({"status": "failed", "last_update_utc": _now()})
            _atomic(state_path, state)
            _finish_queue(manifest_path, "failed", 1)
            return 1

        for gpu in gpu_ids:
            gpu_text = str(gpu)
            if not state["pending"] or gpu_text in state["active"]:
                continue
            if not _gpu_is_free(node, gpu):
                continue
            cell = state["pending"][0]
            run_dir = (
                Path("experiments/runs")
                / f"d1_visual_evidence_{cell['model_key']}_{cell['condition']}_{node}_gpu{gpu}_{queue_tag}"
            )
            command = [
                str(ROOT / "scripts/launch_visual_evidence_ranking_cell.sh"),
                node,
                str(gpu),
                cell["model_key"],
                cell["condition"],
                str(run_dir),
            ]
            launched = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
            if launched.returncode == 75:
                continue
            if launched.returncode != 0:
                state["failed"].append(
                    {
                        **cell,
                        "gpu": gpu,
                        "reason": "launcher_failed",
                        "exit_code": launched.returncode,
                        "stderr": launched.stderr[-2000:],
                    }
                )
                break
            state["pending"].pop(0)
            state["active"][gpu_text] = {
                **cell,
                "gpu": gpu,
                "run_dir": str(run_dir),
                "launch_time_utc": _now(),
            }

        state["last_update_utc"] = _now()
        _atomic(state_path, state)
        if state["failed"]:
            continue
        if state["pending"] or state["active"]:
            time.sleep(poll_seconds)

    matrix_runs = {
        "schema_version": "blind-gains.visual-evidence-ranking-matrix-runs.v1",
        "status": "complete",
        "runs": sorted(
            state["complete"], key=lambda item: (item["model_key"], item["condition"])
        ),
        "performance_values_opened": False,
    }
    _atomic(queue_dir / "matrix_runs.json", matrix_runs)
    state.update({"status": "complete", "last_update_utc": _now()})
    _atomic(state_path, state)
    _finish_queue(manifest_path, "complete", 0)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue-dir", required=True)
    parser.add_argument("--node", choices=("an12", "an29"), required=True)
    parser.add_argument("--gpu-ids", nargs="+", type=int, required=True)
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args()
    if args.config is not None:
        global CONFIG
        CONFIG = args.config.resolve()
    if len(set(args.gpu_ids)) != len(args.gpu_ids) or any(not 0 <= gpu <= 7 for gpu in args.gpu_ids):
        raise ValueError("GPU ids must be unique values in [0,7]")
    if args.poll_seconds < 15:
        raise ValueError("poll interval must be at least 15 seconds")
    raise SystemExit(
        run(
            Path(args.queue_dir),
            args.node,
            args.gpu_ids,
            args.poll_seconds,
            resume=args.resume,
        )
    )


if __name__ == "__main__":
    main()
