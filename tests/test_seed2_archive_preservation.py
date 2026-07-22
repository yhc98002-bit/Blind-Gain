from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_seed2_preservation_launcher_parses_and_is_fail_closed() -> None:
    launcher = ROOT / "scripts/launch_seed2_archive_preservation.sh"
    subprocess.run(["bash", "-n", str(launcher)], check=True)
    source = launcher.read_text(encoding="utf-8")
    assert "git diff --quiet HEAD" in source
    assert "another seed-2 preservation operation is active" in source
    assert "deletion_authorized==false" in source
    assert source.index("completed plan artifacts are absent") < source.index(
        'mkdir -p "${RUN_DIR}/logs"'
    )


def test_seed2_preservation_prevalidates_every_source_before_first_move() -> None:
    source = (ROOT / "scripts/run_seed2_archive_preservation.py").read_text(
        encoding="utf-8"
    )
    prevalidate = source.index(
        "entries = _prevalidate_all(validate_registered_sources(), plan_run_dir)"
    )
    first_move = source.index("relocated = relocate_tree(")
    assert prevalidate < first_move
    assert 'artifact_class="persistent_training_state"' in source
    assert "all_sources_are_verified_symlinks" in source
