#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import csv
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


_MMVP_OPTION = re.compile(r"\(([a-zA-Z])\)\s*(.*?)(?=\s*\([a-zA-Z]\)\s*|$)")


def prepare_mmvp_csv(source: Path, image_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"Index", "Question", "Options", "Correct Answer"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"MMVP CSV missing columns: {sorted(missing)}")
        for expected_index, raw in enumerate(reader, start=1):
            source_index = int(raw["Index"])
            if source_index != expected_index:
                raise ValueError(f"MMVP row order is not contiguous at {source_index}")
            options = [(label.upper(), text.strip()) for label, text in _MMVP_OPTION.findall(raw["Options"])]
            if len(options) < 2 or len({label for label, _ in options}) != len(options):
                raise ValueError(f"MMVP row {source_index} has malformed options: {raw['Options']!r}")
            answer_match = re.fullmatch(r"\s*\(([a-zA-Z])\)\s*", raw["Correct Answer"])
            if not answer_match:
                raise ValueError(f"MMVP row {source_index} has malformed answer: {raw['Correct Answer']!r}")
            answer = answer_match.group(1).upper()
            labels = {label for label, _ in options}
            if answer not in labels:
                raise ValueError(f"MMVP row {source_index} answer {answer} is not an option")
            image_path = (image_root / f"{source_index}.jpg").resolve()
            if not image_path.is_file():
                raise FileNotFoundError(f"MMVP row {source_index} image is missing: {image_path}")
            record: dict[str, Any] = {
                "index": source_index,
                "image_path": str(image_path),
                "question": raw["Question"].strip(),
                "answer": answer,
                "pair_id": (source_index - 1) // 2,
                "pair_member": "A" if source_index % 2 else "B",
                "source_index": source_index,
            }
            record.update(dict(options))
            rows.append(record)
    if len(rows) % 2:
        raise ValueError("MMVP must contain an even number of rows")
    for offset in range(0, len(rows), 2):
        if rows[offset]["question"] != rows[offset + 1]["question"]:
            raise ValueError(f"MMVP pair {offset // 2} does not share one question")
    return rows


def write_external_image_reference(image_dir: Path, source_root: Path) -> None:
    image_dir.mkdir(parents=True, exist_ok=True)
    marker = image_dir / "SOURCE_IMAGES.txt"
    marker.write_text(
        "Images are referenced in place from:\n" + str(source_root.resolve()) + "\n",
        encoding="utf-8",
    )


def _resolve_case_insensitive(path: Path) -> Path:
    if path.is_file():
        return path.resolve()
    if not path.parent.is_dir():
        raise FileNotFoundError(path)
    matches = [candidate for candidate in path.parent.iterdir() if candidate.name.casefold() == path.name.casefold()]
    if len(matches) != 1 or not matches[0].is_file():
        raise FileNotFoundError(path)
    return matches[0].resolve()


def _hallusion_text_only_image(image_dir: Path) -> Path:
    output = image_dir / "hallusion_text_only_blank.png"
    image_dir.mkdir(parents=True, exist_ok=True)
    if not output.exists():
        Image.new("RGB", (28, 28), "white").save(output, format="PNG", optimize=False, compress_level=6)
    return output.resolve()


def prepare_hallusion_json(source: Path, image_dir: Path) -> list[dict[str, Any]]:
    raw_rows = json.loads((source / "HallusionBench.json").read_text(encoding="utf-8"))
    if not isinstance(raw_rows, list):
        raise ValueError("HallusionBench annotation root must be a list")
    blank_path = _hallusion_text_only_image(image_dir)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in raw_rows:
        required = {
            "category",
            "subcategory",
            "visual_input",
            "set_id",
            "figure_id",
            "question_id",
            "question",
            "gt_answer",
        }
        missing = required - set(raw)
        if missing:
            raise ValueError(f"HallusionBench row missing columns: {sorted(missing)}")
        visual_input = str(raw["visual_input"])
        if visual_input == "0":
            image_path = blank_path
            image_is_placeholder = True
        else:
            filename = raw.get("filename")
            if not filename:
                raise ValueError("visual HallusionBench row has no filename")
            relative = Path(str(filename).removeprefix("./"))
            image_path = _resolve_case_insensitive(source / "data" / relative)
            image_is_placeholder = False
        index = "_".join(
            [
                "hallusion",
                str(raw["category"]),
                str(raw["subcategory"]),
                str(raw["set_id"]),
                str(raw["figure_id"]),
                str(raw["question_id"]),
            ]
        )
        if index in seen:
            raise ValueError(f"duplicate HallusionBench index: {index}")
        seen.add(index)
        answer = {"0": "No", "1": "Yes"}.get(str(raw["gt_answer"]))
        if answer is None:
            raise ValueError(f"unsupported HallusionBench answer: {raw['gt_answer']!r}")
        rows.append(
            {
                "index": index,
                "image_path": str(image_path),
                "question": str(raw["question"]).strip(),
                "answer": answer,
                "category": str(raw["category"]),
                "l2-category": str(raw["subcategory"]),
                "visual_input": visual_input,
                "set_id": str(raw["set_id"]),
                "figure_id": str(raw["figure_id"]),
                "question_id": str(raw["question_id"]),
                "sample_note": str(raw.get("sample_note", "")),
                "answer_details": str(raw.get("gt_answer_details", "")),
                "image_is_placeholder": image_is_placeholder,
            }
        )
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
    parser.add_argument("--dataset", choices=("mathvista", "blink", "mmvp", "hallusion"), required=True)
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
    elif args.dataset == "blink":
        sources = sorted(args.source.glob("*/val-*.parquet"))
        if not sources:
            raise FileNotFoundError(f"no BLINK validation parquet files under {args.source}")
        rows = prepare_blink_frames((pd.read_parquet(path) for path in sources), args.image_dir)
        deviations = {}
    elif args.dataset == "mmvp":
        csv_path = args.source / "Questions.csv" if args.source.is_dir() else args.source
        image_root = args.source / "MMVP Images" if args.source.is_dir() else args.source.parent / "MMVP Images"
        sources = [csv_path]
        rows = prepare_mmvp_csv(csv_path, image_root)
        write_external_image_reference(args.image_dir, image_root)
        deviations = {"official_pair_order_preserved": True}
    else:
        annotation_path = args.source / "HallusionBench.json"
        sources = [annotation_path]
        rows = prepare_hallusion_json(args.source, args.image_dir)
        deviations = {
            "text_only_rows_use_deterministic_blank_image": sum(row["image_is_placeholder"] for row in rows),
            "case_insensitive_image_suffix_resolution": True,
        }
    payload = _write_outputs(rows, sources, args.output, args.metadata_output, args.dataset, deviations)
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
