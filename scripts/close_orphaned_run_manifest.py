#!/usr/bin/env python3
"""Post-hoc closer for run manifests whose job died without a finalizer.

Jobs launched through ``scripts/run_manifest_job.py`` close their own manifest
on exit: the runner reads ``payload["command"]``, waits for it, and calls
``finalize_manifest``.  A launcher that execs the trainer directly leaves
nothing alive to stamp the manifest, so it reads ``"status": "running"`` and
``"end_time_utc": null`` forever -- this is exactly what happened to the M7
arms, whose launcher invoked ``verl.trainer.main`` directly until
``scripts/launch_m7_virl_arm.sh`` was routed through the runner.

This script closes such a manifest AFTER the fact.  It delegates the actual
stamping to the tested ``finalize_manifest`` in
``scripts/finalize_run_manifest.py`` -- the manifest is never hand-edited --
and then records honestly what could and could not be observed:

  * ``end_time_utc`` is the finalizer's wall clock AT CLOSE TIME, which for a
    post-hoc close is NOT the true completion time.  ``end_time_utc_source``
    says so in the manifest, and ``observed_completion_utc`` carries the true
    completion time derived from the mtime of the last artifacts the job wrote.
  * no wrapper ever captured the process exit status, so ``--exit-code`` is
    supplied by the operator and ``--exit-code-provenance`` records how it was
    arrived at.  A post-hoc exit code is an inference, and the manifest says so.

SAFETY.  The script refuses to touch a job that may still be in flight:

  * refuses unless the manifest is in ``"running"`` state (never re-closes);
  * reads the run's own ``pids/*.pid`` files and refuses if any recorded pid is
    still alive on the run's node, or if liveness cannot be determined at all.

Exit codes: 0 closed, 3 refused, 2 bad usage.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.finalize_run_manifest import finalize_manifest  # noqa: E402

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_REFUSE = 3

END_TIME_SOURCE = (
    "post-hoc finalizer wall clock at close time; NOT the true completion time. "
    "Use observed_completion_utc for any duration, rate or timing quantity."
)


def iso_utc(epoch: float) -> str:
    return dt.datetime.fromtimestamp(epoch, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def refuse(message: str) -> None:
    print(f"[close-orphaned-manifest] REFUSE: {message}", file=sys.stderr)
    raise SystemExit(EXIT_REFUSE)


def pid_liveness(run_dir: Path, node: str | None) -> list[tuple[int, str, str]]:
    """Return (pid, state, detail) for every pid recorded by the run.

    state is one of "alive", "dead", "unknown".  "unknown" is treated as alive
    by the caller: this fails closed.
    """
    pid_dir = run_dir / "pids"
    results: list[tuple[int, str, str]] = []
    if not pid_dir.is_dir():
        return results
    for pid_file in sorted(pid_dir.glob("*.pid")):
        raw = pid_file.read_text(encoding="utf-8").strip()
        if not raw.isdigit():
            results.append((-1, "unknown", f"{pid_file} holds {raw!r}, not a pid"))
            continue
        pid = int(raw)
        local = node is None or node == socket.gethostname()
        if local:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                results.append((pid, "dead", f"{pid_file.name}: no such process locally"))
            except PermissionError:
                results.append((pid, "alive", f"{pid_file.name}: exists (owned by another user)"))
            else:
                results.append((pid, "alive", f"{pid_file.name}: running locally"))
            continue
        proc = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=25", node, f"kill -0 {pid}"],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            results.append((pid, "alive", f"{pid_file.name}: running on {node}"))
        elif proc.returncode == 1:
            results.append((pid, "dead", f"{pid_file.name}: gone from {node}"))
        else:
            results.append(
                (pid, "unknown", f"{pid_file.name}: ssh {node} exited {proc.returncode}: "
                                 f"{proc.stderr.strip()[:200]}")
            )
    return results


def atomic_update(path: Path, payload: dict) -> None:
    """Same atomic idiom as finalize_run_manifest: .partial + os.replace."""
    temporary = path.with_name(f".{path.name}.close.{os.getpid()}.partial")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest")
    parser.add_argument("--exit-code", type=int, required=True)
    parser.add_argument(
        "--exit-code-provenance",
        required=True,
        help="how the exit code was arrived at; a post-hoc close never observes it directly",
    )
    parser.add_argument(
        "--completion-evidence",
        action="append",
        default=[],
        metavar="PATH",
        help="artifact whose mtime witnesses true completion; repeatable",
    )
    parser.add_argument(
        "--expected-artifact",
        action="append",
        default=[],
        metavar="PATH",
        help="declare expected_artifacts post-hoc when the manifest carries none, "
             "so finalize_manifest's artifacts_exist check is not vacuous; repeatable",
    )
    parser.add_argument("--reason", required=True, help="why this manifest needed a post-hoc close")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    path = Path(args.manifest)
    if not path.is_file():
        print(f"[close-orphaned-manifest] no such manifest: {path}", file=sys.stderr)
        return EXIT_USAGE
    payload = json.loads(path.read_text(encoding="utf-8"))

    status = payload.get("status")
    if status != "running":
        refuse(f"{path} is already closed (status={status!r}); refusing to re-close")

    run_dir = path.parent
    node = payload.get("node")
    liveness = pid_liveness(run_dir, node)
    for pid, state, detail in liveness:
        print(f"[close-orphaned-manifest] pid {pid}: {state} -- {detail}")
    blocking = [entry for entry in liveness if entry[1] != "dead"]
    if blocking:
        refuse(
            f"{path} still has non-dead pids {[(p, s) for p, s, _ in blocking]}; "
            "a job in flight is never closed"
        )
    if not liveness:
        print("[close-orphaned-manifest] no pid file recorded; nothing to check")

    evidence = []
    for item in args.completion_evidence:
        candidate = Path(item)
        if not candidate.exists():
            refuse(f"completion evidence {candidate} does not exist")
        evidence.append({"path": str(candidate), "mtime_utc": iso_utc(candidate.stat().st_mtime)})
    observed = max((e["mtime_utc"] for e in evidence), default=None)

    if args.dry_run:
        print(json.dumps(
            {
                "manifest": str(path),
                "would_set_exit_code": args.exit_code,
                "observed_completion_utc": observed,
                "completion_evidence": evidence,
                "expected_artifacts": args.expected_artifact,
            },
            indent=2,
        ))
        return EXIT_OK

    declared_post_hoc = False
    if args.expected_artifact and not payload.get("expected_artifacts"):
        payload["expected_artifacts"] = list(args.expected_artifact)
        payload["expected_artifacts_declared_post_hoc"] = True
        atomic_update(path, payload)
        declared_post_hoc = True

    finalize_manifest(path, args.exit_code)

    payload = json.loads(path.read_text(encoding="utf-8"))
    closed_at = payload.get("end_time_utc")
    payload["end_time_utc_source"] = END_TIME_SOURCE
    payload["exit_code_provenance"] = args.exit_code_provenance
    if observed is not None:
        payload["observed_completion_utc"] = observed
        payload["observed_completion_evidence"] = evidence
    deviations = payload.get("deviations")
    if not isinstance(deviations, list):
        deviations = []
    deviations.append(
        {
            "code": "post_hoc_manifest_close",
            "closed_at_utc": closed_at,
            "closed_by": "scripts/close_orphaned_run_manifest.py",
            "reason": args.reason,
            "observed_completion_utc": observed,
            "observed_completion_evidence": evidence,
            "exit_code": args.exit_code,
            "exit_code_provenance": args.exit_code_provenance,
            "expected_artifacts_declared_post_hoc": declared_post_hoc,
            "effect": (
                "end_time_utc is the close-time stamp, not the true completion time; "
                "the run's wall-clock duration must be computed from "
                "observed_completion_utc, never from end_time_utc."
            ),
        }
    )
    payload["deviations"] = deviations
    atomic_update(path, payload)

    print(
        f"[close-orphaned-manifest] {path}: status={payload.get('status')} "
        f"exit_code={payload.get('exit_code')} artifacts_exist={payload.get('artifacts_exist')} "
        f"end_time_utc={closed_at} observed_completion_utc={observed}"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
