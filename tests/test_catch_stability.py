"""Adversarial fixtures (I10) for the catch-trial invariance scorer.

Every fixture here encodes a way the instrument could silently lie, headed by
the decisive row from reports/f8_secondaries_v1.md section 2.2: a pair whose
members AGREE but are both WRONG satisfies the invariance criterion while every
pre-existing pair_score field reads negative and cannot distinguish it from a
DISAGREEING pair.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.build_mini_a5_catch_eval_manifest import (
    PINNED_SOURCE_SHA256,
    main as adapter_main,
)
from src.eval.catch_stability import (
    BASE_SEED,
    INDICATORS,
    CatchScoreError,
    aggregate_by_template,
    build_readout,
    catch_pair_score,
    compare_arms,
    main as scorer_main,
    mcnemar_exact_bool,
    paired_bootstrap_diff,
    resolve_seed,
)
from src.eval.fliptrack_metrics import pair_score

REPO_ROOT = Path(__file__).resolve().parents[1]


def _catch_row(uid: str, template: str, gold: str, pred_a: str, pred_b: str) -> dict:
    return {
        "pair_group_uid": uid,
        "pair_id": uid,
        "template_id": template,
        "question": "What code is in row R4, column C2?",
        "answer_a": gold,
        "answer_b": gold,
        "prediction_a": pred_a,
        "prediction_b": pred_b,
    }


# ---------------------------------------------------------------------------
# 1. The decisive row: members agree, both wrong.
# ---------------------------------------------------------------------------

def test_decisive_agree_both_wrong() -> None:
    row = _catch_row("c1", "tpl_a", "B9U", "<answer>C1X</answer>", "<answer>C1X</answer>")
    scored = catch_pair_score(row)
    assert scored["stable_lenient"] is True
    assert scored["stable_strict"] is True  # both in contract
    assert scored["correct_a"] is False
    assert scored["correct_b"] is False
    assert scored["pair_correct"] is False
    assert scored["strict_pair_correct"] is False
    assert scored["stable_and_correct_lenient"] is False
    assert scored["stable_and_correct_strict"] is False
    # The pre-existing agreement field is identically False on equal-gold rows
    # (gated on answer_a != answer_b) — the reason this instrument exists.
    assert pair_score(row)["collapsed"] is False


def test_decisive_row_distinguishable_from_disagreeing_pair() -> None:
    agree_wrong = _catch_row("c1", "tpl_a", "B9U", "<answer>C1X</answer>", "<answer>C1X</answer>")
    disagree = _catch_row("c2", "tpl_a", "B9U", "<answer>B9U</answer>", "<answer>C1X</answer>")
    old_fields = ("pair_correct", "strict_pair_correct", "collapsed")
    old_agree = {key: pair_score(agree_wrong)[key] for key in old_fields}
    old_disagree = {key: pair_score(disagree)[key] for key in old_fields}
    # No pre-existing field separates the two behaviours...
    assert old_agree == old_disagree == {
        "pair_correct": False,
        "strict_pair_correct": False,
        "collapsed": False,
    }
    # ...the new invariance field does.
    assert catch_pair_score(agree_wrong)["stable_lenient"] is True
    assert catch_pair_score(disagree)["stable_lenient"] is False
    assert catch_pair_score(disagree)["stable_strict"] is False


def test_agree_both_right() -> None:
    scored = catch_pair_score(
        _catch_row("c3", "tpl_a", "B9U", "<answer>B9U</answer>", "<answer>B9U</answer>")
    )
    assert scored["stable_lenient"] is True
    assert scored["stable_strict"] is True
    assert scored["pair_correct"] is True
    assert scored["strict_pair_correct"] is True
    assert scored["stable_and_correct_lenient"] is True
    assert scored["stable_and_correct_strict"] is True


# ---------------------------------------------------------------------------
# 2. Agreement reached only out of contract: lenient-stable, never strict.
# ---------------------------------------------------------------------------

def test_out_of_contract_agreement_is_lenient_only() -> None:
    row = _catch_row("c4", "tpl_a", "B9U", "Answer: B9U", "Answer: B9U")
    scored = catch_pair_score(row)
    assert scored["contract_valid_a"] is False
    assert scored["contract_valid_b"] is False
    assert scored["stable_lenient"] is True
    assert scored["stable_strict"] is False
    assert scored["stable_and_correct_strict"] is False
    # correctness severities split the same way (I7)
    assert scored["pair_correct"] is True
    assert scored["strict_pair_correct"] is False


def test_empty_agreement_is_lenient_only() -> None:
    # Degenerate agreement (two empty generations) must not count as strict.
    scored = catch_pair_score(_catch_row("c5", "tpl_a", "B9U", "", ""))
    assert scored["stable_lenient"] is True
    assert scored["stable_strict"] is False
    assert scored["pair_correct"] is False


def test_one_sided_contract_break_is_not_strict_stable() -> None:
    scored = catch_pair_score(
        _catch_row("c6", "tpl_a", "B9U", "<answer>B9U</answer>", "Answer: B9U")
    )
    assert scored["stable_lenient"] is True
    assert scored["stable_strict"] is False


# ---------------------------------------------------------------------------
# 3. Scorer refuses rows outside its domain.
# ---------------------------------------------------------------------------

def test_rejects_non_equal_gold_pairs() -> None:
    row = _catch_row("c7", "tpl_a", "B9U", "<answer>B9U</answer>", "<answer>B9U</answer>")
    row["answer_b"] = "C1X"
    with pytest.raises(CatchScoreError, match="equal-gold"):
        catch_pair_score(row)


def test_rejects_missing_uid_or_template() -> None:
    base = _catch_row("c8", "tpl_a", "B9U", "<answer>B9U</answer>", "<answer>B9U</answer>")
    for key in ("pair_group_uid", "template_id"):
        row = dict(base)
        row[key] = ""
        with pytest.raises(CatchScoreError):
            catch_pair_score(row)
        row.pop(key)
        with pytest.raises(CatchScoreError):
            catch_pair_score(row)


# ---------------------------------------------------------------------------
# 4. Template pooling is structurally impossible (I13).
# ---------------------------------------------------------------------------

def _two_template_rows() -> list[dict]:
    return [
        catch_pair_score(row)
        for row in (
            _catch_row("p1", "tpl_a", "B9U", "<answer>B9U</answer>", "<answer>B9U</answer>"),
            _catch_row("p2", "tpl_a", "B9U", "<answer>C1X</answer>", "<answer>C1X</answer>"),
            _catch_row("p3", "tpl_b", "7", "<answer>7</answer>", "<answer>8</answer>"),
            _catch_row("p4", "tpl_b", "7", "Answer: 7", "Answer: 7"),
        )
    ]


def _walk(node, path=()):  # yields (path, key) for every mapping key
    if isinstance(node, dict):
        for key, value in node.items():
            yield path, key
            yield from _walk(value, path + (key,))
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item, path)


def test_aggregate_schema_has_no_pooled_slot() -> None:
    result = aggregate_by_template(_two_template_rows())
    assert set(result.keys()) == {"per_template"}
    assert set(result["per_template"].keys()) == {"tpl_a", "tpl_b"}
    forbidden = ("pooled", "overall", "all_templates", "combined", "micro", "macro")
    for path, key in _walk(result):
        assert not any(marker in str(key).lower() for marker in forbidden), (path, key)
    # every indicator rate lives under a concrete template id
    indicator_names = {name for name, _, _ in INDICATORS}
    for path, key in _walk(result):
        if key in indicator_names or key == "rate":
            assert path and path[0] == "per_template" and len(path) >= 2, (path, key)


def test_aggregate_rates_hand_checked() -> None:
    result = aggregate_by_template(_two_template_rows())
    tpl_a = result["per_template"]["tpl_a"]
    assert tpl_a["n_pairs"] == 2
    assert tpl_a["stable_lenient"] == {
        "count": 2, "rate": 1.0, "indicator_family": "stability", "severity": "lenient",
    }
    assert tpl_a["pair_correct"]["count"] == 1 and tpl_a["pair_correct"]["rate"] == 0.5
    tpl_b = result["per_template"]["tpl_b"]
    assert tpl_b["stable_lenient"]["count"] == 1  # p3 disagrees, p4 agrees
    assert tpl_b["stable_strict"]["count"] == 0  # p4 agrees out of contract
    assert tpl_b["pair_correct"]["count"] == 1  # p4 lenient-correct
    assert tpl_b["strict_pair_correct"]["count"] == 0


def test_aggregate_refuses_rows_without_template() -> None:
    rows = _two_template_rows()
    rows[0] = dict(rows[0])
    del rows[0]["template_id"]
    with pytest.raises(CatchScoreError, match="template_id"):
        aggregate_by_template(rows)


def test_readout_has_no_pooled_slot_end_to_end() -> None:
    cp = [
        _catch_row("p1", "tpl_a", "B9U", "<answer>B9U</answer>", "<answer>B9U</answer>"),
        _catch_row("p3", "tpl_b", "7", "<answer>7</answer>", "<answer>8</answer>"),
    ]
    member = [
        _catch_row("p1", "tpl_a", "B9U", "<answer>C1X</answer>", "<answer>C1X</answer>"),
        _catch_row("p3", "tpl_b", "7", "<answer>7</answer>", "<answer>7</answer>"),
    ]
    readout = build_readout(cp, member, expect_registered_shape=False)
    indicator_names = {name for name, _, _ in INDICATORS}
    for path, key in _walk(readout):
        if (key in indicator_names and "indicator_indices" not in path) or key == "rate":
            assert "per_template" in path, (path, key)


# ---------------------------------------------------------------------------
# 5. Registered seed derivation and comparison machinery.
# ---------------------------------------------------------------------------

def test_registered_indicator_order_is_fixed() -> None:
    # Reordering INDICATORS would silently remap bootstrap seeds.
    assert INDICATORS == (
        ("stable_lenient", "stability", "lenient"),
        ("stable_strict", "stability", "strict"),
        ("pair_correct", "correctness", "lenient"),
        ("strict_pair_correct", "correctness", "strict"),
        ("stable_and_correct_lenient", "joint", "lenient"),
        ("stable_and_correct_strict", "joint", "strict"),
    )


def test_seed_derivation() -> None:
    assert BASE_SEED == 20260729
    assert resolve_seed(0, 0) == 20260729
    assert resolve_seed(1, 0) == 20261729
    assert resolve_seed(0, 2) == 20260749
    assert resolve_seed(5, 2) == 20265749


def test_compare_arms_seeds_follow_registration() -> None:
    cp = [
        catch_pair_score(_catch_row(f"u{i}", tpl, "7", "<answer>7</answer>", "<answer>7</answer>"))
        for i, tpl in enumerate(["tpl_a"] * 3 + ["tpl_b"] * 3)
    ]
    member = [
        catch_pair_score(_catch_row(f"u{i}", tpl, "7", "<answer>7</answer>", "<answer>8</answer>"))
        for i, tpl in enumerate(["tpl_a"] * 3 + ["tpl_b"] * 3)
    ]
    result = compare_arms(cp, member)
    for template, block in result["per_template"].items():
        t_idx = block["template_index"]
        assert t_idx == sorted(result["per_template"]).index(template)
        for i_idx, (indicator, _, _) in enumerate(INDICATORS):
            entry = block["cp_minus_member"][indicator]
            assert entry["indicator_index"] == i_idx
            assert entry["bootstrap_seed"] == BASE_SEED + 1000 * i_idx + 10 * t_idx
            assert entry["resamples"] == 10000


def test_compare_arms_refuses_mismatched_uid_sets() -> None:
    cp = [catch_pair_score(_catch_row("u1", "tpl_a", "7", "<answer>7</answer>", "<answer>7</answer>"))]
    member = [catch_pair_score(_catch_row("u2", "tpl_a", "7", "<answer>7</answer>", "<answer>7</answer>"))]
    with pytest.raises(CatchScoreError, match="different pair_group_uid sets"):
        compare_arms(cp, member)


def test_compare_arms_refuses_template_disagreement() -> None:
    cp = [catch_pair_score(_catch_row("u1", "tpl_a", "7", "<answer>7</answer>", "<answer>7</answer>"))]
    member = [catch_pair_score(_catch_row("u1", "tpl_b", "7", "<answer>7</answer>", "<answer>7</answer>"))]
    with pytest.raises(CatchScoreError, match="template_id disagrees"):
        compare_arms(cp, member)


def test_paired_bootstrap_identical_indices() -> None:
    # Identical arms must give a degenerate interval at exactly zero: the two
    # sides are resampled on the same indices per replicate.
    values = [1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0]
    entry = paired_bootstrap_diff(values, values, seed=123, n_boot=500)
    assert entry["point"] == 0.0
    assert entry["ci95_low"] == 0.0 and entry["ci95_high"] == 0.0
    assert entry["excludes_zero"] is False


def test_mcnemar_exact_matches_scipy_binomtest() -> None:
    scipy_stats = pytest.importorskip("scipy.stats")
    cases = [(0, 0), (3, 0), (0, 5), (2, 2), (17, 59), (7, 32), (1, 1)]
    for b01, b10 in cases:
        a = [False] * b01 + [True] * b10 + [True] * 4
        b = [True] * b01 + [False] * b10 + [True] * 4
        ours = mcnemar_exact_bool(a, b)
        assert ours["b01"] == b01 and ours["b10"] == b10
        n = b01 + b10
        if n == 0:
            assert ours["p_value"] == 1.0
        else:
            reference = scipy_stats.binomtest(b01, n, 0.5, alternative="two-sided").pvalue
            assert abs(ours["p_value"] - reference) < 1e-12


# ---------------------------------------------------------------------------
# 6. Determinism: two full runs are byte-identical.
# ---------------------------------------------------------------------------

def _write_scores(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _fixture_arm_files(tmp_path: Path) -> tuple[Path, Path]:
    cp_rows = [
        _catch_row("u1", "tpl_a", "B9U", "<answer>B9U</answer>", "<answer>B9U</answer>"),
        _catch_row("u2", "tpl_a", "B9U", "<answer>C1X</answer>", "<answer>C1X</answer>"),
        _catch_row("u3", "tpl_b", "7", "<answer>7</answer>", "<answer>8</answer>"),
        _catch_row("u4", "tpl_b", "7", "Answer: 7", "Answer: 7"),
    ]
    member_rows = [
        _catch_row("u1", "tpl_a", "B9U", "<answer>C1X</answer>", "<answer>B9U</answer>"),
        _catch_row("u2", "tpl_a", "B9U", "<answer>B9U</answer>", "<answer>B9U</answer>"),
        _catch_row("u3", "tpl_b", "7", "<answer>7</answer>", "<answer>7</answer>"),
        _catch_row("u4", "tpl_b", "7", "", ""),
    ]
    cp_path = tmp_path / "cp_scores.jsonl"
    member_path = tmp_path / "member_scores.jsonl"
    _write_scores(cp_path, cp_rows)
    _write_scores(member_path, member_rows)
    return cp_path, member_path


def test_cli_two_runs_byte_identical(tmp_path: Path) -> None:
    cp_path, member_path = _fixture_arm_files(tmp_path)
    outputs = []
    for run in ("one", "two"):
        out_json = tmp_path / f"readout_{run}.json"
        per_row_cp = tmp_path / f"per_row_cp_{run}.jsonl"
        per_row_member = tmp_path / f"per_row_member_{run}.jsonl"
        code = scorer_main([
            "--cp-scores", str(cp_path),
            "--member-scores", str(member_path),
            "--output", str(out_json),
            "--per-row-output-cp", str(per_row_cp),
            "--per-row-output-member", str(per_row_member),
            "--expect", "any",
        ])
        assert code == 0
        outputs.append(
            (out_json.read_bytes(), per_row_cp.read_bytes(), per_row_member.read_bytes())
        )
    assert outputs[0] == outputs[1]


def test_cli_registered_shape_gate(tmp_path: Path) -> None:
    cp_path, member_path = _fixture_arm_files(tmp_path)
    with pytest.raises(CatchScoreError, match="registered catch shape"):
        scorer_main([
            "--cp-scores", str(cp_path),
            "--member-scores", str(member_path),
            "--output", str(tmp_path / "readout.json"),
        ])


# ---------------------------------------------------------------------------
# 7. The pair_group_uid -> pair_id adapter.
# ---------------------------------------------------------------------------

def _source_row(uid: str, template: str, gold: str) -> dict:
    return {
        "pair_group_uid": uid,
        "template_id": template,
        "question": "q?",
        "answer_a": gold,
        "answer_b": gold,
        "image_a_path": f"images/{uid}_a.png",
        "image_b_path": f"images/{uid}_b.png",
    }


def _write_source(path: Path, rows: list[dict]) -> str:
    import hashlib

    payload = ("\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n").encode()
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def test_adapter_maps_uid_to_pair_id_and_records_hashes(tmp_path: Path) -> None:
    source = tmp_path / "pairs.jsonl"
    digest = _write_source(source, [_source_row("g1", "tpl_a", "7"), _source_row("g2", "tpl_b", "8")])
    output = tmp_path / "derived.jsonl"
    args = [
        "--source", str(source),
        "--output", str(output),
        "--expected-source-sha256", digest,
        "--skip-image-check",
        "--allow-nonregistered-shape",
    ]
    assert adapter_main(args) == 0
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert [row["pair_id"] for row in rows] == ["g1", "g2"]
    for row in rows:
        assert row["pair_id"] == row["pair_group_uid"]  # source keys preserved
        assert set(_source_row("x", "t", "1")) <= set(row)
    provenance = json.loads((tmp_path / "derived.jsonl.provenance.json").read_text())
    import hashlib

    assert provenance["source_sha256"] == digest
    assert provenance["output_sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()
    assert provenance["n_rows"] == 2
    # deterministic rebuild: byte-identical output, exit 0
    before = output.read_bytes()
    assert adapter_main(args) == 0
    assert output.read_bytes() == before


def test_adapter_refuses_source_hash_mismatch(tmp_path: Path) -> None:
    source = tmp_path / "pairs.jsonl"
    _write_source(source, [_source_row("g1", "tpl_a", "7")])
    output = tmp_path / "derived.jsonl"
    code = adapter_main([
        "--source", str(source),
        "--output", str(output),
        "--expected-source-sha256", "0" * 64,
        "--skip-image-check",
        "--allow-nonregistered-shape",
    ])
    assert code == 1
    assert not output.exists()


def test_adapter_refuses_source_that_already_has_pair_id(tmp_path: Path) -> None:
    row = _source_row("g1", "tpl_a", "7")
    row["pair_id"] = "other"
    source = tmp_path / "pairs.jsonl"
    digest = _write_source(source, [row])
    code = adapter_main([
        "--source", str(source),
        "--output", str(tmp_path / "derived.jsonl"),
        "--expected-source-sha256", digest,
        "--skip-image-check",
        "--allow-nonregistered-shape",
    ])
    assert code == 1


def test_adapter_refuses_unequal_golds(tmp_path: Path) -> None:
    row = _source_row("g1", "tpl_a", "7")
    row["answer_b"] = "8"
    source = tmp_path / "pairs.jsonl"
    digest = _write_source(source, [row])
    code = adapter_main([
        "--source", str(source),
        "--output", str(tmp_path / "derived.jsonl"),
        "--expected-source-sha256", digest,
        "--skip-image-check",
        "--allow-nonregistered-shape",
    ])
    assert code == 1


def test_adapter_refuses_silent_overwrite(tmp_path: Path) -> None:
    source = tmp_path / "pairs.jsonl"
    digest = _write_source(source, [_source_row("g1", "tpl_a", "7")])
    output = tmp_path / "derived.jsonl"
    output.write_text("something else\n")
    code = adapter_main([
        "--source", str(source),
        "--output", str(output),
        "--expected-source-sha256", digest,
        "--skip-image-check",
        "--allow-nonregistered-shape",
    ])
    assert code == 1
    assert output.read_text() == "something else\n"


@pytest.mark.skipif(
    not (REPO_ROOT / "data/mini_a5_catch_v1/pairs.jsonl").is_file(),
    reason="real catch set not present",
)
def test_adapter_on_real_catch_set(tmp_path: Path) -> None:
    output = tmp_path / "mini_a5_catch_eval_manifest_v1.jsonl"
    code = adapter_main([
        "--source", str(REPO_ROOT / "data/mini_a5_catch_v1/pairs.jsonl"),
        "--output", str(output),
        "--expected-source-sha256", PINNED_SOURCE_SHA256,
        "--image-root", str(REPO_ROOT),
    ])
    assert code == 0
    provenance = json.loads(Path(str(output) + ".provenance.json").read_text())
    assert provenance["n_rows"] == 300
    assert set(provenance["template_pair_counts"].values()) == {100}
