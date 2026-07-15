from __future__ import annotations

from pathlib import Path

from scripts.verify_m11_runtime import EXPECTED_VERSIONS, evaluate_runtime
from scripts.verify_m11_runtime_v2 import (
    EXPECTED_VERSIONS as EXPECTED_V2_VERSIONS,
    evaluate_runtime as evaluate_runtime_v2,
    probe_internvl_model_class,
)


def test_m11_runtime_exact_pins_satisfy_gemma_visual_mask_requirement() -> None:
    checks = evaluate_runtime(
        dict(EXPECTED_VERSIONS),
        cuda_runtime="11.8",
        mask_combinators_available=True,
        gemma_importable=True,
    )

    assert all(checks.values())


def test_m11_runtime_rejects_shared_torch_25_environment() -> None:
    versions = dict(EXPECTED_VERSIONS)
    versions["torch"] = "2.5.1+cu121"

    checks = evaluate_runtime(
        versions,
        cuda_runtime="12.1",
        mask_combinators_available=False,
        gemma_importable=True,
    )

    assert checks["exact_pinned_versions"] is False
    assert checks["cuda_runtime_is_11_8"] is False
    assert checks["torch_mask_combinators_available"] is False


def test_m11_setup_is_isolated_guarded_and_proxy_explicit() -> None:
    root = Path(__file__).resolve().parents[1]
    setup = (root / "scripts/setup_m11_runtime.sh").read_text(encoding="utf-8")
    launcher = (root / "scripts/launch_m11_runtime_setup.sh").read_text(
        encoding="utf-8"
    )

    assert 'ENV_DIR="${ROOT}/.venv-m11"' in setup
    assert "torch==2.6.0+cu118" in setup
    assert "torchvision==0.21.0+cu118" in setup
    assert "http://127.0.0.1:7890" in setup
    assert '"${VIRTUALENV_BIN}" --python python3 "${ENV_DIR}"' in setup
    assert "python3 -m venv" not in setup
    assert "scripts/storage_guard.py" in launcher
    assert "--tier S" in launcher and "--tier T" in launcher
    assert 'job_type: "m11_isolated_runtime_setup"' in launcher
    assert ".venv/bin/python -m pip" not in setup


def test_m11_v2_runtime_requires_internvl_dependency_and_model_import() -> None:
    root = Path(__file__).resolve().parents[1]
    requirements = (
        root / "configs/env/m11_runtime_requirements_v2.txt"
    ).read_text(encoding="utf-8")

    assert "einops==0.8.1" in requirements.splitlines()
    assert EXPECTED_V2_VERSIONS["einops"] == "0.8.1"
    checks = evaluate_runtime_v2(
        dict(EXPECTED_V2_VERSIONS),
        cuda_runtime="11.8",
        mask_combinators_available=True,
        gemma_importable=True,
        internvl_model_class_importable=False,
    )
    assert checks["internvl3_model_class_importable"] is False


def test_m11_v2_model_probe_preserves_missing_dependency_reason(tmp_path) -> None:
    def missing_einops(*args, **kwargs):
        raise ModuleNotFoundError("No module named 'einops'")

    importable, detail = probe_internvl_model_class(
        tmp_path, resolver=missing_einops
    )

    assert importable is False
    assert detail == "ModuleNotFoundError: No module named 'einops'"
