from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from src.decon.core import (
    compare_hash_and_text,
    dhash,
    embedding_entities,
    enrich_records,
    hamming,
    normalize_text,
    phash,
    word_ngrams,
)
from src.decon.embedding_compare import cosine_candidates, merge_embedding_signals
from src.decon.ocr import merge_ocr_signals, ocr_char_ngrams


def _image(path: Path, offset: int = 0) -> None:
    canvas = Image.new("RGB", (96, 72), "white")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((15 + offset, 20, 60 + offset, 50), fill="black")
    canvas.save(path)


def _row(record_id: str, dataset: str, path: Path, question: str, answer: str) -> dict[str, object]:
    return {
        "record_id": record_id,
        "dataset": dataset,
        "split": "train" if dataset == "geometry3k" else "test",
        "item_id": record_id,
        "image_index": 0,
        "image_path": str(path),
        "image_sha256": __import__("hashlib").sha256(path.read_bytes()).hexdigest(),
        "question": question,
        "answer": answer,
        "provenance_id": record_id,
    }


def test_text_normalization_and_word_fivegrams_are_deterministic() -> None:
    assert normalize_text("<image>  Find X! ") == "find x"
    assert word_ngrams("one two three four five six") == {"one two three four five", "two three four five six"}


def test_perceptual_hashes_retain_near_identical_render(tmp_path: Path) -> None:
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    _image(first)
    _image(second, offset=1)
    assert hamming(phash(first), phash(second)) <= 10
    assert hamming(dhash(first), dhash(second)) <= 10


def test_hash_text_comparison_flags_planted_duplicates_and_ignores_random_negative(tmp_path: Path) -> None:
    train_image = tmp_path / "train.png"
    duplicate_image = tmp_path / "duplicate.png"
    negative_image = tmp_path / "negative.png"
    _image(train_image)
    Image.open(train_image).save(duplicate_image, compress_level=1)
    Image.new("RGB", (96, 72), "red").save(negative_image)
    train = enrich_records([_row("train", "geometry3k", train_image, "Find the missing angle in triangle ABC", "40")])
    evaluation = enrich_records(
        [
            _row("duplicate", "mmstar", duplicate_image, "Find the missing angle in triangle ABC", "40"),
            _row("negative", "mmstar", negative_image, "Which animal is shown in the photograph?", "cat"),
        ]
    )
    result = compare_hash_and_text(train, evaluation)
    edge_by_eval = {edge["eval_record_id"]: edge for edge in result["candidate_edges"]}
    assert edge_by_eval["duplicate"]["action"] == "remove"
    assert "image_sha256_exact" not in edge_by_eval["duplicate"]["signals"]
    assert "perceptual_hash" in edge_by_eval["duplicate"]["signals"]
    assert "negative" not in edge_by_eval


def test_embedding_entities_deduplicate_images_but_not_questions(tmp_path: Path) -> None:
    image = tmp_path / "shared.png"
    _image(image)
    rows = enrich_records(
        [
            _row("first", "geometry3k", image, "Question one", "1"),
            _row("second", "geometry3k", image, "Question two", "2"),
        ]
    )
    assert len(embedding_entities(rows, "image")) == 1
    assert [identifier for identifier, _ in embedding_entities(rows, "text")] == ["first", "second"]


def test_text_only_placeholder_is_excluded_from_image_signals_but_kept_for_text(tmp_path: Path) -> None:
    image = tmp_path / "blank.png"
    Image.new("RGB", (32, 32), "white").save(image)
    row = _row("text-only", "hallusionbench", image, "Is this true?", "Yes")
    row["image_applicable"] = False
    enriched = enrich_records([row])
    assert enriched[0]["phash64"] is None
    assert embedding_entities(enriched, "image") == []
    assert embedding_entities(enriched, "text") == [("text-only", "Is this true?")]


def test_embedding_comparison_flags_only_high_cosine_candidate(tmp_path: Path) -> None:
    train_image = tmp_path / "train.png"
    eval_image = tmp_path / "eval.png"
    negative_image = tmp_path / "negative.png"
    _image(train_image)
    _image(eval_image, offset=4)
    Image.new("RGB", (96, 72), "blue").save(negative_image)
    train = enrich_records([_row("train", "geometry3k", train_image, "Find x", "1")])
    evaluation = enrich_records(
        [
            _row("eval", "mmstar", eval_image, "Find y", "2"),
            _row("negative", "mmstar", negative_image, "Name this", "blue"),
        ]
    )
    image_features = {
        train[0]["image_sha256"]: np.asarray([1.0, 0.0], dtype=np.float32),
        evaluation[0]["image_sha256"]: np.asarray([0.99, 0.01], dtype=np.float32),
        evaluation[1]["image_sha256"]: np.asarray([0.0, 1.0], dtype=np.float32),
    }
    text_features = {
        "train": np.asarray([1.0, 0.0], dtype=np.float32),
        "eval": np.asarray([0.0, 1.0], dtype=np.float32),
        "negative": np.asarray([-1.0, 0.0], dtype=np.float32),
    }
    result = merge_embedding_signals(
        {"candidate_edges": []}, train, evaluation, image_features, text_features, device="cpu"
    )
    assert len(result["candidate_edges"]) == 1
    assert result["candidate_edges"][0]["eval_record_id"] == "eval"
    assert result["candidate_edges"][0]["action"] == "remove"


