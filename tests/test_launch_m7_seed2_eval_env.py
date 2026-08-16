"""I10 adversarial fixture for the launch_m7_seed2_eval.sh caption-arm env bug.

On 2026-08-15 the a3_caption seed-2 held-out eval died with rc=127:

    scripts/launch_m7_seed2_eval.sh: line 64:
    VIRL_CAPTION_SHARDS=data/virl39k_caption_store_3b_main_v2.jsonl:
    No such file or directory

Root cause: the launcher passed the caption store via
``${caption_env:+VIRL_CAPTION_SHARDS="$caption_env"}`` inside a command's
assignment prefix.  Bash decides which leading words are assignments at parse
time, before parameter expansion, so the expanded ``VAR=value`` word is
treated as the COMMAND name; it contains a ``/`` and execs as a missing path.
The bug fires only when ``caption_env`` is non-empty, which is why the real,
gray and no-image arms launched fine on 2026-08-09/11 and the caption arm
never did.

The fixed launcher builds a guarded array and passes it through ``env``.

The old launcher fails ``test_launcher_no_longer_uses_prefix_expansion`` (the
broken pattern was present) and the behavioral pair below demonstrates the
failure mode itself, independent of the launcher file.
"""

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LAUNCHER = REPO / "scripts" / "launch_m7_seed2_eval.sh"


def _bash(snippet: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", "-c", snippet], capture_output=True, text=True, cwd=str(REPO)
    )


def test_old_prefix_expansion_runs_assignment_as_command():
    """The pre-fix pattern: expansion becomes the command word -> rc=127."""
    proc = _bash(
        'caption_env="data/x.jsonl"; '
        '${caption_env:+VIRL_CAPTION_SHARDS="$caption_env"} /bin/true'
    )
    assert proc.returncode == 127, (
        "expected the expanded assignment-prefix to be exec'd as a missing "
        f"command (rc=127), got rc={proc.returncode}: {proc.stderr!r}"
    )


def test_env_array_form_propagates_variable_when_set():
    """The fixed pattern: `env` + guarded array delivers the variable."""
    proc = _bash(
        'set -u; caption_env="data/x.jsonl"; caption_args=(); '
        '[[ -n "$caption_env" ]] && caption_args=("VIRL_CAPTION_SHARDS=$caption_env"); '
        'env ${caption_args[@]+"${caption_args[@]}"} '
        'sh -c \'test "${VIRL_CAPTION_SHARDS:-}" = data/x.jsonl\''
    )
    assert proc.returncode == 0, proc.stderr


def test_env_array_form_is_a_noop_when_unset():
    """Non-caption arms: empty array under set -u, variable absent, rc=0."""
    proc = _bash(
        'set -u; caption_env=""; caption_args=(); '
        '[[ -n "$caption_env" ]] && caption_args=("VIRL_CAPTION_SHARDS=$caption_env"); '
        'env ${caption_args[@]+"${caption_args[@]}"} '
        'sh -c \'test -z "${VIRL_CAPTION_SHARDS:-}"\''
    )
    assert proc.returncode == 0, proc.stderr


def test_launcher_no_longer_uses_prefix_expansion():
    """The live launcher carries the env form, not the parse-time trap."""
    text = LAUNCHER.read_text()
    assert '${caption_env:+VIRL_CAPTION_SHARDS=' not in text, (
        "launch_m7_seed2_eval.sh still passes the caption store via an "
        "expanded assignment prefix (the 2026-08-15 rc=127 bug)"
    )
    assert "caption_args" in text and "env VIRL_MANIFEST=" in text, (
        "launch_m7_seed2_eval.sh no longer uses the registered env-array form"
    )


def test_launcher_bash_syntax_ok():
    proc = subprocess.run(
        ["bash", "-n", str(LAUNCHER)], capture_output=True, text=True
    )
    assert proc.returncode == 0, proc.stderr
