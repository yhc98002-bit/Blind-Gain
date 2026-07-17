from __future__ import annotations

import hashlib
import json
import math
import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from src.rewards.answer_reward import PARSER_VERSION, answers_match, normalize_text, numeric_value


SCORER_VERSION = "visual-evidence-ranking-v1"
CANDIDATE_SCHEMA_VERSION = "blind-gains.visual-evidence-candidates.v1"
RESULT_SCHEMA_VERSION = "blind-gains.visual-evidence-ranking-result.v1"
HUMAN_TEMPLATE_LABELS = {
    "starred_series_value_nine_v07": "cued chart point-value reading",
}


def sha256_json(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def candidate_verbalization(answer: Any) -> str:
    text = str(answer).strip()
    if not text:
        raise ValueError("candidate answer must be nonempty")
    if re.search(r"</?answer\b", text, re.IGNORECASE):
        raise ValueError("candidate answer must not contain answer tags")
    return f"<answer>{text}</answer>"


def mathematically_equivalent(left: Any, right: Any) -> bool:
    # Check both directions because canonical-v2 unit handling is intentionally
    # conservative and candidate-set equivalence must be symmetric.
    return answers_match(candidate_verbalization(left), right) and answers_match(
        candidate_verbalization(right), left
    )


def answer_signature(answer: Any) -> str:
    normalized = normalize_text(answer)
    if numeric_value(normalized) is not None:
        return "numeric"
    if re.fullmatch(r"[A-Za-z0-9]+", normalized):
        return f"alnum-length-{len(normalized)}"
    return "text"


def _equivalence_classes(values: Iterable[Any]) -> tuple[list[str], dict[str, str]]:
    representatives: list[str] = []
    member_to_representative: dict[str, str] = {}
    for value in sorted({str(item).strip() for item in values}):
        if not value:
            raise ValueError("candidate universe contains an empty answer")
        match = next(
            (prior for prior in representatives if mathematically_equivalent(value, prior)),
            None,
        )
        if match is None:
            representatives.append(value)
            match = value
        member_to_representative[value] = match
    return representatives, member_to_representative


def _candidate_id(answer: str) -> str:
    return hashlib.sha256(answer.encode("utf-8")).hexdigest()[:16]


def _hash_order(pair_id: str, answer: str) -> str:
    return hashlib.sha256(f"{pair_id}\0{answer}".encode("utf-8")).hexdigest()


def build_candidate_registry_rows(
    rows: Sequence[Mapping[str, Any]], max_candidates: int = 16
) -> list[dict[str, Any]]:
    if max_candidates < 2:
        raise ValueError("max_candidates must be at least two")
    by_template: dict[str, list[str]] = defaultdict(list)
    seen_pair_ids: set[str] = set()
    for row in rows:
        pair_id = str(row.get("pair_id", ""))
        template_id = str(row.get("template_id", ""))
        if not pair_id or not template_id:
            raise ValueError("every source row needs pair_id and template_id")
        if pair_id in seen_pair_ids:
            raise ValueError(f"duplicate pair_id: {pair_id}")
        seen_pair_ids.add(pair_id)
        by_template[template_id].extend([str(row["answer_a"]), str(row["answer_b"])])
    universe_data = {
        template: _equivalence_classes(values) for template, values in by_template.items()
    }

    output: list[dict[str, Any]] = []
    for source in rows:
        row = dict(source)
        pair_id = str(row["pair_id"])
        template_id = str(row["template_id"])
        gold_a = str(row["answer_a"]).strip()
        gold_b = str(row["answer_b"]).strip()
        if mathematically_equivalent(gold_a, gold_b):
            raise ValueError(f"counterfactual answers are equivalent for {pair_id}")

        universe, equivalence_map = universe_data[template_id]
        gold_class_a = equivalence_map[gold_a]
        gold_class_b = equivalence_map[gold_b]
        selected = [gold_a, gold_b]
        eligible_universe = [
            value for value in universe if value not in {gold_class_a, gold_class_b}
        ]
        if len(universe) <= max_candidates:
            selected.extend(eligible_universe)
        else:
            gold_signatures = {answer_signature(gold_a), answer_signature(gold_b)}
            same_type = [
                value
                for value in eligible_universe
                if answer_signature(value) in gold_signatures
            ]
            same_type_set = set(same_type)
            fallback = [
                value
                for value in eligible_universe
                if value not in same_type_set
            ]
            same_type.sort(key=lambda value: _hash_order(pair_id, value))
            fallback.sort(key=lambda value: _hash_order(pair_id, value))
            selected.extend((same_type + fallback)[: max_candidates - 2])

        candidates = selected
        if gold_a not in candidates:
            raise AssertionError(f"gold A absent from candidate set: {pair_id}")
        if gold_b not in candidates:
            raise AssertionError(f"gold B absent from candidate set: {pair_id}")
        if len(candidates) > max_candidates:
            raise AssertionError(f"candidate cap exceeded: {pair_id}")
        if len(candidates) != min(len(universe), max_candidates):
            raise AssertionError(f"candidate count mismatch: {pair_id}")

        # Candidate presentation order is hash-derived and does not reveal which
        # entries are the two gold answers.
        candidates.sort(key=lambda value: _hash_order(pair_id, value))
        candidate_records = [
            {
                "candidate_id": _candidate_id(value),
                "answer": value,
                "answer_signature": answer_signature(value),
                "verbalization": candidate_verbalization(value),
            }
            for value in candidates
        ]

        def gold_id(answer: str) -> str:
            matches = [
                item["candidate_id"]
                for item in candidate_records
                if answer == item["answer"]
            ]
            if len(matches) != 1:
                raise AssertionError(
                    f"gold answer maps to {len(matches)} candidates for {pair_id}"
                )
            return matches[0]

        frozen = {
            "schema_version": CANDIDATE_SCHEMA_VERSION,
            "pair_id": pair_id,
            "source_pair_id": row.get("source_pair_id"),
            "template_id": template_id,
            "template_label": HUMAN_TEMPLATE_LABELS.get(template_id, template_id),
            "category": row.get("category"),
            "question": row["question"],
            "image_a_path": row["image_a_path"],
            "image_a_sha256": row.get("image_a_sha256"),
            "image_b_path": row["image_b_path"],
            "image_b_sha256": row.get("image_b_sha256"),
            "answer_a": gold_a,
            "answer_b": gold_b,
            "gold_candidate_id_a": gold_id(gold_a),
            "gold_candidate_id_b": gold_id(gold_b),
            "candidates": candidate_records,
            "candidate_count": len(candidate_records),
            "candidate_policy": {
                "max_candidates": max_candidates,
                "small_universe_policy": "complete_template_equivalence_universe",
                "large_universe_policy": "both_golds_plus_same_signature_sha256_distractors",
                "selection_uses_model_outputs": False,
                "equivalence_parser": PARSER_VERSION,
            },
        }
        frozen["candidate_set_sha256"] = sha256_json(candidate_records)
        output.append(frozen)
    return output


def score_pair_from_candidates(
    registry_row: Mapping[str, Any],
    scores_a: Mapping[str, float],
    scores_b: Mapping[str, float],
    raw_scores_a: Mapping[str, float] | None = None,
    raw_scores_b: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    candidate_ids = [str(item["candidate_id"]) for item in registry_row["candidates"]]
    if set(scores_a) != set(candidate_ids) or set(scores_b) != set(candidate_ids):
        raise ValueError("score keys do not exactly match the frozen candidate set")
    gold_a = str(registry_row["gold_candidate_id_a"])
    gold_b = str(registry_row["gold_candidate_id_b"])
    margin_a = float(scores_a[gold_a]) - float(scores_a[gold_b])
    margin_b = float(scores_b[gold_b]) - float(scores_b[gold_a])

    def conservative_rank(scores: Mapping[str, float], gold: str) -> int:
        gold_score = float(scores[gold])
        # A numerical tie is resolved against the gold candidate. This prevents a
        # top-1 success from being created by equal candidate scores.
        return 1 + sum(
            candidate != gold and float(score) >= gold_score - 1e-12
            for candidate, score in scores.items()
        )

    rank_a = conservative_rank(scores_a, gold_a)
    rank_b = conservative_rank(scores_b, gold_b)
    result = {
        "margin_a": margin_a,
        "margin_b": margin_b,
        "paired_margin": (margin_a + margin_b) / 2.0,
        "pair_success": margin_a > 0.0 and margin_b > 0.0,
        "rank_a": rank_a,
        "rank_b": rank_b,
        "candidate_top1_a": rank_a == 1,
        "candidate_top1_b": rank_b == 1,
        "candidate_pair_top1": rank_a == 1 and rank_b == 1,
        "mrr_a": 1.0 / rank_a,
        "mrr_b": 1.0 / rank_b,
        "candidate_pair_mrr": (1.0 / rank_a + 1.0 / rank_b) / 2.0,
        "scorer_version": SCORER_VERSION,
    }
    if raw_scores_a is not None and raw_scores_b is not None:
        if set(raw_scores_a) != set(candidate_ids) or set(raw_scores_b) != set(candidate_ids):
            raise ValueError("raw-score keys do not exactly match the frozen candidate set")
        raw_margin_a = float(raw_scores_a[gold_a]) - float(raw_scores_a[gold_b])
        raw_margin_b = float(raw_scores_b[gold_b]) - float(raw_scores_b[gold_a])
        result.update(
            {
                "raw_sum_margin_a_robustness": raw_margin_a,
                "raw_sum_margin_b_robustness": raw_margin_b,
                "raw_sum_paired_margin_robustness": (raw_margin_a + raw_margin_b) / 2.0,
            }
        )
    return result


def image_dependent_effect(
    base_real: Mapping[str, float],
    trained_real: Mapping[str, float],
    base_blind: Mapping[str, float],
    trained_blind: Mapping[str, float],
) -> dict[str, float]:
    identities = [set(values) for values in (base_real, trained_real, base_blind, trained_blind)]
    if not identities[0] or any(identity != identities[0] for identity in identities[1:]):
        raise ValueError("image-dependent effect requires identical nonempty pair identities")
    effects = {
        pair_id: (float(trained_real[pair_id]) - float(base_real[pair_id]))
        - (float(trained_blind[pair_id]) - float(base_blind[pair_id]))
        for pair_id in identities[0]
    }
    return effects


def bootstrap_mean_ci(
    values: Sequence[float], n_boot: int, seed: int, alpha: float = 0.05
) -> tuple[float, float]:
    if not values:
        raise ValueError("bootstrap input must be nonempty")
    if n_boot < 1:
        raise ValueError("n_boot must be positive")
    import numpy as np

    array = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(seed)
    means: list[float] = []
    # Chunking keeps the largest 1,200-pair registered cell well below 100 MiB.
    for start in range(0, n_boot, 1024):
        count = min(1024, n_boot - start)
        indices = rng.integers(0, len(array), size=(count, len(array)))
        means.extend(array[indices].mean(axis=1).tolist())
    means.sort()
    lower = means[max(0, math.floor((alpha / 2.0) * n_boot))]
    upper = means[min(n_boot - 1, math.ceil((1.0 - alpha / 2.0) * n_boot) - 1)]
    return lower, upper


def completion_logprob_from_logits(
    logits: Any,
    input_ids: Any,
    prompt_length: int,
    sequence_length: int,
) -> tuple[float, float, int]:
    """Return mean and sum log probability for the exact completion token span."""
    import torch

    if logits.ndim != 2 or input_ids.ndim != 1:
        raise ValueError("expected one unbatched logit matrix and token vector")
    if prompt_length < 1 or sequence_length <= prompt_length:
        raise ValueError("completion span must follow a nonempty prompt")
    if sequence_length > input_ids.shape[0] or sequence_length > logits.shape[0]:
        raise ValueError("sequence length exceeds tensor bounds")
    targets = input_ids[prompt_length:sequence_length]
    predictive_logits = logits[prompt_length - 1 : sequence_length - 1].float()
    if predictive_logits.shape[0] != targets.shape[0]:
        raise AssertionError("completion logits and targets are misaligned")
    selected = predictive_logits.gather(1, targets.to(torch.long).unsqueeze(1)).squeeze(1)
    token_logprobs = selected - torch.logsumexp(predictive_logits, dim=-1)
    raw_sum = float(token_logprobs.double().sum().item())
    token_count = int(targets.numel())
    return raw_sum / token_count, raw_sum, token_count
