from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from src.decon.core import compare_hash_and_text, dhash, enrich_records, hamming, normalize_text, phash, word_ngrams


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
