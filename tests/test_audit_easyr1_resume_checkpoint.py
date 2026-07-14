from __future__ import annotations

from pathlib import Path

import pytest

from scripts.audit_easyr1_resume_checkpoint import audit_checkpoint


def _checkpoint(root: Path, *, world_size: int = 4) -> Path:
    checkpoint = root / "global_step_60"
    actor = checkpoint / "actor"
    actor.mkdir(parents=True)
    for family in ("model", "optim"):
        for rank in range(world_size):
            (actor / f"{family}_world_size_{world_size}_rank_{rank}.pt").write_bytes(
                f"{family}-{rank}".encode()
            )
    for rank in range(world_size):
        (actor / f"extra_state_world_size_{world_size}_rank_{rank}.pt").write_bytes(
            f"extra-{rank}".encode()
        )
    (checkpoint / "dataloader.pt").write_bytes(b"loader")
    return checkpoint


def test_resume_checkpoint_audit_hashes_complete_rank_sets(tmp_path: Path) -> None:
    payload, checksums = audit_checkpoint(_checkpoint(tmp_path), expected_step=60)

    assert payload["status"] == "pass"
    assert payload["model_rank_count"] == 4
    assert payload["optimizer_rank_count"] == 4
    assert payload["extra_state_rank_count"] == 4
    assert payload["file_count"] == 13
    assert len(checksums.splitlines()) == 13


def test_adversarial_mixed_world_size_cannot_replace_missing_rank(tmp_path: Path) -> None:
    checkpoint = _checkpoint(tmp_path)
    actor = checkpoint / "actor"
    (actor / "model_world_size_4_rank_3.pt").unlink()
    # The old count-only check still sees eight model/optimizer files.
    (actor / "model_world_size_8_rank_4.pt").write_bytes(b"wrong-world")

    with pytest.raises(ValueError, match="unexpected or conflicting rank files"):
        audit_checkpoint(checkpoint, expected_step=60)


def test_resume_checkpoint_audit_rejects_empty_state(tmp_path: Path) -> None:
    checkpoint = _checkpoint(tmp_path)
    (checkpoint / "actor" / "optim_world_size_4_rank_2.pt").write_bytes(b"")

    with pytest.raises(ValueError, match="checkpoint file is empty"):
        audit_checkpoint(checkpoint, expected_step=60)
