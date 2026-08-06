#!/usr/bin/env python3
"""Matched-difference audit for the Mini-A5 Gate-1 completion arms.

Registered by docs/registered_mini_a5_gate1_completion_v1.md acceptance
condition 8 (prework ledger T5): each completion-arm config
(mini_a5_std_3b_v1.yaml / mini_a5_necessity_3b_v1.yaml) must differ from the
member template (mini_a5_same_data_3b_v1.yaml) in exactly three leaf fields:

    data.train_files
    trainer.experiment_name
    trainer.save_checkpoint_path

Everything else — steps, seed, batch geometry, rollout settings, lr, KL,
frozen vision tower, pair_group_mode, reward_function — must be byte-equal at
the flattened-leaf level. Any additional change, any missing change, and any
key added or removed anywhere in the tree is a refusal.

Called by scripts/launch_mini_a5_main.sh for modes std/necessity at launch;
exit 0 iff the diff is exactly the allowed set.

Adversarial fixture (I10): tests/test_check_mini_a5_matched_diff_fixture.py.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

ALLOWED_CHANGED_KEYS = (
    "data.train_files",
    "trainer.experiment_name",
    "trainer.save_checkpoint_path",
)

_SENTINEL = object()


def flatten(node: Any, prefix: str = "") -> dict[str, Any]:
    """Flatten a nested mapping to dot-joined leaf paths. Lists are leaves."""
    if not isinstance(node, dict):
        return {prefix: node}
    flat: dict[str, Any] = {}
    for key, value in node.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            flat.update(flatten(value, path))
        else:
            flat[path] = value
    return flat


def matched_diff(candidate: dict[str, Any], template: dict[str, Any]) -> list[str]:
    """Return the sorted list of flattened leaf keys whose values differ."""
    flat_candidate = flatten(candidate)
    flat_template = flatten(template)
    return sorted(
        key
        for key in set(flat_candidate) | set(flat_template)
        if flat_candidate.get(key, _SENTINEL) != flat_template.get(key, _SENTINEL)
    )


def check(candidate_path: Path, template_path: Path) -> list[str]:
    """Return the list of violations (empty iff the audit passes)."""
    with candidate_path.open(encoding="utf-8") as handle:
        candidate = yaml.safe_load(handle)
    with template_path.open(encoding="utf-8") as handle:
        template = yaml.safe_load(handle)
    diff = matched_diff(candidate, template)
    allowed = sorted(ALLOWED_CHANGED_KEYS)
    violations: list[str] = []
    for key in diff:
        if key not in allowed:
            violations.append(f"disallowed change: {key}")
    for key in allowed:
        if key not in diff:
            violations.append(f"required change absent (config not per-mode): {key}")
    return violations


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--template", type=Path, required=True)
    args = parser.parse_args()
    violations = check(args.candidate, args.template)
    if violations:
        for violation in violations:
            print(f"matched-difference audit failed: {violation}", file=sys.stderr)
        raise SystemExit(2)
    print("matched-difference audit passed: exactly "
          f"{sorted(ALLOWED_CHANGED_KEYS)} differ")


if __name__ == "__main__":
    main()
