from pathlib import Path


def test_checkpoint_merge_launcher_accepts_any_world_size_and_guards_output() -> None:
    root = Path(__file__).resolve().parents[1]
    script = (root / "scripts" / "launch_easyr1_checkpoint_merge.sh").read_text(encoding="utf-8")
    assert 'MODEL_SHARDS=("${ROOT}/${ACTOR_DIR}"/model_world_size_*_rank_*.pt)' in script
    assert "model_world_size_2_rank_0.pt" not in script
    assert 'sha256sum "${MODEL_SHARDS[@]}"' in script
    assert "scripts/storage_guard.py" in script
    assert "--tier S" in script
    assert "--operation checkpoint_merge" in script
    assert 'MERGE_REQUIRED_BYTES="$((MERGE_REQUIRED_BYTES + SHARD_BYTES))"' in script
