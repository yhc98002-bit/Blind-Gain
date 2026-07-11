from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from scripts.pilot_storage_dry_cycle import run_cycle
from src.ops.storage_guard import GIB


def test_dry_cycle_sweeps_both_payload_types_and_reads_archive_back(tmp_path: Path) -> None:
    quota_root = tmp_path / "quota"
    shared_parent = quota_root / "project/checkpoints/pilot"
    shared = shared_parent / "cycle"
    archive_parent = tmp_path / "archive"
    archive = archive_parent / "cycle"
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    manifest = run_dir / "run_manifest.json"
    manifest.write_text('{"run_id": "test", "storage_retention_events": []}\n', encoding="utf-8")
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(
        json.dumps(
            {
                "status": "pass",
                "quota_root": str(quota_root),
                "measured_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "used_bytes": 1 * GIB,
            }
        ),
        encoding="utf-8",
    )

    payload = run_cycle(
        shared_checkpoint_root=shared,
        archive_root=archive,
        run_manifest=manifest,
        result_path=run_dir / "result.json",
        usage_snapshot=snapshot,
        quota_root=quota_root,
        guard_log=run_dir / "guard.jsonl",
        approved_shared_root=shared_parent,
        approved_archive_root=archive_parent,
    )

    assert payload["status"] == "pass"
    assert all(payload["checks"].values())
    assert not any((shared / "global_step_1/actor").glob("*_world_size_*_rank_*.pt"))
    assert not (shared / "global_step_1/actor/huggingface").exists()
    assert (archive / "global_step_1/actor/raw_training_state.source.sha256").is_file()
    assert (archive / "global_step_1/actor/huggingface/merged_checkpoint.source.sha256").is_file()


def test_dry_cycle_refuses_a_checkpoint_outside_the_approved_shared_root(tmp_path: Path) -> None:
    try:
        run_cycle(
            shared_checkpoint_root=tmp_path / "wrong/cycle",
            archive_root=tmp_path / "archive/cycle",
            run_manifest=tmp_path / "missing.json",
            result_path=tmp_path / "result.json",
            usage_snapshot=tmp_path / "snapshot.json",
            quota_root=tmp_path,
            guard_log=tmp_path / "guard.jsonl",
            approved_shared_root=tmp_path / "approved",
            approved_archive_root=tmp_path / "archive",
        )
    except ValueError as error:
        assert "shared checkpoint root" in str(error)
    else:
        raise AssertionError("cycle accepted a checkpoint path outside checkpoints/pilot")
