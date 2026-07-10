from __future__ import annotations

from typing import Any, Iterable

from src.decon.calibration import threshold_summary
from src.decon.core import DEFAULT_THRESHOLDS, jaccard
from src.decon.ocr import ocr_char_ngrams, ocr_entry_eligible


def calibrate_ocr_pairs(
    pairs: Iterable[dict[str, Any]],
    entries: Iterable[dict[str, Any]],
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    by_hash = {str(entry["image_sha256"]): dict(entry) for entry in entries}
    positive_scores = []
    negative_scores = []
    total = 0
    for pair in pairs:
        total += 1
        source = by_hash.get(str(pair["source_image_sha256"]))
        positive = by_hash.get(str(pair["transformed_image_sha256"]))
        negative = by_hash.get(str(pair["negative_image_sha256"]))
        if source is not None and positive is not None and all(
            ocr_entry_eligible(entry, thresholds) and not entry.get("error")
            for entry in (source, positive)
        ):
            positive_scores.append(
                jaccard(ocr_char_ngrams(source["text"]), ocr_char_ngrams(positive["text"]))
            )
        if source is not None and negative is not None and all(
            ocr_entry_eligible(entry, thresholds) and not entry.get("error")
            for entry in (source, negative)
        ):
            negative_scores.append(
                jaccard(ocr_char_ngrams(source["text"]), ocr_char_ngrams(negative["text"]))
            )
    if not positive_scores or not negative_scores:
        raise ValueError("OCR calibration has no eligible positive or negative pairs")
    return {
        "schema_version": "blind-gains.decon-ocr-calibration.v1",
        "thresholds": thresholds,
        "n_planted_pairs": total,
        "eligible_positive_pairs": len(positive_scores),
        "eligible_negative_pairs": len(negative_scores),
        "positive_coverage": len(positive_scores) / total,
        "negative_coverage": len(negative_scores) / total,
        "ocr_char5_jaccard": threshold_summary(
            positive_scores,
            negative_scores,
            float(thresholds["ocr_char5_remove_min"]),
            float(thresholds["ocr_char5_inspect_min"]),
            higher_is_duplicate=True,
        ),
        "policy": (
            "OCR-only overlap is inspection-only; a remove-threshold OCR score can upgrade an edge "
            "only when SHA, perceptual hash, or DINOv2 independently corroborates the image match."
        ),
    }
