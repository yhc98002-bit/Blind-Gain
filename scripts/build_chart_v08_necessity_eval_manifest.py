#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "blind-gains.chart-v08-necessity-eval-manifest.v1"
SIDECAR_SCHEMA = "blind-gains.chart-v08-necessity-sidecar.v2"
INTERVENTIONS = ("no_star", "random_star")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            rows.append(row)
    if not rows:
        raise ValueError(f"empty JSONL: {path}")
    return rows


def _index_unique(rows: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        pair_id = str(row.get("pair_id", ""))
        if not pair_id:
            raise ValueError(f"{label} row has no pair_id")
        if pair_id in index:
            raise ValueError(f"duplicate {label} pair_id: {pair_id}")
        index[pair_id] = row
    return index


def _resolve_asset(root: Path, raw: Any) -> Path:
    if not isinstance(raw, str) or not raw:
        raise ValueError("diagnostic image path is absent")
    path = (root / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"diagnostic image escapes project root: {raw}") from error
    return path


def build_manifest(
    *,
    root: Path,
    source_manifest: Path,
    sidecar: Path,
    output: Path,
    metadata_output: Path,
) -> dict[str, Any]:
    if output.exists() or metadata_output.exists():
        raise FileExistsError("refusing to overwrite chart-v08 necessity artifacts")
    source_rows = _read_jsonl(source_manifest)
    sidecar_rows = _read_jsonl(sidecar)
    source_by_id = _index_unique(source_rows, "source")
    sidecar_by_id = _index_unique(sidecar_rows, "sidecar")
    if set(source_by_id) != set(sidecar_by_id):
        raise ValueError("source and sidecar pair identities differ")
    source_hash = _sha256(source_manifest)
    output_rows: list[dict[str, Any]] = []
    template_counts: Counter[str] = Counter()
    for source in source_rows:
        pair_id = str(source["pair_id"])
        diagnostic = sidecar_by_id[pair_id]
        if diagnostic.get("schema_version") != SIDECAR_SCHEMA:
            raise ValueError(f"unexpected sidecar schema for {pair_id}")
        if diagnostic.get("source_manifest_sha256") != source_hash:
            raise ValueError(f"sidecar source hash mismatch for {pair_id}")
        for field in ("question", "answer_a", "answer_b"):
            if str(diagnostic.get(field)) != str(source.get(field)):
                raise ValueError(f"sidecar {field} mismatch for {pair_id}")
        random_star = diagnostic["random_star"]
        if (
            str(random_star.get("implied_answer_a")) == str(source["answer_a"])
            or str(random_star.get("implied_answer_b")) == str(source["answer_b"])
        ):
            raise ValueError(f"random-star intervention is not answer-discordant: {pair_id}")
        for intervention in INTERVENTIONS:
            intervention_row = diagnostic[intervention]
            assets: dict[str, str] = {}
            for member in ("a", "b"):
                raw_path = intervention_row[f"image_{member}_path"]
                path = _resolve_asset(root, raw_path)
                if not path.is_file():
                    raise FileNotFoundError(path)
                expected_hash = str(intervention_row[f"image_{member}_sha256"])
                if _sha256(path) != expected_hash:
                    raise ValueError(
                        f"diagnostic image hash mismatch for {pair_id}:{intervention}:{member}"
                    )
                assets[f"image_{member}_path"] = str(path.relative_to(root.resolve()))
                assets[f"image_{member}_sha256"] = expected_hash
            template_id = f"{source['template_id']}__{intervention}"
            output_rows.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "pair_id": f"{pair_id}__{intervention}",
                    "source_pair_id": pair_id,
                    "category": source.get("category"),
                    "template_id": template_id,
                    "intervention": intervention,
                    "question": source["question"],
                    "answer_a": str(source["answer_a"]),
                    "answer_b": str(source["answer_b"]),
                    "scoring_target": "original_member_answer",
                    **assets,
                }
            )
            template_counts[template_id] += 1

    output.parent.mkdir(parents=True, exist_ok=True)
    partial_output = output.with_name(f".{output.name}.{os.getpid()}.partial")
    partial_output.write_text(
        "".join(
            json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n"
            for row in output_rows
        ),
        encoding="utf-8",
    )
    os.replace(partial_output, output)
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "status": "pass",
        "source_manifest": str(source_manifest),
        "source_manifest_sha256": source_hash,
        "sidecar": str(sidecar),
        "sidecar_sha256": _sha256(sidecar),
        "output": str(output),
        "output_sha256": _sha256(output),
        "source_pairs": len(source_rows),
        "evaluation_rows": len(output_rows),
        "interventions": list(INTERVENTIONS),
        "template_counts": dict(sorted(template_counts.items())),
        "scoring_target": "original_member_answer",
        "scientific_gate_decision": None,
    }
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    partial_metadata = metadata_output.with_name(
        f".{metadata_output.name}.{os.getpid()}.partial"
    )
    partial_metadata.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(partial_metadata, metadata_output)
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--sidecar", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metadata-output", type=Path, required=True)
    args = parser.parse_args()
    result = build_manifest(
        root=args.root.resolve(),
        source_manifest=args.source_manifest,
        sidecar=args.sidecar,
        output=args.output,
        metadata_output=args.metadata_output,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
