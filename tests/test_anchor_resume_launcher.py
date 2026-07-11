from pathlib import Path


def test_anchor_resume_keeps_native_recipe_and_single_node_placement() -> None:
    source = Path("scripts/launch_anchor_step80_resume.sh").read_text(encoding="utf-8")

    assert "configs/train/anchor_a0_recipe_3b_geo3k.yaml" in source
    assert "trainer.load_checkpoint_path=${RESUME_CHECKPOINT}" in source
    assert "trainer.find_last_checkpoint=false" in source
    assert 'COMMAND="PYTHONPATH=${ROOT}/artifacts/repos/EasyR1:${ROOT} python' in source
    assert 'tensor_parallel_width: 1' in source
    assert 'replica_count: 1' in source
    assert 'gpu_ids: [0,1,2,3]' in source
    assert "pilot_reward" not in source
    assert "[r]un_blind_solvability_v2.py|[V]LMEvalKit/run.py" in source
    assert "short_ray_tmp_dir" in source


def test_anchor_resume_requires_checksum_restore_marker() -> None:
    source = Path("scripts/launch_anchor_step80_resume.sh").read_text(encoding="utf-8")

    assert "RAW_STATE_RESTORED_FOR_RESUME.json" in source
    assert 'restored_for_optimizer_resume' in source
    assert "raw_training_state.source.sha256" in source
    assert "resume_artifact_hash" in source
    assert 'jq -r .data_manifest_hash' in source
