"""I10 fixture for the E3 STAGE-B merge-launcher arity defect (infra 1c).

The registered E3 runner calls the caption-store merge launcher with exactly
one shard (RUN_TAG RELEASE_MANIFEST SHARD — three arguments). The launcher's
original arity check was ``$# -lt 4``, so the registered single-shard call was
refused with rc=2 and E3 aborted at ``failed_stage: "caption_merge"``
(2026-08-11, provenance failed_20260811T155104Z). The check was corrected to
``$# -lt 3`` in commit da0751d — WITHOUT the adversarial fixture that I10
requires every fix to ship. This file is that fixture, added by the
2026-08-16 dispatch: under the pre-fix launcher the single-shard case below
is refused with the usage message and the test fails.

No test here mutates anything: the three-argument case uses a nonexistent
manifest, which the launcher refuses AFTER the arity gate but BEFORE creating
any run directory.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LAUNCHER = REPO / "scripts" / "launch_caption_store_merge.sh"
E3_RUNNER = REPO / "scripts" / "run_e3_caption_stress.sh"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(LAUNCHER), *args], capture_output=True, text=True, cwd=str(REPO)
    )


def test_single_shard_call_clears_the_arity_gate() -> None:
    """Three args (one shard) must pass arity and fail only on the missing
    input file — the pre-fix ``-lt 4`` check refuses this with the usage
    message before looking at any file."""
    proc = _run("fixture_tag", "does/not/exist.jsonl", "also/missing.jsonl")
    assert proc.returncode == 2
    assert "Missing caption merge input" in proc.stderr
    assert "Usage:" not in proc.stderr


def test_two_arguments_still_refused_as_usage_error() -> None:
    proc = _run("fixture_tag", "does/not/exist.jsonl")
    assert proc.returncode == 2
    assert "Usage:" in proc.stderr


def test_registered_e3_stage_b_call_matches_launcher_contract() -> None:
    """The runner's STAGE-B invocation passes RUN_TAG, RELEASE_MANIFEST, then
    exactly the single shard — the argument order the launcher declares."""
    text = E3_RUNNER.read_text(encoding="utf-8")
    assert (
        'bash scripts/launch_caption_store_merge.sh "$MERGE_RUN_TAG" '
        '"$COVERAGE_MANIFEST" "$CAP_SHARD"' in text
    )
    launcher_text = LAUNCHER.read_text(encoding="utf-8")
    assert "$# -lt 3" in launcher_text
    assert "$# -lt 4" not in launcher_text
