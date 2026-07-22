from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts.relocate_rederivable_tree import (
    inventory_tree,
    prepare_relocation_plan,
    relocate_tree,
)
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
        destination_tier="T",
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


def test_shared_destination_uses_quota_guard_not_scratch_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "scratch" / "cache"
    source.mkdir(parents=True)
    (source / "payload.bin").write_bytes(b"shared-destination")
    destination = tmp_path / "shared" / "cache"
    manifest = tmp_path / "manifest.json"
    observed: dict[str, object] = {}
    allowed = GuardResult(
        schema_version=1,
        event="storage_guard",
        checked_at_utc="2026-07-16T00:00:00Z",
        status="pass",
        tier="S",
        operation="fixture",
        path=str(destination.parent),
        required_bytes=len(b"shared-destination"),
        capacity_bytes=100,
        used_bytes=10,
        free_bytes_before=90,
        free_bytes_after=72,
        floor_bytes=20,
        filesystem_type=None,
        reason="ok",
    )

    def capture_guard(**kwargs: object) -> GuardResult:
        observed.update(kwargs)
        return allowed

    monkeypatch.setattr(
        "scripts.relocate_rederivable_tree.check_storage", capture_guard
    )
    relocate_tree(
        source=source,
        destination=destination,
        manifest_path=manifest,
        operation="fixture",
        destination_tier="S",
        shared_quota_root=tmp_path / "shared",
        shared_usage_snapshot=tmp_path / "usage.json",
    )

    assert observed["tier"] == "S"
    assert observed["shared_quota_root"] == tmp_path / "shared"
    assert "usage_probe" in observed
    assert "scratch_floor_bytes" not in observed


def test_persistent_relocation_rejects_source_changed_after_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "scratch" / "seed2_raw"
    source.mkdir(parents=True)
    payload = source / "optim.pt"
    payload.write_bytes(b"hash-before-plan")
    source.joinpath("raw.source.sha256").write_text(
        f"{hashlib.sha256(payload.read_bytes()).hexdigest()}  optim.pt\n",
        encoding="utf-8",
    )
    destination = tmp_path / "shared" / "seed2_raw"
    plan = tmp_path / "plan.json"
    manifest = tmp_path / "manifest.json"
    prepare_relocation_plan(
        source=source,
        destination=destination,
        plan_path=plan,
        operation="preserve_seed2_raw",
        artifact_class="persistent_training_state",
    )

    # This is the adversarial state the old one-pass mover could not distinguish
    # from the reviewed dry-run: the source changed after approval.
    payload.write_bytes(b"different-after-plan")
    monkeypatch.setattr(
        "scripts.relocate_rederivable_tree.check_storage",
        lambda **_: pytest.fail("guard must not run after plan mismatch"),
    )
    with pytest.raises(RuntimeError, match="immutable relocation plan"):
        relocate_tree(
            source=source,
            destination=destination,
            manifest_path=manifest,
            operation="preserve_seed2_raw",
            destination_tier="S",
            artifact_class="persistent_training_state",
            expected_plan_path=plan,
        )

    assert source.is_dir() and not source.is_symlink()
    assert not destination.exists()
    assert not manifest.exists()


def test_persistent_plan_rejects_stale_embedded_checksum(tmp_path: Path) -> None:
    source = tmp_path / "seed2_raw"
    source.mkdir()
    source.joinpath("model.pt").write_bytes(b"current")
    source.joinpath("raw.source.sha256").write_text(
        f"{hashlib.sha256(b'old').hexdigest()}  model.pt\n", encoding="utf-8"
    )

    with pytest.raises(RuntimeError, match="embedded checksum"):
        prepare_relocation_plan(
            source=source,
            destination=tmp_path / "persistent" / "seed2_raw",
            plan_path=tmp_path / "plan.json",
            operation="preserve_seed2_raw",
            artifact_class="persistent_training_state",
        )
