from __future__ import annotations

import ast
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from PIL import Image
from scipy.fft import dctn


SCHEMA_VERSION = "blind-gains.decon-records.v1"
DEFAULT_THRESHOLDS = {
    "phash_remove_max": 6,
    "phash_inspect_max": 10,
    "image_embedding_remove_min": 0.95,
    "image_embedding_inspect_min": 0.90,
    "text_jaccard_remove_min": 0.80,
    "text_jaccard_inspect_min": 0.70,
    "text_embedding_remove_min": 0.95,
    "text_embedding_inspect_min": 0.90,
    "ocr_char5_remove_min": 0.90,
    "ocr_char5_inspect_min": 0.75,
    "ocr_min_compact_chars": 8,
    "ocr_min_tokens_or_lines": 2,
}


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value)).casefold().replace("<image>", " ")
    text = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE)
    return " ".join(text.split())


def word_ngrams(value: Any, n: int = 5) -> frozenset[str]:
    tokens = normalize_text(value).split()
    if not tokens:
        return frozenset()
    if len(tokens) < n:
        return frozenset({" ".join(tokens)})
    return frozenset(" ".join(tokens[index : index + n]) for index in range(len(tokens) - n + 1))


def jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def _bits_to_int(bits: np.ndarray) -> int:
    value = 0
    for bit in bits.reshape(-1):
        value = (value << 1) | int(bool(bit))
    return value


def phash(path: str | Path) -> int:
    with Image.open(path) as opened:
        gray = np.asarray(opened.convert("L").resize((32, 32), Image.Resampling.LANCZOS), dtype=np.float32)
    coefficients = dctn(gray, type=2, norm="ortho")[:8, :8]
    median = float(np.median(coefficients.reshape(-1)[1:]))
    return _bits_to_int(coefficients > median)


def dhash(path: str | Path) -> int:
    with Image.open(path) as opened:
        gray = np.asarray(opened.convert("L").resize((9, 8), Image.Resampling.LANCZOS), dtype=np.float32)
    return _bits_to_int(gray[:, 1:] > gray[:, :-1])


