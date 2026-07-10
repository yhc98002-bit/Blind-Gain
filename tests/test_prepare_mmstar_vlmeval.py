from __future__ import annotations

import csv
from pathlib import Path

from scripts.prepare_mmstar_vlmeval import normalize_tsv, parse_question_options


def test_parse_question_options_preserves_internal_commas() -> None:
    stem, options = parse_question_options(
        "Which description?\nOptions: A: red, white, and blue, B: green field, C: two birds, flying, D: none"
    )
    assert stem == "Which description?"
    assert options == {
        "A": "red, white, and blue",
        "B": "green field",
        "C": "two birds, flying",
        "D": "none",
    }


def test_parse_question_options_accepts_line_choices_and_three_options() -> None:
    stem, options = parse_question_options(
        "Hint: choose one.\nQuestion: Which?\nChoices:\n(A) alpha\n(B) beta\n(C) gamma"
    )
    assert stem == "Hint: choose one.\nQuestion: Which?"
    assert options == {"A": "alpha", "B": "beta", "C": "gamma"}


def test_normalize_tsv_splits_choices_without_changing_image_payload(tmp_path: Path) -> None:
    source = tmp_path / "source.tsv"
    fields = ["index", "question", "answer", "category", "l2_category", "bench", "image"]
    with source.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for index in range(1500):
            writer.writerow(
                {
                    "index": index,
                    "question": "Question?\nOptions: A: alpha, B: beta, C: gamma, D: delta",
                    "answer": "B",
                    "category": "category",
                    "l2_category": "detail",
                    "bench": "bench",
                    "image": "x" * 140_000 if index == 0 else "base64-payload",
                }
            )
    output = tmp_path / "normalized.tsv"
    metadata = tmp_path / "metadata.json"
    payload = normalize_tsv(source, output, metadata)
    with output.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    assert payload["n_rows"] == 1500
    assert rows[0]["question"] == "Question?"
    assert rows[0]["B"] == "beta"
    assert len(rows[0]["image"]) == 140_000
