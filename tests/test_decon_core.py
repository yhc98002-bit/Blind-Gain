from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from PIL import Image, ImageDraw

from src.decon.core import (
    compare_hash_and_text,
    dhash,
    embedding_entities,
    enrich_records,
    hamming,
    normalize_text,
    phash,
    load_layer1_records,
    load_virl39k_records,
    word_ngrams,
)
from src.decon.embedding_compare import cosine_candidates, merge_embedding_signals
from src.decon.ocr import merge_ocr_signals, ocr_char_ngrams
from src.decon.ocr_text import normalize_ocr_text


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
    assert normalize_ocr_text("<image>  Find X! ") == "find x"
    assert word_ngrams("one two three four five six") == {"one two three four five", "two three four five six"}
    assert word_ngrams("Find x") == set()


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


def test_generic_exact_question_answer_is_inspection_only_without_visual_corroboration(
    tmp_path: Path,
) -> None:
    train_image = tmp_path / "train.png"
    eval_image = tmp_path / "eval.png"
    _image(train_image)
    Image.effect_noise((96, 72), 80).convert("RGB").save(eval_image)
    train = enrich_records([_row("train", "geometry3k", train_image, "Find x", "5")])
    evaluation = enrich_records([_row("eval", "geometry3k", eval_image, "Find x", "5")])
    evaluation[0]["phash64"] = "ffffffffffffffff"
    evaluation[0]["dhash64"] = "ffffffffffffffff"
    train[0]["phash64"] = "0000000000000000"
    train[0]["dhash64"] = "0000000000000000"

    result = compare_hash_and_text(train, evaluation)

    assert result["schema_version"] == "blind-gains.decon-comparison.v2"
    assert len(result["candidate_edges"]) == 1
    edge = result["candidate_edges"][0]
    assert edge["action"] == "inspect"
    assert edge["signals"]["question_answer_exact"] == {
        "exact": True,
        "distinctive_question": False,
    }
    assert "question_5gram_jaccard" not in edge["signals"]


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


def test_virl_loader_preserves_item_linkage_and_strata_for_multi_image_rows(tmp_path: Path) -> None:
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    _image(image_dir / "a.png")
    _image(image_dir / "b.png", offset=2)
    table = pa.Table.from_pylist(
        [
            {
                "question": "<image><image> Which diagram is symmetric?",
                "answer": "\\boxed{A}",
                "PassRate_32BTrained": 0.5,
                "PassRate_7BBase": 0.25,
                "category": "Spatial Reasoning",
                "source": "fixture-source",
                "qid": "fixture-qid",
                "image": ["images/a.png", "images/b.png"],
            }
        ]
    )
    parquet = tmp_path / "virl.parquet"
    pq.write_table(table, parquet)

    records = load_virl39k_records(parquet, tmp_path)

    assert [record["record_id"] for record in records] == [
        "virl39k:train:fixture-qid:image0",
        "virl39k:train:fixture-qid:image1",
    ]
    assert {record["item_id"] for record in records} == {"fixture-qid"}
    assert {record["source"] for record in records} == {"fixture-source"}
    assert {record["category"] for record in records} == {"Spatial Reasoning"}


def test_virl_loader_rejects_image_free_rows_in_decon_path(tmp_path: Path) -> None:
    table = pa.Table.from_pylist(
        [
            {
                "question": "No image",
                "answer": "1",
                "PassRate_32BTrained": 0.0,
                "PassRate_7BBase": 0.0,
                "category": "fixture",
                "source": "fixture",
                "qid": "missing-images",
                "image": [],
            }
        ]
    )
    parquet = tmp_path / "virl.parquet"
    pq.write_table(table, parquet)

    with pytest.raises(ValueError, match="has no images"):
        load_virl39k_records(parquet, tmp_path)


def test_layer1_loader_expands_mmmu_multi_image_rows(tmp_path: Path) -> None:
    images = tmp_path / "images"
    images.mkdir()
    paths = []
    for name, offset in (("a.png", 0), ("b.png", 2)):
        path = images / name
        _image(path, offset=offset)
        paths.append(str(path))

    def write_tsv(name: str, rows: list[dict[str, object]]) -> Path:
        path = tmp_path / name
        pd.DataFrame(rows).to_csv(path, sep="\t", index=False)
        return path

    mmstar = write_tsv("mmstar.tsv", [{"index": 1, "question": "q", "answer": "a"}])
    _image(tmp_path / "1.png")
    mathvista = write_tsv(
        "mathvista.tsv",
        [{"index": 1, "image_path": paths[0], "question": "q", "answer": "a"}],
    )
    blink = write_tsv(
        "blink.tsv",
        [{"index": 1, "image_path": paths[0], "question": "q", "answer": "a"}],
    )
    mathverse = write_tsv(
        "mathverse.tsv",
        [{"index": 1, "image_path": paths[0], "question": "q", "answer": "a"}],
    )
    mmmu = write_tsv(
        "mmmu.tsv",
        [
            {
                "index": "multi",
                "image_path": repr(paths),
                "question": "compare both",
                "answer": "A",
                "split": "validation",
            }
        ],
    )

    records = load_layer1_records(
        mmstar,
        tmp_path,
        mathvista,
        blink,
        mathverse_tsv=mathverse,
        mmmu_tsv=mmmu,
    )
    mmmu_records = [record for record in records if record["dataset"] == "mmmu"]

    assert [record["record_id"] for record in mmmu_records] == [
        "mmmu:validation:multi:image0",
        "mmmu:validation:multi:image1",
    ]


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


