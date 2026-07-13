from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_7b_wrapper_pins_node_local_tp1_contract() -> None:
    wrapper = (ROOT / "scripts/launch_virl39k_7b_blind_v1_condition.sh").read_text(
        encoding="utf-8"
    )

    assert 'VIRL_MODEL_LOCATION="node-local"' in wrapper
    assert "Qwen2.5-VL-7B-Instruct@cc594898" in wrapper
    assert "VIRL_CAPTION_EXPECTED_SHARDS=1" in wrapper
    assert 'VIRL_JOB_TYPE="m8_virl39k_7b_blind_solvability_v1"' in wrapper
    assert "launch_virl39k_blind_v1_condition.sh" in wrapper


def test_generic_launcher_keeps_3b_defaults_and_labels_overrides() -> None:
    launcher = (ROOT / "scripts/launch_virl39k_blind_v1_condition.sh").read_text(
        encoding="utf-8"
    )

    assert (
        "VIRL_MODEL_PATH:-artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct" in launcher
    )
    assert "VIRL_CAPTION_EXPECTED_SHARDS:-3" in launcher
    assert 'job_type: $job_type' in launcher
    assert 'model_revision: $model_revision' in launcher
    assert 'model_path: $model_path' in launcher
    assert 'model_path: "${MODEL_PATH}"' not in launcher
    assert 'model_location: $model_location' in launcher
    assert "Required node-local model path is absent" in launcher
