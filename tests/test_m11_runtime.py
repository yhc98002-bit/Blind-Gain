from __future__ import annotations

from pathlib import Path

from scripts.verify_m11_runtime import EXPECTED_VERSIONS, evaluate_runtime


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
    assert "scripts/storage_guard.py" in launcher
    assert "--tier S" in launcher and "--tier T" in launcher
    assert 'job_type: "m11_isolated_runtime_setup"' in launcher
    assert ".venv/bin/python -m pip" not in setup
