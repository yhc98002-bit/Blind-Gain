from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.cleanup_pilot_reward_smoke_checkpoint import cleanup_checkpoint


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    run_id = "pilot_reward_smoke_an29_fixture"
    run_dir = tmp_path / "experiments" / "runs" / run_id
    run_dir.mkdir(parents=True)
    checkpoint = tmp_path / "checkpoints" / "smoke" / run_id / "global_step_5" / "actor"
    checkpoint.mkdir(parents=True)
    (checkpoint / "model.pt").write_bytes(b"model")
    (checkpoint / "optim.pt").write_bytes(b"optim")
    manifest_path = run_dir / "run_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "job_type": "l3_pilot_reward_plumbing_smoke",
                "status": "complete",
                "exit_code": 0,
                "checkpoint_path": str(checkpoint.parents[1]),
            }
        ),
        encoding="utf-8",
    )
    audit_path = tmp_path / "audit.json"
    audit_path.write_text(
        json.dumps(
            {
                "schema_version": "blind-gains.pilot-reward-smoke-audit.v5",
                "status": "pass",
                "run_manifest": str(manifest_path),
                "placement_audit": {"status": "pass", "checks": {"tp1": True}},
            }
        ),
        encoding="utf-8",
    )
    return run_dir, manifest_path, audit_path


def test_cleanup_lists_hashes_before_deleting_and_records_manifest(tmp_path: Path) -> None:
    run_dir, manifest_path, audit_path = _fixture(tmp_path)
    checksum = run_dir / "checkpoint.sha256"
    predelete = run_dir / "predelete.json"
    deletion = run_dir / "deletion.json"

    payload = cleanup_checkpoint(
        manifest_path,
        audit_path,
        checksum,
        predelete,
        deletion,
        root=tmp_path,
    )

    assert payload["status"] == "deleted"
    assert payload["classification"] == "retention-expired"
    assert payload["file_count"] == 2
    assert payload["size_bytes"] == 10
    assert not (tmp_path / "checkpoints" / "smoke" / run_dir.name).exists()
    assert hashlib.sha256(checksum.read_bytes()).hexdigest() == payload[
        "checksum_manifest_sha256"
    ]
    predelete_payload = json.loads(predelete.read_text(encoding="utf-8"))
    assert predelete_payload["status"] == "retention-expired-listed-before-deletion"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["storage_retention_events"][0]["status"] == "retention-expired-deleted"


def test_cleanup_rejects_shared_pilot_namespace_without_deleting(tmp_path: Path) -> None:
    run_dir, manifest_path, audit_path = _fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    protected = tmp_path / "checkpoints" / "pilot" / run_dir.name
    protected.mkdir(parents=True)
    (protected / "keep.bin").write_bytes(b"keep")
    manifest["checkpoint_path"] = str(protected)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="checkpoint_namespace_exact"):
        cleanup_checkpoint(
            manifest_path,
            audit_path,
            run_dir / "checkpoint.sha256",
            run_dir / "predelete.json",
            run_dir / "deletion.json",
            root=tmp_path,
        )

    assert (protected / "keep.bin").read_bytes() == b"keep"


def test_cleanup_rejects_failed_audit(tmp_path: Path) -> None:
    run_dir, manifest_path, audit_path = _fixture(tmp_path)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["status"] = "fail"
    audit_path.write_text(json.dumps(audit), encoding="utf-8")

    with pytest.raises(ValueError, match="audit_v5_pass"):
        cleanup_checkpoint(
            manifest_path,
            audit_path,
            run_dir / "checkpoint.sha256",
            run_dir / "predelete.json",
            run_dir / "deletion.json",
            root=tmp_path,
        )
