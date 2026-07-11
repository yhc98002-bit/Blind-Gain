from __future__ import annotations

import json
from pathlib import Path

from scripts.watch_anchor_checkpoints import (
    merged_checkpoint_complete,
    raw_signature,
    tracker_reached,
    valid_relocation_marker,
)


def _raw(actor: Path, world_size: int = 2) -> None:
    actor.mkdir(parents=True)
    for family in ("model", "optim"):
        for rank in range(world_size):
            (actor / f"{family}_world_size_{world_size}_rank_{rank}.pt").write_bytes(
                f"{family}-{rank}".encode("ascii")
            )


def test_raw_signature_rejects_checkpoint_missing_one_optimizer_rank(tmp_path: Path) -> None:
    actor = tmp_path / "actor"
    _raw(actor)
    (actor / "optim_world_size_2_rank_1.pt").unlink()

    assert raw_signature(actor) is None


def test_raw_signature_changes_when_a_shard_is_rewritten(tmp_path: Path) -> None:
    actor = tmp_path / "actor"
    _raw(actor)
    before = raw_signature(actor)
    shard = actor / "model_world_size_2_rank_0.pt"
    shard.write_bytes(b"replacement-with-different-size")
    after = raw_signature(actor)

    assert before is not None
    assert after is not None
    assert before != after


def test_tracker_requires_registered_step(tmp_path: Path) -> None:
    (tmp_path / "checkpoint_tracker.json").write_text(
        json.dumps({"last_global_step": 60}), encoding="utf-8"
    )

    assert tracker_reached(tmp_path, 60)
    assert not tracker_reached(tmp_path, 80)


def test_tracker_treats_partial_json_as_not_ready(tmp_path: Path) -> None:
    (tmp_path / "checkpoint_tracker.json").write_text('{"last_global_step":', encoding="utf-8")

    assert not tracker_reached(tmp_path, 80)


def test_valid_raw_marker_allows_restart_after_source_shards_moved(tmp_path: Path) -> None:
    actor = tmp_path / "global_step_80" / "actor"
    archive = tmp_path / "archive" / "global_step_80" / "actor"
    actor.mkdir(parents=True)
    archive.mkdir(parents=True)
    (actor / "RAW_STATE_RELOCATED.json").write_text(
        json.dumps(
            {
                "status": "raw_training_state_relocated_due_to_shared_quota",
                "archive_path": str(archive),
            }
        ),
        encoding="utf-8",
    )

    assert valid_relocation_marker(actor, "RAW_STATE_RELOCATED.json")
    assert raw_signature(actor) is None


def test_relocation_marker_is_invalid_if_archive_disappears(tmp_path: Path) -> None:
    actor = tmp_path / "actor"
    actor.mkdir()
    (actor / "MERGED_CHECKPOINT_RELOCATED.json").write_text(
        json.dumps(
            {
                "status": "merged_checkpoint_relocated",
                "archive_path": str(tmp_path / "missing"),
            }
        ),
        encoding="utf-8",
    )

    assert not valid_relocation_marker(actor, "MERGED_CHECKPOINT_RELOCATED.json")


def test_merged_checkpoint_requires_every_indexed_shard(tmp_path: Path) -> None:
    merged = tmp_path / "huggingface"
    merged.mkdir()
    (merged / "model.safetensors.index.json").write_text(
        json.dumps(
            {
                "weight_map": {
                    "a": "model-00001-of-00002.safetensors",
                    "b": "model-00002-of-00002.safetensors",
                }
            }
        ),
        encoding="utf-8",
    )
    (merged / "model-00001-of-00002.safetensors").write_bytes(b"one")

    assert not merged_checkpoint_complete(merged)
    (merged / "model-00002-of-00002.safetensors").write_bytes(b"two")
    assert merged_checkpoint_complete(merged)


def test_watcher_never_reads_training_or_validation_metric_logs() -> None:
    root = Path(__file__).resolve().parents[1]
    source = (root / "scripts" / "watch_anchor_checkpoints.py").read_text(encoding="utf-8")
    assert "experiment_log.jsonl" not in source
    assert "generations.log" not in source
    assert "best_val_reward_score" not in source
