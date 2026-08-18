#!/usr/bin/env python3
"""Build `artifacts/repos/EasyR1-hier` = arm 1's trainer tree + the grouping patch.

ST3's two arms must differ only in the intervention, so arm 2's trainer tree has
to be arm 1's tree (`artifacts/repos/EasyR1`) plus the grouping patch and
nothing else. This constructs it and then PROVES that property by diffing.

The patch is not written from scratch: it is taken from
`artifacts/repos/EasyR1-mini-a5`, the tree Mini-A5's CP arm actually ran and
which the registration names as C2's reference implementation, with only the
grouping module swapped. `src/train/cp_grouping.py` hardcodes the member names
to {a, b} (`PAIR_MEMBERS`), which would force ST3's meaningful member labels
(`l3`, `probe`) to be renamed in every batch, reward and shadow log; the k-ary
`src/train/hier_group_scoring.py` is name-agnostic and reduces exactly to the
binary semantics, which `tests/test_hier_group_scoring.py` asserts row by row
against `cp_grouping` itself.

Neither `EasyR1` nor `EasyR1-mini-a5` is modified. Both are left byte-identical,
so arm 1 (running) and Mini-A5's sha pin are untouched.

Refuses to overwrite an existing tree.
"""
from __future__ import annotations

import argparse
import filecmp
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOS = ROOT / "artifacts/repos"
PATCHED_FILES = (
    "verl/trainer/config.py",
    "verl/trainer/ray_trainer.py",
    "verl/workers/reward/function.py",
)
# (old, new, expected occurrences) applied to the mini-a5 copies
SWAPS = (
    ("from src.train.cp_grouping import (",
     "from src.train.hier_group_scoring import (", 1),
    ("compute_pair_level_grpo_advantage", "compute_group_level_grpo_advantage", 2),
    ("repeated_pair_metadata", "repeated_group_metadata", 3),
    # the module's keyword is `group_mode`; the config key stays `pair_group_mode`
    ("repeat_times,\n                    pair_group_mode=",
     "repeat_times,\n                    group_mode=", 1),
    ("self.config.worker.rollout.n,\n                    pair_group_mode=",
     "self.config.worker.rollout.n,\n                    group_mode=", 1),
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=REPOS / "EasyR1")
    parser.add_argument("--patched", type=Path, default=REPOS / "EasyR1-mini-a5")
    parser.add_argument("--out", type=Path, default=REPOS / "EasyR1-hier")
    parser.add_argument("--report", type=Path,
                        default=ROOT / "reports/easyr1_hier_tree_v1.json")
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)

    base_before = {name: sha(args.base / name) for name in PATCHED_FILES}
    patched_before = {name: sha(args.patched / name) for name in PATCHED_FILES}

    shutil.copytree(args.base, args.out, symlinks=True)

    applied = {}
    for name in PATCHED_FILES:
        text = (args.patched / name).read_text()
        if name == "verl/trainer/ray_trainer.py":
            for old, new, expected in SWAPS:
                found = text.count(old)
                if found != expected:
                    raise AssertionError(
                        f"swap {old!r} expected {expected} occurrence(s), found {found}")
                text = text.replace(old, new)
        (args.out / name).write_text(text)
        applied[name] = sha(args.out / name)

    trainer = (args.out / "verl/trainer/ray_trainer.py").read_text()
    for forbidden in ("cp_grouping", "repeated_pair_metadata",
                      "compute_pair_level_grpo_advantage"):
        if forbidden in trainer:
            raise AssertionError(f"{forbidden} still referenced in the hier tree")
    # the local compute_advantage parameter keeps its name; the two module calls
    # must have been renamed
    if trainer.count("group_mode=self.config.algorithm.pair_group_mode") != 3:
        raise AssertionError("unexpected group_mode call count")
    if trainer.count("pair_group_mode=self.config.algorithm.pair_group_mode") != 1:
        raise AssertionError("compute_advantage's own kwarg was renamed")

    # PROOF: the hier tree differs from arm 1's tree in exactly the patched files
    diff = subprocess.run(
        ["diff", "-rq", "--exclude=.git", "--exclude=__pycache__", "--exclude=*.pyc",
         str(args.base), str(args.out)],
        capture_output=True, text=True)
    differing = sorted(
        line.split()[1].replace(str(args.base) + "/", "")
        for line in diff.stdout.splitlines() if line.startswith("Files "))
    if differing != sorted(PATCHED_FILES):
        raise AssertionError(f"unexpected tree differences: {differing}")

    # neither source tree was touched
    for name in PATCHED_FILES:
        if sha(args.base / name) != base_before[name]:
            raise AssertionError(f"base tree modified: {name}")
        if sha(args.patched / name) != patched_before[name]:
            raise AssertionError(f"mini-a5 tree modified: {name}")
    if not filecmp.cmp(args.base / "verl/trainer/main.py",
                       args.out / "verl/trainer/main.py", shallow=False):
        raise AssertionError("unpatched file diverged")

    report = {
        "schema_version": "blind-gains.easyr1-hier-tree.v1",
        "purpose": "ST3 arm 2 trainer tree: arm 1's tree + the grouping patch only",
        "base_tree": str(args.base),
        "patch_source_tree": str(args.patched),
        "out_tree": str(args.out),
        "patched_files": list(PATCHED_FILES),
        "differing_files_vs_base": differing,
        "base_file_sha256": base_before,
        "patch_source_sha256": patched_before,
        "hier_file_sha256": applied,
        "grouping_module": "src/train/hier_group_scoring.py",
        "grouping_module_sha256": sha(ROOT / "src/train/hier_group_scoring.py"),
        "swaps": [{"old": o, "new": n, "occurrences": c} for o, n, c in SWAPS],
    }
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({"out_tree": str(args.out),
                      "differing_files_vs_base": differing,
                      "hier_ray_trainer_sha256": applied["verl/trainer/ray_trainer.py"]},
                     indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
