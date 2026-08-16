#!/usr/bin/env python3
"""Mechanical checkpoint retention per the PI storage rule (dispatch 2026-08-16 item 2).

RULE (verbatim intent): delete non-terminal checkpoint steps NOT referenced in
the RESULTS.md §21 evidence ledger; keep terminal, best, and every
§21-referenced step. Applied after the mini-A5 ranking-cell reference check
(2026-08-16: every mini_a5 ranking/endpoint/catch report references
global_step_120 only).

SCOPE (rule replaces the 08-14 open menu): the run families below. NOT in
scope, never touched: checkpoints/m7/** (feeds the pending two-seed R3
readout; "Mini-A5/M7/LH2 artifacts untouched" governs their runs),
checkpoints/lh2_anchor_seed2_3b_geo3k/** (live stage).

§21 RESOLUTION RECORD (three tiers, resolved 2026-08-16 against
/media/sf_VM-Transfer/BlindGain_RESULTS.md sha-identical mirror
reports/RESULTS.md, §21 = L2255-2417):
  - tier 1, step-encoded eval-cell names: mini_a5 std/necessity/member(std
    family run mini_a5_same_data_seed1 is unreferenced)/cp cells all carry
    "_step120_" (L2319-2322, L2331, L2334) -> step 120 for every mini_a5 run.
  - tier 2, pointer files logs/c5_endgame_state/cell_* (L2297-2300) and
    logs/c6_cells/<label> (L2345-2346): resolve to the two C5 7B arms'
    global_step_100 (step recorded at L1947-1948).
  - tier 3, report-internal blocks: reports/m7_r3_readout_v1.json .runs ->
    m7 seed-1 cells (out of scope here); M5 trajectory: §21 L2269 "step 400"
    prose + integrity note L1487-1496 "Steps 150 and 400 match their eval
    runs" -> step 150 (m5_anchor_longhorizon_400) and step 400 (resume150).
  - §21 carries ZERO references to pilot/, smoke/, stage0_repro,
    anchor_a0_recipe_3b_geo3k (grep verified) -> keep terminal+best only.
  - mini_a5 acceptance audits list steps 20..120 as save-ladder PROVENANCE
    (hashes recorded in the audit artifacts); they are audit records, not
    §21 step references, and do not extend the keep-list.

Fail-closed: a run whose checkpoint_tracker.json is missing or unparseable is
SKIPPED (nothing deleted) and reported. A run whose keep-steps are not all on
disk is SKIPPED. Any scope path resolving into m7/ or lh2 aborts the program.

Usage:
    apply_storage_retention_rule_20260816.py --dry-run
    apply_storage_retention_rule_20260816.py --apply --record reports/storage_cleanup_20260814.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CHECKPOINTS = REPO / "checkpoints"

# Families whose children are run dirs, and directly-named run dirs.
FAMILY_DIRS = ["mini_a5", "c5", "pilot", "smoke"]
DIRECT_RUN_DIRS = [
    "m5_anchor_longhorizon_400",
    "m5_anchor_longhorizon_400_resume150",
    "stage0_repro",
    "anchor_a0_recipe_3b_geo3k",
]
FORBIDDEN_MARKERS = ("/m7/", "lh2")

# §21-referenced steps per run (see the resolution record in the docstring).
SECTION21_STEPS: dict[str, set[int]] = {
    "mini_a5_std_seed1": {120},
    "mini_a5_necessity_seed1": {120},
    "mini_a5_same_data_seed1": {120},
    "mini_a5_cp_seed1": {120},
    "c5_a1_real_seed1_7b": {100},
    "c5_a2_gray_seed1_7b": {100},
    "m5_anchor_longhorizon_400": {150},
    "m5_anchor_longhorizon_400_resume150": {400},
}

STEP_RE = re.compile(r"^global_step_(\d+)$")


def discover_run_dirs() -> list[Path]:
    runs: list[Path] = []
    for family in FAMILY_DIRS:
        family_dir = CHECKPOINTS / family
        if family_dir.is_dir():
            runs.extend(sorted(p for p in family_dir.iterdir() if p.is_dir()))
    for name in DIRECT_RUN_DIRS:
        run_dir = CHECKPOINTS / name
        if run_dir.is_dir():
            runs.append(run_dir)
    for run in runs:
        text = str(run)
        if any(marker in text for marker in FORBIDDEN_MARKERS):
            sys.exit(f"ABORT: forbidden path in scope: {run}")
    return runs


def tracker_steps(run_dir: Path) -> tuple[int | None, int | None] | None:
    tracker = run_dir / "checkpoint_tracker.json"
    try:
        payload = json.loads(tracker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    best = payload.get("best_global_step")
    last = payload.get("last_global_step")
    best = best if isinstance(best, int) else None
    last = last if isinstance(last, int) else None
    return best, last


def du_bytes(path: Path) -> int:
    completed = subprocess.run(
        ["du", "-sb", str(path)], check=True, capture_output=True, text=True
    )
    return int(completed.stdout.split(maxsplit=1)[0])


def plan(runs: list[Path]) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    skipped: list[str] = []
    for run_dir in runs:
        step_dirs = {
            int(match.group(1)): child
            for child in run_dir.iterdir()
            if child.is_dir() and (match := STEP_RE.match(child.name))
        }
        if not step_dirs:
            continue
        steps = tracker_steps(run_dir)
        if steps is None:
            skipped.append(f"{run_dir}: no parseable checkpoint_tracker.json — SKIPPED (fail-closed)")
            continue
        best, last = steps
        keep: set[int] = set()
        reasons: dict[int, list[str]] = {}
        for step, why in ((best, "best"), (last, "terminal")):
            if step is not None:
                keep.add(step)
                reasons.setdefault(step, []).append(why)
        for step in SECTION21_STEPS.get(run_dir.name, set()):
            keep.add(step)
            reasons.setdefault(step, []).append("§21")
        missing_keeps = [step for step in keep if step in reasons and step not in step_dirs]
        if missing_keeps:
            skipped.append(
                f"{run_dir}: keep-step dirs missing on disk {sorted(missing_keeps)} — SKIPPED"
            )
            continue
        for step in sorted(step_dirs):
            action = "keep" if step in keep else "delete"
            rows.append(
                {
                    "run": str(run_dir.relative_to(REPO)),
                    "step": step,
                    "path": str(step_dirs[step].relative_to(REPO)),
                    "action": action,
                    "reason": "+".join(reasons.get(step, [])) if action == "keep" else "non-terminal, not best, not §21-referenced",
                }
            )
    return rows, skipped


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--record", type=Path, default=REPO / "reports" / "storage_cleanup_20260814.md")
    args = parser.parse_args()

    rows, skipped = plan(discover_run_dirs())
    deletions = [row for row in rows if row["action"] == "delete"]

    for row in rows:
        print(f"{row['action']:6} {row['path']}  ({row['reason']})")
    for line in skipped:
        print(f"skip   {line}")
    print(f"planned deletions: {len(deletions)} step dirs across "
          f"{len({row['run'] for row in deletions})} runs")

    if args.dry_run:
        return 0

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "",
        f"## Retention-rule application {stamp} (dispatch 2026-08-16 item 2)",
        "",
        "Rule: delete non-terminal checkpoint steps not referenced in §21; keep",
        "terminal + best + every §21-referenced step. Scope: mini_a5, c5, pilot,",
        "smoke, m5_anchor_longhorizon_400{,_resume150}, stage0_repro,",
        "anchor_a0_recipe_3b_geo3k. m7/ and lh2/ untouched. Resolution record in",
        "`scripts/apply_storage_retention_rule_20260816.py` (committed).",
        "",
        "| path | bytes | action |",
        "|---|---:|---|",
    ]
    total = 0
    for row in rows:
        if row["action"] != "delete":
            continue
        target = REPO / row["path"]
        size = du_bytes(target)
        shutil.rmtree(target)
        total += size
        lines.append(f"| `{row['path']}` | {size} | deleted |")
        print(f"deleted {row['path']} ({size} bytes)")
    kept_rows = [row for row in rows if row["action"] == "keep"]
    lines.append("")
    lines.append(f"TOTAL_BYTES_DELETED={total}")
    lines.append(f"Kept ({len(kept_rows)} step dirs): " + "; ".join(
        f"`{row['path']}` ({row['reason']})" for row in kept_rows))
    if skipped:
        lines.append("Skipped fail-closed: " + " | ".join(skipped))
    with args.record.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    print(f"TOTAL_BYTES_DELETED={total}")
    print(f"record appended: {args.record}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
