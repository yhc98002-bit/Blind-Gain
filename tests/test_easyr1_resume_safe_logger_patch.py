from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EASYR1 = ROOT / "artifacts" / "repos" / "EasyR1"
PATCH = ROOT / "docs" / "easyr1_resume_safe_logger_patch.diff"
LOGGER = EASYR1 / "verl" / "utils" / "logger" / "logger.py"
MARKER = "Preserving existing EasyR1 file logger artifact during resume"


def test_resume_safe_logger_patch_is_applied_or_cleanly_applicable() -> None:
    source = LOGGER.read_text(encoding="utf-8")
    if MARKER not in source:
        subprocess.run(
            ["git", "-C", str(EASYR1), "apply", "--check", str(PATCH)],
            check=True,
        )
    patch = PATCH.read_text(encoding="utf-8")
    assert 'resume_requested = bool(config["trainer"].get("load_checkpoint_path"))' in patch
    assert "existing and not resume_requested" in patch
    assert "raise FileExistsError" in patch
    assert 'open(config_path, "x")' in patch
    assert 'open(path, "x")' in patch


def test_old_unconditional_truncation_lines_are_removed_by_patch() -> None:
    patch = PATCH.read_text(encoding="utf-8")

    assert '-        with open(os.path.join(config["trainer"]["save_checkpoint_path"], "experiment_log.jsonl"), "w") as f:' in patch
    assert '-        with open(os.path.join(config["trainer"]["save_checkpoint_path"], "generations.log"), "w") as f:' in patch
    assert "+        if resume_requested:" in patch
