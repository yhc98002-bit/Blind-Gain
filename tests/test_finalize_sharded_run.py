from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from scripts.finalize_sharded_run import finalize_if_complete


def _write_manifest(path: Path, job_type: str) -> None:
    path.write_text(
        json.dumps(
            {
                "job_type": job_type,
                "expected_shards": 2,
                "status": "running",
                "end_time_utc": None,
            }
        ),
        encoding="utf-8",
    )


def test_caption_run_finalizes_only_after_all_valid_shards_exist(tmp_path: Path) -> None:
    manifest = tmp_path / "run_manifest.json"
    _write_manifest(manifest, "fliptrack_question_blind_caption_generation")
    shards = tmp_path / "shards"
    shards.mkdir()
    (shards / "captions_shard_0.jsonl").write_text('{"pair_id":"p0"}\n', encoding="utf-8")
    assert not finalize_if_complete(manifest)

    (shards / "captions_shard_1.jsonl").write_text('{"pair_id":"p1"}\n', encoding="utf-8")
    finished = dt.datetime(2026, 7, 10, 1, 2, 3, tzinfo=dt.timezone.utc)
    assert finalize_if_complete(manifest, now=finished)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["status"] == "complete"
    assert payload["end_time_utc"] == "2026-07-10T01:02:03Z"
    assert payload["artifact_count"] == 2
    assert len(payload["artifact_sha256"]) == 64


def test_eval_run_rejects_invalid_or_missing_metrics(tmp_path: Path) -> None:
    manifest = tmp_path / "run_manifest.json"
    _write_manifest(manifest, "fliptrack_v02_image_evaluation")
    (tmp_path / "shards").mkdir()
    (tmp_path / "metrics").mkdir()
    for index in range(2):
        (tmp_path / "shards" / f"shard_{index}.jsonl").write_text('{"pair_id":"p"}\n', encoding="utf-8")
    (tmp_path / "metrics" / "shard_0.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "metrics" / "shard_1.json").write_text("not-json\n", encoding="utf-8")
    assert not finalize_if_complete(manifest)

    (tmp_path / "metrics" / "shard_1.json").write_text("{}\n", encoding="utf-8")
    assert finalize_if_complete(manifest)
