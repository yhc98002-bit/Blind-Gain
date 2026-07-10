#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
import json
import random
from pathlib import Path

import numpy as np
from PIL import Image

from scripts.extract_decon_embeddings import image_embeddings, text_embeddings
from src.decon.calibration import select_distinct_negatives, threshold_summary
from src.decon.core import DEFAULT_THRESHOLDS, dhash, hamming, jaccard, phash, read_jsonl, word_ngrams


def transformed_copy(source: Path, target: Path) -> None:
    with Image.open(source) as opened:
        image = opened.convert("RGB")
    reduced = image.resize((max(32, image.width * 3 // 4), max(32, image.height * 3 // 4)), Image.Resampling.LANCZOS)
    restored = reduced.resize(image.size, Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    restored.save(buffer, format="JPEG", quality=85, optimize=True)
    buffer.seek(0)
    with Image.open(buffer) as recompressed:
        recompressed.convert("RGB").save(target, format="PNG", compress_level=6)


def _cosine_pairs(features: np.ndarray, left: list[int], right: list[int]) -> list[float]:
    values = features.astype(np.float32)
    values /= np.maximum(np.linalg.norm(values, axis=1, keepdims=True), 1e-12)
    return [float(np.dot(values[a], values[b])) for a, b in zip(left, right)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--transform-dir", type=Path, required=True)
    parser.add_argument("--dino-model", default="facebook/dinov2-small")
    parser.add_argument("--text-model", required=True)
    parser.add_argument("--sample-size", type=int, default=64)
    parser.add_argument("--seed", type=int, default=20260710)
    args = parser.parse_args()
    if args.output.exists() or args.transform_dir.exists():
        raise FileExistsError("refusing to overwrite decontamination calibration")

    rows = read_jsonl(args.records)
    by_hash = {}
    for row in rows:
        by_hash.setdefault(row["image_sha256"], row)
    candidates = list(by_hash.values())
    selected = random.Random(args.seed).sample(candidates, min(args.sample_size, len(candidates)))
    if len(selected) < 8:
        raise ValueError("decontamination calibration requires at least eight unique images")
    args.transform_dir.mkdir(parents=True)
    transformed_paths = []
    for index, row in enumerate(selected):
        path = args.transform_dir / f"near_duplicate_{index:04d}.png"
        transformed_copy(Path(row["image_path"]), path)
        transformed_paths.append(path)

    negative_rows = select_distinct_negatives(selected, candidates, args.seed + 1)
    phash_positive = []
    phash_negative = []
    for row, transformed, negative in zip(selected, transformed_paths, negative_rows):
        original_p, original_d = int(row["phash64"], 16), int(row["dhash64"], 16)
        phash_positive.append(min(hamming(original_p, phash(transformed)), hamming(original_d, dhash(transformed))))
        phash_negative.append(
            min(
                hamming(original_p, int(negative["phash64"], 16)),
                hamming(original_d, int(negative["dhash64"], 16)),
            )
        )

    image_entities = (
        [(f"original:{index}", row["image_path"]) for index, row in enumerate(selected)]
        + [(f"transformed:{index}", str(path)) for index, path in enumerate(transformed_paths)]
    )
    image_features = image_embeddings(image_entities, args.dino_model, batch_size=32)
    count = len(selected)
    dino_positive = _cosine_pairs(image_features, list(range(count)), list(range(count, 2 * count)))
    negative_image_entities = [(f"negative:{index}", row["image_path"]) for index, row in enumerate(negative_rows)]
    negative_image_features = image_embeddings(negative_image_entities, args.dino_model, batch_size=32)
    combined_image_features = np.concatenate([image_features[:count], negative_image_features], axis=0)
    dino_negative = _cosine_pairs(combined_image_features, list(range(count)), list(range(count, 2 * count)))

    original_questions = [str(row["question"]) for row in selected]
    positive_questions = [f"{question.rstrip()} Please solve the same problem carefully." for question in original_questions]
    text_entities = (
        [(f"original:{index}", value) for index, value in enumerate(original_questions)]
        + [(f"variant:{index}", value) for index, value in enumerate(positive_questions)]
    )
    text_features = text_embeddings(text_entities, args.text_model, batch_size=64)
    bge_positive = _cosine_pairs(text_features, list(range(count)), list(range(count, 2 * count)))
    negative_text_entities = [(f"negative:{index}", str(row["question"])) for index, row in enumerate(negative_rows)]
    negative_text_features = text_embeddings(negative_text_entities, args.text_model, batch_size=64)
    combined_text_features = np.concatenate([text_features[:count], negative_text_features], axis=0)
    bge_negative = _cosine_pairs(combined_text_features, list(range(count)), list(range(count, 2 * count)))
    jaccard_positive = [jaccard(word_ngrams(a), word_ngrams(b)) for a, b in zip(original_questions, positive_questions)]
    jaccard_negative = [
        jaccard(word_ngrams(question), word_ngrams(negative["question"]))
        for question, negative in zip(original_questions, negative_rows)
    ]

    result = {
        "schema_version": "blind-gains.decon-calibration.v1",
        "seed": args.seed,
        "sample_size": count,
        "source_records": str(args.records),
        "positive_definition": {
            "image": "75% downsample/upscale followed by JPEG quality 85 and PNG re-encode",
            "text": "same question with a semantically neutral solve-carefully suffix",
        },
        "negative_definition": (
            "seeded random Geometry3K pairs constrained to different image hashes, normalized questions, "
            "word-5-gram Jaccard below 0.3, and minimum pHash/dHash Hamming above 10"
        ),
        "phash_or_dhash_min_hamming": threshold_summary(
            phash_positive,
            phash_negative,
            DEFAULT_THRESHOLDS["phash_remove_max"],
            DEFAULT_THRESHOLDS["phash_inspect_max"],
            higher_is_duplicate=False,
        ),
        "dinov2_cosine": threshold_summary(
            dino_positive,
            dino_negative,
            DEFAULT_THRESHOLDS["image_embedding_remove_min"],
            DEFAULT_THRESHOLDS["image_embedding_inspect_min"],
            higher_is_duplicate=True,
        ),
        "question_5gram_jaccard": threshold_summary(
            jaccard_positive,
            jaccard_negative,
            DEFAULT_THRESHOLDS["text_jaccard_remove_min"],
            DEFAULT_THRESHOLDS["text_jaccard_inspect_min"],
            higher_is_duplicate=True,
        ),
        "bge_question_cosine": threshold_summary(
            bge_positive,
            bge_negative,
            DEFAULT_THRESHOLDS["text_embedding_remove_min"],
            DEFAULT_THRESHOLDS["text_embedding_inspect_min"],
            higher_is_duplicate=True,
        ),
        "models": {"image": args.dino_model, "text": args.text_model},
        "known_gap": "OCR overlap is not calibrated because no local OCR model is installed.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"sample_size": count, "output": str(args.output)}))


if __name__ == "__main__":
    main()
