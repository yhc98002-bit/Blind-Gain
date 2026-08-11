"""Diff a seed-1 replay against reports/m7_r3_readout_v1.json.

Only three fields may differ, and each for a reason that is NOT the seed-1 code
path:
  - provenance.analysis_git_head : recorded from live HEAD at run time
  - joined_items_artifact        : embeds the --artifact-dir path
  - support_sharpening.arms[*].candidate_artifact : same

EVERY numeric value and EVERY content hash (joined_items_sha256,
candidate_sha256, per_item_sha256, run_manifest_sha256, heldout_sha256) must be
identical. Anything else that differs is a real regression.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

NORMALIZED = {
    ("provenance", "analysis_git_head"),
    ("joined_items_artifact",),
}


def flatten(node, prefix=()):
    if isinstance(node, dict):
        for key in sorted(node):
            yield from flatten(node[key], prefix + (key,))
    elif isinstance(node, list):
        for index, item in enumerate(node):
            yield from flatten(item, prefix + (f"[{index}]",))
    else:
        yield prefix, node


def is_normalized(path: tuple[str, ...]) -> bool:
    if path in NORMALIZED:
        return True
    return (
        len(path) == 4
        and path[0] == "support_sharpening"
        and path[1] == "arms"
        and path[3] == "candidate_artifact"
    )


def main() -> None:
    published = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    replay = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    left = dict(flatten(published))
    right = dict(flatten(replay))

    only_published = sorted(set(left) - set(right))
    only_replay = sorted(set(right) - set(left))
    differing = sorted(
        key for key in set(left) & set(right) if left[key] != right[key]
    )

    print(f"published leaf fields : {len(left)}")
    print(f"replay    leaf fields : {len(right)}")
    print(f"keys only in published: {len(only_published)} {only_published[:5]}")
    print(f"keys only in replay   : {len(only_replay)} {only_replay[:5]}")
    print(f"differing leaf values : {len(differing)}")
    for key in differing:
        marker = "NORMALIZED" if is_normalized(key) else "*** REGRESSION ***"
        print(f"  {marker}  {'.'.join(key)}")
        print(f"      published: {left[key]!r}")
        print(f"      replay   : {right[key]!r}")

    unexpected = [key for key in differing if not is_normalized(key)]
    hashes = sorted(
        key
        for key in set(left) & set(right)
        if key[-1].endswith("sha256")
    )
    hash_mismatch = [key for key in hashes if left[key] != right[key]]
    print(f"content-hash fields compared: {len(hashes)}; mismatched: {len(hash_mismatch)}")
    for key in hash_mismatch:
        print(f"  *** HASH MISMATCH *** {'.'.join(key)}")

    ok = not unexpected and not only_published and not only_replay and not hash_mismatch
    print("VERDICT:", "IDENTICAL-MODULO-NORMALIZED-PATH-AND-HEAD-FIELDS" if ok else "REGRESSION")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
