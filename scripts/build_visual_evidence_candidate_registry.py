#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.eval.visual_evidence_ranking import build_candidate_registry_rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--metadata-output", required=True)
    parser.add_argument("--max-candidates", type=int, default=16)
    args = parser.parse_args()

    source = Path(args.source)
    output = Path(args.output)
    metadata_output = Path(args.metadata_output)
    if output.exists() or metadata_output.exists():
        raise FileExistsError("refusing to overwrite frozen candidate-registry artifacts")
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line]
    frozen = build_candidate_registry_rows(rows, max_candidates=args.max_candidates)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.{os.getpid()}.partial")
    with temporary.open("x", encoding="utf-8") as handle:
        for row in frozen:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
    os.replace(temporary, output)

    counts: dict[str, dict[str, int]] = {}
    for row in frozen:
        template = str(row["template_id"])
        cell = counts.setdefault(template, {"pairs": 0, "candidate_min": 10**9, "candidate_max": 0})
        cell["pairs"] += 1
        cell["candidate_min"] = min(cell["candidate_min"], int(row["candidate_count"]))
        cell["candidate_max"] = max(cell["candidate_max"], int(row["candidate_count"]))
    metadata = {
        "schema_version": "blind-gains.visual-evidence-candidate-registry-metadata.v1",
        "status": "complete",
        "source": str(source),
        "source_sha256": sha256_file(source),
        "output": str(output),
        "output_sha256": sha256_file(output),
        "pair_count": len(frozen),
        "max_candidates": args.max_candidates,
        "selection_uses_model_outputs": False,
        "templates": counts,
    }
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(metadata, sort_keys=True))


if __name__ == "__main__":
    main()