def test_ocr_overlap_is_inspection_only_without_image_corroboration(tmp_path: Path) -> None:
    train_image = tmp_path / "train.png"
    eval_image = tmp_path / "eval.png"
    _image(train_image)
    _image(eval_image, offset=4)
    train = enrich_records([_row("train", "geometry3k", train_image, "Find x", "1")])
    evaluation = enrich_records([_row("eval", "mmstar", eval_image, "Find y", "2")])
    entries = [
        {"image_sha256": train[0]["image_sha256"], "text": "Triangle ABC angle 42", "line_count": 2},
        {"image_sha256": evaluation[0]["image_sha256"], "text": "Triangle ABC angle 42", "line_count": 2},
    ]
    result = merge_ocr_signals(
        {"candidate_edges": [], "completed_layers": [], "pending_layers": ["ocr_text_overlap"]},
        train,
        evaluation,
        entries,
    )
    assert result["pending_layers"] == []
    assert result["candidate_edges"][0]["action"] == "inspect"
    assert result["candidate_edges"][0]["signals"]["ocr_char5_jaccard"]["exact"] is True


def test_ocr_overlap_upgrades_corroborated_image_match(tmp_path: Path) -> None:
    train_image = tmp_path / "train.png"
    eval_image = tmp_path / "eval.png"
    _image(train_image)
    _image(eval_image, offset=4)
    train = enrich_records([_row("train", "geometry3k", train_image, "Find x", "1")])
    evaluation = enrich_records([_row("eval", "mmstar", eval_image, "Find y", "2")])
    baseline = {
        "candidate_edges": [
            {
                "train_record_id": "train",
                "eval_record_id": "eval",
                "train_dataset": "geometry3k",
                "eval_dataset": "mmstar",
                "action": "inspect",
                "signals": {"dinov2_cosine": 0.93},
            }
        ],
        "completed_layers": ["dinov2_image_embedding"],
        "pending_layers": ["ocr_text_overlap"],
    }
    entries = [
        {"image_sha256": train[0]["image_sha256"], "text": "Triangle ABC angle 42", "line_count": 2},
        {"image_sha256": evaluation[0]["image_sha256"], "text": "Triangle ABC angle 42", "line_count": 2},
    ]
    result = merge_ocr_signals(baseline, train, evaluation, entries)
    assert result["candidate_edges"][0]["action"] == "remove"
    assert "ocr_text_overlap" in result["completed_layers"]


def test_ocr_short_generic_labels_do_not_create_edges(tmp_path: Path) -> None:
    train_image = tmp_path / "train.png"
    eval_image = tmp_path / "eval.png"
    _image(train_image)
    _image(eval_image, offset=4)
    train = enrich_records([_row("train", "geometry3k", train_image, "Find x", "1")])
    evaluation = enrich_records([_row("eval", "mmstar", eval_image, "Find y", "2")])
    entries = [
        {"image_sha256": train[0]["image_sha256"], "text": "A B C", "line_count": 1},
        {"image_sha256": evaluation[0]["image_sha256"], "text": "A B C", "line_count": 1},
    ]
    result = merge_ocr_signals(
        {"candidate_edges": [], "completed_layers": [], "pending_layers": ["ocr_text_overlap"]},
        train,
        evaluation,
        entries,
    )
    assert result["candidate_edges"] == []
    assert not ocr_char_ngrams("A B C")


def test_ocr_extraction_error_keeps_layer_pending(tmp_path: Path) -> None:
    image = tmp_path / "image.png"
    _image(image)
    train = enrich_records([_row("train", "geometry3k", image, "Find x", "1")])
    result = merge_ocr_signals(
        {"candidate_edges": [], "completed_layers": [], "pending_layers": ["ocr_text_overlap"]},
        train,
        [],
        [{"image_sha256": train[0]["image_sha256"], "text": "", "line_count": 0, "error": "decode"}],
    )
    assert result["pending_layers"] == ["ocr_text_overlap"]
    assert result["ocr_coverage"]["error_images"] == 1
