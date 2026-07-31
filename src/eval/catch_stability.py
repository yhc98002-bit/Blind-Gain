#!/usr/bin/env python3
"""Catch-trial invariance (stability) scorer for the Mini-A5 catch set.

This is the instrument that reports/f8_secondaries_v1.md section 2.4 specifies
and section 2 reports as ABSENT: Mini-A5 secondary endpoint 2 (catch-trial
stability, docs/registered_mini_a5_main_v1.md line 92, addendum section 6.2).

The invariance criterion (the field that did not exist before this module):

    stable_lenient := normalize_text(extracted_answer_a)
                      == normalize_text(extracted_answer_b)

evaluated REGARDLESS of whether either side matches the gold, and NOT gated on
``answer_a != answer_b``. All 300 catch pairs are equal-gold, so the existing
``pair_score`` field ``collapsed`` — which is hard-suppressed to False whenever
``normalize_text(answer_a) == normalize_text(answer_b)`` — carries zero
information on catch pairs and is not used here (f8_secondaries_v1.md sec 2.2).

Both severities are reported (I7):
  lenient  : the equality above.
  strict   : the equality AND contract_valid_a AND contract_valid_b, so a pair
             whose members agree only because both fell out of contract does
             not count as stable.

Correctness stays separable from stability (the two members share one gold):
``correct_a`` / ``correct_b`` come from the P0.2-fixed equal-gold path inside
``src.eval.fliptrack_metrics.pair_score`` (``golds_equivalent`` short-circuits
the discriminative criterion; success is matching the single gold).

Aggregation is PER TEMPLATE ONLY. Three catch templates, 100 pairs each; their
roles within the catch design are not established anywhere, so pooling is
unjustified under I13. No function in this module computes a pooled number and
the output schema has no slot for one.

CP-vs-member machinery: paired item bootstrap on ``pair_group_uid``, 10,000
draws, percentile 2.5/97.5, both arms resampled on identical indices per
replicate, exact two-sided McNemar alongside. Seeds derive deterministically
from the pinned base seed 20260729 as

    seed = 20260729 + 1000 * indicator_index + 10 * template_index

(the reports/f8_secondaries_v1.md section 1.6 procedure with the indicator
enumeration fixed by ``INDICATORS`` below; template_index is the sorted
template-id order). Intervals quantify evaluation uncertainty on a fixed pair
set only; they do not estimate run-to-run RL variance. Each arm is one run.

Registered in docs/registered_mini_a5_catch_stability_v1.md. The eval that
feeds this scorer launches only after that registration merges (I9).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.eval.fliptrack_metrics import golds_equivalent, pair_score
from src.eval.prompt_contract import PromptContractLike, prompt_contract_metadata
from src.rewards.answer_reward import PARSER_VERSION, normalize_text

SCHEMA_VERSION = "blind-gains.mini-a5-catch-stability.v1"
BASE_SEED = 20260729
N_BOOT = 10000

REGISTERED_TEMPLATES = (
    "mini_a5_catch_distractor_matrix_v1",
    "mini_a5_catch_distractor_scatter_v1",
    "mini_a5_catch_distractor_trajectory_v1",
)
REGISTERED_PAIRS_PER_TEMPLATE = 100

# (row field, indicator family, severity). The tuple ORDER fixes
# indicator_index in the seed derivation and is registered; do not reorder.
INDICATORS = (
    ("stable_lenient", "stability", "lenient"),
    ("stable_strict", "stability", "strict"),
    ("pair_correct", "correctness", "lenient"),
    ("strict_pair_correct", "correctness", "strict"),
    ("stable_and_correct_lenient", "joint", "lenient"),
    ("stable_and_correct_strict", "joint", "strict"),
)

SEED_DERIVATION = "seed = 20260729 + 1000*indicator_index + 10*template_index"


class CatchScoreError(ValueError):
    """A row or row-set violates the catch-scoring contract."""


def resolve_seed(indicator_index: int, template_index: int) -> int:
    return BASE_SEED + 1000 * indicator_index + 10 * template_index


def catch_pair_score(
    row: dict[str, Any], prompt_contract: PromptContractLike = None
) -> dict[str, Any]:
    """Score one catch pair from its raw predictions.

    Requires ``pair_group_uid``, ``template_id``, equal golds, and the two
    prediction fields. Recomputes everything from ``prediction_a`` /
    ``prediction_b``; never trusts stability-adjacent fields already present
    on the row.
    """
    for key in ("pair_group_uid", "template_id"):
        value = row.get(key)
        if not isinstance(value, str) or not value:
            raise CatchScoreError(f"catch row is missing a nonempty '{key}': {value!r}")
    for key in ("answer_a", "answer_b"):
        if not str(row.get(key, "")).strip():
            raise CatchScoreError(f"catch row has an empty gold '{key}'")
    if not golds_equivalent(row["answer_a"], row["answer_b"]):
        raise CatchScoreError(
            "catch scorer is defined only on equal-gold pairs; got "
            f"answer_a={row['answer_a']!r} answer_b={row['answer_b']!r} "
            f"(pair_group_uid={row['pair_group_uid']!r})"
        )
    scored = pair_score(row, prompt_contract=prompt_contract)
    contract_valid_a = bool(scored["contract_valid_a"])
    contract_valid_b = bool(scored["contract_valid_b"])
    # The invariance criterion: model self-consistency under a non-queried
    # visual change, regardless of gold, ungated on answer_a != answer_b.
    stable_lenient = normalize_text(scored["extracted_answer_a"]) == normalize_text(
        scored["extracted_answer_b"]
    )
    stable_strict = stable_lenient and contract_valid_a and contract_valid_b
    correct_a = bool(scored["correct_a"])
    correct_b = bool(scored["correct_b"])
    pair_correct = bool(scored["pair_correct"])
    strict_pair_correct = bool(scored["strict_pair_correct"])
    return {
        "pair_group_uid": row["pair_group_uid"],
        "template_id": row["template_id"],
        "prediction_a": str(row.get("prediction_a", "")),
        "prediction_b": str(row.get("prediction_b", "")),
        "extracted_answer_a": scored["extracted_answer_a"],
        "extracted_answer_b": scored["extracted_answer_b"],
        "stable_lenient": stable_lenient,
        "stable_strict": stable_strict,
        "correct_a": correct_a,
        "correct_b": correct_b,
        "pair_correct": pair_correct,
        "strict_pair_correct": strict_pair_correct,
        "stable_and_correct_lenient": stable_lenient and pair_correct,
        "stable_and_correct_strict": stable_strict and strict_pair_correct,
        "contract_valid_a": contract_valid_a,
        "contract_valid_b": contract_valid_b,
        "equal_gold": True,
        "parser_version": PARSER_VERSION,
        **prompt_contract_metadata(prompt_contract),
    }


def aggregate_by_template(scored_rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Per-template rates for every registered indicator, both severities.

    Returns ``{"per_template": {template_id: block}}`` and nothing else: the
    schema deliberately has no slot for a pooled-across-templates number (I13).
    """
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in scored_rows:
        template = row.get("template_id")
        if not isinstance(template, str) or not template:
            raise CatchScoreError(
                f"scored row lacks a nonempty template_id; refusing to aggregate: {row!r}"
            )
        grouped.setdefault(template, []).append(row)
    if not grouped:
        raise CatchScoreError("no scored rows to aggregate")
    per_template: dict[str, Any] = {}
    for template in sorted(grouped):
        rows = grouped[template]
        n = len(rows)
        block: dict[str, Any] = {"n_pairs": n}
        for indicator, family, severity in INDICATORS:
            count = sum(bool(row[indicator]) for row in rows)
            block[indicator] = {
                "count": count,
                "rate": count / n,
                "indicator_family": family,
                "severity": severity,
            }
        per_template[template] = block
    return {"per_template": per_template}


