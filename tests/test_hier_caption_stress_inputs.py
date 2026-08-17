"""Fixtures for scripts/build_hier_caption_stress_inputs.py: file-suffix side
binding (the swap must NOT be applied), invariance exclusion, on-disk sha
verification, and overwrite refusal."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_hier_caption_stress_inputs",
    ROOT / "scripts/build_hier_caption_stress_inputs.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def _write_pair(images: Path, pair_id: str) -> dict:
    row = {"pair_id": pair_id, "question": f"q for {pair_id}",
           "template_id": "hier_test_v0", "role": "target_switch",
           "provenance": {"semantic_side_assignment_swapped": False}}
    for side in ("a", "b"):
        blob = f"{pair_id}_{side}_png_bytes".encode()
        path = images / f"{pair_id}_{side}.png"
        path.write_bytes(blob)
        row[f"image_{side}_path"] = str(path)
        row[f"image_{side}_sha256"] = hashlib.sha256(blob).hexdigest()
        row[f"answer_{side}"] = f"ans_{pair_id}_{side}"
    return row


def _build_fixture(tmp_path: Path) -> Path:
    data_dir = tmp_path / "dev"
    images = data_dir / "src_images"
    images.mkdir(parents=True)
    rows = [_write_pair(images, "hier1_test_c1_target_switch_0001"),
            _write_pair(images, "hier1_test_c1_target_stable_0002"),
            _write_pair(images, "hier1_test_c1_invariance_0003")]
    rows[1]["role"] = "target_stable"
    rows[1]["provenance"]["semantic_side_assignment_swapped"] = True
    rows[2]["role"] = "invariance"
    (data_dir / "manifest_hier_test_v1_c1_l3.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return data_dir


def _run(data_dir: Path, report: Path) -> None:
    argv = sys.argv
    sys.argv = ["build_hier_caption_stress_inputs.py",
                "--data-dir", str(data_dir), "--report", str(report)]
    try:
        MOD.main()
    finally:
        sys.argv = argv


def test_builds_release_and_key_with_file_suffix_binding(tmp_path, monkeypatch):
    data_dir = _build_fixture(tmp_path)
    monkeypatch.setattr(MOD, "FAMILIES", {"hier_test_v1": ("c1",)})
    report = tmp_path / "report.json"
    _run(data_dir, report)

    release = [json.loads(l) for l in
               (data_dir / "caption_stress_hier_test_v1/manifest.jsonl")
               .read_text().splitlines()]
    key = [json.loads(l) for l in
           (data_dir / "caption_stress_key_hier_test_v1.jsonl")
           .read_text().splitlines()]
    assert len(release) == 2 and len(key) == 2  # invariance excluded
    assert all("invariance" not in r["pair_id"] for r in release)
    # swapped pair: answer must still follow the FILE-SUFFIX side
    swapped = next(k for k in key if "target_stable" in k["pair_id"])
    by_side = {m["source_side"]: m["answer"] for m in swapped["members"]}
    assert by_side["a"] == f"ans_{swapped['pair_id']}_a"
    assert by_side["b"] == f"ans_{swapped['pair_id']}_b"
    # images hard-linked and hashes recorded
    member = release[0]["members"][0]
    linked = data_dir / "caption_stress_hier_test_v1" / member["image_path"]
    assert linked.is_file()
    assert hashlib.sha256(linked.read_bytes()).hexdigest() == member["image_sha256"]
    assert json.loads(report.read_text())["families"]["hier_test_v1"]["pairs"] == 2

    with pytest.raises(FileExistsError):
        _run(data_dir, tmp_path / "report2.json")  # release dir already exists


def test_refuses_on_disk_sha_mismatch(tmp_path, monkeypatch):
    data_dir = _build_fixture(tmp_path)
    monkeypatch.setattr(MOD, "FAMILIES", {"hier_test_v1": ("c1",)})
    manifest = data_dir / "manifest_hier_test_v1_c1_l3.jsonl"
    rows = [json.loads(l) for l in manifest.read_text().splitlines()]
    rows[0]["image_a_sha256"] = "0" * 64
    manifest.write_text("".join(json.dumps(r) + "\n" for r in rows))
    with pytest.raises(ValueError, match="on-disk sha mismatch"):
        _run(data_dir, tmp_path / "report.json")
