"""Contract fixtures for scripts/track4_premise_v2_gates.sh.

The runner previously fail-stopped the whole chain on a blocked E3, which
silently skipped E4 even though the two gates are independent in the
registration and E4's inputs were fine.  These fixtures lock the properties
that fix depends on.  They are static/text checks: the runner claims a GPU and
dispatches multi-hour jobs, so it is never executed here.

The GATES_ONLY fixtures below are the exception: the gate-selection block and
the gate_block guard are pure bookkeeping over shell variables, so they are
extracted between their markers and EXECUTED VERBATIM in a stub harness.  That
is the only way to show the selector picks the gates it claims to pick rather
than merely mentioning them in a string.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "track4_premise_v2_gates.sh"
GATES = ("E1", "E2", "E3", "E4")


@pytest.fixture(scope="module")
def source() -> str:
    return RUNNER.read_text(encoding="utf-8")


def _function_body(text: str, name: str) -> str:
    start = text.index(f"{name}() {{")
    end = text.index("\n}\n", start)
    return text[start:end]


def _function_source(text: str, name: str) -> str:
    """Like _function_body but keeps the closing brace, so it is runnable."""
    start = text.index(f"{name}() {{")
    end = text.index("\n}\n", start)
    return text[start : end + 3]


def _gate_selection_block(text: str) -> str:
    start = text.index("# BEGIN_GATE_SELECTION")
    start = text.index("\n", start) + 1
    end = text.index("# END_GATE_SELECTION")
    block = text[start:end]
    assert "GATES_ONLY" in block, "gate-selection block must be the GATES_ONLY parser"
    return block


_SELECTION_HARNESS = """
set -uo pipefail
GATES=(E1 E2 E3 E4)
declare -A GATE_STATUS=([E1]=pending [E2]=pending [E3]=pending [E4]=pending)
declare -A GATE_REASON=([E1]="" [E2]="" [E3]="" [E4]="")
log() { printf 'LOG %s\\n' "$*" >&2; }
cleanup_lock() { printf 'CLEANUP\\n' >&2; }
GATES_ONLY="${GATES_ONLY:-}"
@@BLOCK@@
printf 'SELECTED=%s\\n' "$GATES_SELECTED"
for g in "${GATES[@]}"; do printf 'STATUS %s=%s\\n' "$g" "${GATE_STATUS[$g]}"; done
"""


def _run_selection(tmp_path: Path, block: str, gates_only: str | None):
    script = tmp_path / "sel.sh"
    script.write_text(_SELECTION_HARNESS.replace("@@BLOCK@@", block), encoding="utf-8")
    env = {"PATH": "/usr/bin:/bin"}
    if gates_only is not None:
        env["GATES_ONLY"] = gates_only
    return subprocess.run(
        ["bash", str(script)], capture_output=True, text=True, env=env
    )


def _parse_selection(proc) -> tuple[str, dict[str, str]]:
    selected = ""
    status: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if line.startswith("SELECTED="):
            selected = line[len("SELECTED=") :]
        elif line.startswith("STATUS "):
            gate, _, value = line[len("STATUS ") :].partition("=")
            status[gate] = value
    return selected, status


def test_runner_parses(source: str) -> None:
    assert subprocess.run(["bash", "-n", str(RUNNER)], capture_output=True).returncode == 0


def test_every_gate_has_its_own_runner_function_and_is_dispatched(source: str) -> None:
    for gate in GATES:
        assert f"gate_{gate.lower()}() {{" in source
        assert re.search(rf"^\s+{gate}\) gate_{gate.lower()} ;;", source, re.MULTILINE)
    # the dispatch loop walks every gate rather than falling through in order
    assert 'for gate in "${GATES[@]}"; do' in source
    assert 'GATES=(E1 E2 E3 E4)' in source


def test_a_blocked_or_failed_gate_does_not_stop_the_run(source: str) -> None:
    # the whole-chain abort used by the old runner is gone
    assert "fail_stop" not in source
    for helper in ("gate_block", "gate_fail"):
        body = _function_body(source, helper)
        assert "exit" not in body, f"{helper} must not exit the run"
        assert "abort_run" not in body, f"{helper} must not abort the run"
    # the dispatch loop skips an already-blocked gate but keeps iterating
    assert "continue" in source
    assert "independent gates still run" in source


def test_step_drivers_return_rc_instead_of_killing_the_run(source: str) -> None:
    for driver in ("run_gpu_step", "run_login_step"):
        body = _function_body(source, driver)
        assert "abort_run" not in body, f"{driver} must not abort the whole run"
        assert re.search(r"^\s+return ", body, re.MULTILINE), f"{driver} must return an rc"


def test_only_infrastructure_failures_abort_the_whole_run(source: str) -> None:
    aborting = re.findall(r'abort_run "([a-z0-9_]+)"', source)
    assert set(aborting) == {"gpu_guard_precheck", "gpu_claim_write", "gpu_guard_recheck"}


def test_guard_claim_recheck_discipline_is_preserved(source: str) -> None:
    # order matters in the executable body only; the header comment describes it too
    code = source[source.index("set -uo pipefail") :]
    guard = code.index("m7_gpu_occupancy_guard.py --node")
    claim = code.index("write_claim null")
    recheck = code.index("--ignore-claim-run-id")
    assert guard < claim < recheck, "guard -> claim -> re-check order must hold"
    assert "CLAIM_HELD=1" in source
    assert source.count("release_claim") >= 3


def test_steps_jsonl_record_format_is_unchanged(source: str) -> None:
    body = _function_body(source, "record_step")
    for field in (
        "step:$step",
        "gate:$gate",
        "registered_ref:$ref",
        "node:$node",
        "gpu:$gpu",
        "command:$command",
        "start_utc:$start",
        "end_utc:$end",
        "rc:$rc",
        "status:$status",
        "log:$steplog",
        "artifacts:$artifacts",
    ):
        assert field in body


def test_e3_preflight_checks_e3_inputs_not_the_attacker_files(source: str) -> None:
    block = source[source.index("# --- E3:") : source.index("# --- E4:")]
    assert "$E3_RELEASE_MANIFEST" in block and "$E3_KEY_FILE" in block
    assert "attacker_release" not in block and "attacker_key" not in block
    # E3's own consumer contract
    for field in ("question", "image_sha256", "source_pair_id", "answer", "source_side"):
        assert field in block
    assert 'E3_RELEASE_MANIFEST="$DATA/caption_qa_inputs/manifest.jsonl"' in source
    assert 'E3_KEY_FILE="$DATA/caption_qa_inputs/key.jsonl"' in source


def test_e4_preflight_checks_only_the_fields_its_reader_consumes(source: str) -> None:
    block = source[source.index("# --- E4:") : source.index("# --- do any gates remain?")]
    assert "$E4_RELEASE_DIR/manifest.jsonl" in block and "$E4_KEY_FILE" in block
    # the reader is quoted in the comment so the contract is auditable in place
    assert "build_packaged_member_table" in block
    assert 'labels.append(0 if private["source_side"] == "a" else 1)' in block
    # exactly the four consumed fields, and none of E3's
    for consumed in ("pair_id", "member_id", "image_path", "template_id", "source_side"):
        assert consumed in block
    predicate = block[block.index("jq -s -e") :]
    for not_consumed in ("question", "image_sha256", "source_pair_id", '"answer"'):
        assert not_consumed not in predicate, f"E4 must not require {not_consumed}"


def test_attacker_files_are_never_written_by_this_runner(source: str) -> None:
    for line in source.splitlines():
        if "attacker_release" in line or "attacker_key" in line:
            assert not re.search(r">\s*\"?\$?(DATA|E4)", line), line


def test_terminal_status_reflects_gates_attempted_and_never_overclaims(source: str) -> None:
    assert "CHAIN_STATUS=complete" in source
    assert "CHAIN_STATUS=incomplete" in source
    assert "CHAIN_STATUS=selected_complete" in source
    assert 'exit "$EXIT_CODE"' in source
    tail = source[source.index("# Terminal status") :]
    # the denominator is what this run attempted, not the whole registry ...
    assert "N_OK -ne $N_SELECTED" in tail
    # ... but only a run that attempted every registered gate may say "complete"
    complete_at = tail.index("CHAIN_STATUS=complete\n")
    guard = tail.rindex('N_SELECTED -eq ${#GATES[@]}', 0, complete_at)
    assert guard > tail.index("N_OK -ne $N_SELECTED")
    # provenance carries the per-gate breakdown
    for field in (
        "gates:",
        "gates_complete:",
        "gates_failed:",
        "gates_blocked:",
        "gates_not_attempted:",
        "gates_not_selected:",
    ):
        assert field in source


def test_runner_still_records_only_and_judges_nothing(source: str) -> None:
    assert "computed_here: false" in source
    assert "0.133" not in source and "0.105" not in source and "0.286" not in source
    assert "member_accuracy" not in source


# --- GATES_ONLY: per-run gate selection --------------------------------------


def test_gates_only_default_unset_runs_all_four(tmp_path: Path, source: str) -> None:
    block = _gate_selection_block(source)
    proc = _run_selection(tmp_path, block, None)
    assert proc.returncode == 0, proc.stderr
    selected, status = _parse_selection(proc)
    assert selected == "E1 E2 E3 E4"
    assert status == {g: "pending" for g in GATES}


def test_gates_only_empty_string_runs_all_four(tmp_path: Path, source: str) -> None:
    proc = _run_selection(tmp_path, _gate_selection_block(source), "")
    assert proc.returncode == 0, proc.stderr
    selected, status = _parse_selection(proc)
    assert selected == "E1 E2 E3 E4"
    assert status == {g: "pending" for g in GATES}


@pytest.mark.parametrize(
    "value,want",
    [
        ("E3 E4", ["E3", "E4"]),
        ("E3,E4", ["E3", "E4"]),
        ("E4 E3", ["E3", "E4"]),  # registered order, not operator order
        ("E4", ["E4"]),
        ("E1 E2 E3 E4", ["E1", "E2", "E3", "E4"]),
        ("E3 E3", ["E3"]),  # duplicates collapse
        ("  E3   E4  ", ["E3", "E4"]),
    ],
)
def test_gates_only_selects_exactly_those_gates_and_no_others(
    tmp_path: Path, source: str, value: str, want: list[str]
) -> None:
    proc = _run_selection(tmp_path, _gate_selection_block(source), value)
    assert proc.returncode == 0, proc.stderr
    selected, status = _parse_selection(proc)
    assert selected.split() == want
    for gate in GATES:
        expected = "pending" if gate in want else "not_selected"
        assert status[gate] == expected, f"{gate}: {status[gate]} != {expected}"


@pytest.mark.parametrize(
    "value",
    [
        "E5",
        "E3 E5",  # fail closed even though one name is valid
        "e3",  # case must match the registered names
        "*",  # must not glob-expand against the repo
        "E3*",
        " ",  # names nothing
        ",",
        "E1,,E9",
    ],
)
def test_gates_only_refuses_an_unknown_or_empty_selection(
    tmp_path: Path, source: str, value: str
) -> None:
    proc = _run_selection(tmp_path, _gate_selection_block(source), value)
    assert proc.returncode == 2, f"expected refusal for {value!r}, got {proc.returncode}"
    assert "SELECTED=" not in proc.stdout, "a refused run must select nothing"
    assert "PREFLIGHT REFUSE" in proc.stderr
    assert "CLEANUP" in proc.stderr, "a refusal must still drop the lock"


def test_gates_only_refusal_happens_before_any_gpu_is_touched(source: str) -> None:
    code = source[source.index("set -uo pipefail") :]
    end_of_selection = code.index("# END_GATE_SELECTION")
    guard = code.index("m7_gpu_occupancy_guard.py --node")
    assert end_of_selection < guard, "GATES_ONLY must be validated before the GPU guard"


def test_a_not_selected_gate_is_never_dispatched(source: str) -> None:
    # the dispatch loop runs a gate only while it is still pending, and the
    # selector is the only thing that writes not_selected
    loop = source[source.index("# Gate sequence") :]
    assert '[[ "${GATE_STATUS[$gate]}" != "pending" ]]' in loop
    assert "continue" in loop
    assert source.count("GATE_STATUS[$gate]=not_selected") == 1


def test_gate_block_never_overwrites_a_not_selected_gate(tmp_path: Path, source: str) -> None:
    """A skipped gate must not be reported as blocked: this run did not test it."""
    harness = tmp_path / "gb.sh"
    harness.write_text(
        "set -uo pipefail\n"
        'declare -A GATE_STATUS=([E1]=not_selected [E2]=pending)\n'
        'declare -A GATE_REASON=([E1]="" [E2]="")\n'
        "log() { :; }\n"
        + _function_source(source, "gate_block")
        + '\ngate_block E1 "some preflight reason"\n'
        'gate_block E2 "some preflight reason"\n'
        "printf 'E1=%s\\n' \"${GATE_STATUS[E1]}\"\n"
        "printf 'E2=%s\\n' \"${GATE_STATUS[E2]}\"\n"
        "printf 'E1R=%s\\n' \"${GATE_REASON[E1]}\"\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        ["bash", str(harness)], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"}
    )
    assert proc.returncode == 0, proc.stderr
    out = dict(line.split("=", 1) for line in proc.stdout.splitlines())
    assert out["E1"] == "not_selected", "a not-selected gate must keep its status"
    assert out["E1R"] == "", "a not-selected gate must not carry a blocked reason"
    assert out["E2"] == "blocked", "a selected gate must still block normally"


def test_preflights_still_run_and_record_every_gate_separately(source: str) -> None:
    """Selection must narrow what RUNS, not what is diagnosed and recorded."""
    preflights = source[
        source.index("# END_GATE_SELECTION") : source.index("# --- do any gates remain?")
    ]
    assert "not_selected" not in preflights, (
        "preflights must be unconditional; the gate_block guard, not a skip, "
        "keeps a not-selected gate from being mislabelled"
    )
    # each gate still gets its own recorded preflight step
    assert 'record_step "preflight_${gate,,}_eval_inputs" "$gate"' in preflights
    for gate in ("E3", "E4"):
        assert re.search(rf'record_step "preflight_{gate.lower()}[a-z0-9_]*" "{gate}"', preflights)


def test_provenance_reports_selection_without_judging_skipped_gates(source: str) -> None:
    assert 'gates_with_status not_selected' in source
    assert "gates_only:" in source
    assert "gates_attempted_this_run:" in source
    # the runner must say plainly that it makes no claim about a skipped gate
    note = source[source.index("gate_selection: {") : source.index("gate_independence:")]
    assert "makes no claim" in note