def mcnemar_exact_bool(a: Sequence[bool], b: Sequence[bool]) -> dict[str, Any]:
    """Exact two-sided McNemar on paired boolean indicators."""
    if len(a) != len(b):
        raise CatchScoreError("mcnemar needs equal-length paired vectors")
    b01 = sum((not x) and y for x, y in zip(a, b))
    b10 = sum(x and (not y) for x, y in zip(a, b))
    n = b01 + b10
    if n == 0:
        p = 1.0
    else:
        k = min(b01, b10)
        p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / (2**n))
    return {"b01": b01, "b10": b10, "n_discordant": n, "p_value": p}


def paired_bootstrap_diff(
    x: Sequence[float], y: Sequence[float], seed: int, n_boot: int = N_BOOT
) -> dict[str, Any]:
    """Percentile CI for mean(x) - mean(y); identical resample indices for both."""
    ax = np.asarray(x, dtype=np.float64)
    ay = np.asarray(y, dtype=np.float64)
    if ax.shape != ay.shape or ax.size == 0:
        raise CatchScoreError("paired bootstrap needs equal nonempty vectors")
    rng = np.random.default_rng(seed)
    n = ax.size
    diffs = np.empty(n_boot, dtype=np.float64)
    filled = 0
    while filled < n_boot:
        block = min(1024, n_boot - filled)
        idx = rng.integers(0, n, size=(block, n))
        diffs[filled : filled + block] = ax[idx].mean(axis=1) - ay[idx].mean(axis=1)
        filled += block
    diffs.sort()
    lo = float(diffs[max(0, math.floor(0.025 * n_boot))])
    hi = float(diffs[min(n_boot - 1, math.ceil(0.975 * n_boot) - 1)])
    return {
        "point": float(ax.mean() - ay.mean()),
        "ci95_low": lo,
        "ci95_high": hi,
        "excludes_zero": bool(lo > 0.0 or hi < 0.0),
        "bootstrap_seed": seed,
        "resamples": n_boot,
    }


