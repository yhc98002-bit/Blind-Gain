from __future__ import annotations

import json
import os
from pathlib import Path

from PIL import Image, PngImagePlugin

from src.fliptrack.manifest_linter import lint_package
from src.fliptrack.package_v02 import package_manifest


def _write_source(tmp_path: Path, answers: tuple[str, str] = ("7", "8"), n_pairs: int = 6) -> Path:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    rows = []
    for index in range(n_pairs):
        image_a = Image.new("RGB", (24, 24), (240, 240, 240))
        image_b = image_a.copy()
        image_a.putpixel((10, 10), (index, 10, 20))
        image_b.putpixel((10, 10), (index, 20, 10))
        mask = Image.new("L", (24, 24), 0)
        mask.putpixel((10, 10), 255)
        paths = {}
        for name, image in (("image_a", image_a), ("image_b", image_b), ("mask_a", mask), ("mask_b", mask)):
            path = source_dir / f"{index}_{name}.png"
            image.save(path)
            paths[name] = path
        rows.append(
            {
                "pair_id": f"source_{index}",
                "question": "What value is shown?",
                "answer_a": answers[0],
                "answer_b": answers[1],
                "image_a_path": str(paths["image_a"]),
                "image_b_path": str(paths["image_b"]),
                "changed_region_mask_a": str(paths["mask_a"]),
                "changed_region_mask_b": str(paths["mask_b"]),
                "category": "unit",
                "template_id": "deliberately_secret_template",
                "catch_twin_id": None,
            }
        )
    manifest = tmp_path / "source.jsonl"
    manifest.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return manifest


def _package(tmp_path: Path, answers: tuple[str, str] = ("7", "8")) -> tuple[Path, Path]:
    release = tmp_path / "release"
    key = tmp_path / "private" / "key.jsonl"
    salt = tmp_path / "private" / "salt.bin"
    salt.parent.mkdir(parents=True, exist_ok=True)
    salt.write_bytes(b"fixed-test-salt" * 2)
    package_manifest(_write_source(tmp_path, answers), release, key, salt)
    return release, key


def test_packaged_fixture_passes_linter(tmp_path: Path) -> None:
    release, key = _package(tmp_path)
    result = lint_package(release, key)

    assert result["status"] is True
    assert all(result["checks"].values())
    assert result["stats"]["member_order_counts"]["ab"] > 0
    assert result["stats"]["member_order_counts"]["ba"] > 0


def test_linter_rejects_leaky_path_metadata_and_untruthful_mask(tmp_path: Path) -> None:
    release, key = _package(tmp_path)
    manifest_path = release / "manifest.jsonl"
    rows = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines()]
    member = rows[0]["members"][0]
    old_path = release / member["image_path"]
    leaky_path = release / "images" / "side_a_answer_template.png"
    with Image.open(old_path) as image:
        modified = image.convert("RGB")
    modified.putpixel((0, 0), (1, 2, 3))
    pnginfo = PngImagePlugin.PngInfo()
    pnginfo.add_text("answer", "leak")
    modified.save(leaky_path, pnginfo=pnginfo)
    os.utime(leaky_path, (123, 123))
    old_path.unlink()
    member["image_path"] = leaky_path.relative_to(release).as_posix()
    manifest_path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    result = lint_package(release, key)
    codes = {error["code"] for error in result["errors"]}

    assert result["status"] is False
    assert "leaky_path" in codes
    assert "nonopaque_filename" in codes
    assert "png_ancillary_chunk" in codes
    assert "mtime_mismatch" in codes
    assert "untruthful_mask" in codes


def test_linter_rejects_numeric_equivalent_answers(tmp_path: Path) -> None:
    release, key = _package(tmp_path, answers=("7", "7.0"))
    result = lint_package(release, key)

    assert result["status"] is False
    assert result["checks"]["answers_distinguishable"] is False
    assert any(error["code"] == "answers_cross_match" for error in result["errors"])
