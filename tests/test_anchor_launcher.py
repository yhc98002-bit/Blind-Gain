from pathlib import Path

import yaml


def test_anchor_launcher_uses_immutable_run_checkpoint_and_stoppable_pid() -> None:
    source = Path("scripts/launch_anchor_a0_recipe_3b_geo3k.sh").read_text(encoding="utf-8")

    assert 'CHECKPOINT_PATH="${ROOT}/checkpoints/anchor_a0_recipe_3b_geo3k/${RUN_ID}"' in source
    assert "trainer.save_checkpoint_path=${CHECKPOINT_PATH}" in source
    assert "trainer.experiment_name=${RUN_ID}" in source
    assert "flock -n --no-fork" in source


def test_anchor_validation_batch_bounds_multimodal_object_gather() -> None:
    config = yaml.safe_load(Path("configs/train/anchor_a0_recipe_3b_geo3k.yaml").read_text(encoding="utf-8"))
    trainer_source = Path("artifacts/repos/EasyR1/verl/trainer/ray_trainer.py").read_text(encoding="utf-8")
    sharding_source = Path("artifacts/repos/EasyR1/verl/workers/sharding_manager/fsdp_vllm.py").read_text(encoding="utf-8")

    assert config["data"]["val_batch_size"] <= 64
    assert "for batch_dict in self.val_dataloader" in trainer_source
    assert "all_gather_data_proto" in sharding_source


def test_checkpoint_merge_launcher_is_immutable_and_logged() -> None:
    launcher = Path("scripts/launch_easyr1_checkpoint_merge.sh").read_text(encoding="utf-8")

    assert "Refusing to overwrite an already merged checkpoint" in launcher
    assert "model.safetensors.index.json" in launcher
    assert "model_merger_no_deepspeed.py" in launcher
    assert "run_manifest_job.py" in launcher
    assert "data_manifest_hash" in launcher
    assert "CUDA_HOME=/usr/local/cuda" in launcher
