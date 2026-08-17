#!/usr/bin/env python3
"""Convert the ST3 training corpus into the geometry-manifest schema the
registered blind-solvability harness consumes, so C1's Δq can be measured on
the model that will be trained.

This is the ST3 analogue of `build_mini_a5_blind_solvability_manifest.py`,
written as a separate script rather than a generalisation of that one because
the Mini-A5 builder is pinned by `registered_mini_a5_gate1_completion_v1.md`
(source hashes, pairs.jsonl cross-checks) and must not move.

Emits, row-for-row and in frozen corpus order:

    {"split": "train", "row_index": i, "qid": "<pair_group_uid>:<pair_member>",
     "problem": ..., "answer": ..., "images": [{"path", "sha256"}],
     "metadata": {...}, "schema_version": ...}

Byte-correspondence audit (refuses on any mismatch): every emitted row is
checked against the corpus row at the same index — identical problem, answer
and image path — the image sha256 is recomputed from the bytes on disk,
row_index is contiguous, and every qid is unique. Refuses to overwrite.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SCHEMA_VERSION = "blind-gains.st3-blind-solvability-manifest.v1"
SPLIT = "train"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path,
                        default=ROOT / "data/st3_train_v1/train.jsonl")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "data/st3_train_blind_solvability_manifest_v1.jsonl")
    parser.add_argument("--report", type=Path,
                        default=ROOT / "reports/st3_blind_solvability_manifest_v1.json")
    args = parser.parse_args()
    for path in (args.output, args.report):
        if path.exists():
            raise FileExistsError(path)

    corpus = [json.loads(l) for l in args.corpus.read_text().splitlines() if l.strip()]
    if not corpus:
        raise SystemExit(f"empty corpus: {args.corpus}")

    rows = []
    seen_qids: set[str] = set()
    for index, source in enumerate(corpus):
        image_rel = source["images"][0]
        image_path = ROOT / image_rel
        if not image_path.is_file():
            raise FileNotFoundError(image_rel)
        qid = f"{source['pair_group_uid']}:{source['pair_member']}"
        if qid in seen_qids:
            raise AssertionError(f"duplicate qid: {qid}")
        seen_qids.add(qid)
        rows.append({
            "split": SPLIT,
            "row_index": index,
            "qid": qid,
            "problem": source["problem"],
            "answer": source["answer"],
            "images": [{"path": image_rel, "sha256": sha256_file(image_path)}],
            "metadata": {
                "pair_group_uid": source["pair_group_uid"],
                "pair_member": source["pair_member"],
                "template_id": source["template_id"],
                "category": source["category"],
                "source_corpus": str(args.corpus.relative_to(ROOT)),
            },
            "schema_version": SCHEMA_VERSION,
        })

    # byte correspondence against the corpus at the same index
    for index, (row, source) in enumerate(zip(rows, corpus)):
        if row["row_index"] != index:
            raise AssertionError(f"row_index not contiguous at {index}")
        if row["problem"] != source["problem"] or row["answer"] != source["answer"]:
            raise AssertionError(f"problem/answer drift at row {index}")
        if row["images"][0]["path"] != source["images"][0]:
            raise AssertionError(f"image path drift at row {index}")

    blob = "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)
    args.output.write_text(blob, encoding="utf-8")
    report = {
        "schema_version": "blind-gains.st3-blind-solvability-manifest-build.v1",
        "corpus": str(args.corpus.relative_to(ROOT)),
        "corpus_rows": len(corpus),
        "manifest": str(args.output.relative_to(ROOT)),
        "manifest_rows": len(rows),
        "manifest_sha256": hashlib.sha256(blob.encode()).hexdigest(),
        "unique_qids": len(seen_qids),
        "byte_correspondence": "problem/answer/image path checked per index; "
                               "image sha256 recomputed from bytes on disk",
        "purpose": "C1 necessity sampling: q_real and q_blind per training item "
                   "(16 samples, T=1) measured on the 7B base",
    }
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({k: report[k] for k in
                      ("corpus_rows", "manifest_rows", "unique_qids",
                       "manifest_sha256")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
