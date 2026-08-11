"""Adversarial fixtures for scripts/build_track4_premise_v2_gate_readout.py (I10).

Every fixture builds a synthetic six-cell corpus under tmp_path with HAND-PLANTED
per-member outcomes, so every reported accuracy is hand-computable from the plant
and can be asserted exactly.

The plants are expressed as per-member codes:

    "ct"  correct, answer-tags contract satisfied   -> lenient YES, strict YES
    "cu"  correct, contract NOT satisfied (no tags) -> lenient YES, strict NO
    "w"   wrong                                     -> lenient NO,  strict NO

The corpus builder scores every planted row with the same frozen scorer the
evaluation harness uses (`src.eval.fliptrack_metrics.pair_score`, exactly as
`scripts/eval_qwen_vl_fliptrack.py` does) and ASSERTS that each planted member
landed on the intended verdict, so a plant can never silently drift.

Coverage:
  - planted per-intervention-type accuracies recovered exactly (member + pair,
    both contracts);
  - the E1 band verdict under both contracts, in a corpus where lenient and
    strict DISAGREE (proving the two contracts are never merged), including the
    section-5 branch each one fires;
  - two intervention types at different n_points with the SAME blind premise
    accuracy, one passing and one failing because each is judged by its own
    2/(n_points-1) ceiling;
  - the E2 final-member ceiling on both sides of 0.133 and exactly at it
    (0.132 pass / 0.133 pass / 0.134 fail), flipping the verdict and the
    blind-solvable pair_id report;
  - refusals: unmatched prediction row, duplicate pair_id, missing
    intervention_type, non-single-valued n_points within a type, tampered banked
    verdict, mixed equal-gold within a type, swapped manifests, wrong image-mode
    cell, registration drift, existing output;
  - `--expect registered` rejecting a non-section-8 composition;
  - byte-determinism of both artifacts.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.eval.fliptrack_metrics import aggregate_pair_metrics, pair_score  # noqa: E402
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT  # noqa: E402
from src.rewards.answer_reward import PARSER_VERSION  # noqa: E402

SCRIPT = ROOT / "scripts" / "build_track4_premise_v2_gate_readout.py"
REGISTRATION_RELPATH = "docs/registered_track4_premise_v2_design_v1.md"

CT = "ct"
CU = "cu"
W = "w"

PREMISE_GOLDS_DIFFERING = ("W8", "H7")
PREMISE_GOLDS_EQUAL = ("W8", "W8")
FINAL_GOLDS = ("3", "5")
WRONG_ANSWER = "ZZ9"

PREMISE_FAMILY = "premise"
FINAL_FAMILY = "final"
MODES = ("real", "gray", "no_image")
BLIND_MODES = ("gray", "no_image")
CELL_DIRNAME = {
    (PREMISE_FAMILY, "real"): "premise_probe",
    (PREMISE_FAMILY, "gray"): "premise_probe_gray",
    (PREMISE_FAMILY, "no_image"): "premise_probe_no_image",
    (FINAL_FAMILY, "real"): "final",
    (FINAL_FAMILY, "gray"): "final_gray",
    (FINAL_FAMILY, "no_image"): "final_no_image",
}
CELL_FLAG = {
    (PREMISE_FAMILY, "real"): "--probe-real",
    (PREMISE_FAMILY, "gray"): "--probe-gray",
    (PREMISE_FAMILY, "no_image"): "--probe-no-image",
    (FINAL_FAMILY, "real"): "--final-real",
    (FINAL_FAMILY, "gray"): "--final-gray",
    (FINAL_FAMILY, "no_image"): "--final-no-image",
}

PROBE_MANIFEST_RELPATH = "data/fixture/manifest_premise_probe.jsonl"
CAUSAL_MANIFEST_RELPATH = "data/fixture/manifest_causal_pairs.jsonl"
RUN_RELPATH = "experiments/runs/fixture_gates"


# ---------------------------------------------------------------------------
# Corpus construction
# ---------------------------------------------------------------------------


def make_plan(n_pairs: int, n_correct_members: int, untagged: tuple[int, ...] = ()) -> list[str]:
    """Member codes in (pair0.a, pair0.b, pair1.a, ...) order.

    The first `n_correct_members` members are correct; those whose member index
    is in `untagged` are correct WITHOUT satisfying the answer-tags contract.
    """
    assert 0 <= n_correct_members <= 2 * n_pairs
    codes = []
    for index in range(2 * n_pairs):
        if index >= n_correct_members:
            codes.append(W)
        elif index in untagged:
            codes.append(CU)
        else:
            codes.append(CT)
    assert all(index < n_correct_members for index in untagged)
    return codes


def _prediction(gold: str, code: str) -> str:
    if code == CT:
        return f"<answer>{gold}</answer>"
    if code == CU:
        return str(gold)
    if code == W:
        return f"<answer>{WRONG_ANSWER}</answer>"
    raise AssertionError(f"unknown plant code {code!r}")


def _pair_id(itype: str, index: int) -> str:
    return f"{itype}_p{index:04d}"


def _golds(family: str, type_spec: dict[str, Any]) -> tuple[str, str]:
    if family == FINAL_FAMILY:
        return FINAL_GOLDS
    return PREMISE_GOLDS_EQUAL if type_spec["equal_premise_golds"] else PREMISE_GOLDS_DIFFERING


def _manifest_row(family: str, itype: str, type_spec: dict[str, Any], index: int) -> dict[str, Any]:
    gold_a, gold_b = _golds(family, type_spec)
    row: dict[str, Any] = {
        "pair_id": _pair_id(itype, index),
        "intervention_type": itype,
        "template_id": type_spec["template_id"],
        "difficulty_knobs": {
            "n_points": type_spec["n_points"],
            "template_id": type_spec["template_id"],
        },
        "answer_a": gold_a,
        "answer_b": gold_b,
        "category": "t4v2_premise_construct",
        "split": "development",
        "schema_version": "fliptrack.v0",
    }
    if family == PREMISE_FAMILY:
        row["probe"] = "premise"
        row["premise_answer_a"] = gold_a
        row["premise_answer_b"] = gold_b
    return row


def _prediction_row(
    family: str,
    mode: str,
    itype: str,
    type_spec: dict[str, Any],
    index: int,
    code_a: str,
    code_b: str,
) -> dict[str, Any]:
    gold_a, gold_b = _golds(family, type_spec)
    row: dict[str, Any] = {
        "pair_id": _pair_id(itype, index),
        "intervention_type": itype,
        "template_id": type_spec["template_id"],
        "difficulty_knobs": {
            "n_points": type_spec["n_points"],
            "template_id": type_spec["template_id"],
        },
        "eval_image_mode": mode,
        "answer_a": gold_a,
        "answer_b": gold_b,
        "prediction_a": _prediction(gold_a, code_a),
        "prediction_b": _prediction(gold_b, code_b),
    }
    row.update(pair_score(row))
    # The plant must land where it was aimed, or every downstream number is a lie.
    for side, code in (("a", code_a), ("b", code_b)):
        expect_lenient = code in (CT, CU)
        expect_strict = code == CT
        assert row[f"correct_{side}"] is expect_lenient, (
            f"plant drift: {itype} {family}/{mode} pair {index} side {side} code {code}"
            f" scored lenient {row[f'correct_{side}']}, expected {expect_lenient}"
        )
        assert row[f"strict_correct_{side}"] is expect_strict, (
            f"plant drift: {itype} {family}/{mode} pair {index} side {side} code {code}"
            f" scored strict {row[f'strict_correct_{side}']}, expected {expect_strict}"
        )
    assert row["prompt_contract_id"] == DEFAULT_PROMPT_CONTRACT.contract_id
    assert row["parser_version"] == PARSER_VERSION
    return row


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8"
    )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_corpus(root: Path, spec: dict[str, Any]) -> None:
    """Materialize a six-cell corpus, two manifests and a registration copy."""
    types: dict[str, dict[str, Any]] = spec["types"]
    plants: dict[tuple[str, str], dict[str, list[str]]] = spec["plants"]

    probe_rows: list[dict[str, Any]] = []
    causal_rows: list[dict[str, Any]] = []
    for itype in sorted(types):
        type_spec = types[itype]
        for index in range(type_spec["n_causal"]):
            causal_rows.append(_manifest_row(FINAL_FAMILY, itype, type_spec, index))
        for index in range(type_spec.get("n_probe") or 0):
            probe_rows.append(_manifest_row(PREMISE_FAMILY, itype, type_spec, index))
    _write_jsonl(root / PROBE_MANIFEST_RELPATH, probe_rows)
    _write_jsonl(root / CAUSAL_MANIFEST_RELPATH, causal_rows)

    for family in (PREMISE_FAMILY, FINAL_FAMILY):
        for mode in MODES:
            rows: list[dict[str, Any]] = []
            for itype in sorted(types):
                type_spec = types[itype]
                n_pairs = (
                    type_spec["n_causal"]
                    if family == FINAL_FAMILY
                    else (type_spec.get("n_probe") or 0)
                )
                if n_pairs == 0:
                    continue
                codes = plants[(family, mode)][itype]
                assert len(codes) == 2 * n_pairs, (
                    f"plant length mismatch for {itype} {family}/{mode}:"
                    f" {len(codes)} codes for {n_pairs} pairs"
                )
                for index in range(n_pairs):
                    rows.append(
                        _prediction_row(
                            family,
                            mode,
                            itype,
                            type_spec,
                            index,
                            codes[2 * index],
                            codes[2 * index + 1],
                        )
                    )
            cell_dir = root / RUN_RELPATH / CELL_DIRNAME[(family, mode)]
            _write_jsonl(cell_dir / "predictions.jsonl", rows)
            (cell_dir / "metrics.json").write_text(
                json.dumps(
                    {
                        "image_mode": mode,
                        "n_pairs": float(len(rows)),
                        "seed": 0,
                        "noise_seed": 0,
                        "max_new_tokens": 32,
                        "prompt_contract_id": DEFAULT_PROMPT_CONTRACT.contract_id,
                        "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
                        "parser_version": PARSER_VERSION,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

    registration = root / REGISTRATION_RELPATH
    registration.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / REGISTRATION_RELPATH, registration)


# ---------------------------------------------------------------------------
# The standard corpus
# ---------------------------------------------------------------------------
#
# types      chained_premise_easy  n_points  8   10 probe pairs / 10 causal pairs
#            premise_transition    n_points 20   10 probe pairs / 10 causal pairs
#            fact_read             n_points 20   no premise rows / 5 causal pairs
#
# E1 (real images), hand-computed:
#   chained_premise_easy premise: 10/20 lenient members = 0.50  -> in [0.40,0.60]
#                                  7/20 strict  members = 0.35  -> below the band
#   premise_transition   premise:  4/20 = 0.20 (both contracts)
#   chained_premise_easy final  :  2/20 = 0.10 ; premise_transition final 0.00
#   fact_read            final  :  6/10 = 0.60
#
# E2 (blind), hand-computed:
#   ceilings  chained_premise_easy 2/(8-1)  = 0.2857142857142857
#             premise_transition   2/(20-1) = 0.10526315789473684
#   blind premise member accuracy is 0.20 for BOTH types:
#             chained_premise_easy 0.20 <= 0.2857  -> ok
#             premise_transition   0.20 >  0.1053  -> OVER its own ceiling
#   blind final member accuracy: 0.10 / 0.00 / 0.10 (all <= 0.133)
#   => premise_transition FAILS, chained_premise_easy and fact_read PASS.

STANDARD_TYPES: dict[str, dict[str, Any]] = {
    "chained_premise_easy": {
        "n_points": 8,
        "template_id": "t4v2_coordinate_register_n8_v1",
        "n_probe": 10,
        "n_causal": 10,
        "equal_premise_golds": True,
    },
    "premise_transition": {
        "n_points": 20,
        "template_id": "t4v2_coordinate_register_n20_v1",
        "n_probe": 10,
        "n_causal": 10,
        "equal_premise_golds": False,
    },
    "fact_read": {
        "n_points": 20,
        "template_id": "t4v2_coordinate_register_n20_v1",
        "n_probe": None,
        "n_causal": 5,
        "equal_premise_golds": False,
    },
}

STANDARD_PLANTS: dict[tuple[str, str], dict[str, list[str]]] = {
    (PREMISE_FAMILY, "real"): {
        # 10 correct members of 20; members 0,1,2 correct but contract-invalid
        "chained_premise_easy": make_plan(10, 10, untagged=(0, 1, 2)),
        "premise_transition": make_plan(10, 4),
    },
    (PREMISE_FAMILY, "gray"): {
        "chained_premise_easy": make_plan(10, 4),
        "premise_transition": make_plan(10, 4),
    },
    (PREMISE_FAMILY, "no_image"): {
        "chained_premise_easy": make_plan(10, 4),
        "premise_transition": make_plan(10, 4),
    },
    (FINAL_FAMILY, "real"): {
        "chained_premise_easy": make_plan(10, 2),
        "premise_transition": make_plan(10, 0),
        "fact_read": make_plan(5, 6),
    },
    (FINAL_FAMILY, "gray"): {
        "chained_premise_easy": make_plan(10, 2),
        "premise_transition": make_plan(10, 0),
        "fact_read": make_plan(5, 1),
    },
    (FINAL_FAMILY, "no_image"): {
        "chained_premise_easy": make_plan(10, 2),
        "premise_transition": make_plan(10, 0),
        "fact_read": make_plan(5, 1),
    },
}

STANDARD_SPEC: dict[str, Any] = {"types": STANDARD_TYPES, "plants": STANDARD_PLANTS}


def boundary_spec(n_correct_blind_final_members: int) -> dict[str, Any]:
    """One type, 500 causal pairs => blind final member accuracy = k/1000."""
    types = {
        "chained_premise_easy": {
            "n_points": 8,
            "template_id": "t4v2_coordinate_register_n8_v1",
            "n_probe": 3,
            "n_causal": 500,
            "equal_premise_golds": True,
        }
    }
    plants = {
        (PREMISE_FAMILY, "real"): {"chained_premise_easy": make_plan(3, 3)},
        (PREMISE_FAMILY, "gray"): {"chained_premise_easy": make_plan(3, 0)},
        (PREMISE_FAMILY, "no_image"): {"chained_premise_easy": make_plan(3, 0)},
        (FINAL_FAMILY, "real"): {"chained_premise_easy": make_plan(500, 0)},
        (FINAL_FAMILY, "gray"): {
            "chained_premise_easy": make_plan(500, n_correct_blind_final_members)
        },
        (FINAL_FAMILY, "no_image"): {
            "chained_premise_easy": make_plan(500, n_correct_blind_final_members)
        },
    }
    return {"types": types, "plants": plants}


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_readout(
    root: Path,
    *,
    json_name: str = "reports/gate_readout.json",
    markdown_name: str = "reports/gate_readout.md",
    expect: str = "any",
    probe_manifest: str = PROBE_MANIFEST_RELPATH,
    causal_manifest: str = CAUSAL_MANIFEST_RELPATH,
    cell_overrides: dict[tuple[str, str], str] | None = None,
) -> subprocess.CompletedProcess[str]:
    argv = [sys.executable, str(SCRIPT), "--root", str(root)]
    overrides = cell_overrides or {}
    for key, flag in CELL_FLAG.items():
        argv += [flag, overrides.get(key, f"{RUN_RELPATH}/{CELL_DIRNAME[key]}")]
    argv += [
        "--probe-manifest",
        probe_manifest,
        "--causal-manifest",
        causal_manifest,
        "--json-output",
        json_name,
        "--markdown-output",
        markdown_name,
        "--expect",
        expect,
    ]
    return subprocess.run(argv, text=True, capture_output=True, check=False)


def build_and_run(tmp_path: Path, spec: dict[str, Any] | None = None, **kwargs: Any):
    write_corpus(tmp_path, spec or STANDARD_SPEC)
    result = run_readout(tmp_path, **kwargs)
    return result


def load_payload(tmp_path: Path, name: str = "reports/gate_readout.json") -> dict[str, Any]:
    return json.loads((tmp_path / name).read_text(encoding="utf-8"))


def mutate_jsonl(path: Path, mutator) -> None:
    rows = _read_jsonl(path)
    rows = [row for row in (mutator(row) for row in rows) if row is not None]
    _write_jsonl(path, rows)


def cell_predictions(root: Path, family: str, mode: str) -> Path:
    return root / RUN_RELPATH / CELL_DIRNAME[(family, mode)] / "predictions.jsonl"


def _keys_containing(node: Any, needle: str) -> list[str]:
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if needle in key.lower():
                found.append(key)
            found.extend(_keys_containing(value, needle))
    elif isinstance(node, list):
        for item in node:
            found.extend(_keys_containing(item, needle))
    return found


# ---------------------------------------------------------------------------
# 1. Planted accuracies are recovered exactly
# ---------------------------------------------------------------------------


def test_planted_per_type_accuracies_recovered_exactly(tmp_path: Path) -> None:
    result = build_and_run(tmp_path)
    assert result.returncode == 0, result.stderr
    payload = load_payload(tmp_path)
    e1 = payload["e1_difficulty_band"]["per_intervention_type"]

    cpe_premise = e1["chained_premise_easy"]["premise_member_and_pair_accuracy"]
    assert cpe_premise["n_pairs"] == 10
    assert cpe_premise["n_members"] == 20
    assert cpe_premise["lenient"]["member_correct"] == 10
    assert cpe_premise["lenient"]["member_accuracy"] == 10 / 20
    assert cpe_premise["lenient"]["pair_accuracy"] == 5 / 10
    assert cpe_premise["strict"]["member_correct"] == 7
    assert cpe_premise["strict"]["member_accuracy"] == 7 / 20
    assert cpe_premise["strict"]["pair_accuracy"] == 3 / 10

    pt_premise = e1["premise_transition"]["premise_member_and_pair_accuracy"]
    assert pt_premise["lenient"]["member_accuracy"] == 4 / 20
    assert pt_premise["lenient"]["pair_accuracy"] == 2 / 10
    assert pt_premise["strict"]["member_accuracy"] == 4 / 20

    assert (
        e1["chained_premise_easy"]["final_member_and_pair_accuracy"]["lenient"]["member_accuracy"]
        == 2 / 20
    )
    assert (
        e1["premise_transition"]["final_member_and_pair_accuracy"]["lenient"]["member_accuracy"]
        == 0.0
    )
    fact_read = e1["fact_read"]
    assert fact_read["premise_member_and_pair_accuracy"] is None
    assert "no premise fields at all" in fact_read["premise_absent_reason"]
    assert fact_read["final_member_and_pair_accuracy"]["n_pairs"] == 5
    assert fact_read["final_member_and_pair_accuracy"]["lenient"]["member_accuracy"] == 6 / 10
    assert fact_read["final_member_and_pair_accuracy"]["lenient"]["pair_accuracy"] == 3 / 5

    # Section-4 semantics are labelled per type and never pooled together.
    assert "premise_stability" in cpe_premise["premise_pair_accuracy_semantics"]
    assert "premise_transition_accuracy" in pt_premise["premise_pair_accuracy_semantics"]

    # I13: no key anywhere in the two gate blocks pools across intervention types.
    assert _keys_containing(payload["e1_difficulty_band"], "pool") == []
    assert _keys_containing(payload["e2_blind_floor"], "pool") == []
    assert _keys_containing(payload["e1_difficulty_band"], "overall") == []
    assert _keys_containing(payload["e2_blind_floor"], "overall") == []


def test_per_type_numbers_match_the_frozen_repo_aggregator_and_not_the_pooled_one(
    tmp_path: Path,
) -> None:
    """Each type's reported numbers == aggregate_pair_metrics over that type's rows.

    The same function run over the WHOLE cell (pooling every intervention type)
    produces a number that must appear nowhere as a reported endpoint -- that
    pooled value is exactly what I13 forbids and what each cell's own
    metrics.json contains.
    """
    result = build_and_run(tmp_path)
    assert result.returncode == 0, result.stderr
    e1 = load_payload(tmp_path)["e1_difficulty_band"]["per_intervention_type"]

    rows = _read_jsonl(cell_predictions(tmp_path, PREMISE_FAMILY, "real"))
    by_type: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_type.setdefault(row["intervention_type"], []).append(row)
    assert sorted(by_type) == ["chained_premise_easy", "premise_transition"]

    for itype, type_rows in sorted(by_type.items()):
        repo = aggregate_pair_metrics(type_rows)
        block = e1[itype]["premise_member_and_pair_accuracy"]
        assert repo["n_pairs"] == float(block["n_pairs"])
        assert block["lenient"]["member_accuracy"] == repo["member_accuracy"]
        assert block["lenient"]["pair_accuracy"] == repo["pair_accuracy"]
        assert block["strict"]["member_accuracy"] == repo["strict_member_accuracy"]
        assert block["strict"]["pair_accuracy"] == repo["strict_pair_accuracy"]
        assert "aggregate_pair_metrics" in block["accuracy_convention_cross_checked_against"]

    # The pooled reading (10 + 4 correct lenient members over 40) is 0.35 and is
    # not any type's reported lenient endpoint (0.50 and 0.20).
    pooled = aggregate_pair_metrics(rows)
    assert pooled["member_accuracy"] == 14 / 40
    reported_lenient = {
        e1[itype]["premise_member_and_pair_accuracy"]["lenient"]["member_accuracy"]
        for itype in by_type
    }
    assert reported_lenient == {0.50, 0.20}
    assert pooled["member_accuracy"] not in reported_lenient


# ---------------------------------------------------------------------------
# 2. E1 band verdict under both contracts, which here disagree
# ---------------------------------------------------------------------------


def test_e1_band_verdicts_reported_per_contract_and_never_merged(tmp_path: Path) -> None:
    result = build_and_run(tmp_path)
    assert result.returncode == 0, result.stderr
    payload = load_payload(tmp_path)
    e1 = payload["e1_difficulty_band"]
    verdicts = e1["verdict_by_scoring_contract_never_merged_I7"]

    assert e1["band_carrier_intervention_type"] == "chained_premise_easy"
    assert verdicts["lenient"]["value"] == 0.50
    assert verdicts["lenient"]["band_low"] == 0.40
    assert verdicts["lenient"]["band_high"] == 0.60
    assert verdicts["lenient"]["in_band"] is True
    assert verdicts["lenient"]["verdict"] == "PASS"
    assert verdicts["lenient"]["section5_branch_fired"]["branch"] == "a"
    assert "band hit" in verdicts["lenient"]["section5_branch_fired"]["label"]
    assert "`n=8` is frozen as the Phase-2" in verdicts["lenient"]["section5_branch_fired"][
        "registration_quote"
    ]

    assert verdicts["strict"]["value"] == 0.35
    assert verdicts["strict"]["in_band"] is False
    assert verdicts["strict"]["verdict"] == "FAIL"
    assert verdicts["strict"]["section5_branch_fired"]["branch"] == "c"
    assert "still too hard" in verdicts["strict"]["section5_branch_fired"]["label"]
    assert "one pre-committed step to `n=5`" in verdicts["strict"]["section5_branch_fired"][
        "registration_quote"
    ]

    # The two contracts disagree and the instrument reports the disagreement
    # rather than resolving it.
    assert e1["contracts_agree"] is False
    assert "does not choose between them" in e1["contract_not_named_by_registration"]
    # No merged/averaged E1 number exists.
    assert "0.425" not in json.dumps(e1)


def test_e1_band_edges_are_inclusive(tmp_path: Path) -> None:
    """0.40 and 0.60 are inside the band; 0.65 fires branch (b)."""
    for n_correct, expected_verdict, expected_branch in (
        (8, "PASS", "a"),   # 8/20 = 0.40, the lower edge
        (12, "PASS", "a"),  # 12/20 = 0.60, the upper edge
        (13, "FAIL", "b"),  # 13/20 = 0.65, too easy
        (7, "FAIL", "c"),   # 7/20 = 0.35, too hard
    ):
        root = tmp_path / f"edge_{n_correct}"
        root.mkdir()
        plants = {key: dict(value) for key, value in STANDARD_PLANTS.items()}
        plants[(PREMISE_FAMILY, "real")] = {
            "chained_premise_easy": make_plan(10, n_correct),
            "premise_transition": make_plan(10, 4),
        }
        write_corpus(root, {"types": STANDARD_TYPES, "plants": plants})
        result = run_readout(root)
        assert result.returncode == 0, result.stderr
        verdicts = load_payload(root)["e1_difficulty_band"][
            "verdict_by_scoring_contract_never_merged_I7"
        ]
        assert verdicts["lenient"]["value"] == n_correct / 20
        assert verdicts["lenient"]["verdict"] == expected_verdict
        assert verdicts["lenient"]["section5_branch_fired"]["branch"] == expected_branch


# ---------------------------------------------------------------------------
# 3. E2: each type judged by its own n_points ceiling
# ---------------------------------------------------------------------------


def test_e2_each_type_judged_by_its_own_n_points_ceiling(tmp_path: Path) -> None:
    result = build_and_run(tmp_path)
    assert result.returncode == 0, result.stderr
    e2 = load_payload(tmp_path)["e2_blind_floor"]
    per_type = e2["per_intervention_type"]

    assert per_type["chained_premise_easy"]["n_points"] == 8
    assert per_type["chained_premise_easy"]["premise_member_accuracy_ceiling"] == 2 / 7
    assert per_type["premise_transition"]["n_points"] == 20
    assert per_type["premise_transition"]["premise_member_accuracy_ceiling"] == 2 / 19

    for mode in BLIND_MODES:
        # identical blind premise accuracy, opposite verdicts
        cpe = per_type["chained_premise_easy"]["criteria"][mode]["premise_member_accuracy"]
        pt = per_type["premise_transition"]["criteria"][mode]["premise_member_accuracy"]
        assert cpe["value"] == 0.20
        assert pt["value"] == 0.20
        assert cpe["ok"] is True
        assert pt["ok"] is False
        assert per_type["chained_premise_easy"]["criteria"][mode]["final_member_accuracy"][
            "value"
        ] == 2 / 20
        assert per_type["chained_premise_easy"]["criteria"][mode]["final_member_accuracy"][
            "ok"
        ] is True

    assert per_type["chained_premise_easy"]["verdict"] == "PASS"
    assert per_type["premise_transition"]["verdict"] == "FAIL"
    assert e2["failing_types"] == ["premise_transition"]
    assert e2["passing_types"] == ["chained_premise_easy", "fact_read"]
    assert per_type["premise_transition"]["failing_criteria"] == [
        "gray:premise_member_accuracy",
        "no_image:premise_member_accuracy",
    ]

    # fact_read: no premise clause, final criterion only
    assert per_type["fact_read"]["premise_criterion_applicable"] is False
    assert per_type["fact_read"]["premise_member_accuracy_ceiling"] is None
    assert "no premise fields at all" in per_type["fact_read"]["premise_absent_reason"]
    assert per_type["fact_read"]["criteria"]["gray"]["premise_member_accuracy"] is None
    assert per_type["fact_read"]["criteria"]["gray"]["final_member_accuracy"]["value"] == 1 / 10
    assert per_type["fact_read"]["verdict"] == "PASS"

    # The failing type's blind-solvable pair_ids are reported; passing types
    # carry no such list.
    failing = per_type["premise_transition"]
    assert failing["registered_consequence"]["training_use"] == "EXCLUDED"
    assert "excluded from any training use" in failing["registered_consequence"][
        "registration_quote"
    ]
    for mode in BLIND_MODES:
        premise_ids = failing["blind_solvable_pair_ids"][mode]["premise"]
        assert premise_ids["scoring_contract"] == "lenient"
        assert premise_ids["any_member_correct"] == [
            "premise_transition_p0000",
            "premise_transition_p0001",
        ]
        assert premise_ids["both_members_correct"] == [
            "premise_transition_p0000",
            "premise_transition_p0001",
        ]
        final_ids = failing["blind_solvable_pair_ids"][mode]["final"]
        assert final_ids["any_member_correct"] == []
    assert "blind_solvable_pair_ids" not in per_type["chained_premise_easy"]
    assert "blind_solvable_pair_ids" not in per_type["fact_read"]

    # E2's contract of record is lenient; strict is carried separately.
    assert e2["scoring_contract_of_record"] == "lenient"
    strict = e2["strict_contract_reported_separately_NOT_A_CRITERION"]
    assert strict["premise_transition"]["gray"]["premise_member_accuracy_strict"] == 0.20


@pytest.mark.parametrize(
    ("n_correct_members", "accuracy", "verdict"),
    [
        (132, 0.132, "PASS"),
        (133, 0.133, "PASS"),  # exactly at the registered ceiling: <= is inclusive
        (134, 0.134, "FAIL"),
    ],
)
def test_e2_final_ceiling_boundary_both_sides_of_0133(
    tmp_path: Path, n_correct_members: int, accuracy: float, verdict: str
) -> None:
    write_corpus(tmp_path, boundary_spec(n_correct_members))
    result = run_readout(tmp_path)
    assert result.returncode == 0, result.stderr
    e2 = load_payload(tmp_path)["e2_blind_floor"]
    entry = e2["per_intervention_type"]["chained_premise_easy"]
    for mode in BLIND_MODES:
        criterion = entry["criteria"][mode]["final_member_accuracy"]
        assert criterion["value"] == accuracy
        assert criterion["ceiling"] == 0.133
        assert criterion["ok"] is (verdict == "PASS")
    assert entry["verdict"] == verdict
    assert e2["failing_types"] == ([] if verdict == "PASS" else ["chained_premise_easy"])
    if verdict == "FAIL":
        # 134 correct members = the first 67 pairs, both sides
        listing = entry["blind_solvable_pair_ids"]["gray"]["final"]
        assert listing["n_any_member_correct"] == 67
        assert listing["n_both_members_correct"] == 67
        assert listing["any_member_correct"][0] == "chained_premise_easy_p0000"
        assert listing["any_member_correct"][-1] == "chained_premise_easy_p0066"
    else:
        assert "blind_solvable_pair_ids" not in entry


# ---------------------------------------------------------------------------
# 4. Refusals
# ---------------------------------------------------------------------------


def _assert_refused(result: subprocess.CompletedProcess[str], needle: str, root: Path) -> None:
    assert result.returncode == 2, f"expected refusal, got rc={result.returncode}\n{result.stdout}"
    assert "REFUSED:" in result.stderr
    assert needle in result.stderr, result.stderr
    assert not (root / "reports/gate_readout.json").exists()
    assert not (root / "reports/gate_readout.md").exists()


def test_refuses_unmatched_prediction_row(tmp_path: Path) -> None:
    write_corpus(tmp_path, STANDARD_SPEC)
    path = cell_predictions(tmp_path, FINAL_FAMILY, "gray")

    def mutator(row: dict[str, Any]) -> dict[str, Any]:
        if row["pair_id"] == "fact_read_p0000":
            row["pair_id"] = "fact_read_p9999_not_in_manifest"
        return row

    mutate_jsonl(path, mutator)
    _assert_refused(run_readout(tmp_path), "have no manifest row", tmp_path)


def test_refuses_duplicate_pair_id(tmp_path: Path) -> None:
    write_corpus(tmp_path, STANDARD_SPEC)
    path = cell_predictions(tmp_path, PREMISE_FAMILY, "real")
    rows = _read_jsonl(path)
    rows.append(dict(rows[0]))
    _write_jsonl(path, rows)
    _assert_refused(run_readout(tmp_path), "duplicate pair_id", tmp_path)


def test_refuses_duplicate_pair_id_in_manifest(tmp_path: Path) -> None:
    write_corpus(tmp_path, STANDARD_SPEC)
    path = tmp_path / CAUSAL_MANIFEST_RELPATH
    rows = _read_jsonl(path)
    rows.append(dict(rows[0]))
    _write_jsonl(path, rows)
    _assert_refused(run_readout(tmp_path), "duplicate pair_id", tmp_path)


def test_refuses_missing_intervention_type(tmp_path: Path) -> None:
    write_corpus(tmp_path, STANDARD_SPEC)
    path = cell_predictions(tmp_path, FINAL_FAMILY, "no_image")

    def mutator(row: dict[str, Any]) -> dict[str, Any]:
        if row["pair_id"] == "premise_transition_p0003":
            row.pop("intervention_type")
        return row

    mutate_jsonl(path, mutator)
    _assert_refused(run_readout(tmp_path), "'intervention_type' is absent", tmp_path)


def test_refuses_non_single_valued_n_points_within_a_type(tmp_path: Path) -> None:
    write_corpus(tmp_path, STANDARD_SPEC)
    target = "premise_transition_p0005"

    def mutator(row: dict[str, Any]) -> dict[str, Any]:
        if row["pair_id"] == target:
            row["difficulty_knobs"] = dict(row["difficulty_knobs"], n_points=9)
        return row

    for family in (PREMISE_FAMILY, FINAL_FAMILY):
        for mode in MODES:
            mutate_jsonl(cell_predictions(tmp_path, family, mode), mutator)
    for manifest in (PROBE_MANIFEST_RELPATH, CAUSAL_MANIFEST_RELPATH):
        mutate_jsonl(tmp_path / manifest, mutator)

    _assert_refused(
        run_readout(tmp_path),
        "difficulty_knobs.n_points is not single-valued",
        tmp_path,
    )


def test_refuses_missing_n_points(tmp_path: Path) -> None:
    write_corpus(tmp_path, STANDARD_SPEC)

    def mutator(row: dict[str, Any]) -> dict[str, Any]:
        if row["pair_id"] == "premise_transition_p0002":
            knobs = dict(row["difficulty_knobs"])
            knobs.pop("n_points")
            row["difficulty_knobs"] = knobs
        return row

    mutate_jsonl(tmp_path / PROBE_MANIFEST_RELPATH, mutator)
    _assert_refused(run_readout(tmp_path), "'difficulty_knobs.n_points' is absent", tmp_path)


def test_refuses_tampered_banked_verdict(tmp_path: Path) -> None:
    """A hand-edited verdict field is caught by the independent re-score."""
    write_corpus(tmp_path, STANDARD_SPEC)
    path = cell_predictions(tmp_path, FINAL_FAMILY, "gray")

    def mutator(row: dict[str, Any]) -> dict[str, Any]:
        if row["pair_id"] == "premise_transition_p0000":
            row["correct_a"] = True  # the prediction is ZZ9; the verdict is a lie
        return row

    mutate_jsonl(path, mutator)
    _assert_refused(
        run_readout(tmp_path),
        "not reproduced by src.eval.fliptrack_metrics.pair_score",
        tmp_path,
    )


def test_refuses_mixed_equal_gold_within_one_type(tmp_path: Path) -> None:
    """Pooling stability items with transition items would merge two I13 metrics."""
    write_corpus(tmp_path, STANDARD_SPEC)
    target = "premise_transition_p0009"

    def manifest_mutator(row: dict[str, Any]) -> dict[str, Any]:
        if row["pair_id"] == target:
            row["answer_b"] = row["answer_a"]
            row["premise_answer_b"] = row["premise_answer_a"]
        return row

    mutate_jsonl(tmp_path / PROBE_MANIFEST_RELPATH, manifest_mutator)
    for mode in MODES:
        path = cell_predictions(tmp_path, PREMISE_FAMILY, mode)
        rows = _read_jsonl(path)
        rebuilt = []
        for row in rows:
            if row["pair_id"] == target:
                base = {
                    key: row[key]
                    for key in (
                        "pair_id",
                        "intervention_type",
                        "template_id",
                        "difficulty_knobs",
                        "eval_image_mode",
                        "prediction_a",
                        "prediction_b",
                    )
                }
                base["answer_a"] = row["answer_a"]
                base["answer_b"] = row["answer_a"]
                base.update(pair_score(base))
                row = base
            rebuilt.append(row)
        _write_jsonl(path, rebuilt)

    _assert_refused(run_readout(tmp_path), "mix equal-gold", tmp_path)


def test_refuses_swapped_manifests(tmp_path: Path) -> None:
    write_corpus(tmp_path, STANDARD_SPEC)
    result = run_readout(
        tmp_path,
        probe_manifest=CAUSAL_MANIFEST_RELPATH,
        causal_manifest=PROBE_MANIFEST_RELPATH,
    )
    _assert_refused(result, "manifests were swapped", tmp_path)


def test_refuses_cell_with_wrong_image_mode(tmp_path: Path) -> None:
    write_corpus(tmp_path, STANDARD_SPEC)
    result = run_readout(
        tmp_path,
        cell_overrides={
            (PREMISE_FAMILY, "real"): f"{RUN_RELPATH}/{CELL_DIRNAME[(PREMISE_FAMILY, 'gray')]}"
        },
    )
    _assert_refused(result, "image_mode is 'gray', expected 'real'", tmp_path)


def test_refuses_registration_drift(tmp_path: Path) -> None:
    write_corpus(tmp_path, STANDARD_SPEC)
    registration = tmp_path / REGISTRATION_RELPATH
    text = registration.read_text(encoding="utf-8")
    assert "one pre-committed step to `n=5`" in text
    registration.write_text(
        text.replace("one pre-committed step to `n=5`", "one pre-committed step to `n=4`"),
        encoding="utf-8",
    )
    _assert_refused(run_readout(tmp_path), "registration drift", tmp_path)


def test_refuses_missing_registration(tmp_path: Path) -> None:
    write_corpus(tmp_path, STANDARD_SPEC)
    (tmp_path / REGISTRATION_RELPATH).unlink()
    _assert_refused(run_readout(tmp_path), "missing registration document", tmp_path)


def test_refuses_to_overwrite_existing_outputs(tmp_path: Path) -> None:
    result = build_and_run(tmp_path)
    assert result.returncode == 0, result.stderr
    before_json = (tmp_path / "reports/gate_readout.json").read_bytes()
    before_md = (tmp_path / "reports/gate_readout.md").read_bytes()
    again = run_readout(tmp_path)
    assert again.returncode == 2
    assert "refusing to overwrite" in again.stderr
    assert (tmp_path / "reports/gate_readout.json").read_bytes() == before_json
    assert (tmp_path / "reports/gate_readout.md").read_bytes() == before_md


def test_expect_registered_refuses_a_non_section8_composition(tmp_path: Path) -> None:
    write_corpus(tmp_path, STANDARD_SPEC)
    result = run_readout(tmp_path, expect="registered")
    _assert_refused(result, "section-8 composition violated", tmp_path)


def test_refuses_incomplete_cell(tmp_path: Path) -> None:
    write_corpus(tmp_path, STANDARD_SPEC)
    path = cell_predictions(tmp_path, PREMISE_FAMILY, "no_image")

    def mutator(row: dict[str, Any]):
        return None if row["pair_id"] == "chained_premise_easy_p0007" else row

    mutate_jsonl(path, mutator)
    _assert_refused(run_readout(tmp_path), "have no prediction", tmp_path)


# ---------------------------------------------------------------------------
# 5. Determinism and the markdown twin
# ---------------------------------------------------------------------------


def test_outputs_are_byte_deterministic(tmp_path: Path) -> None:
    write_corpus(tmp_path, STANDARD_SPEC)
    json_path = tmp_path / "reports/gate_readout.json"
    markdown_path = tmp_path / "reports/gate_readout.md"

    first = run_readout(tmp_path)
    assert first.returncode == 0, first.stderr
    first_json = json_path.read_bytes()
    first_markdown = markdown_path.read_bytes()
    assert not re.search(
        r"\d{4}-\d{2}-\d{2}T\d{2}", first_json.decode("utf-8")
    ), "no build timestamp may leak into the artifact"

    json_path.unlink()
    markdown_path.unlink()
    second = run_readout(tmp_path)
    assert second.returncode == 0, second.stderr
    assert json_path.read_bytes() == first_json
    assert markdown_path.read_bytes() == first_markdown


def test_markdown_twin_carries_verdicts_provenance_and_quotes(tmp_path: Path) -> None:
    result = build_and_run(tmp_path)
    assert result.returncode == 0, result.stderr
    markdown = (tmp_path / "reports/gate_readout.md").read_text(encoding="utf-8")
    payload = load_payload(tmp_path)

    assert "# Track-4 premise-v2 acceptance gates E1 + E2" in markdown
    # registered criteria are quoted verbatim
    assert "Pass: `chained_premise_easy` premise member accuracy in" in markdown
    assert "blind (no_image and gray) **final** member accuracy ≤ 0.133" in markdown
    assert "one pre-committed step to `n=5`" in markdown  # branch (c), fired by strict
    assert "`n=8` is frozen as the Phase-2" in markdown  # branch (a), fired by lenient
    # verdicts and the failing type's pair_ids
    assert "0.500000" in markdown and "0.350000" in markdown
    assert "premise_transition_p0000" in markdown
    # provenance
    assert payload["provenance"]["manifests"]["premise_probe"]["sha256"] in markdown
    assert payload["provenance"]["cells"]["final_gray"]["predictions_sha256"] in markdown
    assert "NOT the registered endpoint" in markdown or "NOT the endpoint" in markdown


def test_provenance_and_schema_are_complete(tmp_path: Path) -> None:
    result = build_and_run(tmp_path)
    assert result.returncode == 0, result.stderr
    payload = load_payload(tmp_path)
    assert payload["schema_version"] == "blind-gains.track4-premise-v2-gate-readout.v1"
    provenance = payload["provenance"]
    assert set(provenance["cells"]) == {
        "premise_probe_real",
        "premise_probe_gray",
        "premise_probe_no_image",
        "final_real",
        "final_gray",
        "final_no_image",
    }
    for cell in provenance["cells"].values():
        assert len(cell["predictions_sha256"]) == 64
        assert len(cell["metrics_sha256"]) == 64
        assert cell["n_rows"] > 0
        assert "NOT the registered endpoint" in cell["metrics_note"]
    assert provenance["cells"]["premise_probe_real"]["rows_by_intervention_type"] == {
        "chained_premise_easy": 10,
        "premise_transition": 10,
    }
    assert provenance["cells"]["final_real"]["rows_by_intervention_type"] == {
        "chained_premise_easy": 10,
        "fact_read": 5,
        "premise_transition": 10,
    }
    assert provenance["manifests"]["premise_probe"]["n_rows"] == 20
    assert provenance["manifests"]["causal_pairs"]["n_rows"] == 25
    assert len(provenance["registration"]["sha256"]) == 64
    assert "e1_readout" in provenance["registration"]["quotes_verified"]
    assert "section5_branch_a" in provenance["registration"]["quotes_verified"]
    assert payload["decoding_lock"]["prompt_contract_id"] == "answer-tags-v1"
    assert payload["decoding_lock"]["parser_version"] == PARSER_VERSION
    # git HEAD is recorded exactly or recorded as null; never fabricated
    assert provenance["git_head"] is None or len(provenance["git_head"]) == 40
    assert payload["per_intervention_type_n_points"] == {
        "chained_premise_easy": 8,
        "fact_read": 20,
        "premise_transition": 20,
    }
