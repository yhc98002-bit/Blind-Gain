from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.run_l10_layer1_queue import (
    EXPECTED_JOB_IDS,
    find_base_workbook,
    parse_gpu_memory,
    validate_config,
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _queue_config(root: Path) -> dict[str, object]:
    jobs = []
    for index, job_id in enumerate(sorted(EXPECTED_JOB_IDS)):
        config = Path("configs/eval") / f"{job_id}.json"
        _write_json(root / config, {"model": {"m": {}}, "data": {"d": {}}})
        jobs.append(
            {
                "id": job_id,
                "gpu": index,
                "config": str(config),
                "mode": "infer" if "mathverse" in job_id else "all",
            }
        )
    return {
        "schema_version": "blind-gains.l10-layer1-queue.v1",
        "node": "an12",
        "jobs": jobs,
    }


def test_l10_queue_requires_exact_registered_job_matrix(tmp_path: Path) -> None:
    config = _queue_config(tmp_path)
    assert {job["id"] for job in validate_config(tmp_path, config)} == EXPECTED_JOB_IDS
    config["jobs"].pop()
    with pytest.raises(ValueError, match="job IDs drifted"):
        validate_config(tmp_path, config)


def test_l10_queue_rejects_gpu_collision(tmp_path: Path) -> None:
    config = _queue_config(tmp_path)
    config["jobs"][1]["gpu"] = config["jobs"][0]["gpu"]
    with pytest.raises(ValueError, match="GPU assignments"):
        validate_config(tmp_path, config)


def test_parse_gpu_memory_is_strict() -> None:
    assert parse_gpu_memory("4, 12\n5, 1024\n") == {4: 12, 5: 1024}
    with pytest.raises(ValueError, match="unexpected nvidia-smi row"):
        parse_gpu_memory("GPU 4 is free")


def test_find_base_workbook_requires_exact_unjudged_filename(tmp_path: Path) -> None:
    config = Path("configs/eval/job.json")
    _write_json(
        tmp_path / config,
        {"model": {"Model": {}}, "data": {"Dataset": {}}},
    )
    run = Path("experiments/runs/eval")
    base = tmp_path / run / "work/Model/timestamp/Model_Dataset.xlsx"
    base.parent.mkdir(parents=True)
    base.write_bytes(b"base")
    (base.parent / "Model_Dataset_exact_matching_result.xlsx").write_bytes(b"judge")

    assert find_base_workbook(tmp_path, run, config) == base.relative_to(tmp_path)
