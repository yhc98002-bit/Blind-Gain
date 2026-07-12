from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.relocate_easyr1_raw_checkpoint import relocate_raw_checkpoint


def _actor(tmp_path: Path, *, merged: bool = True) -> Path:
    actor = tmp_path / "checkpoint" / "actor"
    actor.mkdir(parents=True)
    for family in ("model", "optim"):
        for rank in range(2):
            (actor / f"{family}_world_size_2_rank_{rank}.pt").write_bytes(
                f"{family}-{rank}".encode("ascii")
            )
    if merged:
        huggingface = actor / "huggingface"
        huggingface.mkdir()
        (huggingface / "model.safetensors.index.json").write_text(
            '{"weight_map": {"weight": "model-00001-of-00001.safetensors"}}\n',
            encoding="ascii",
        )
        (huggingface / "model-00001-of-00001.safetensors").write_bytes(b"merged")
    return actor


def test_relocation_verifies_archive_before_removing_raw_shards(tmp_path: Path) -> None:
    actor = _actor(tmp_path)
    archive = tmp_path / "archive"

    payload = relocate_raw_checkpoint(actor, archive)

    assert payload["status"] == "raw_training_state_relocated_due_to_shared_quota"
    assert len(payload["files"]) == 4
    assert not list(actor.glob("model_world_size_*.pt"))
    assert not list(actor.glob("optim_world_size_*.pt"))
    assert (actor / "huggingface" / "model.safetensors.index.json").is_file()
    marker = json.loads((actor / "RAW_STATE_RELOCATED.json").read_text(encoding="utf-8"))
    assert marker["archive_path"] == str(archive.resolve())
    assert sorted(path.name for path in archive.glob("*.pt")) == sorted(
        record["file"] for record in payload["files"]
    )


def test_relocation_refuses_to_remove_shards_without_merged_checkpoint(tmp_path: Path) -> None:
    actor = _actor(tmp_path, merged=False)

    with pytest.raises(FileNotFoundError, match="merged Hugging Face checkpoint"):
        relocate_raw_checkpoint(actor, tmp_path / "archive")

    assert len(list(actor.glob("*_world_size_*.pt"))) == 4


def test_relocation_rejects_conflicting_archive_file(tmp_path: Path) -> None:
    actor = _actor(tmp_path)
    archive = tmp_path / "archive"
    archive.mkdir()
    (archive / "model_world_size_2_rank_0.pt").write_bytes(b"wrong")

    with pytest.raises(RuntimeError, match="mismatch"):
        relocate_raw_checkpoint(actor, archive)

    assert len(list(actor.glob("*_world_size_*.pt"))) == 4


def test_relocation_rejects_incomplete_rank_set(tmp_path: Path) -> None:
    actor = _actor(tmp_path)
    (actor / "optim_world_size_2_rank_1.pt").unlink()

    with pytest.raises(ValueError, match="incomplete optim shards"):
        relocate_raw_checkpoint(actor, tmp_path / "archive")

    assert len(list(actor.glob("*_world_size_*.pt"))) == 3


def _archived_raw_state(run_root: Path, step: int, *, corrupt: bool = False) -> Path:
    actor = run_root / f"global_step_{step}" / "actor"
    actor.mkdir(parents=True)
    lines = []
    for family in ("model", "optim"):
        for rank in range(2):
            path = actor / f"{family}_world_size_2_rank_{rank}.pt"
            path.write_bytes(f"{family}-{rank}-step-{step}".encode("ascii"))
            lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n")
    (actor / "raw_training_state.source.sha256").write_text("".join(lines), encoding="ascii")
    if corrupt:
        (actor / "model_world_size_2_rank_0.pt").write_bytes(b"changed after manifest")
    return actor


