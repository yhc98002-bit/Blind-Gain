"""Adversarial fixtures (I10) for the single-arm catch-stability wrapper.

The wrapper (src/eval/catch_stability_single_arm.py) scores the Gate-1
completion arms (std, necessity) on the catch set by importing the
arm-agnostic core of the REGISTERED two-arm instrument unchanged. These
fixtures encode every way the wrapper could silently lie:

  - planted invariance values not recovered exactly under both contracts;
  - a new arm scored under a cp/member label (or any unknown label);
  - an arm label that disagrees with the run's recorded checkpoint;
  - a scored item set that drifts from the catch manifest;
  - incomplete or missing run manifests accepted;
  - nondeterministic output;
  - the registered cp/member path (sha-pinned files) silently modified.

This is a NEW file: tests/test_catch_stability.py is itself sha-pinned by
docs/registered_mini_a5_catch_stability_v1.md section 5 and is not touched.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.eval.catch_stability import INDICATORS, CatchScoreError
from src.eval.catch_stability_single_arm import (
    ARM_CHECKPOINT_TOKENS,
    SCHEMA_VERSION,
    TWO_ARM_SCHEMA_VERSION,
    SingleArmRefusal,
    build_single_arm_readout,
    main as single_arm_main,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

# Pins from docs/registered_mini_a5_catch_stability_v1.md (sections 3 and 5).
# If either fails, the registered cp/member path has been modified — exactly
# what this wrapper exists to avoid.
REGISTERED_SCORER_SHA256 = (
    "d15eaa5d878cb757aa8dbae17d446c98cd6675cdc10fbd1a23bac1d7af1d8e91"
)
REGISTERED_TEST_SHA256 = (
    "c809be291181eaabeffea770e85ee04945c562fdcb1993df31f6315b41e49209"
)


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


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _default_rows() -> list[dict]:
    # Planted per-template truth (see EXPECTED_* below). Covers the decisive
    # agree-both-wrong row (u2) and lenient-only agreements (u4, u5).
    return [
        _catch_row("u1", "tpl_a", "B9U", "<answer>B9U</answer>", "<answer>B9U</answer>"),
        _catch_row("u2", "tpl_a", "B9U", "<answer>C1X</answer>", "<answer>C1X</answer>"),
        _catch_row("u3", "tpl_a", "B9U", "<answer>B9U</answer>", "<answer>C1X</answer>"),
        _catch_row("u4", "tpl_b", "7", "Answer: 7", "Answer: 7"),
        _catch_row("u5", "tpl_b", "7", "", ""),
        _catch_row("u6", "tpl_b", "7", "<answer>7</answer>", "<answer>7</answer>"),
    ]


# Hand-derived indicator counts for _default_rows(), n=3 per template.
EXPECTED_TPL_A = {
    "stable_lenient": 2,  # u1, u2 agree; u3 disagrees
    "stable_strict": 2,  # both agreements are in contract
    "pair_correct": 1,  # u1 only
    "strict_pair_correct": 1,
    "stable_and_correct_lenient": 1,
    "stable_and_correct_strict": 1,
}
EXPECTED_TPL_B = {
    "stable_lenient": 3,  # u4 (out of contract), u5 (empty), u6 all agree
    "stable_strict": 1,  # only u6 agrees in contract
    "pair_correct": 2,  # u4 lenient-correct, u6 correct
    "strict_pair_correct": 1,  # u6 only
    "stable_and_correct_lenient": 2,  # u4, u6
    "stable_and_correct_strict": 1,  # u6
}


def _manifest_rows_for(rows: list[dict]) -> list[dict]:
    return [
        {
            "pair_group_uid": row["pair_group_uid"],
            "pair_id": row["pair_group_uid"],
            "template_id": row["template_id"],
            "answer_a": row["answer_a"],
            "answer_b": row["answer_b"],
        }
        for row in rows
    ]


def _build_fixture(
    tmp_path: Path,
    arm: str = "std",
    rows: list[dict] | None = None,
    manifest_rows: list[dict] | None = None,
    model_path: str | None = None,
    status: str = "complete",
    data_manifest_hash: str | None = "auto",
    write_run_manifest: bool = True,
    write_shards: bool = True,
) -> tuple[Path, Path]:
    """Write a synthetic catch-cell run dir + catch manifest; return their paths."""
    rows = _default_rows() if rows is None else rows
    manifest_rows = _manifest_rows_for(rows) if manifest_rows is None else manifest_rows
    catch_manifest = tmp_path / "catch_manifest.jsonl"
    _write_jsonl(catch_manifest, manifest_rows)
    digest = hashlib.sha256(catch_manifest.read_bytes()).hexdigest()
    run_dir = tmp_path / f"mini_a5_catch_{arm}_fixture"
    (run_dir / "shards").mkdir(parents=True)
    if write_shards:
        _write_jsonl(run_dir / "shards" / "shard_0.jsonl", rows)
    if model_path is None:
        token = ARM_CHECKPOINT_TOKENS.get(arm, "mini_a5_std_seed1")
        model_path = f"/ckpt/{token}/global_step_120/actor/huggingface"
    manifest: dict = {
        "status": status,
        "model_path": model_path,
        "run_id": f"mini_a5_catch_{arm}_fixture",
    }
    if data_manifest_hash == "auto":
        manifest["data_manifest_hash"] = digest
    elif data_manifest_hash is not None:
        manifest["data_manifest_hash"] = data_manifest_hash
    if write_run_manifest:
        (run_dir / "run_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return run_dir, catch_manifest


# ---------------------------------------------------------------------------
# 1. The registered cp/member path is byte-stable.
# ---------------------------------------------------------------------------

def test_registered_pinned_files_unchanged() -> None:
    scorer = (REPO_ROOT / "src/eval/catch_stability.py").read_bytes()
    tests = (REPO_ROOT / "tests/test_catch_stability.py").read_bytes()
    assert hashlib.sha256(scorer).hexdigest() == REGISTERED_SCORER_SHA256
    assert hashlib.sha256(tests).hexdigest() == REGISTERED_TEST_SHA256


def test_schema_version_is_new_and_distinct() -> None:
    assert SCHEMA_VERSION == "blind-gains.mini-a5-catch-stability-single-arm.v1"
    assert SCHEMA_VERSION != TWO_ARM_SCHEMA_VERSION
    assert TWO_ARM_SCHEMA_VERSION == "blind-gains.mini-a5-catch-stability.v1"


# ---------------------------------------------------------------------------
# 2. Planted invariance values recovered exactly, both contracts (I7).
# ---------------------------------------------------------------------------

def test_planted_values_recovered_exactly_under_both_contracts(tmp_path: Path) -> None:
    run_dir, catch_manifest = _build_fixture(tmp_path)
    readout, scored = build_single_arm_readout(
        "std", run_dir, catch_manifest, expect="any"
    )
    per_template = readout["levels"]["per_template"]
    assert set(per_template) == {"tpl_a", "tpl_b"}
    for template, expected in (("tpl_a", EXPECTED_TPL_A), ("tpl_b", EXPECTED_TPL_B)):
        block = per_template[template]
        assert block["n_pairs"] == 3
        for indicator, family, severity in INDICATORS:
            assert block[indicator] == {
                "count": expected[indicator],
                "rate": expected[indicator] / 3,
                "indicator_family": family,
                "severity": severity,
            }, (template, indicator)
    # The decisive row survives the pipeline: agree-both-wrong is stable but
    # not correct, at both severities.
    by_uid = {row["pair_group_uid"]: row for row in scored}
    assert by_uid["u2"]["stable_lenient"] is True
    assert by_uid["u2"]["stable_strict"] is True
    assert by_uid["u2"]["pair_correct"] is False
    assert by_uid["u2"]["strict_pair_correct"] is False
    # Out-of-contract agreement is lenient-only (I7 severities never merge).
    assert by_uid["u4"]["stable_lenient"] is True
    assert by_uid["u4"]["stable_strict"] is False
    assert by_uid["u5"]["stable_lenient"] is True
    assert by_uid["u5"]["stable_strict"] is False


def test_cli_end_to_end_recovers_planted_values(tmp_path: Path) -> None:
    run_dir, catch_manifest = _build_fixture(tmp_path, arm="necessity")
    out_json = tmp_path / "levels.json"
    per_row = tmp_path / "rows.jsonl"
    code = single_arm_main([
        "--arm-label", "necessity",
        "--run-dir", str(run_dir),
        "--catch-manifest", str(catch_manifest),
        "--output", str(out_json),
        "--per-row-output", str(per_row),
        "--expect", "any",
    ])
    assert code == 0
    readout = json.loads(out_json.read_text(encoding="utf-8"))
    assert readout["schema_version"] == SCHEMA_VERSION
    assert readout["arm"]["label"] == "necessity"
    assert readout["arm"]["arm_number"] == 3
    assert readout["arm"]["checkpoint_token"] == "mini_a5_necessity_seed1"
    assert readout["checks"]["template_pair_counts"] == {"tpl_a": 3, "tpl_b": 3}
    assert readout["checks"]["item_set_matches_catch_manifest"] is True
    assert readout["automatic_branch_assignment"] is False
    for template, expected in (("tpl_a", EXPECTED_TPL_A), ("tpl_b", EXPECTED_TPL_B)):
        block = readout["levels"]["per_template"][template]
        for indicator, _, _ in INDICATORS:
            assert block[indicator]["count"] == expected[indicator], (template, indicator)
    # Input provenance records the actual bytes read.
    assert readout["inputs"]["catch_manifest"]["sha256"] == hashlib.sha256(
        catch_manifest.read_bytes()
    ).hexdigest()
    shard = run_dir / "shards" / "shard_0.jsonl"
    assert readout["inputs"]["scores"] == [
        {"path": str(shard), "sha256": hashlib.sha256(shard.read_bytes()).hexdigest()}
    ]
    # Per-row output is sorted by uid and carries the planted stability values.
    rows = [json.loads(line) for line in per_row.read_text().splitlines()]
    assert [row["pair_group_uid"] for row in rows] == ["u1", "u2", "u3", "u4", "u5", "u6"]
    assert rows[1]["stable_lenient"] is True and rows[1]["pair_correct"] is False


# ---------------------------------------------------------------------------
# 3. Label discipline: cp/member and unknown labels refused; label must match
#    the run's recorded checkpoint.
# ---------------------------------------------------------------------------

def test_cp_and_member_labels_refused_even_on_valid_run_dir(tmp_path: Path) -> None:
    # The run dir itself is perfectly scoreable — the refusal is about the
    # label alone, so a new arm can never ride under a cp/member slot and the
    # registered arms can never be re-scored here.
    run_dir, catch_manifest = _build_fixture(tmp_path)
    for label in ("cp", "member"):
        with pytest.raises(SingleArmRefusal, match="reserved for the registered two-arm"):
            build_single_arm_readout(label, run_dir, catch_manifest, expect="any")


def test_unknown_label_refused(tmp_path: Path) -> None:
    run_dir, catch_manifest = _build_fixture(tmp_path)
    with pytest.raises(SingleArmRefusal, match="unknown arm label"):
        build_single_arm_readout("base", run_dir, catch_manifest, expect="any")


def test_label_checkpoint_mismatch_refused(tmp_path: Path) -> None:
    # A necessity checkpoint scored under --arm-label std must be refused.
    run_dir, catch_manifest = _build_fixture(
        tmp_path,
        arm="std",
        model_path="/ckpt/mini_a5_necessity_seed1/global_step_120/actor/huggingface",
    )
    with pytest.raises(SingleArmRefusal, match="arm label mismatch"):
        build_single_arm_readout("std", run_dir, catch_manifest, expect="any")


# ---------------------------------------------------------------------------
# 4. Item-set discipline against the catch manifest.
# ---------------------------------------------------------------------------

def test_scores_missing_a_manifest_pair_refused(tmp_path: Path) -> None:
    rows = _default_rows()
    manifest_rows = _manifest_rows_for(rows) + [
        {
            "pair_group_uid": "u7",
            "pair_id": "u7",
            "template_id": "tpl_a",
            "answer_a": "X",
            "answer_b": "X",
        }
    ]
    run_dir, catch_manifest = _build_fixture(
        tmp_path, rows=rows, manifest_rows=manifest_rows
    )
    with pytest.raises(SingleArmRefusal, match="item-set mismatch"):
        build_single_arm_readout("std", run_dir, catch_manifest, expect="any")


def test_scores_with_extra_pair_refused(tmp_path: Path) -> None:
    rows = _default_rows()
    manifest_rows = _manifest_rows_for(rows[:-1])  # manifest lacks u6
    run_dir, catch_manifest = _build_fixture(
        tmp_path, rows=rows, manifest_rows=manifest_rows
    )
    with pytest.raises(SingleArmRefusal, match="item-set mismatch"):
        build_single_arm_readout("std", run_dir, catch_manifest, expect="any")


def test_template_disagreement_with_manifest_refused(tmp_path: Path) -> None:
    rows = _default_rows()
    manifest_rows = _manifest_rows_for(rows)
    manifest_rows[-1]["template_id"] = "tpl_a"  # u6 is tpl_b in the scores
    run_dir, catch_manifest = _build_fixture(
        tmp_path, rows=rows, manifest_rows=manifest_rows
    )
    with pytest.raises(SingleArmRefusal, match="template_id mismatch"):
        build_single_arm_readout("std", run_dir, catch_manifest, expect="any")


# ---------------------------------------------------------------------------
# 5. Run-manifest discipline: incomplete or missing manifests refused.
# ---------------------------------------------------------------------------

def test_missing_run_manifest_refused(tmp_path: Path) -> None:
    run_dir, catch_manifest = _build_fixture(tmp_path, write_run_manifest=False)
    with pytest.raises(SingleArmRefusal, match="missing run manifest"):
        build_single_arm_readout("std", run_dir, catch_manifest, expect="any")


def test_incomplete_status_refused(tmp_path: Path) -> None:
    run_dir, catch_manifest = _build_fixture(tmp_path, status="running")
    with pytest.raises(SingleArmRefusal, match="not 'complete'"):
        build_single_arm_readout("std", run_dir, catch_manifest, expect="any")


def test_run_manifest_without_data_manifest_hash_refused(tmp_path: Path) -> None:
    run_dir, catch_manifest = _build_fixture(tmp_path, data_manifest_hash=None)
    with pytest.raises(SingleArmRefusal, match="lacks a data_manifest_hash"):
        build_single_arm_readout("std", run_dir, catch_manifest, expect="any")


def test_run_over_different_manifest_refused(tmp_path: Path) -> None:
    run_dir, catch_manifest = _build_fixture(tmp_path, data_manifest_hash="0" * 64)
    with pytest.raises(SingleArmRefusal, match="catch-manifest mismatch"):
        build_single_arm_readout("std", run_dir, catch_manifest, expect="any")


def test_missing_scores_refused(tmp_path: Path) -> None:
    run_dir, catch_manifest = _build_fixture(tmp_path, write_shards=False)
    with pytest.raises(SingleArmRefusal, match="no shard files"):
        build_single_arm_readout("std", run_dir, catch_manifest, expect="any")


def test_non_equal_gold_row_refused_end_to_end(tmp_path: Path) -> None:
    # Fail-closed behavior inherited unchanged from the registered core.
    rows = _default_rows()
    rows[2]["answer_b"] = "ZZZ"
    run_dir, catch_manifest = _build_fixture(tmp_path, rows=rows)
    with pytest.raises(CatchScoreError, match="equal-gold"):
        build_single_arm_readout("std", run_dir, catch_manifest, expect="any")


# ---------------------------------------------------------------------------
# 6. Registered shape gate and determinism.
# ---------------------------------------------------------------------------

def test_cli_default_expect_registered_refuses_fixture_shape(tmp_path: Path) -> None:
    run_dir, catch_manifest = _build_fixture(tmp_path)
    with pytest.raises(CatchScoreError, match="registered catch shape"):
        single_arm_main([
            "--arm-label", "std",
            "--run-dir", str(run_dir),
            "--catch-manifest", str(catch_manifest),
            "--output", str(tmp_path / "levels.json"),
        ])


def test_cli_two_runs_byte_identical(tmp_path: Path) -> None:
    run_dir, catch_manifest = _build_fixture(tmp_path)
    outputs = []
    for run in ("one", "two"):
        out_json = tmp_path / f"levels_{run}.json"
        per_row = tmp_path / f"rows_{run}.jsonl"
        code = single_arm_main([
            "--arm-label", "std",
            "--run-dir", str(run_dir),
            "--catch-manifest", str(catch_manifest),
            "--output", str(out_json),
            "--per-row-output", str(per_row),
            "--expect", "any",
        ])
        assert code == 0
        outputs.append((out_json.read_bytes(), per_row.read_bytes()))
    assert outputs[0] == outputs[1]


def test_cli_refuses_to_overwrite_existing_output(tmp_path: Path) -> None:
    run_dir, catch_manifest = _build_fixture(tmp_path)
    out_json = tmp_path / "levels.json"
    out_json.write_text("already here\n")
    with pytest.raises(SingleArmRefusal, match="refusing to overwrite"):
        single_arm_main([
            "--arm-label", "std",
            "--run-dir", str(run_dir),
            "--catch-manifest", str(catch_manifest),
            "--output", str(out_json),
            "--expect", "any",
        ])
    assert out_json.read_text() == "already here\n"


def test_cli_refuses_to_overwrite_existing_per_row_output(tmp_path: Path) -> None:
    run_dir, catch_manifest = _build_fixture(tmp_path)
    per_row = tmp_path / "rows.jsonl"
    per_row.write_text("already here\n")
    with pytest.raises(SingleArmRefusal, match="refusing to overwrite"):
        single_arm_main([
            "--arm-label", "std",
            "--run-dir", str(run_dir),
            "--catch-manifest", str(catch_manifest),
            "--output", str(tmp_path / "levels.json"),
            "--per-row-output", str(per_row),
            "--expect", "any",
        ])
    assert per_row.read_text() == "already here\n"


# ---------------------------------------------------------------------------
# 7. Pooling is structurally impossible in the new schema too (I13).
# ---------------------------------------------------------------------------

def _walk(node, path=()):  # yields (path, key) for every mapping key
    if isinstance(node, dict):
        for key, value in node.items():
            yield path, key
            yield from _walk(value, path + (key,))
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item, path)


def test_readout_has_no_pooled_slot(tmp_path: Path) -> None:
    run_dir, catch_manifest = _build_fixture(tmp_path)
    readout, _ = build_single_arm_readout("std", run_dir, catch_manifest, expect="any")
    forbidden = ("pooled", "overall", "all_templates", "combined", "micro", "macro")
    for path, key in _walk(readout):
        assert not any(marker in str(key).lower() for marker in forbidden), (path, key)
    indicator_names = {name for name, _, _ in INDICATORS}
    for path, key in _walk(readout):
        if (key in indicator_names and "indicator_indices" not in path) or key == "rate":
            assert "per_template" in path, (path, key)