def compare_arms(
    cp_scored: Sequence[dict[str, Any]], member_scored: Sequence[dict[str, Any]]
) -> dict[str, Any]:
    """CP minus member, per template, per registered indicator. Never pooled."""
    cp: dict[str, dict[str, Any]] = {}
    member: dict[str, dict[str, Any]] = {}
    for label, source, target in (("cp", cp_scored, cp), ("member", member_scored, member)):
        for row in source:
            uid = row["pair_group_uid"]
            if uid in target:
                raise CatchScoreError(f"duplicate pair_group_uid in {label} rows: {uid}")
            target[uid] = row
    if set(cp) != set(member):
        only_cp = sorted(set(cp) - set(member))[:5]
        only_member = sorted(set(member) - set(cp))[:5]
        raise CatchScoreError(
            f"arms cover different pair_group_uid sets; cp-only={only_cp}, member-only={only_member}"
        )
    uids = sorted(cp)
    for uid in uids:
        if cp[uid]["template_id"] != member[uid]["template_id"]:
            raise CatchScoreError(f"template_id disagrees across arms for {uid}")
    templates = sorted({cp[uid]["template_id"] for uid in uids})
    checks = {
        # join coverage, not a metric: no indicator value is ever pooled (I13)
        "n_pairs_joined": len(uids),
        "templates": templates,
        "template_pair_counts": {
            template: sum(1 for uid in uids if cp[uid]["template_id"] == template)
            for template in templates
        },
        "identical_uid_sets": True,
        "template_id_agrees_across_arms": True,
    }
    per_template: dict[str, Any] = {}
    for template_index, template in enumerate(templates):
        template_uids = [uid for uid in uids if cp[uid]["template_id"] == template]
        block: dict[str, Any] = {
            "n_pairs": len(template_uids),
            "template_index": template_index,
            "cp_minus_member": {},
        }
        for indicator_index, (indicator, family, severity) in enumerate(INDICATORS):
            cp_vals = [bool(cp[uid][indicator]) for uid in template_uids]
            member_vals = [bool(member[uid][indicator]) for uid in template_uids]
            entry = paired_bootstrap_diff(
                [float(v) for v in cp_vals],
                [float(v) for v in member_vals],
                resolve_seed(indicator_index, template_index),
            )
            entry["mcnemar_exact_two_sided"] = mcnemar_exact_bool(cp_vals, member_vals)
            entry["indicator_family"] = family
            entry["severity"] = severity
            entry["indicator_index"] = indicator_index
            block["cp_minus_member"][indicator] = entry
        per_template[template] = block
    return {
        "per_template": per_template,
        "checks": checks,
        "seed_derivation": SEED_DERIVATION,
        "base_seed": BASE_SEED,
        "n_boot": N_BOOT,
    }


