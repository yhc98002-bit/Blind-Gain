from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_caption_launcher_rejects_token_budget_in_gpu_position(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            "bash",
            "scripts/launch_fliptrack_caption_shards.sh",
            "an29",
            "0",
            "2",
            "model",
            "manifest",
            str(tmp_path / "run"),
            "384",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert "GPU_LIST" in result.stderr


def test_caption_qa_launcher_rejects_invalid_gpu_list(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            "bash",
            "scripts/launch_caption_qa_shards.sh",
            "an29",
            "0",
            "2",
            "model",
            "caption-run",
            str(tmp_path / "qa-run"),
            "8",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert "GPU_LIST" in result.stderr


def test_image_eval_launcher_rejects_mapping_that_launches_zero_workers(tmp_path: Path) -> None:
    manifest = tmp_path / "input.jsonl"
    manifest.write_text('{"pair_id":"p"}\n', encoding="utf-8")
    result = subprocess.run(
        [
            "bash",
            "scripts/launch_fliptrack_eval_shards.sh",
            "an29",
            "1",
            "1",
            "model",
            str(manifest),
            str(tmp_path / "run"),
            "64",
            "1",
            "real",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert "No evaluation workers launched" in result.stderr


def test_image_eval_launcher_rejects_negative_shard_mapping_before_ssh(tmp_path: Path) -> None:
    manifest = tmp_path / "input.jsonl"
    manifest.write_text('{"pair_id":"p"}\n', encoding="utf-8")
    result = subprocess.run(
        [
            "bash",
            "scripts/launch_fliptrack_eval_shards.sh",
            "host-that-must-not-be-contacted",
            "-1",
            "1",
            "model",
            str(manifest),
            str(tmp_path / "negative-run"),
            "64",
            "0",
            "real",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert "No evaluation workers launched" in result.stderr
    assert "Could not resolve hostname" not in result.stderr


def test_image_eval_launcher_refuses_an_occupied_gpu_before_creating_run(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "input.jsonl"
    manifest.write_text('{"pair_id":"p"}\n', encoding="utf-8")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text("#!/usr/bin/env bash\nprintf '4321\\n'\n", encoding="utf-8")
    fake_ssh.chmod(0o755)
    run_dir = tmp_path / "must-not-exist"
    environment = dict(os.environ)
    environment["PATH"] = f"{fake_bin}:{environment['PATH']}"

    result = subprocess.run(
        [
            "bash",
            "scripts/launch_fliptrack_eval_shards.sh",
            "an29",
            "0",
            "1",
            "model",
            str(manifest),
            str(run_dir),
            "32",
            "4",
            "real",
        ],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 75
    assert "GPU 4 on an29 is occupied" in result.stderr
    assert not run_dir.exists()


@pytest.mark.parametrize(
    "launcher",
    [
        "launch_fliptrack_eval_shards.sh",
        "launch_fliptrack_caption_shards.sh",
        "launch_caption_qa_shards.sh",
        "launch_caption_store_shards.sh",
    ],
)
def test_sharded_launchers_reject_negative_indices_and_use_remote_finalizer(launcher: str) -> None:
    source = (ROOT / "scripts" / launcher).read_text(encoding="utf-8")
    assert '"${SHARD_INDEX}" -lt 0' in source
    assert 'scripts/launch_remote_sharded_finalizer.sh "${NODE}"' in source


def test_remote_finalizer_is_started_on_compute_node() -> None:
    source = (ROOT / "scripts/launch_remote_sharded_finalizer.sh").read_text(encoding="utf-8")
    assert 'ssh "${NODE}"' in source
    assert "scripts/finalize_sharded_run.py" in source


def test_caption_store_launcher_hashes_symlink_targets() -> None:
    source = (ROOT / "scripts/launch_caption_store_shards.sh").read_text(encoding="utf-8")
    assert 'find -L "${IMAGE_DIR}" -type f' in source


def test_eval_manifests_record_all_behavior_changing_launcher_arguments() -> None:
    image_source = (ROOT / "scripts" / "launch_fliptrack_eval_shards.sh").read_text(encoding="utf-8")
    caption_source = (ROOT / "scripts" / "launch_caption_qa_shards.sh").read_text(encoding="utf-8")
    assert "'${GPU_LIST}' ${IMAGE_MODE}" in image_source
    assert "'${GPU_LIST}' ${MAX_NEW_TOKENS}" in caption_source
    assert '"run_id": "$(basename' in image_source
    assert '"run_id": "$(basename' in caption_source


def test_image_eval_launcher_pins_seed_model_revision_and_atomic_outputs() -> None:
    launcher = (ROOT / "scripts" / "launch_fliptrack_eval_shards.sh").read_text(
        encoding="utf-8"
    )
    evaluator = (ROOT / "scripts" / "eval_qwen_vl_fliptrack.py").read_text(
        encoding="utf-8"
    )

    assert 'EVAL_SEED="${BLIND_GAINS_EVAL_SEED:-0}"' in launcher
    assert '"model_revision": "${MODEL_PATH}"' in launcher
    assert '"seed": ${EVAL_SEED}' in launcher
    assert '"prompt_contract": ${PROMPT_CONTRACT_JSON}' in launcher
    assert '"prompt_contract_sha256": "${PROMPT_CONTRACT_SHA256}"' in launcher
    assert "--seed ${EVAL_SEED} --noise-seed ${EVAL_SEED}" in launcher
    assert 'raise FileExistsError(f"refusing to overwrite FlipTrack predictions:' in evaluator
    assert 'partial_out.open("x"' in evaluator
    assert "os.replace(partial_out, out_path)" in evaluator
    assert "os.replace(partial_metrics, metrics_path)" in evaluator


def test_image_eval_launcher_refuses_an_existing_run_directory(tmp_path: Path) -> None:
    run_dir = tmp_path / "existing"
    run_dir.mkdir()
    result = subprocess.run(
        [
            "bash",
            str(ROOT / "scripts/launch_fliptrack_eval_shards.sh"),
            "an29",
            "0",
            "1",
            "missing-model",
            "missing-manifest",
            str(run_dir),
            "32",
            "0",
            "real",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 73
    assert "Refusing to overwrite evaluation run directory" in result.stderr


def test_image_eval_launcher_binds_registered_pilot_checkpoint_metadata() -> None:
    launcher = (ROOT / "scripts/launch_fliptrack_eval_shards.sh").read_text(
        encoding="utf-8"
    )
    assert "BLIND_GAINS_PILOT_SOURCE_RUN" in launcher
    assert "BLIND_GAINS_PILOT_GLOBAL_STEP" in launcher
    assert "Pilot source run must be complete" in launcher
    assert "Pilot checkpoint path does not match the registered source run and step" in launcher
    assert "load_checkpoint_path" in launcher
    assert "Pilot evaluation manifest is not the locked R19 manifest" in launcher
    assert '"source_training_run": ${PILOT_SOURCE_JSON}' in launcher
    assert '"global_step": ${PILOT_STEP_JSON}' in launcher


def test_image_eval_maps_noncontiguous_gpus_by_replica_ordinal() -> None:
    source = (ROOT / "scripts" / "launch_fliptrack_eval_shards.sh").read_text(
        encoding="utf-8"
    )

    assert 'read -r -a GPU_IDS <<< "${GPU_LIST}"' in source
    assert 'for POSITION in "${!GPU_IDS[@]}"' in source
    assert 'GPU="${GPU_IDS[${POSITION}]}"' in source
    assert "SHARD_INDEX=$((SHARD_OFFSET + POSITION))" in source
    assert "SHARD_INDEX=$((SHARD_OFFSET + GPU))" not in source
    assert "shards assigned by replica ordinal" in source


def test_caption_qa_maps_noncontiguous_gpus_by_replica_ordinal() -> None:
    source = (ROOT / "scripts" / "launch_caption_qa_shards.sh").read_text(
        encoding="utf-8"
    )

    assert 'read -r -a GPU_IDS <<< "${GPU_LIST}"' in source
    assert 'for POSITION in "${!GPU_IDS[@]}"' in source
    assert 'GPU="${GPU_IDS[${POSITION}]}"' in source
    assert "SHARD_INDEX=$((SHARD_OFFSET + POSITION))" in source
    assert "SHARD_INDEX=$((SHARD_OFFSET + GPU))" not in source
    assert "exactly one TP1 GPU replica per shard" in source
    assert "--query-compute-apps=pid" in source
    assert "nohup setsid env" in source


@pytest.mark.parametrize(
    "launcher",
    [
        "launch_fliptrack_caption_shards.sh",
        "launch_caption_store_shards.sh",
        "launch_parser_agreement_generation.sh",
    ],
)
def test_single_artifact_workers_publish_only_by_atomic_rename(launcher: str) -> None:
    source = (ROOT / "scripts" / launcher).read_text(encoding="utf-8")
    assert '.partial"' in source
    assert "&& mv '" in source
