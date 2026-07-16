from __future__ import annotations

from pathlib import Path

from PIL import Image

from scripts.audit_mini_a5_corpus import audit_pair_files
from src.fliptrack.schema import sha256_file


def _pair(tmp_path: Path) -> dict:
    image_a = tmp_path / "image_a.png"
    image_b = tmp_path / "image_b.png"
    mask_a = tmp_path / "mask_a.png"
    mask_b = tmp_path / "mask_b.png"
    Image.new("RGB", (720, 520), "white").save(image_a)
    changed = Image.new("RGB", (720, 520), "white")
    changed.putpixel((10, 10), (0, 0, 0))
    changed.save(image_b)
    mask = Image.new("L", (720, 520), 0)
    mask.putpixel((10, 10), 255)
    mask.save(mask_a)
    mask.save(mask_b)
    return {
        "pair_group_uid": "p1",
        "image_a_path": str(image_a),
        "image_b_path": str(image_b),
        "changed_region_mask_a": str(mask_a),
        "changed_region_mask_b": str(mask_b),
        "image_a_sha256": sha256_file(image_a),
        "image_b_sha256": sha256_file(image_b),
        "mask_sha256": sha256_file(mask_a),
    }


def test_exact_pair_files_pass(tmp_path: Path) -> None:
    assert audit_pair_files(_pair(tmp_path), tmp_path) == []


def test_adversarial_mask_hiding_changed_pixel_fails(tmp_path: Path) -> None:
    pair = _pair(tmp_path)
    bad_mask = Image.new("L", (720, 520), 0)
    bad_mask.save(pair["changed_region_mask_a"])
    pair["mask_sha256"] = sha256_file(pair["changed_region_mask_a"])
    errors = audit_pair_files(pair, tmp_path)
    assert any("mask B hash mismatch" in error or "mask hash mismatch" in error for error in errors)
    assert any("mask A is not the exact changed-pixel mask" in error for error in errors)
