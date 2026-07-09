from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from src.eval.image_conditions import IMAGE_MODES, materialize_image


def _checkerboard(path: Path, size: int = 128) -> None:
    y, x = np.indices((size, size))
    pixels = (((x // 4 + y // 4) % 2) * 255).astype(np.uint8)
    image = np.repeat(pixels[:, :, None], 3, axis=2)
    Image.fromarray(image, mode="RGB").save(path)


def _edge_energy(path: str) -> float:
    with Image.open(path) as image:
        pixels = np.asarray(image.convert("L"), dtype=np.float32)
    return float(np.abs(np.diff(pixels, axis=0)).mean() + np.abs(np.diff(pixels, axis=1)).mean())


def test_degradation_curve_is_deterministic_and_strictly_removes_detail(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    _checkerboard(source)
    cache = tmp_path / "cache"
    outputs = {mode: materialize_image(str(source), mode, cache) for mode in IMAGE_MODES}

    assert outputs["real"] == str(source)
    assert outputs["mild"] == materialize_image(str(source), "mild", cache)
    energies = [_edge_energy(outputs[mode]) for mode in ("real", "mild", "medium", "severe", "gray")]
    assert energies == sorted(energies, reverse=True)
    assert len(set(energies)) == len(energies)
    with Image.open(outputs["noise"]) as noise:
        assert noise.size == (128, 128)


def test_cache_key_uses_content_not_only_source_path(tmp_path: Path) -> None:
    source = tmp_path / "mutable.png"
    Image.new("RGB", (16, 16), "red").save(source)
    first = materialize_image(str(source), "gray", tmp_path / "cache")
    Image.new("RGB", (16, 16), "blue").save(source)
    second = materialize_image(str(source), "gray", tmp_path / "cache")
    assert first != second


def test_unknown_image_condition_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    Image.new("RGB", (8, 8), "white").save(source)
    with pytest.raises(ValueError, match="unsupported image mode"):
        materialize_image(str(source), "unregistered", tmp_path / "cache")
