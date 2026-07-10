#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import re
import string
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
from PIL import Image


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _decoded_bytes(value: Any) -> bytes:
    if isinstance(value, dict) and isinstance(value.get("bytes"), bytes):
        return value["bytes"]
    raise ValueError("expected an embedded image record with a bytes field")


def _materialize_png(value: Any, image_dir: Path) -> Path:
    raw = _decoded_bytes(value)
    content_hash = hashlib.sha256(raw).hexdigest()
    output = image_dir / f"{content_hash[:24]}.png"
    if output.exists():
        return output.resolve()
    image_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(io.BytesIO(raw)) as opened:
        image = opened.convert("RGB")
        image.save(output, format="PNG", optimize=False, compress_level=6)
    return output.resolve()


def _as_list(value: Any) -> list[Any]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if hasattr(value, "tolist"):
        value = value.tolist()
    return list(value) if isinstance(value, (list, tuple)) else [value]


def _mathvista_answer_option(answer: Any, choices: list[Any]) -> str:
    normalized = str(answer).strip()
    matches = [index for index, choice in enumerate(choices) if str(choice).strip() == normalized]
    if len(matches) != 1:
        raise ValueError(f"MathVista answer must match exactly one choice, found {len(matches)}")
    return string.ascii_uppercase[matches[0]]


def prepare_mathvista_frame(
    frame: pd.DataFrame,
    image_dir: Path,
    *,
    drop_ambiguous_choices: bool = False,
    dropped_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    required = {"pid", "question", "decoded_image", "answer", "question_type", "answer_type"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"MathVista parquet missing columns: {sorted(missing)}")
    rows: list[dict[str, Any]] = []
    for raw in frame.to_dict(orient="records"):
        choices = _as_list(raw.get("choices"))
        metadata = raw.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise ValueError(f"MathVista row {raw['pid']} metadata is not a mapping")
        question_type = str(raw["question_type"])
        answer_option = ""
        if question_type == "multi_choice":
            try:
                answer_option = _mathvista_answer_option(raw["answer"], choices)
            except ValueError:
                if not drop_ambiguous_choices:
                    raise
                if dropped_ids is not None:
                    dropped_ids.append(str(raw["pid"]))
                continue
        prompt = raw.get("query")
        if not isinstance(prompt, str) or not prompt.strip():
            prompt = str(raw["question"])
        rows.append(
            {
                "index": f"mathvista_{raw['pid']}",
                "image_path": str(_materialize_png(raw["decoded_image"], image_dir)),
                "question": prompt.strip(),
                "answer": str(raw["answer"]),
                "question_type": question_type,
                "answer_type": str(raw["answer_type"]),
                "choices": repr([str(choice) for choice in choices]),
                "answer_option": answer_option,
                "task": str(metadata.get("task", "unknown")),
                "skills": repr([str(skill) for skill in _as_list(metadata.get("skills"))]),
                "source_pid": str(raw["pid"]),
            }
        )
    return rows


_BLINK_CHOICE_BLOCK = re.compile(r"\nSelect from the following choices\.\s*\n[\s\S]*$", re.IGNORECASE)
_BLINK_OPTION_LINE = re.compile(r"\n\([A-Z]\)\s")


def _blink_prompt_without_choices(raw: dict[str, Any]) -> str:
    prompt = str(raw.get("prompt") or raw["question"]).strip()
    prompt = _BLINK_CHOICE_BLOCK.sub("", prompt).strip()
    option = _BLINK_OPTION_LINE.search(prompt)
    if option:
        prompt = prompt[: option.start()].strip()
    return prompt


def _blink_answer_label(value: Any, choice_count: int) -> str:
    match = re.fullmatch(r"\s*\(?([A-Z])\)?\s*", str(value))
    if not match:
        raise ValueError(f"unrecognized BLINK answer label: {value!r}")
    label = match.group(1)
    if string.ascii_uppercase.index(label) >= choice_count:
        raise ValueError(f"BLINK answer {label} exceeds {choice_count} choices")
    return label


def prepare_blink_frames(frames: Iterable[pd.DataFrame], image_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for frame in frames:
        required = {"idx", "question", "choices", "answer", "sub_task", "image_1"}
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"BLINK parquet missing columns: {sorted(missing)}")
        for raw in frame.to_dict(orient="records"):
            source_id = str(raw["idx"])
            if source_id in seen:
                raise ValueError(f"duplicate BLINK id: {source_id}")
            seen.add(source_id)
            choices = [str(choice) for choice in _as_list(raw["choices"])]
            if not 2 <= len(choices) <= len(string.ascii_uppercase):
                raise ValueError(f"BLINK row {source_id} has invalid choice count {len(choices)}")
            paths = []
            for key in ("image_1", "image_2", "image_3", "image_4"):
                value = raw.get(key)
                if isinstance(value, dict) and isinstance(value.get("bytes"), bytes):
                    paths.append(str(_materialize_png(value, image_dir)))
            if not paths:
                raise ValueError(f"BLINK row {source_id} has no readable images")
            record: dict[str, Any] = {
                "index": f"blink_{source_id}",
                "image_path": repr(paths) if len(paths) > 1 else paths[0],
                "question": _blink_prompt_without_choices(raw),
                "answer": _blink_answer_label(raw["answer"], len(choices)),
                "category": str(raw["sub_task"]),
                "source_id": source_id,
            }
            record.update({string.ascii_uppercase[index]: choice for index, choice in enumerate(choices)})
            rows.append(record)
    return rows


def _write_outputs(
    rows: list[dict[str, Any]],
    source_paths: list[Path],
    output: Path,
    metadata_output: Path,
    dataset: str,
    deviations: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if output.exists() or metadata_output.exists():
        raise FileExistsError(f"refusing to overwrite adapter outputs: {output} / {metadata_output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output, sep="\t", index=False)
    image_paths = []
    for row in rows:
        value = row["image_path"]
        if isinstance(value, str) and value.startswith("["):
            image_paths.extend(ast.literal_eval(value))
        else:
            image_paths.append(str(value))
    payload = {
        "schema_version": "blind-gains.layer1-vlmeval-adapter.v1",
        "dataset": dataset,
        "rows": len(rows),
        "unique_images": len(set(image_paths)),
        "source_files": [{"path": str(path), "sha256": sha256_file(path)} for path in source_paths],
        "output": str(output),
        "output_sha256": sha256_file(output),
        "deviations": deviations or {},
    }
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=("mathvista", "blink"), required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image-dir", type=Path, required=True)
    parser.add_argument("--metadata-output", type=Path, required=True)
    parser.add_argument("--drop-ambiguous-mathvista-choices", action="store_true")
    args = parser.parse_args()

    if args.dataset == "mathvista":
        sources = [args.source]
        dropped_ids: list[str] = []
        rows = prepare_mathvista_frame(
            pd.read_parquet(args.source),
            args.image_dir,
            drop_ambiguous_choices=args.drop_ambiguous_mathvista_choices,
            dropped_ids=dropped_ids,
        )
        deviations = {"dropped_ambiguous_choice_ids": dropped_ids}
    else:
        sources = sorted(args.source.glob("*/val-*.parquet"))
        if not sources:
            raise FileNotFoundError(f"no BLINK validation parquet files under {args.source}")
        rows = prepare_blink_frames((pd.read_parquet(path) for path in sources), args.image_dir)
        deviations = {}
    payload = _write_outputs(rows, sources, args.output, args.metadata_output, args.dataset, deviations)
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