def _read_jsonl_paths(paths: Sequence[str]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows: list[dict[str, Any]] = []
    provenance: list[dict[str, str]] = []
    for raw in paths:
        path = Path(raw)
        data = path.read_bytes()
        provenance.append({"path": str(raw), "sha256": hashlib.sha256(data).hexdigest()})
        for line in data.decode("utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows, provenance


def _require_registered_shape(scored: Sequence[dict[str, Any]], arm: str) -> None:
    counts: dict[str, int] = {}
    for row in scored:
        counts[row["template_id"]] = counts.get(row["template_id"], 0) + 1
    if tuple(sorted(counts)) != REGISTERED_TEMPLATES or any(
        counts[t] != REGISTERED_PAIRS_PER_TEMPLATE for t in counts
    ):
        raise CatchScoreError(
            f"{arm} rows do not match the registered catch shape "
            f"(3 templates x {REGISTERED_PAIRS_PER_TEMPLATE}): {counts}"
        )


def score_rows(
    rows: Iterable[dict[str, Any]], prompt_contract: PromptContractLike = None
) -> list[dict[str, Any]]:
    scored = [catch_pair_score(row, prompt_contract=prompt_contract) for row in rows]
    seen: set[str] = set()
    for row in scored:
        if row["pair_group_uid"] in seen:
            raise CatchScoreError(f"duplicate pair_group_uid: {row['pair_group_uid']}")
        seen.add(row["pair_group_uid"])
    return sorted(scored, key=lambda row: row["pair_group_uid"])


def build_readout(
    cp_rows: Iterable[dict[str, Any]],
    member_rows: Iterable[dict[str, Any]],
    cp_provenance: list[dict[str, str]] | None = None,
    member_provenance: list[dict[str, str]] | None = None,
    prompt_contract: PromptContractLike = None,
    expect_registered_shape: bool = True,
) -> dict[str, Any]:
    cp_scored = score_rows(cp_rows, prompt_contract=prompt_contract)
    member_scored = score_rows(member_rows, prompt_contract=prompt_contract)
    if expect_registered_shape:
        _require_registered_shape(cp_scored, "cp")
        _require_registered_shape(member_scored, "member")
    return {
        "schema_version": SCHEMA_VERSION,
        "endpoint": (
            "Mini-A5 secondary 2 (addendum section 6.2): catch-trial stability — "
            "self-consistency under a non-queried visual change"
        ),
        "aggregation_rule": "per catch template id only; never pooled across templates (I13)",
        "severity_rule": "every indicator reported lenient and contract-strict (I7)",
        "interval_note": (
            "Paired item bootstrap on pair_group_uid, 10,000 draws, percentile "
            "2.5/97.5, both arms resampled on identical indices per replicate; "
            "exact two-sided McNemar alongside. Quantifies evaluation "
            "uncertainty on a fixed pair set only; does not estimate "
            "run-to-run RL variance. Each arm is one run."
        ),
        "seed_derivation": SEED_DERIVATION,
        "indicator_indices": {
            indicator: index for index, (indicator, _, _) in enumerate(INDICATORS)
        },
        "parser_version": PARSER_VERSION,
        **prompt_contract_metadata(prompt_contract),
        "inputs": {
            "cp_scores": cp_provenance or [],
            "member_scores": member_provenance or [],
        },
        "arms": {
            "cp": aggregate_by_template(cp_scored),
            "member": aggregate_by_template(member_scored),
        },
        "cp_vs_member": compare_arms(cp_scored, member_scored),
        "automatic_branch_assignment": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cp-scores", nargs="+", required=True,
        help="FlipTrack-harness scores.jsonl file(s) for the CP arm over the catch manifest",
    )
    parser.add_argument(
        "--member-scores", nargs="+", required=True,
        help="FlipTrack-harness scores.jsonl file(s) for the member arm over the catch manifest",
    )
    parser.add_argument("--output", required=True, help="readout JSON path")
    parser.add_argument(
        "--per-row-output-cp", default=None, help="optional per-row scored jsonl (cp)"
    )
    parser.add_argument(
        "--per-row-output-member", default=None, help="optional per-row scored jsonl (member)"
    )
    parser.add_argument(
        "--expect", choices=("registered", "any"), default="registered",
        help="registered: require 3 templates x 100 pairs per arm (default)",
    )
    args = parser.parse_args(argv)

    cp_rows, cp_provenance = _read_jsonl_paths(args.cp_scores)
    member_rows, member_provenance = _read_jsonl_paths(args.member_scores)
    expect_registered = args.expect == "registered"
    readout = build_readout(
        cp_rows,
        member_rows,
        cp_provenance=cp_provenance,
        member_provenance=member_provenance,
        expect_registered_shape=expect_registered,
    )
    if args.per_row_output_cp or args.per_row_output_member:
        for path_value, rows in (
            (args.per_row_output_cp, cp_rows),
            (args.per_row_output_member, member_rows),
        ):
            if not path_value:
                continue
            scored = score_rows(rows)
            path = Path(path_value)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as handle:
                for row in scored:
                    handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(readout, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    for arm in ("cp", "member"):
        for template, block in readout["arms"][arm]["per_template"].items():
            summary = "  ".join(
                f"{indicator}={block[indicator]['count']}/{block['n_pairs']}"
                for indicator, _, _ in INDICATORS
            )
            print(f"{arm:<7} {template}  {summary}")
    for template, block in readout["cp_vs_member"]["per_template"].items():
        for indicator, entry in block["cp_minus_member"].items():
            print(
                f"CP-member {template} {indicator:<28} {entry['point']:+.4f} "
                f"[{entry['ci95_low']:+.4f},{entry['ci95_high']:+.4f}] "
                f"excl0={entry['excludes_zero']} "
                f"mcnemar_p={entry['mcnemar_exact_two_sided']['p_value']:.4g}"
            )
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
