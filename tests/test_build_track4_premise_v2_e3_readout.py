"""Adversarial fixtures for the Track-4 premise-v2 E3 per-type readout (I10).

Synthetic rows only; must pass before the instrument reads a real cell.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_track4_premise_v2_e3_readout import (  # noqa: E402
    E3_MARGIN,
    REGISTERED_FINAL_BLIND_CEILING,
    ReadoutRefusal,
    SCHEMA_VERSION,
    build_report,
    render_markdown,
)

TYPES = ("premise_transition", "premise_transition_easy", "chained_premise", "fact_read")


def _row(pair_id, n_correct_members, strict_correct_members=None):
    """n_correct_members in {0,1,2}; strict defaults to the same."""
    if strict_correct_members is None:
        strict_correct_members = n_correct_members
    return {
        "pair_id": pair_id,
        "template_id": "t4v2_coordinate_register_n20_v1",
        "parser_version": "canonical-v2",
        "prompt_contract_id": "answer-tags-v1",
        "acc_final_a": n_correct_members >= 1,
        "acc_final_b": n_correct_members >= 2,
        "acc_strict_a": strict_correct_members >= 1,
        "acc_strict_b": strict_correct_members >= 2,
        "pair_correct": n_correct_members == 2,
        "strict_pair_correct": strict_correct_members == 2,
        "collapsed": False,
    }


def _write(tmp_path, preds, manifest_rows):
    p = tmp_path / "predictions.jsonl"
    m = tmp_path / "manifest_causal_pairs.jsonl"
    p.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in preds), encoding="utf-8")
    m.write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in manifest_rows), encoding="utf-8"
    )
    return p, m


def _bench(tmp_path, plan):
    """plan: {type: [n_correct_members, ...]} -> (predictions path, manifest path)"""
    preds, manifest = [], []
    for itype, counts in plan.items():
        for i, n in enumerate(counts):
            pid = f"t4v2c_{itype}_{i:04d}"
            preds.append(_row(pid, n))
            manifest.append({"pair_id": pid, "intervention_type": itype})
    return _write(tmp_path, preds, manifest)


def test_planted_per_type_member_accuracy_recovered_exactly(tmp_path):
    # premise_transition: 10 pairs, 3 correct members of 20 -> 0.15
    # fact_read:          10 pairs, 12 correct members of 20 -> 0.60
    plan = {
        "premise_transition": [2, 1] + [0] * 8,
        "fact_read": [2] * 6 + [0] * 4,
    }
    p, m = _bench(tmp_path, plan)
    report = build_report(p, m)
    assert report["schema_version"] == SCHEMA_VERSION
    pt = report["per_intervention_type"]["premise_transition"]
    fr = report["per_intervention_type"]["fact_read"]
    assert pt["caption_member_accuracy_lenient"] == pytest.approx(0.15)
    assert fr["caption_member_accuracy_lenient"] == pytest.approx(0.60)
    assert pt["n_members"] == 20 and fr["n_members"] == 20
    # ceiling (a) = 0.133 + 0.10 = 0.233
    assert pt["readings"]["a_registered_ceiling"]["e3_ceiling"] == pytest.approx(0.233)
    assert pt["readings"]["a_registered_ceiling"]["lenient_verdict"] == "PASS"
    assert fr["readings"]["a_registered_ceiling"]["lenient_verdict"] == "FAIL"
    assert report["summary"]["failing_types_under_reading_a"] == ["fact_read"]


def test_boundary_is_inclusive_at_the_ceiling(tmp_path):
    # exactly 0.233 must PASS ("<=" in the registered text). 0.233 * 20 is not an
    # integer, so use a type whose accuracy lands exactly on the ceiling via
    # reading (b) with a planted floor.
    plan = {"chained_premise": [2, 2] + [0] * 8}  # 4/20 = 0.20
    p, m = _bench(tmp_path, plan)
    report = build_report(p, m, measured_blind_floors={"chained_premise": 0.10})
    b = report["per_intervention_type"]["chained_premise"]["readings"]["b_measured_floor"]
    assert b["e3_ceiling"] == pytest.approx(0.20)
    assert b["lenient_verdict"] == "PASS"  # 0.20 <= 0.20


def test_both_readings_reported_and_disagreement_flagged(tmp_path):
    plan = {"premise_transition": [2, 2, 1] + [0] * 7}  # 5/20 = 0.25
    p, m = _bench(tmp_path, plan)
    report = build_report(p, m, measured_blind_floors={"premise_transition": 0.1375})
    e = report["per_intervention_type"]["premise_transition"]
    a = e["readings"]["a_registered_ceiling"]
    b = e["readings"]["b_measured_floor"]
    assert a["e3_ceiling"] == pytest.approx(0.233)
    assert b["e3_ceiling"] == pytest.approx(0.2375)
    assert a["lenient_verdict"] == "FAIL"   # 0.25 > 0.233
    assert b["lenient_verdict"] == "FAIL"   # 0.25 > 0.2375
    assert e["readings_agree"] is True
    # now a case where they disagree
    plan2 = {"premise_transition": [2, 2] + [1] + [0] * 7}
    # same 0.25; instead move the floor so (b) passes
    p2, m2 = _bench(tmp_path / "x", plan2) if False else (p, m)
    report2 = build_report(p2, m2, measured_blind_floors={"premise_transition": 0.20})
    e2 = report2["per_intervention_type"]["premise_transition"]
    assert e2["readings"]["a_registered_ceiling"]["lenient_verdict"] == "FAIL"
    assert e2["readings"]["b_measured_floor"]["lenient_verdict"] == "PASS"  # 0.25 <= 0.30
    assert e2["readings_agree"] is False


def test_contracts_reported_separately_and_never_merged(tmp_path):
    preds, manifest = [], []
    for i in range(10):
        pid = f"t4v2c_chained_premise_{i:04d}"
        # lenient 2 correct, strict 0 correct -> the contracts must differ
        preds.append(_row(pid, 2 if i < 3 else 0, strict_correct_members=0))
        manifest.append({"pair_id": pid, "intervention_type": "chained_premise"})
    p, m = _write(tmp_path, preds, manifest)
    e = build_report(p, m)["per_intervention_type"]["chained_premise"]
    assert e["caption_member_accuracy_lenient"] == pytest.approx(0.30)
    assert e["caption_member_accuracy_strict"] == pytest.approx(0.0)
    a = e["readings"]["a_registered_ceiling"]
    assert a["lenient_verdict"] == "FAIL" and a["strict_verdict"] == "PASS"


def test_pair_id_missing_from_causal_manifest_refused(tmp_path):
    plan = {"premise_transition": [0] * 4}
    p, m = _bench(tmp_path, plan)
    rows = [json.loads(l) for l in m.read_text().splitlines() if l.strip()]
    m.write_text("".join(json.dumps(r) + "\n" for r in rows[:-1]), encoding="utf-8")
    with pytest.raises(ReadoutRefusal, match="not in the causal manifest"):
        build_report(p, m)


def test_manifest_row_without_intervention_type_refused(tmp_path):
    plan = {"fact_read": [0] * 4}
    p, m = _bench(tmp_path, plan)
    rows = [json.loads(l) for l in m.read_text().splitlines() if l.strip()]
    rows[0].pop("intervention_type")
    m.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    with pytest.raises(ReadoutRefusal, match="no intervention_type"):
        build_report(p, m)


def test_duplicate_pair_id_refused(tmp_path):
    plan = {"fact_read": [0] * 3}
    p, m = _bench(tmp_path, plan)
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    p.write_text(
        "".join(json.dumps(r) + "\n" for r in rows + [rows[0]]), encoding="utf-8"
    )
    with pytest.raises(ReadoutRefusal, match="duplicate pair_id"):
        build_report(p, m)


def test_wrong_parser_version_refused(tmp_path):
    plan = {"fact_read": [0] * 3}
    p, m = _bench(tmp_path, plan)
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    rows[0]["parser_version"] = "legacy-v1"
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    with pytest.raises(ReadoutRefusal, match="parser_version"):
        build_report(p, m)


def test_missing_measured_floor_refused_when_reading_b_requested(tmp_path):
    plan = {"fact_read": [0] * 3, "chained_premise": [0] * 3}
    p, m = _bench(tmp_path, plan)
    with pytest.raises(ReadoutRefusal, match="measured blind floor not supplied"):
        build_report(p, m, measured_blind_floors={"fact_read": 0.2})


def test_pooled_value_is_labelled_not_an_endpoint(tmp_path):
    plan = {"fact_read": [2] * 5, "chained_premise": [0] * 5}
    p, m = _bench(tmp_path, plan)
    report = build_report(p, m)
    assert "POOLED_ACROSS_TYPES_NOT_AN_ENDPOINT" in report
    for key in report:
        if "pooled" in key.lower():
            assert "NOT_AN_ENDPOINT" in key


def test_unlabelled_pooled_key_is_refused_by_the_audit(tmp_path):
    import scripts.build_track4_premise_v2_e3_readout as mod

    plan = {"fact_read": [0] * 4}
    p, m = _bench(tmp_path, plan)
    report = build_report(p, m)
    report["summary"]["pooled_member_accuracy"] = 0.1
    with pytest.raises(ReadoutRefusal, match="pooled key without NOT_AN_ENDPOINT"):
        mod._audit(report["summary"], "/summary")


def test_deterministic_and_markdown_renders_every_type(tmp_path):
    plan = {"premise_transition": [1] * 6, "fact_read": [2] * 6}
    p, m = _bench(tmp_path, plan)
    first = json.dumps(build_report(p, m), sort_keys=True)
    second = json.dumps(build_report(p, m), sort_keys=True)
    assert first == second
    md = render_markdown(build_report(p, m))
    assert "premise_transition" in md and "fact_read" in md
    assert "lenient" in md.lower() and "strict" in md.lower()


def test_refuses_to_overwrite_existing_output(tmp_path, monkeypatch):
    import scripts.build_track4_premise_v2_e3_readout as mod

    plan = {"fact_read": [0] * 3}
    p, m = _bench(tmp_path, plan)
    out = tmp_path / "e3.json"
    out.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", [
        "build_track4_premise_v2_e3_readout.py",
        "--predictions", str(p),
        "--causal-manifest", str(m),
        "--json-output", str(out),
    ])
    with pytest.raises(FileExistsError):
        mod.main()


def test_registered_constants_are_what_the_registration_says():
    assert REGISTERED_FINAL_BLIND_CEILING == 0.133
    assert E3_MARGIN == 0.10
