from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from scripts.build_human_audit_bundle import build_bundle


def _jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{json.dumps(row)}\n" for row in rows), encoding="utf-8")


def _fixture(tmp_path: Path) -> dict[str, Path]:
    package = tmp_path / "release"
    images = package / "images"
    images.mkdir(parents=True)
    image_rows: dict[str, dict] = {}
    for opaque_id in ("opaque-a-first", "opaque-a-second", "opaque-b-first"):
        members = []
        for side in ("1", "2"):
            data = f"{opaque_id}-{side}".encode()
            filename = f"{opaque_id}-{side}.png"
            (images / filename).write_bytes(data)
            members.append(
                {
                    "member_id": f"{opaque_id}-member-{side}",
                    "image_path": f"images/{filename}",
                    "image_sha256": hashlib.sha256(data).hexdigest(),
                }
            )
        image_rows[opaque_id] = {
            "pair_id": opaque_id,
            "question": f"Question for {opaque_id}?",
            "members": members,
        }

    source = tmp_path / "source.jsonl"
    release = package / "manifest.jsonl"
    key = tmp_path / "key.jsonl"
    viewer = tmp_path / "viewer.html"
    _jsonl(
        source,
        [
            {"pair_id": "source-a-first", "template_id": "template-a"},
            {"pair_id": "source-b-first", "template_id": "template-b"},
            {"pair_id": "source-a-second", "template_id": "template-a"},
        ],
    )
    # Release order is intentionally different from frozen source order.
    _jsonl(
        release,
        [
            image_rows["opaque-a-second"],
            image_rows["opaque-b-first"],
            image_rows["opaque-a-first"],
        ],
    )
    _jsonl(
        key,
        [
            {
                "pair_id": "opaque-a-second",
                "source_pair_id": "source-a-second",
                "template_id": "template-a",
                "category": "a",
                "members": [
                    {"member_id": "opaque-a-second-member-1", "answer": "1"},
                    {"member_id": "opaque-a-second-member-2", "answer": "2"},
                ],
            },
            {
                "pair_id": "opaque-a-first",
                "source_pair_id": "source-a-first",
                "template_id": "template-a",
                "category": "a",
                "members": [
                    {"member_id": "opaque-a-first-member-1", "answer": "1"},
                    {"member_id": "opaque-a-first-member-2", "answer": "2"},
                ],
            },
            {
                "pair_id": "opaque-b-first",
                "source_pair_id": "source-b-first",
                "template_id": "template-b",
                "category": "b",
                "members": [
                    {"member_id": "opaque-b-first-member-1", "answer": "1"},
                    {"member_id": "opaque-b-first-member-2", "answer": "2"},
                ],
            },
        ],
    )
    viewer.write_text("<!doctype html><title>fixture</title>", encoding="utf-8")
    return {
        "source": source,
        "release": release,
        "key": key,
        "package": package,
        "viewer": viewer,
    }


def _build(paths: dict[str, Path], output: Path) -> dict:
    return build_bundle(
        source_manifest=paths["source"],
        release_manifest=paths["release"],
        answer_key=paths["key"],
        package_dir=paths["package"],
        viewer=paths["viewer"],
        output_zip=output,
        bundle_name="audit_fixture",
        pairs_per_template=1,
    )


def test_bundle_uses_source_order_not_randomized_release_order(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    output = tmp_path / "audit.zip"

    result = _build(paths, output)

    assert result["pair_count"] == 2
    assert result["image_count"] == 4
    assert result["template_counts"] == {"template-a": 1, "template-b": 1}
    with ZipFile(output) as archive:
        names = set(archive.namelist())
        manifest = [
            json.loads(line)
            for line in archive.read("audit_fixture/package/manifest.jsonl").decode().splitlines()
        ]
        keys = [
            json.loads(line)
            for line in archive.read("audit_fixture/private/answer_key.jsonl").decode().splitlines()
        ]
        metadata = json.loads(archive.read("audit_fixture/bundle_manifest.json"))

    assert [row["pair_id"] for row in manifest] == ["opaque-a-first", "opaque-b-first"]
    assert [row["source_pair_id"] for row in keys] == ["source-a-first", "source-b-first"]
    assert metadata["selection"]["strategy"] == "first_n_per_template_in_source_manifest_order"
    assert metadata["selection"]["opaque_pair_ids"] == ["opaque-a-first", "opaque-b-first"]
    assert "audit_fixture/human_audit_viewer.html" in names
    assert "audit_fixture/README.txt" in names
    assert not any("a-second" in name for name in names if name.endswith(".png"))


def test_bundle_rejects_unsafe_image_path(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    rows = [json.loads(line) for line in paths["release"].read_text().splitlines()]
    target = next(row for row in rows if row["pair_id"] == "opaque-a-first")
    target["members"][0]["image_path"] = "../private/key.jsonl"
    _jsonl(paths["release"], rows)

    with pytest.raises(ValueError, match="unsafe relative path"):
        _build(paths, tmp_path / "unsafe.zip")


def test_bundle_rejects_image_hash_mismatch(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    rows = [json.loads(line) for line in paths["release"].read_text().splitlines()]
    target = next(row for row in rows if row["pair_id"] == "opaque-a-first")
    target["members"][0]["image_sha256"] = "0" * 64
    _jsonl(paths["release"], rows)

    with pytest.raises(ValueError, match="image hash mismatch"):
        _build(paths, tmp_path / "bad-hash.zip")


def test_bundle_refuses_to_overwrite_archive(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    output = tmp_path / "existing.zip"
    output.write_bytes(b"existing")

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        _build(paths, output)
