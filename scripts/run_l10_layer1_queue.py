#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_JOB_IDS = {"mathverse3b", "mathverse7b", "mmmu3b", "mmmu7b"}
REQUIRED_METRICS = {
    "Acc_final",
    "Acc_strict",
    "Extractor_valid",
    "Contract_valid",
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = Path(f"{path}.partial")
    partial.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(partial, path)


def validate_config(root: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    if config.get("schema_version") != "blind-gains.l10-layer1-queue.v1":
        raise ValueError("unsupported L10 queue schema")
    if config.get("node") not in {"an12", "an29"}:
        raise ValueError("L10 queue node must be an12 or an29")
    jobs = config.get("jobs")
    if not isinstance(jobs, list):
        raise ValueError("L10 queue jobs must be a list")
    ids = [str(job.get("id")) for job in jobs if isinstance(job, dict)]
    if set(ids) != EXPECTED_JOB_IDS or len(ids) != len(EXPECTED_JOB_IDS):
        raise ValueError(f"L10 queue job IDs drifted: {ids}")
    gpus = [job.get("gpu") for job in jobs]
    if len(set(gpus)) != len(gpus) or any(not isinstance(gpu, int) or gpu not in range(8) for gpu in gpus):
        raise ValueError(f"L10 queue GPU assignments are invalid: {gpus}")
    for job in jobs:
        if job.get("mode") not in {"all", "infer"}:
            raise ValueError(f"invalid L10 mode for {job.get('id')}")
        path = root / str(job.get("config", ""))
        if not path.is_file():
            raise ValueError(f"L10 evaluation config is absent: {path}")
    return jobs


def parse_gpu_memory(output: str) -> dict[int, int]:
    memory = {}
    for line in output.splitlines():
        if not line.strip():
            continue
        fields = [field.strip() for field in line.split(",")]
        if len(fields) != 2:
            raise ValueError(f"unexpected nvidia-smi row: {line}")
        memory[int(fields[0])] = int(fields[1])
    return memory


def _gpu_memory(node: str) -> dict[int, int]:
    completed = subprocess.run(
        [
            "ssh",
            node,
            "nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return parse_gpu_memory(completed.stdout)


def find_base_workbook(root: Path, run_dir: Path, eval_config: Path) -> Path:
    config = _read_json(root / eval_config)
    models = list(config.get("model", {}))
    datasets = list(config.get("data", {}))
    if len(models) != 1 or len(datasets) != 1:
        raise ValueError(f"L10 config must register one model and one dataset: {eval_config}")
    expected_name = f"{models[0]}_{datasets[0]}.xlsx"
    matches = sorted((root / run_dir / "work").rglob(expected_name))
    if len(matches) != 1:
        raise ValueError(
            f"expected one base workbook named {expected_name} in {run_dir}, found {len(matches)}"
        )
    return matches[0].relative_to(root)


def _run_dir_from_stdout(stdout: str, label: str) -> Path:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    matches = [Path(line) for line in lines if line.startswith("experiments/runs/")]
    if len(matches) != 1:
        raise RuntimeError(f"{label} launcher returned ambiguous run paths: {lines}")
    return matches[0]


def _launch_eval(node: str, job: dict[str, Any]) -> Path:
    completed = subprocess.run(
        [
            "bash",
            "scripts/launch_vlmevalkit_eval.sh",
            node,
            str(job["gpu"]),
            str(job["config"]),
            str(job["run_tag"]),
            str(job["judge"]),
            "",
            str(job["mode"]),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return _run_dir_from_stdout(completed.stdout, str(job["id"]))


def _launch_postprocess(job: dict[str, Any], source_run: Path, workbook: Path) -> Path:
    completed = subprocess.run(
        [
            "bash",
            "scripts/launch_vlmeval_postprocess.sh",
            str(workbook),
            str(source_run),
            f"{job['run_tag']}_canonicalv2",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return _run_dir_from_stdout(completed.stdout, f"{job['id']} postprocess")


def _manifest_status(run_dir: Path) -> str:
    path = ROOT / run_dir / "run_manifest.json"
    return str(_read_json(path).get("status")) if path.is_file() else "missing"


def _wait_for_upstream(path: Path, poll_seconds: int) -> None:
    while True:
        status = _read_json(path).get("status")
        if status == "complete":
            return
        if status == "fail":
            raise RuntimeError(f"upstream R20 queue failed: {path}")
        print(f"l10_queue_wait upstream_status={status}", flush=True)
        time.sleep(poll_seconds)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--upstream-state", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    args = parser.parse_args()
    config = _read_json(args.config)
    jobs = validate_config(ROOT, config)
    poll_seconds = int(config.get("poll_seconds", 60))
    threshold = int(config.get("gpu_free_threshold_mib", 1024))
    if poll_seconds <= 0 or threshold < 0:
        raise ValueError("L10 queue poll/threshold values are invalid")
    config_hash = _sha256(args.config)

    state = _read_json(args.state) if args.state.is_file() else {
        "schema_version": "blind-gains.l10-layer1-queue-state.v1",
        "status": "waiting_upstream",
        "config_sha256": config_hash,
        "upstream_state": str(args.upstream_state),
        "jobs": {},
    }
    if state.get("config_sha256") != config_hash or state.get("upstream_state") != str(args.upstream_state):
        raise ValueError("L10 queue state/config identity mismatch")
    if state.get("status") == "complete":
        for record in state["jobs"].values():
            metrics = ROOT / record["postprocess_run"] / "metrics.json"
            if not metrics.is_file() or _sha256(metrics) != record["metrics_sha256"]:
                raise ValueError(f"completed L10 queue output drift: {metrics}")
        print(json.dumps(state, sort_keys=True))
        return
    _atomic_write(args.state, state)

    _wait_for_upstream(args.upstream_state, poll_seconds)
    node = str(config["node"])
    while any(str(job["id"]) not in state["jobs"] for job in jobs):
        memory = _gpu_memory(node)
        target_gpus = [int(job["gpu"]) for job in jobs if str(job["id"]) not in state["jobs"]]
        busy = {gpu: memory.get(gpu) for gpu in target_gpus if memory.get(gpu, threshold + 1) > threshold}
        if busy:
            state["status"] = "waiting_gpus"
            state["last_gpu_memory_mib"] = memory
            _atomic_write(args.state, state)
            print(f"l10_queue_wait busy_gpus={busy}", flush=True)
            time.sleep(poll_seconds)
            continue
        for job in jobs:
            job_id = str(job["id"])
            if job_id in state["jobs"]:
                continue
            run_dir = _launch_eval(node, job)
            state["jobs"][job_id] = {
                "eval_run": str(run_dir),
                "postprocess_run": None,
            }
            state["status"] = "evaluating"
            _atomic_write(args.state, state)

    while True:
        statuses = {
            job_id: _manifest_status(Path(record["eval_run"]))
            for job_id, record in state["jobs"].items()
        }
        failed = {key: value for key, value in statuses.items() if value == "fail"}
        if failed:
            raise RuntimeError(f"L10 evaluation failed: {failed}")
        if all(value == "complete" for value in statuses.values()):
            break
        print(f"l10_queue_wait eval_statuses={statuses}", flush=True)
        time.sleep(poll_seconds)

    jobs_by_id = {str(job["id"]): job for job in jobs}
    state["status"] = "postprocessing"
    _atomic_write(args.state, state)
    for job_id, record in state["jobs"].items():
        postprocess_value = record.get("postprocess_run")
        if postprocess_value:
            if _manifest_status(Path(str(postprocess_value))) != "complete":
                raise RuntimeError(f"recorded L10 postprocess is not complete: {postprocess_value}")
            continue
        job = jobs_by_id[job_id]
        source_run = Path(record["eval_run"])
        workbook = find_base_workbook(ROOT, source_run, Path(str(job["config"])))
        postprocess_run = _launch_postprocess(job, source_run, workbook)
        metrics_path = ROOT / postprocess_run / "metrics.json"
        metrics = _read_json(metrics_path)
        overall = metrics.get("overall", {})
        if (
            metrics.get("parser_version") != "canonical-v2"
            or metrics.get("prompt_contract_resolution") != "embedded-run-manifest"
            or not REQUIRED_METRICS.issubset(overall)
        ):
            raise RuntimeError(f"L10 postprocess contract failed: {postprocess_run}")
        record.update(
            {
                "workbook": str(workbook),
                "postprocess_run": str(postprocess_run),
                "metrics_sha256": _sha256(metrics_path),
            }
        )
        _atomic_write(args.state, state)

    state["status"] = "complete"
    _atomic_write(args.state, state)
    print(json.dumps(state, sort_keys=True))


if __name__ == "__main__":
    main()