def test_relocation_keeps_only_latest_raw_state_and_records_deletions(tmp_path: Path) -> None:
    shared = tmp_path / "shared"
    actor = _actor(shared)
    (shared / "checkpoint").rename(shared / "global_step_60")
    actor = shared / "global_step_60" / "actor"
    run_archive = tmp_path / "archive" / "run"
    old20 = _archived_raw_state(run_archive, 20)
    old40 = _archived_raw_state(run_archive, 40)
    run_manifest = tmp_path / "run_manifest.json"
    run_manifest.write_text('{"run_id": "test", "status": "running"}\n', encoding="utf-8")
    report = tmp_path / "retention.md"

    payload = relocate_raw_checkpoint(
        actor,
        run_archive / "global_step_60" / "actor",
        run_archive_root=run_archive,
        run_manifest=run_manifest,
        retention_report=report,
    )

    assert not old20.exists()
    assert not old40.exists()
    assert (run_archive / "global_step_60" / "actor" / "model_world_size_2_rank_0.pt").is_file()
    assert [record["step"] for record in payload["retention_expired_states"]] == [20, 40]
    assert "global_step_20" in report.read_text(encoding="utf-8")
    manifest = json.loads(run_manifest.read_text(encoding="utf-8"))
    event = manifest["storage_retention_events"][0]
    assert event["status"] == "deleted_after_verification"
    assert event["merged_checkpoint_sha256"] == payload["merged_checkpoint_sha256"]


def test_retention_refuses_to_delete_archive_with_checksum_drift(tmp_path: Path) -> None:
    shared = tmp_path / "shared"
    actor = _actor(shared)
    (shared / "checkpoint").rename(shared / "global_step_60")
    actor = shared / "global_step_60" / "actor"
    run_archive = tmp_path / "archive" / "run"
    old = _archived_raw_state(run_archive, 40, corrupt=True)
    run_manifest = tmp_path / "run_manifest.json"
    run_manifest.write_text('{"run_id": "test", "status": "running"}\n', encoding="utf-8")

    with pytest.raises(RuntimeError, match="checksum mismatch"):
        relocate_raw_checkpoint(
            actor,
            run_archive / "global_step_60" / "actor",
            run_archive_root=run_archive,
            run_manifest=run_manifest,
            retention_report=tmp_path / "retention.md",
        )

    assert old.is_dir()
    assert len(list(actor.glob("*_world_size_*.pt"))) == 4


def test_retention_refuses_unexpected_sidecar_before_deleting_any_raw_state(tmp_path: Path) -> None:
    shared = tmp_path / "shared"
    actor = _actor(shared)
    (shared / "checkpoint").rename(shared / "global_step_60")
    actor = shared / "global_step_60" / "actor"
    run_archive = tmp_path / "archive" / "run"
    old = _archived_raw_state(run_archive, 40)
    (old / "unregistered_resume_note.txt").write_text("must survive\n", encoding="utf-8")
    run_manifest = tmp_path / "run_manifest.json"
    run_manifest.write_text('{"run_id": "test", "status": "running"}\n', encoding="utf-8")

    with pytest.raises(RuntimeError, match="unexpected entries"):
        relocate_raw_checkpoint(
            actor,
            run_archive / "global_step_60" / "actor",
            run_archive_root=run_archive,
            run_manifest=run_manifest,
            retention_report=tmp_path / "retention.md",
        )

    assert (old / "unregistered_resume_note.txt").is_file()
    assert len(list(old.glob("*_world_size_*.pt"))) == 4


def test_retention_expires_only_raw_files_and_preserves_merged_intermediate(tmp_path: Path) -> None:
    shared = tmp_path / "shared"
    actor = _actor(shared)
    (shared / "checkpoint").rename(shared / "global_step_80")
    actor = shared / "global_step_80" / "actor"
    run_archive = tmp_path / "archive" / "run"
    old = _archived_raw_state(run_archive, 60)
    merged = old / "huggingface"
    merged.mkdir()
    (merged / "model.safetensors.index.json").write_text("{}\n", encoding="utf-8")
    (merged / "merged_checkpoint.source.sha256").write_text(
        "0" * 64 + "  model.safetensors.index.json\n",
        encoding="ascii",
    )
    run_manifest = tmp_path / "run_manifest.json"
    run_manifest.write_text('{"run_id": "test", "status": "running"}\n', encoding="utf-8")

    relocate_raw_checkpoint(
        actor,
        run_archive / "global_step_80" / "actor",
        run_archive_root=run_archive,
        run_manifest=run_manifest,
        retention_report=tmp_path / "retention.md",
    )

    assert merged.is_dir()
    assert (merged / "model.safetensors.index.json").is_file()
    assert not list(old.glob("*_world_size_*.pt"))
    assert not (old / "raw_training_state.source.sha256").exists()


