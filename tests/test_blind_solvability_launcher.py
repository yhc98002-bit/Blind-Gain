from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_generic_launcher_rejects_caption_condition_without_store(tmp_path: Path) -> None:
    manifest = tmp_path / "sample.jsonl"
    manifest.write_text('{"split":"audit"}\n', encoding="utf-8")
    result = subprocess.run(
        [
            "bash",
            "scripts/launch_manifest_blind_solvability.sh",
            "node-not-contacted",
            "0",
            "caption",
            "model",
            str(manifest),
            "audit",
            "test",
            "-",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert "requires a completed caption run" in result.stderr
    assert "Could not resolve hostname" not in result.stderr


def test_generic_launcher_rejects_mismatched_resume_contract_before_ssh(tmp_path: Path) -> None:
    manifest = tmp_path / "sample.jsonl"
    manifest.write_text('{"split":"audit"}\n', encoding="utf-8")
    run_dir = tmp_path / "failed_run"
    run_dir.mkdir()
    resume = run_dir / "per_item.jsonl"
    resume.write_text('{"partial":true}\n', encoding="utf-8")
    (run_dir / "run_manifest.json").write_text(
        '{"condition":"gray","model_revision":"model","data_manifest":"wrong",'
        '"split":"audit","batch_size":2,"max_model_len":8192,"group_size":5,'
        '"sample_count":16,"sample_temperature":1}\n',
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            "bash",
            "scripts/launch_manifest_blind_solvability.sh",
            "node-not-contacted",
            "0",
            "noise",
            "model",
            str(manifest),
            "audit",
            "test",
            "-",
            "2",
            "8192",
            str(resume),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert "contract does not match" in result.stderr
    assert "Could not resolve hostname" not in result.stderr


def test_generic_launcher_records_manifest_split_and_multi_image_context() -> None:
    source = (ROOT / "scripts/launch_manifest_blind_solvability.sh").read_text(encoding="utf-8")
    assert "--manifest ${MANIFEST}" in source
    assert "--splits ${SPLIT}" in source
    assert "--max-model-len ${MAX_MODEL_LEN}" in source
    assert "--resume-from %q" in source
    assert "BLIND_GAINS_CACHE_ROOT:-/dev/shm/blind-gains" in source
    assert 'data_manifest: $manifest' in source
    assert 'resume_from: (if $resume_from == "-" then null else $resume_from end)' in source


def test_geometry_launcher_uses_memory_backed_condition_cache() -> None:
    source = (ROOT / "scripts/launch_blind_solvability_condition.sh").read_text(encoding="utf-8")
    assert "BLIND_GAINS_CACHE_ROOT:-/dev/shm/blind-gains" in source
