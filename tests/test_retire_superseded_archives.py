from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.retire_superseded_archives import retire_archives


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    archive_root = tmp_path / "shared"
    symlink_root = tmp_path / "scratch"
    archive = archive_root / "failed-run"
    archive.mkdir(parents=True)
    payload = archive / "payload.bin"
    payload.write_bytes(b"verified payload")
    symlink_root.mkdir()
    source = symlink_root / "failed-run"
    source.symlink_to(archive, target_is_directory=True)
    checksums = tmp_path / "checksums.sha256"
    checksums.write_text(
        f"{hashlib.sha256(payload.read_bytes()).hexdigest()}  ./payload.bin\n",
        encoding="utf-8",
    )
    failed = tmp_path / "failed.json"
    replacement = tmp_path / "replacement.json"
    _write_json(
        failed,
        {"run_id": "failed", "status": "fail", "exit_code": 1, "seed": 1, "arm": "a1_real"},
    )
    _write_json(
        replacement,
        {"run_id": "replacement", "status": "complete", "exit_code": 0, "seed": 1, "arm": "a1_real"},
    )
    plan = tmp_path / "plan.json"
    _write_json(
        plan,
        {
            "status": "approved_for_exact_retirement",
            "entries": [
                {
                    "destination": str(archive),
                    "source_symlink": str(source),
                    "checksum_manifest": str(checksums),
                    "failed_run_manifest": str(failed),
                    "replacement_run_manifest": str(replacement),
                    "expected_files": 1,
                    "expected_bytes": len(b"verified payload"),
                }
            ],
        },
    )
    return plan, archive_root, symlink_root, archive


def test_dry_run_hash_verifies_without_deletion(tmp_path: Path) -> None:
    plan, archive_root, symlink_root, archive = _fixture(tmp_path)

    result = retire_archives(
        plan,
        tmp_path / "dry.json",
        execute=False,
        archive_root=archive_root,
        symlink_root=symlink_root,
    )

    assert result["status"] == "validated_not_executed"
    assert archive.is_dir()
    assert (symlink_root / "failed-run").is_symlink()


def test_execute_removes_only_validated_archive_and_link(tmp_path: Path) -> None:
    plan, archive_root, symlink_root, archive = _fixture(tmp_path)
    neighbor = archive_root / "untouched"
    neighbor.mkdir()
    (neighbor / "keep").write_text("keep", encoding="utf-8")

    result = retire_archives(
        plan,
        tmp_path / "execute.json",
        execute=True,
        archive_root=archive_root,
        symlink_root=symlink_root,
    )

    assert result["status"] == "complete"
    assert not archive.exists()
    assert not (symlink_root / "failed-run").exists()
    assert (neighbor / "keep").read_text(encoding="utf-8") == "keep"


def test_adversarial_extra_file_blocks_retirement(tmp_path: Path) -> None:
    plan, archive_root, symlink_root, archive = _fixture(tmp_path)
    (archive / "unregistered.bin").write_bytes(b"do not delete")

    with pytest.raises(ValueError, match="file set differs"):
        retire_archives(
            plan,
            tmp_path / "blocked.json",
            execute=True,
            archive_root=archive_root,
            symlink_root=symlink_root,
        )

    assert archive.is_dir()
    assert (symlink_root / "failed-run").is_symlink()


def test_adversarial_incomplete_replacement_blocks_retirement(tmp_path: Path) -> None:
    plan, archive_root, symlink_root, archive = _fixture(tmp_path)
    plan_payload = json.loads(plan.read_text(encoding="utf-8"))
    replacement = Path(plan_payload["entries"][0]["replacement_run_manifest"])
    replacement_payload = json.loads(replacement.read_text(encoding="utf-8"))
    replacement_payload["status"] = "running"
    _write_json(replacement, replacement_payload)

    with pytest.raises(ValueError, match="replacement run is not complete"):
        retire_archives(
            plan,
            tmp_path / "blocked.json",
            execute=True,
            archive_root=archive_root,
            symlink_root=symlink_root,
        )

    assert archive.is_dir()


def test_adversarial_nested_archive_path_blocks_retirement(tmp_path: Path) -> None:
    plan, archive_root, symlink_root, archive = _fixture(tmp_path)
    nested = archive / "nested"
    nested.mkdir()
    plan_payload = json.loads(plan.read_text(encoding="utf-8"))
    plan_payload["entries"][0]["destination"] = str(nested)
    _write_json(plan, plan_payload)

    with pytest.raises(ValueError, match="outside the allowlisted root"):
        retire_archives(
            plan,
            tmp_path / "blocked.json",
            execute=True,
            archive_root=archive_root,
            symlink_root=symlink_root,
        )

    assert archive.is_dir()