def test_same_dataset_dino_similarity_requires_corroboration(tmp_path: Path) -> None:
    train_image = tmp_path / "train.png"
    eval_image = tmp_path / "eval.png"
    _image(train_image)
    Image.new("RGB", (96, 72), "yellow").save(eval_image)
    train = enrich_records(
        [_row("train", "geometry3k", train_image, "Find the missing triangle angle", "40")]
    )
    evaluation = enrich_records(
        [_row("eval", "geometry3k", eval_image, "Compute the circle diameter shown", "12")]
    )
    image_features = {
        train[0]["image_sha256"]: np.asarray([1.0, 0.0], dtype=np.float32),
        evaluation[0]["image_sha256"]: np.asarray([1.0, 0.0], dtype=np.float32),
    }
    text_features = {
        "train": np.asarray([1.0, 0.0], dtype=np.float32),
        "eval": np.asarray([0.0, 1.0], dtype=np.float32),
    }

    result = merge_embedding_signals(
        {"candidate_edges": []}, train, evaluation, image_features, text_features, device="cpu"
    )

    assert result["candidate_edges"][0]["signals"] == {"dinov2_cosine": 1.0}
    assert result["candidate_edges"][0]["action"] == "inspect"


def test_generic_bge_similarity_cannot_bypass_distinctiveness_guard(tmp_path: Path) -> None:
    train_image = tmp_path / "train.png"
    eval_image = tmp_path / "eval.png"
    _image(train_image)
    Image.new("RGB", (96, 72), "green").save(eval_image)
    train = enrich_records([_row("train", "geometry3k", train_image, "Find x", "5")])
    evaluation = enrich_records([_row("eval", "geometry3k", eval_image, "Find x", "9")])
    image_features = {
        train[0]["image_sha256"]: np.asarray([1.0, 0.0], dtype=np.float32),
        evaluation[0]["image_sha256"]: np.asarray([0.0, 1.0], dtype=np.float32),
    }
    text_features = {
        "train": np.asarray([1.0, 0.0], dtype=np.float32),
        "eval": np.asarray([1.0, 0.0], dtype=np.float32),
    }

    result = merge_embedding_signals(
        {"candidate_edges": []}, train, evaluation, image_features, text_features, device="cpu"
    )

    assert result["candidate_edges"][0]["signals"] == {"bge_question_cosine": 1.0}
    assert result["candidate_edges"][0]["action"] == "inspect"


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


def test_same_dataset_text_similarity_is_inspection_only_after_final_policy(
    tmp_path: Path,
) -> None:
    train_image = tmp_path / "train.png"
    eval_image = tmp_path / "eval.png"
    _image(train_image)
    Image.new("RGB", (96, 72), "purple").save(eval_image)
    train = enrich_records(
        [_row("train", "geometry3k", train_image, "Find the area rounded to nearest tenth", "12")]
    )
    evaluation = enrich_records(
        [_row("eval", "geometry3k", eval_image, "Find the area rounded to nearest tenth", "42")]
    )
    baseline = {
        "candidate_edges": [
            {
                "train_record_id": "train",
                "eval_record_id": "eval",
                "train_dataset": "geometry3k",
                "eval_dataset": "geometry3k",
                "action": "remove",
                "signals": {"bge_question_cosine": 0.99, "question_5gram_jaccard": 1.0},
            }
        ],
        "completed_layers": ["bge_text_embedding"],
        "pending_layers": ["ocr_text_overlap"],
    }
    entries = [
        {"image_sha256": train[0]["image_sha256"], "text": "", "line_count": 0},
        {"image_sha256": evaluation[0]["image_sha256"], "text": "", "line_count": 0},
    ]

    result = merge_ocr_signals(baseline, train, evaluation, entries)

    assert result["schema_version"] == "blind-gains.decon-comparison.v4"
    assert result["candidate_edges"][0]["action"] == "inspect"
    assert result["candidate_edges"][0]["same_dataset_policy"] == "remove_downgraded_to_inspect"


def test_same_dataset_distinctive_exact_question_answer_preserves_removal(
    tmp_path: Path,
) -> None:
    train_image = tmp_path / "train.png"
    eval_image = tmp_path / "eval.png"
    _image(train_image)
    Image.new("RGB", (96, 72), "orange").save(eval_image)
    train = enrich_records(
        [_row("train", "geometry3k", train_image, "Find the exact missing exterior angle", "72")]
    )
    evaluation = enrich_records(
        [_row("eval", "geometry3k", eval_image, "Find the exact missing exterior angle", "72")]
    )
    baseline = {
        "candidate_edges": [
            {
                "train_record_id": "train",
                "eval_record_id": "eval",
                "train_dataset": "geometry3k",
                "eval_dataset": "geometry3k",
                "action": "remove",
                "signals": {
                    "question_answer_exact": {
                        "exact": True,
                        "distinctive_question": True,
                    }
                },
            }
        ],
        "completed_layers": [],
        "pending_layers": ["ocr_text_overlap"],
    }
    entries = [
        {"image_sha256": train[0]["image_sha256"], "text": "", "line_count": 0},
        {"image_sha256": evaluation[0]["image_sha256"], "text": "", "line_count": 0},
    ]

    result = merge_ocr_signals(baseline, train, evaluation, entries)

    assert result["candidate_edges"][0]["action"] == "remove"
    assert result["candidate_edges"][0]["same_dataset_policy"] == (
        "distinctive_exact_question_answer"
    )
