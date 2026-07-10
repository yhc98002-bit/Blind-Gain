from __future__ import annotations

import hashlib
import re
from collections import Counter, defaultdict
from typing import Any, Iterable

from src.decon.core import DEFAULT_THRESHOLDS, jaccard
from src.decon.ocr_text import normalize_ocr_text


def ocr_char_ngrams(value: Any, n: int = 5) -> frozenset[str]:
    compact = re.sub(r"\s+", "", normalize_ocr_text(value))
    if len(compact) < n:
        return frozenset()
    return frozenset(compact[index : index + n] for index in range(len(compact) - n + 1))


def ocr_entry_eligible(entry: dict[str, Any], thresholds: dict[str, float]) -> bool:
    normalized = normalize_ocr_text(entry.get("text", ""))
    compact = normalized.replace(" ", "")
    minimum_chars = int(thresholds["ocr_min_compact_chars"])
    minimum_parts = int(thresholds["ocr_min_tokens_or_lines"])
    return len(compact) >= minimum_chars and (
        len(normalized.split()) >= minimum_parts or int(entry.get("line_count", 0)) >= minimum_parts
    )


def _text_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def merge_ocr_signals(
    baseline: dict[str, Any],
    train_rows: list[dict[str, Any]],
    eval_rows: list[dict[str, Any]],
    ocr_entries: Iterable[dict[str, Any]],
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Merge OCR overlap without allowing an OCR-only match to auto-remove data.

    OCR strings in diagrams are often short and generic. A high OCR overlap can
    therefore upgrade a corroborated image match to removal, but is inspection-only
    when no hash or image-embedding signal supports it.
    """

    thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    entries: dict[str, dict[str, Any]] = {}
    for raw in ocr_entries:
        digest = str(raw["image_sha256"])
        if digest in entries:
            if normalize_ocr_text(entries[digest].get("text", "")) != normalize_ocr_text(raw.get("text", "")):
                raise ValueError(f"conflicting OCR output for image {digest}")
            continue
        entries[digest] = dict(raw)

    expected_hashes = {
        str(row["image_sha256"])
        for row in [*train_rows, *eval_rows]
        if row.get("image_applicable", True)
    }
    missing_hashes = sorted(expected_hashes - entries.keys())

    train_by_hash: dict[str, list[dict[str, Any]]] = defaultdict(list)
    eval_by_hash: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in train_rows:
        if row.get("image_applicable", True):
            train_by_hash[str(row["image_sha256"])].append(row)
    for row in eval_rows:
        if row.get("image_applicable", True):
            eval_by_hash[str(row["image_sha256"])].append(row)

    eval_grams: dict[str, frozenset[str]] = {}
    inverted: dict[str, set[str]] = defaultdict(set)
    for digest in eval_by_hash:
        entry = entries.get(digest)
        if entry is None or not ocr_entry_eligible(entry, thresholds):
            continue
        grams = ocr_char_ngrams(entry.get("text", ""))
        if not grams:
            continue
        eval_grams[digest] = grams
        for gram in grams:
            inverted[gram].add(digest)

    edge_map = {
        (edge["train_record_id"], edge["eval_record_id"]): dict(edge)
        for edge in baseline.get("candidate_edges", [])
    }
    action_rank = {"none": 0, "inspect": 1, "remove": 2}
    image_corroborators = {"image_sha256_exact", "perceptual_hash", "dinov2_cosine"}
    inspect_min = float(thresholds["ocr_char5_inspect_min"])
    remove_min = float(thresholds["ocr_char5_remove_min"])

    def add_signal(train: dict[str, Any], evaluation: dict[str, Any], score: float) -> None:
        key = (train["record_id"], evaluation["record_id"])
        edge = edge_map.setdefault(
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
        train_text = normalize_ocr_text(entries[str(train["image_sha256"])].get("text", ""))
        eval_text = normalize_ocr_text(entries[str(evaluation["image_sha256"])].get("text", ""))
        corroborated = bool(image_corroborators & set(edge["signals"]))
        proposed_action = "remove" if score >= remove_min and corroborated else "inspect"
        edge["signals"]["ocr_char5_jaccard"] = {
            "score": score,
            "exact": train_text == eval_text,
            "corroborated_image_signal": corroborated,
            "train_text_sha256": _text_digest(train_text),
            "eval_text_sha256": _text_digest(eval_text),
        }
        if action_rank[proposed_action] > action_rank[edge["action"]]:
            edge["action"] = proposed_action

    for train_digest, train_records in train_by_hash.items():
        entry = entries.get(train_digest)
        if entry is None or not ocr_entry_eligible(entry, thresholds):
            continue
        train_grams = ocr_char_ngrams(entry.get("text", ""))
        candidate_hashes: set[str] = set()
        for gram in train_grams:
            candidate_hashes.update(inverted.get(gram, set()))
        for eval_digest in candidate_hashes:
            score = jaccard(train_grams, eval_grams[eval_digest])
            if score < inspect_min:
                continue
            for train in train_records:
                for evaluation in eval_by_hash[eval_digest]:
                    add_signal(train, evaluation, score)

    edges = sorted(edge_map.values(), key=lambda row: (row["train_record_id"], row["eval_record_id"]))
    error_hashes = sorted(
        digest for digest in expected_hashes & entries.keys() if entries[digest].get("error")
    )
    pending = [layer for layer in baseline.get("pending_layers", []) if layer != "ocr_text_overlap"]
    if missing_hashes or error_hashes:
        pending.append("ocr_text_overlap")
    completed = list(baseline.get("completed_layers", []))
    if not missing_hashes and not error_hashes and "ocr_text_overlap" not in completed:
        completed.append("ocr_text_overlap")
    result = {key: value for key, value in baseline.items() if key not in {"candidate_edges", "pending_layers", "completed_layers"}}
    result.update(
        {
            "schema_version": "blind-gains.decon-comparison.v3",
            "thresholds": thresholds,
            "n_candidate_edges": len(edges),
            "action_counts": dict(sorted(Counter(edge["action"] for edge in edges).items())),
            "signal_counts": dict(sorted(Counter(signal for edge in edges for signal in edge["signals"]).items())),
            "candidate_edges": edges,
            "completed_layers": completed,
            "pending_layers": pending,
            "ocr_coverage": {
                "expected_unique_images": len(expected_hashes),
                "present_unique_images": len(expected_hashes & entries.keys()),
                "missing_unique_images": len(missing_hashes),
                "error_images": len(error_hashes),
                "nonempty_text_images": sum(bool(normalize_ocr_text(entries[digest].get("text", ""))) for digest in expected_hashes & entries.keys()),
                "eligible_text_images": sum(ocr_entry_eligible(entries[digest], thresholds) for digest in expected_hashes & entries.keys()),
            },
        }
    )
    return result