def hamming(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def _record(
    dataset: str,
    split: str,
    item_id: Any,
    image_index: int,
    image_path: Any,
    question: Any,
    answer: Any,
    provenance_id: Any = None,
    image_sha256: str | None = None,
    image_applicable: bool = True,
) -> dict[str, Any]:
    path = Path(str(image_path))
    if not path.is_file():
        raise FileNotFoundError(path)
    item_id = str(item_id)
    return {
        "schema_version": SCHEMA_VERSION,
        "record_id": f"{dataset}:{split}:{item_id}:image{image_index}",
        "dataset": dataset,
        "split": split,
        "item_id": item_id,
        "image_index": image_index,
        "image_path": str(path),
        "image_sha256": image_sha256 or sha256_file(path),
        "image_applicable": image_applicable,
        "question": str(question),
        "answer": str(answer),
        "provenance_id": None if provenance_id is None else str(provenance_id),
    }


def load_geometry3k_records(manifest: str | Path, split: str = "train") -> list[dict[str, Any]]:
    records = []
    with Path(manifest).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["split"] != split:
                continue
            for image_index, image in enumerate(row["images"]):
                records.append(
                    _record(
                        dataset="geometry3k",
                        split=split,
                        item_id=row["row_index"],
                        image_index=image_index,
                        image_path=image["path"],
                        image_sha256=image["sha256"],
                        question=row["problem"],
                        answer=row["answer"],
                        provenance_id=f"hiyouga/geometry3k:{split}:{row['row_index']}",
                    )
                )
    return records


def _parse_paths(value: Any) -> list[str]:
    if isinstance(value, str) and value.strip().startswith("["):
        parsed = ast.literal_eval(value)
        return [str(item) for item in parsed]
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    return [str(value)]


def load_layer1_records(
    mmstar_tsv: str | Path,
    mmstar_image_root: str | Path,
    mathvista_tsv: str | Path,
    blink_tsv: str | Path,
    mmvp_tsv: str | Path | None = None,
    hallusion_tsv: str | Path | None = None,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    mmstar = pd.read_csv(mmstar_tsv, sep="\t")
    for row in mmstar.to_dict(orient="records"):
        index = str(row["index"])
        records.append(
            _record(
                dataset="mmstar",
                split="test",
                item_id=index,
                image_index=0,
                image_path=Path(mmstar_image_root) / f"{index}.png",
                question=row["question"],
                answer=row["answer"],
                provenance_id=f"{row.get('bench', 'unknown')}:{index}",
            )
        )

    mathvista = pd.read_csv(mathvista_tsv, sep="\t")
    for row in mathvista.to_dict(orient="records"):
        records.append(
            _record(
                dataset="mathvista",
                split="testmini",
                item_id=row["index"],
                image_index=0,
                image_path=row["image_path"],
                question=row["question"],
                answer=row["answer"],
                provenance_id=f"MathVista:testmini:{row.get('source_pid', row['index'])}",
            )
        )

    blink = pd.read_csv(blink_tsv, sep="\t")
    for row in blink.to_dict(orient="records"):
        for image_index, path in enumerate(_parse_paths(row["image_path"])):
            records.append(
                _record(
                    dataset="blink",
                    split="validation",
                    item_id=row["index"],
                    image_index=image_index,
                    image_path=path,
                    question=row["question"],
                    answer=row["answer"],
                    provenance_id=f"BLINK:{row.get('source_id', row['index'])}:image{image_index}",
                )
            )

    if mmvp_tsv is not None:
        mmvp = pd.read_csv(mmvp_tsv, sep="\t")
        for row in mmvp.to_dict(orient="records"):
            records.append(
                _record(
                    dataset="mmvp",
                    split="test",
                    item_id=row["index"],
                    image_index=0,
                    image_path=row["image_path"],
                    question=row["question"],
                    answer=row["answer"],
                    provenance_id=f"MMVP:{row.get('source_index', row['index'])}",
                )
            )

    if hallusion_tsv is not None:
        hallusion = pd.read_csv(hallusion_tsv, sep="\t")
        for row in hallusion.to_dict(orient="records"):
            placeholder = str(row.get("image_is_placeholder", "false")).strip().casefold() == "true"
            records.append(
                _record(
                    dataset="hallusionbench",
                    split="test",
                    item_id=row["index"],
                    image_index=0,
                    image_path=row["image_path"],
                    question=row["question"],
                    answer=row["answer"],
                    provenance_id=(
                        f"HallusionBench:{row.get('category', 'unknown')}:"
                        f"{row.get('set_id', 'unknown')}:{row.get('figure_id', 'unknown')}:"
                        f"{row.get('question_id', 'unknown')}"
                    ),
                    image_applicable=not placeholder,
                )
            )
    return records


def enrich_records(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    image_cache: dict[str, tuple[int, int]] = {}
    enriched = []
    for raw in records:
        row = dict(raw)
        digest = row["image_sha256"]
        image_applicable = bool(row.get("image_applicable", True))
        if image_applicable and digest not in image_cache:
            image_cache[digest] = (phash(row["image_path"]), dhash(row["image_path"]))
        p_value, d_value = image_cache[digest] if image_applicable else (None, None)
        row.update(
            {
                "phash64": f"{p_value:016x}" if p_value is not None else None,
                "dhash64": f"{d_value:016x}" if d_value is not None else None,
                "question_normalized": normalize_text(row["question"]),
                "question_answer_normalized": normalize_text(f"{row['question']} {row['answer']}"),
            }
        )
        enriched.append(row)
    return enriched


def write_jsonl(rows: Iterable[dict[str, Any]], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def embedding_entities(records: Iterable[dict[str, Any]], kind: str) -> list[tuple[str, str]]:
    if kind == "image":
        by_hash: dict[str, str] = {}
        for row in records:
            if not row.get("image_applicable", True):
                continue
            by_hash.setdefault(row["image_sha256"], row["image_path"])
        return sorted(by_hash.items())
    if kind == "text":
        return sorted((row["record_id"], str(row["question"])) for row in records)
    raise ValueError(f"unsupported embedding kind: {kind}")


def compare_hash_and_text(
    train_rows: list[dict[str, Any]],
    eval_rows: list[dict[str, Any]],
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    edges: dict[tuple[str, str], dict[str, Any]] = {}
    action_rank = {"none": 0, "inspect": 1, "remove": 2}

    def add_signal(train: dict[str, Any], evaluation: dict[str, Any], signal: str, value: Any, action: str) -> None:
        key = (train["record_id"], evaluation["record_id"])
        edge = edges.setdefault(
            key,
            {
                "train_record_id": key[0],
                "eval_record_id": key[1],
                "train_dataset": train["dataset"],
                "eval_dataset": evaluation["dataset"],
                "action": "none",
                "signals": {},
            },
        )
        edge["signals"][signal] = value
        if action_rank[action] > action_rank[edge["action"]]:
            edge["action"] = action

    eval_by_sha: dict[str, list[dict[str, Any]]] = defaultdict(list)
    eval_by_question: dict[str, list[dict[str, Any]]] = defaultdict(list)
    eval_by_question_answer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in eval_rows:
        if row.get("image_applicable", True):
            eval_by_sha[row["image_sha256"]].append(row)
        eval_by_question[row["question_normalized"]].append(row)
        eval_by_question_answer[row["question_answer_normalized"]].append(row)

    for train in train_rows:
        for evaluation in eval_by_sha[train["image_sha256"]]:
            add_signal(train, evaluation, "image_sha256_exact", True, "remove")
        for evaluation in eval_by_question_answer[train["question_answer_normalized"]]:
            add_signal(train, evaluation, "question_answer_exact", True, "remove")
        for evaluation in eval_by_question[train["question_normalized"]]:
            add_signal(train, evaluation, "question_exact", True, "inspect")

    eval_hashes = [
        (row, int(row["phash64"], 16), int(row["dhash64"], 16))
        for row in eval_rows
        if row.get("image_applicable", True)
    ]
    inspect_max = int(thresholds["phash_inspect_max"])
    remove_max = int(thresholds["phash_remove_max"])
    for train in train_rows:
        train_p = int(train["phash64"], 16)
        train_d = int(train["dhash64"], 16)
        for evaluation, eval_p, eval_d in eval_hashes:
            p_distance = hamming(train_p, eval_p)
            d_distance = hamming(train_d, eval_d)
            minimum = min(p_distance, d_distance)
            if minimum <= inspect_max:
                action = "remove" if minimum <= remove_max else "inspect"
                add_signal(
                    train,
                    evaluation,
                    "perceptual_hash",
                    {"phash_hamming": p_distance, "dhash_hamming": d_distance, "minimum": minimum},
                    action,
                )

    eval_shingles = [word_ngrams(row["question"]) for row in eval_rows]
    inverted: dict[str, list[int]] = defaultdict(list)
    for index, shingles in enumerate(eval_shingles):
        for shingle in shingles:
            inverted[shingle].append(index)
    inspect_min = float(thresholds["text_jaccard_inspect_min"])
    remove_min = float(thresholds["text_jaccard_remove_min"])
    for train in train_rows:
        shingles = word_ngrams(train["question"])
        overlaps: Counter[int] = Counter()
        for shingle in shingles:
            overlaps.update(inverted.get(shingle, []))
        for index in overlaps:
            score = jaccard(shingles, eval_shingles[index])
            if score >= inspect_min:
                action = "remove" if score >= remove_min else "inspect"
                add_signal(train, eval_rows[index], "question_5gram_jaccard", score, action)

    output_edges = sorted(edges.values(), key=lambda row: (row["train_record_id"], row["eval_record_id"]))
    return {
        "schema_version": "blind-gains.decon-comparison.v1",
        "thresholds": thresholds,
        "n_train_records": len(train_rows),
        "n_eval_records": len(eval_rows),
        "n_candidate_edges": len(output_edges),
        "action_counts": dict(sorted(Counter(edge["action"] for edge in output_edges).items())),
        "signal_counts": dict(sorted(Counter(signal for edge in output_edges for signal in edge["signals"]).items())),
        "candidate_edges": output_edges,
        "pending_layers": ["dinov2_image_embedding", "ocr_text_overlap", "bge_text_embedding"],
        "template_disjointness_rule": (
            "Future CP training template IDs must be disjoint from every FlipTrack evaluation template ID."
        ),
    }
