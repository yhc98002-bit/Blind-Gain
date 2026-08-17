#!/usr/bin/env python3
"""Question-operand audit (08-12 dispatch P0.1; I21).

The cue-ladder invalidation was an OPERAND bug: its verifier checked gold
against the *target* while the question named a different entity. This audit
closes that class from disk for every generator whose manifests record enough
truth to check:

- point-target families (B1, premise-v2, R19 coordinate register): the entity
  named in the question ("point <LABEL>") must equal
  `verifier_results.target_label`;
- R19 coordinate register: golds are RECOMPUTED from the recorded
  `target_a`/`target_b` coordinates under the declared
  `semantic_side_assignment_swapped` convention (answer = target's
  x-coordinate; pinned empirically 600/600 before this audit shipped);
- chart-v08 families: the x named in the question ("x = N") must equal
  `verifier_results.target_x` (pinned empirically 100/100);
- hier_v1 families (pre-freeze cleanup, 2026-08-17 — previously these rows
  fell into the unchecked bucket because their operands live under
  `target_label_a/b`): L3 and probe questions must name NEITHER side's
  target (discovery withholds identity); L2/L1 questions must name exactly
  the shared target identity, which must agree between sides (A2: layers
  with an identity-given question exist only where one truthful identity
  holds for both sides).

Rows that carry none of the checkable operands are counted as such, never
silently passed. Exit 1 on any problem.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Labels are uppercase-headed (G7, N9, T4); the uppercase requirement keeps
# prose like "the point is" from matching as a label.
POINT_RE = re.compile(r"point ([A-Z][A-Za-z0-9]*)")
X_RE = re.compile(r"x = (-?\d+)")
SERIES_RE = re.compile(r"series ([A-Z][A-Za-z]*)")


def question_named_point(question: str) -> str | None:
    match = POINT_RE.search(question or "")
    return match.group(1) if match else None


def question_named_series(question: str) -> str | None:
    match = SERIES_RE.search(question or "")
    return match.group(1) if match else None


def question_named_x(question: str) -> int | None:
    match = X_RE.search(question or "")
    return int(match.group(1)) if match else None


def audit_row(row: dict) -> tuple[list[str], list[str]]:
    """Return (checks_applied, problems) for one manifest row."""
    checks: list[str] = []
    problems: list[str] = []
    vr = row.get("verifier_results") or {}
    pair_id = row.get("pair_id", "<no pair_id>")
    question = row.get("question") or ""

    target_label = vr.get("target_label")
    if target_label is not None and "point " in question:
        checks.append("question_names_target_label")
        named = question_named_point(question)
        if named != str(target_label):
            problems.append(
                f"{pair_id}: question names point {named!r} but "
                f"verifier_results.target_label is {target_label!r}"
            )

    target_a, target_b = vr.get("target_a"), vr.get("target_b")
    if (
        isinstance(target_a, (list, tuple))
        and isinstance(target_b, (list, tuple))
        and "x-coordinate" in question
    ):
        checks.append("coord_register_gold_recompute")
        swapped = bool(vr.get("semantic_side_assignment_swapped"))
        expected_a = str((target_b if swapped else target_a)[0])
        expected_b = str((target_a if swapped else target_b)[0])
        if str(row.get("answer_a")) != expected_a or str(row.get("answer_b")) != expected_b:
            problems.append(
                f"{pair_id}: recomputed golds ({expected_a}, {expected_b}) != "
                f"recorded ({row.get('answer_a')}, {row.get('answer_b')}) "
                f"[swapped={swapped}]"
            )

    if row.get("category") == "hier_v1":
        layer = row.get("layer")
        label_a = str(vr.get("target_label_a"))
        label_b = str(vr.get("target_label_b"))
        if layer in ("l3", "probe"):
            checks.append("hier_l3_probe_names_no_target")
            leaked = sorted(lbl for lbl in {label_a, label_b}
                            if lbl and lbl != "None" and lbl in question)
            if leaked:
                problems.append(
                    f"{pair_id}: {layer} question names target(s) {leaked} "
                    f"(discovery must withhold identity)")
        elif layer in ("l2", "l1"):
            checks.append("hier_l2_l1_names_target")
            named = question_named_point(question) or question_named_series(question)
            if label_a != label_b:
                problems.append(
                    f"{pair_id}: {layer} row exists but target identity "
                    f"differs between sides ({label_a!r} vs {label_b!r}; A2)")
            elif named != label_a:
                problems.append(
                    f"{pair_id}: {layer} question names {named!r} but the "
                    f"target identity is {label_a!r}")

    target_x = vr.get("target_x")
    if target_x is not None:
        named_x = question_named_x(question)
        if named_x is not None:
            checks.append("question_names_target_x")
            if named_x != target_x:
                problems.append(
                    f"{pair_id}: question names x = {named_x} but "
                    f"verifier_results.target_x is {target_x}"
                )

    return checks, problems


def audit_manifest(path: Path) -> dict:
    rows = checked = 0
    unchecked = 0
    check_counts: dict[str, int] = {}
    problems: list[str] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows += 1
            row = json.loads(line)
            checks, row_problems = audit_row(row)
            if checks:
                checked += 1
                for check in checks:
                    check_counts[check] = check_counts.get(check, 0) + 1
            else:
                unchecked += 1
            problems.extend(row_problems)
    return {
        "manifest": str(path),
        "rows": rows,
        "rows_checked": checked,
        "rows_without_checkable_operands": unchecked,
        "checks_applied": check_counts,
        "n_problems": len(problems),
        "problems": problems[:20],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, action="append", required=True)
    args = parser.parse_args()
    results = [audit_manifest(path) for path in args.manifest]
    print(json.dumps(results, indent=2, sort_keys=True))
    return 1 if any(result["n_problems"] for result in results) else 0


if __name__ == "__main__":
    sys.exit(main())
