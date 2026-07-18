from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from PIL import Image

from scripts.caption_image_store_vllm import (
    discover_image_roots,
    validate_serving_manifest,
)


def _write_image(path: Path, color: tuple[int, int, int]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (8, 8), color).save(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_discover_image_roots_deduplicates_content_across_r19_and_r20(
    tmp_path: Path,
) -> None:
    r19 = tmp_path / "r19"
    r20 = tmp_path / "r20"
    shared_hash = _write_image(r19 / "a.png", (255, 0, 0))
    (r20 / "copy.png").parent.mkdir(parents=True)
    (r20 / "copy.png").write_bytes((r19 / "a.png").read_bytes())
    unique_hash = _write_image(r20 / "b.png", (0, 255, 0))

    rows = discover_image_roots([r19, r20])

    assert [row["image_sha256"] for row in rows] == sorted([shared_hash, unique_hash])
    shared = next(row for row in rows if row["image_sha256"] == shared_hash)
    assert len(shared["duplicate_paths"]) == 1
    assert {shared["image_path"], *shared["duplicate_paths"]} == {
        str(r19 / "a.png"),
        str(r20 / "copy.png"),
    }


def test_serving_manifest_requires_one_single_node_tp4_replica(tmp_path: Path) -> None:
    model_path = Path("/dev/shm/blind-gains/models/qwen72b")
    manifest = tmp_path / "run_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "job_type": "l9_strong_caption_store_generation",
                "gpu_ids": [1, 5, 6, 7],
                "tensor_parallel_width": 4,
                "replica_count": 1,
                "model_path": str(model_path),
            }
        ),
        encoding="utf-8",
    )

    payload = validate_serving_manifest(
        manifest,
        tensor_parallel_size=4,
        model_path=model_path,
    )
    assert payload["gpu_ids"] == [1, 5, 6, 7]

    payload["replica_count"] = 4
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="replica_count"):
        validate_serving_manifest(
            manifest,
            tensor_parallel_size=4,
            model_path=model_path,
        )


def test_serving_manifest_accepts_registered_m12_job_but_rejects_unknown_job(
    tmp_path: Path,
) -> None:
    model_path = Path("/dev/shm/blind-gains/models/qwen72b")
    manifest = tmp_path / "run_manifest.json"
    payload = {
        "job_type": "m12_chart_v08_strong_caption_store_generation",
        "gpu_ids": [4, 5, 6, 7],
        "tensor_parallel_width": 4,
        "replica_count": 1,
        "model_path": str(model_path),
    }
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    assert (
        validate_serving_manifest(
            manifest, tensor_parallel_size=4, model_path=model_path
        )["job_type"]
        == "m12_chart_v08_strong_caption_store_generation"
    )

    payload["job_type"] = "unregistered_caption_job"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="job_type"):
        validate_serving_manifest(
            manifest, tensor_parallel_size=4, model_path=model_path
        )


def test_strong_caption_launcher_cannot_use_tp1_or_cross_node() -> None:
    launcher = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "launch_strong_caption_72b.sh"
    ).read_text(encoding="utf-8")

    assert "TP_WIDTH=4" in launcher
    assert "replica_count: 1" in launcher
    assert "--tensor-parallel-size ${TP_WIDTH}" in launcher
    assert "CUDA_VISIBLE_DEVICES=${GPU_LIST}" in launcher
    assert "Qwen2.5-VL-72B cannot fit on one A800" in launcher
    assert "an12|an29" in launcher
    assert "torchrun" not in launcher


def test_strong_caption_launcher_locks_before_expensive_input_hashing() -> None:
    launcher = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "launch_strong_caption_72b.sh"
    ).read_text(encoding="utf-8")

    assert 'exec 9>"${LOCK_PATH}"' in launcher
    assert "flock -n 9" in launcher
    assert launcher.index("flock -n 9") < launcher.index('R19_HASH="$(find -L')


def test_chart_v08_strong_caption_launcher_uses_exact_m12_provenance() -> None:
    launcher = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "launch_chart_v08_strong_caption_72b.sh"
    ).read_text(encoding="utf-8")

    assert 'job_type: "m12_chart_v08_strong_caption_store_generation"' in launcher
    assert "EXPECTED_MANIFEST_SHA256" in launcher
    assert "expected_unique_image_count: 200" in launcher
    assert "chart_v08_legend_target_flip" in launcher
    assert "chart_v08_point_value_flip" in launcher
    assert "R19_IMAGES" not in launcher
    assert "R20_IMAGES" not in launcher
    assert "TP_WIDTH=4" in launcher
    assert "MIN_HOST_AVAILABLE_BYTES" in launcher
    assert "HOST_AVAILABLE_KIB" in launcher
    assert "HOST_AVAILABLE_BYTES=$((HOST_AVAILABLE_KIB * 1024))" in launcher
    assert "awk '/MemAvailable:/" not in launcher
