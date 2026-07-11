from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.easyr1_checkpoint_guard import guard_easyr1_checkpoint_save
from src.ops.storage_guard import GIB, StorageGuardRefusal


def test_anchor_path_is_untouched_when_pilot_guard_flag_is_absent(tmp_path: Path) -> None:
    called = False

    def fail_if_called(_: Path) -> int:
        nonlocal called
        called = True
        raise AssertionError("disabled guard must not probe storage")

    result = guard_easyr1_checkpoint_save(
        tmp_path / "anchor",
        60,
        environment={},
        free_probe=fail_if_called,
    )

    assert result is None
    assert not called


def test_enabled_pilot_guard_fails_loudly_without_expected_checkpoint_size(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="REQUIRED_BYTES"):
        guard_easyr1_checkpoint_save(
            tmp_path / "pilot",
            20,
            environment={
                "BLIND_GAINS_STORAGE_GUARD_ENABLED": "1",
                "BLIND_GAINS_CHECKPOINT_TIER": "T",
            },
        )


def test_enabled_pilot_guard_refuses_low_scratch_before_save(tmp_path: Path) -> None:
    log = tmp_path / "guard.jsonl"
    with pytest.raises(StorageGuardRefusal, match="free-space floor"):
        guard_easyr1_checkpoint_save(
            tmp_path / "pilot",
            20,
            environment={
                "BLIND_GAINS_STORAGE_GUARD_ENABLED": "1",
                "BLIND_GAINS_CHECKPOINT_TIER": "T",
                "BLIND_GAINS_CHECKPOINT_REQUIRED_BYTES": str(6 * GIB),
                "BLIND_GAINS_STORAGE_GUARD_LOG": str(log),
            },
            free_probe=lambda _: 45 * GIB,
            filesystem_probe=lambda _: "xfs",
        )

    assert '"status": "refused"' in log.read_text(encoding="utf-8")


def test_patch_places_guard_before_checkpoint_deletion_and_write() -> None:
    root = Path(__file__).resolve().parents[1]
    patch = (root / "docs" / "easyr1_storage_guard_patch.diff").read_text(encoding="utf-8")
    guard_offset = patch.index("guard_easyr1_checkpoint_save(")
    save_offset = patch.index("if self.val_reward_score")
    assert guard_offset < save_offset
