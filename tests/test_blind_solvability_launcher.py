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


def test_generic_launcher_records_manifest_split_and_multi_image_context() -> None:
    source = (ROOT / "scripts/launch_manifest_blind_solvability.sh").read_text(encoding="utf-8")
    assert "--manifest ${MANIFEST}" in source
    assert "--splits ${SPLIT}" in source
    assert "--max-model-len ${MAX_MODEL_LEN}" in source
    assert 'data_manifest: $manifest' in source
