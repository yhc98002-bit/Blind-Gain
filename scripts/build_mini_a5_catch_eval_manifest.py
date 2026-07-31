#!/usr/bin/env python3
"""pair_group_uid -> pair_id adapter for the Mini-A5 catch set.

The generation harness ``scripts/eval_qwen_vl_fliptrack.py`` reads exactly
``pair_id`` per row; ``data/mini_a5_catch_v1/pairs.jsonl`` keys its rows
``pair_group_uid`` (reports/f8_secondaries_v1.md section 2.4, missing piece i).
This script derives an eval-ready manifest WITHOUT touching the source set:

  - verifies the source file against its pinned sha256 before reading a row;
  - copies every source field unchanged and adds ``pair_id`` :=
    ``pair_group_uid`` (refusing sources that already carry ``pair_id``);
  - validates the catch invariants it depends on (300 rows, 3 registered
    templates x 100, equal nonempty golds, unique uids, images on disk);
  - writes ``data/derived/mini_a5_catch_eval_manifest_v1.jsonl``
    deterministically (sorted keys, ascii) plus a provenance sidecar with the
    source and output sha256, so the derived manifest is hash-recorded;
  - refuses to overwrite a differing existing output without --force.

Registered in docs/registered_mini_a5_catch_stability_v1.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

SOURCE_DEFAULT = "data/mini_a5_catch_v1/pairs.jsonl"
OUTPUT_DEFAULT = "data/derived/mini_a5_catch_eval_manifest_v1.jsonl"
# Pinned at docs/registered_mini_a5_main_v1.md (catch audit) and re-verified in
# reports/f8_secondaries_v1.md section 2.3.
PINNED_SOURCE_SHA256 = "fbd83d52fa01103bfb839fa2572eb9164c532f8c3a3431da6ca8f6033d6a9728"
REGISTERED_TEMPLATES = (
    "mini_a5_catch_distractor_matrix_v1",
    "mini_a5_catch_distractor_scatter_v1",
    "mini_a5_catch_distractor_trajectory_v1",
)
PROVENANCE_SCHEMA = "blind-gains.mini-a5-catch-eval-manifest-provenance.v1"


class AdapterError(RuntimeError):
    pass


def convert_rows(
    source_rows: list[dict],
    image_root: Path | None,
    require_registered_shape: bool = True,
) -> list[dict]:
    out_rows: list[dict] = []
    uids: set[str] = set()
    for index, row in enumerate(source_rows):
        if "pair_id" in row:
            raise AdapterError(
                f"source row {index} already carries 'pair_id'; refusing an ambiguous mapping"
            )
        uid = row.get("pair_group_uid")
        if not isinstance(uid, str) or not uid:
            raise AdapterError(f"source row {index} lacks a nonempty pair_group_uid")
        if uid in uids:
            raise AdapterError(f"duplicate pair_group_uid: {uid}")
        uids.add(uid)
        for key in ("question", "template_id", "image_a_path", "image_b_path"):
            if not isinstance(row.get(key), str) or not row[key]:
                raise AdapterError(f"row {uid} lacks a nonempty '{key}'")
        answer_a = str(row.get("answer_a", "")).strip()
        answer_b = str(row.get("answer_b", "")).strip()
        if not answer_a or answer_a != answer_b:
            raise AdapterError(
                f"row {uid} violates the equal-nonempty-gold catch invariant: "
                f"answer_a={row.get('answer_a')!r} answer_b={row.get('answer_b')!r}"
            )
        if image_root is not None:
            for key in ("image_a_path", "image_b_path"):
                image_path = image_root / row[key]
                if not image_path.is_file():
                    raise AdapterError(f"row {uid}: image missing on disk: {image_path}")
        out_row = dict(row)
        out_row["pair_id"] = uid
        out_rows.append(out_row)
    counts = Counter(row["template_id"] for row in out_rows)
    if require_registered_shape:
        if len(out_rows) != 300 or tuple(sorted(counts)) != REGISTERED_TEMPLATES or any(
            counts[t] != 100 for t in counts
        ):
            raise AdapterError(
                f"source does not match the registered catch shape (300 rows, "
                f"3 templates x 100): n={len(out_rows)} counts={dict(counts)}"
            )
    return out_rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=SOURCE_DEFAULT)
    parser.add_argument("--output", default=OUTPUT_DEFAULT)
    parser.add_argument(
        "--expected-source-sha256", default=PINNED_SOURCE_SHA256,
        help="sha256 the source file must match before any row is read",
    )
    parser.add_argument(
        "--image-root", default=str(REPO_ROOT),
        help="root against which relative image paths are checked for existence",
    )
    parser.add_argument(
        "--skip-image-check", action="store_true",
        help="skip on-disk image existence checks (fixtures only)",
    )
    parser.add_argument(
        "--allow-nonregistered-shape", action="store_true",
        help="drop the 300-rows/3x100 shape requirement (fixtures only)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="overwrite an existing, differing output",
    )
    args = parser.parse_args(argv)

    source_path = Path(args.source)
    if not source_path.is_absolute():
        source_path = REPO_ROOT / source_path
    source_bytes = source_path.read_bytes()
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    if source_sha256 != args.expected_source_sha256:
        print(
            f"ERROR: source sha256 mismatch for {source_path}\n"
            f"  expected {args.expected_source_sha256}\n"
            f"  observed {source_sha256}",
            file=sys.stderr,
        )
        return 1

    source_rows = [
        json.loads(line) for line in source_bytes.decode("utf-8").splitlines() if line.strip()
    ]
    image_root = None if args.skip_image_check else Path(args.image_root)
    try:
        out_rows = convert_rows(
            source_rows,
            image_root=image_root,
            require_registered_shape=not args.allow_nonregistered_shape,
        )
    except AdapterError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    payload = (
        "\n".join(json.dumps(row, sort_keys=True, ensure_ascii=True) for row in out_rows)
        + "\n"
    ).encode("utf-8")
    output_sha256 = hashlib.sha256(payload).hexdigest()

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = REPO_ROOT / output_path
    if output_path.exists():
        existing = output_path.read_bytes()
        if existing == payload:
            print(f"unchanged: {output_path} (sha256 {output_sha256})")
        elif not args.force:
            print(
                f"ERROR: {output_path} exists with different content "
                f"(sha256 {hashlib.sha256(existing).hexdigest()}); rerun with --force to replace",
                file=sys.stderr,
            )
            return 1
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(payload)

    provenance = {
        "schema_version": PROVENANCE_SCHEMA,
        "generator": "scripts/build_mini_a5_catch_eval_manifest.py",
        "key_mapping": "pair_id := pair_group_uid; every source field preserved unchanged",
        "source_path": args.source,
        "source_sha256": source_sha256,
        "output_path": args.output,
        "output_sha256": output_sha256,
        "n_rows": len(out_rows),
        "template_pair_counts": dict(sorted(Counter(r["template_id"] for r in out_rows).items())),
    }
    provenance_path = Path(str(output_path) + ".provenance.json")
    provenance_path.write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(provenance, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
