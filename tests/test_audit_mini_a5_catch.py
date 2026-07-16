from __future__ import annotations

from pathlib import Path

from PIL import Image

from scripts.audit_mini_a5_catch import (
    audit_identity_disjointness,
    audit_pair_semantics,
    recorded_zero_overlap_is_complete,
)
from src.fliptrack.build_mini_a5_catch import CATCH_TEMPLATE_IDS, SCHEMA_VERSION
from src.fliptrack.schema import sha256_file


def _pair(tmp_path: Path) -> dict:
    image_a = tmp_path / "image_a.png"
    image_b = tmp_path / "image_b.png"
    mask_a = tmp_path / "mask_a.png"
    mask_b = tmp_path / "mask_b.png"
    source_a = Image.new("RGB", (720, 520), "white")
    source_b = source_a.copy()
    source_b.putpixel((300, 300), (0, 0, 0))
    source_a.save(image_a)
    source_b.save(image_b)
    mask = Image.new("L", (720, 520), 0)
    mask.putpixel((300, 300), 255)
    mask.save(mask_a)
    mask.save(mask_b)
    return {
        "schema_version": SCHEMA_VERSION,
        "pair_group_uid": "catch-1",
        "template_id": CATCH_TEMPLATE_IDS[0],
        "answer_a": "K7Q",
        "answer_b": "K7Q",
        "image_a_path": str(image_a),
        "image_b_path": str(image_b),
        "changed_region_mask_a": str(mask_a),
        "changed_region_mask_b": str(mask_b),
        "image_a_sha256": sha256_file(image_a),
        "image_b_sha256": sha256_file(image_b),
        "mask_sha256": sha256_file(mask_a),
        "provenance": {
            "answer_pointing_cue": False,
            "selection_on_model_performance": False,
        },
        "verifier_results": {
            "target_fact_a": "K7Q",
            "target_fact_b": "K7Q",
            "answer_preserved": True,
            "target_fact_preserved": True,
            "target_region_xyxy": [10, 10, 30, 30],
            "target_region_pixel_invariant": True,
            "exact_by_construction": True,
            "changed_mask_is_exact_pixel_diff": True,
        },
    }


def test_answer_preserving_target_invariant_pair_passes(tmp_path: Path) -> None:
    assert audit_pair_semantics(_pair(tmp_path), tmp_path) == []


def test_adversarial_answer_change_is_rejected(tmp_path: Path) -> None:
    pair = _pair(tmp_path)
    pair["answer_b"] = "WRONG"
    errors = audit_pair_semantics(pair, tmp_path)
    assert any("answer is not nonempty and preserved" in error for error in errors)
    assert any("target facts do not equal" in error for error in errors)


def test_adversarial_nuisance_edit_inside_target_region_is_rejected(
    tmp_path: Path,
) -> None:
    pair = _pair(tmp_path)
    image_b = Path(pair["image_b_path"])
    source = Image.open(image_b).convert("RGB")
    source.putpixel((20, 20), (0, 0, 0))
    source.save(image_b)
    pair["image_b_sha256"] = sha256_file(image_b)
    mask = Image.new("L", (720, 520), 0)
    mask.putpixel((20, 20), 255)
    mask.putpixel((300, 300), 255)
    for field in ("changed_region_mask_a", "changed_region_mask_b"):
        mask.save(pair[field])
    pair["mask_sha256"] = sha256_file(Path(pair["changed_region_mask_a"]))
    errors = audit_pair_semantics(pair, tmp_path)
    assert any("changes the queried pixel region" in error for error in errors)


def test_adversarial_source_overlap_is_rejected() -> None:
    catch = {
        "template_ids": {"catch-template"},
        "pair_ids": {"reused-pair"},
        "image_hashes": {"catch-image"},
    }
    training = {
        "template_ids": {"train-template"},
        "pair_ids": {"reused-pair"},
        "image_hashes": {"train-image"},
    }
    evaluation = {
        "template_ids": {"catch-template"},
        "pair_ids": {"eval-pair"},
        "image_hashes": {"eval-image"},
    }
    overlaps, errors = audit_identity_disjointness(catch, training, evaluation)
    assert overlaps["training"]["pair_ids"] == ["reused-pair"]
    assert overlaps["evaluation"]["template_ids"] == ["catch-template"]
    assert len(errors) == 2


def test_adversarial_missing_overlap_accounting_is_not_vacuously_zero() -> None:
    assert recorded_zero_overlap_is_complete({}) is False
    complete = {
        source: {field: 0 for field in ("template_ids", "pair_ids", "image_hashes")}
        for source in ("training_overlap", "evaluation_overlap")
    }
    assert recorded_zero_overlap_is_complete(complete) is True