def test_later_retention_ignores_merged_only_older_step(tmp_path: Path) -> None:
    shared = tmp_path / "shared"
    actor = _actor(shared)
    (shared / "checkpoint").rename(shared / "global_step_100")
    actor = shared / "global_step_100" / "actor"
    run_archive = tmp_path / "archive" / "run"

    merged_only = run_archive / "global_step_60" / "actor" / "huggingface"
    merged_only.mkdir(parents=True)
    (merged_only / "model.safetensors.index.json").write_text("{}\n", encoding="utf-8")
    (merged_only / "merged_checkpoint.source.sha256").write_text("kept\n", encoding="ascii")
    latest_old_raw = _archived_raw_state(run_archive, 80)
    run_manifest = tmp_path / "run_manifest.json"
    run_manifest.write_text('{"run_id": "test", "status": "running"}\n', encoding="utf-8")

    payload = relocate_raw_checkpoint(
        actor,
        run_archive / "global_step_100" / "actor",
        run_archive_root=run_archive,
        run_manifest=run_manifest,
        retention_report=tmp_path / "retention.md",
    )

    assert merged_only.is_dir()
    assert not latest_old_raw.exists()
    assert [record["step"] for record in payload["retention_expired_states"]] == [80]


def _restored_shared_state(run_root: Path, step: int, *, corrupt: bool = False) -> Path:
    actor = run_root / f"global_step_{step}" / "actor"
    actor.mkdir(parents=True)
    records = []
    for family in ("model", "optim"):
        for rank in range(2):
            path = actor / f"{family}_world_size_2_rank_{rank}.pt"
            path.write_bytes(f"restored-{family}-{rank}-step-{step}".encode("ascii"))
            records.append(
                {
                    "file": path.name,
                    "bytes": path.stat().st_size,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
    (actor / "RAW_STATE_RESTORED_FOR_RESUME.json").write_text(
        json.dumps(
            {
                "status": "restored_for_optimizer_resume",
                "checksum_manifest_sha256": "a" * 64,
                "files": records,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    if corrupt:
        (actor / "model_world_size_2_rank_0.pt").write_bytes(b"corrupt")
    return actor


def test_retention_removes_verified_restored_shared_resume_copy(tmp_path: Path) -> None:
    shared = tmp_path / "shared"
    restored = _restored_shared_state(shared, 80)
    actor = _actor(shared)
    (shared / "checkpoint").rename(shared / "global_step_100")
    actor = shared / "global_step_100" / "actor"
    run_archive = tmp_path / "archive" / "run"
    run_manifest = tmp_path / "run_manifest.json"
    run_manifest.write_text('{"run_id": "test", "status": "running"}\n', encoding="utf-8")

    payload = relocate_raw_checkpoint(
        actor,
        run_archive / "global_step_100" / "actor",
        run_archive_root=run_archive,
        run_manifest=run_manifest,
        retention_report=tmp_path / "retention.md",
    )

    assert not list(restored.glob("*_world_size_*_rank_*.pt"))
    marker = json.loads(
        (restored / "RESTORED_RAW_STATE_RETENTION_EXPIRED.json").read_text(
            encoding="utf-8"
        )
    )
    assert marker["status"] == "restored_raw_state_deleted_after_verification"
    assert payload["retention_expired_states"][0]["retention_source"] == (
        "shared_restored_resume_copy"
    )
    event = json.loads(run_manifest.read_text(encoding="utf-8"))[
        "storage_retention_events"
    ][0]
    assert event["status"] == "deleted_after_verification"


def test_retention_refuses_corrupt_restored_shared_resume_copy(tmp_path: Path) -> None:
    shared = tmp_path / "shared"
    restored = _restored_shared_state(shared, 80, corrupt=True)
    actor = _actor(shared)
    (shared / "checkpoint").rename(shared / "global_step_100")
    actor = shared / "global_step_100" / "actor"
    run_archive = tmp_path / "archive" / "run"
    run_manifest = tmp_path / "run_manifest.json"
    run_manifest.write_text('{"run_id": "test", "status": "running"}\n', encoding="utf-8")

    with pytest.raises(RuntimeError, match="restored shared raw-state checksum mismatch"):
        relocate_raw_checkpoint(
            actor,
            run_archive / "global_step_100" / "actor",
            run_archive_root=run_archive,
            run_manifest=run_manifest,
            retention_report=tmp_path / "retention.md",
        )

    assert list(restored.glob("*_world_size_*_rank_*.pt"))
    assert list(actor.glob("*_world_size_*_rank_*.pt"))
