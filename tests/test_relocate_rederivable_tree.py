from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts.relocate_rederivable_tree import inventory_tree, relocate_tree
from src.ops.storage_guard import GuardResult


def test_relocation_hashes_then_replaces_source_with_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "shared" / "cache"
    source.mkdir(parents=True)
    (source / "image.bin").write_bytes(b"deterministic-cache")
    destination = tmp_path / "scratch" / "cache"
    manifest = tmp_path / "shared" / "manifest.json"

    allowed = GuardResult(
        schema_version=1,
        event="storage_guard",
        checked_at_utc="2026-07-12T00:00:00Z",
        status="pass",
        tier="T",
        operation="fixture",
        path=str(tmp_path / "scratch"),
        required_bytes=0,
        capacity_bytes=None,
        used_bytes=None,
        free_bytes_before=100,
        free_bytes_after=100,
        floor_bytes=0,
        filesystem_type="ext4",
        reason="ok",
    )

    monkeypatch.setattr(
        "scripts.relocate_rederivable_tree.check_storage",
        lambda **_: allowed,
    )
    payload = relocate_tree(
        source=source,
        destination=destination,
        manifest_path=manifest,
        operation="fixture",
    )

    assert source.is_symlink()
    assert source.resolve() == destination.resolve()
    assert destination.joinpath("image.bin").read_bytes() == b"deterministic-cache"
    assert payload["total_bytes"] == len(b"deterministic-cache")
    assert payload["files"][0]["sha256"] == hashlib.sha256(
        b"deterministic-cache"
    ).hexdigest()
    assert manifest.is_file()


def test_inventory_rejects_symlink_payload(tmp_path: Path) -> None:
    source = tmp_path / "cache"
    source.mkdir()
    target = tmp_path / "external.bin"
    target.write_bytes(b"must-not-follow")
    source.joinpath("linked.bin").symlink_to(target)

    with pytest.raises(ValueError, match="contains a symlink"):
        inventory_tree(source)
