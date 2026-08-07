"""Adversarial fixtures (I10) for the four-arm Gate-1 endpoint readout.

Each fixture plants a failure mode the registered instrument
scripts/build_mini_a5_gate1_endpoint_readout.py must refuse, plus a positive
control whose planted per-arm accuracies must be recovered exactly under both
contracts (I7), per task role with no pooling (I13). The predecessor
instrument (scripts/compare_fliptrack_runs.py) fails every fixture here: it
accepts exactly two arms, reads no run manifest, checks no run status, no arm
label, and no registered item-set shape.

No real training-arm data is touched: every row, manifest, base cell, and F8
block is synthetic and lives under pytest tmp_path.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.build_mini_a5_gate1_endpoint_readout import (
    ARM_CHECKPOINT_TOKENS,
    F8_SCHEMA_VERSION,
    ReadoutRefusal,
    SCHEMA_VERSION,
    build_readout,
    main,
)

TEMPLATE_A = "t_alpha"
TEMPLATE_B = "t_beta"

# Planted pair-correctness patterns, 4 pairs per template per arm.
# All dyadic fractions so exact float equality is safe.
PLANTED = {
    "std": {TEMPLATE_A: [1, 0, 0, 0], TEMPLATE_B: [1, 1, 0, 0]},
    "member": {TEMPLATE_A: [1, 1, 0, 0], TEMPLATE_B: [1, 1, 1, 0]},
    "necessity": {TEMPLATE_A: [1, 1, 1, 0], TEMPLATE_B: [1, 1, 1, 1]},
    "cp": {TEMPLATE_A: [1, 0, 1, 0], TEMPLATE_B: [0, 0, 0, 0]},
}

# member (t_alpha, pair 0) is emitted WITHOUT answer tags: lenient-correct but
# contract-invalid, planting a lenient/strict divergence (I7).
MEMBER_UNTAGGED = {(TEMPLATE_A, 0)}

BASE_TABLE = {
    TEMPLATE_A: {"pair_accuracy": 0.25, "strict_pair_accuracy": 0.0, "n_pairs": 4},
    TEMPLATE_B: {"pair_accuracy": 0.5, "strict_pair_accuracy": 0.5, "n_pairs": 4},
}


def _row(pair_id: str, template: str, correct: bool, *, tagged: bool = True) -> dict:
    prediction_a = "left"
    prediction_b = "right" if correct else "left"
    if tagged:
        prediction_a = f"<answer>{prediction_a}</answer>"
        prediction_b = f"<answer>{prediction_b}</answer>"
    return {
        "pair_id": pair_id,
        "template_id": template,
        "answer_a": "left",
        "answer_b": "right",
        "prediction_a": prediction_a,
        "prediction_b": prediction_b,
    }


def _write_arm(
    root: Path,
    arm: str,
    planted: dict[str, list[int]],
    *,
    status: str = "complete",
    model_token: str | None = None,
    drop_pair: str | None = None,
    untagged: set[tuple[str, int]] = frozenset(),
) -> Path:
    run_dir = root / f"run_{arm}"
    (run_dir / "shards").mkdir(parents=True)
    rows = []
    for template in sorted(planted):
        for index, correct in enumerate(planted[template]):
            pair_id = f"{template}_p{index:03d}"
            if pair_id == drop_pair:
                continue
            rows.append(
                _row(
                    pair_id,
                    template,
                    bool(correct),
                    tagged=(template, index) not in untagged,
                )
            )
    (run_dir / "shards" / "shard_0.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )
    token = model_token or ARM_CHECKPOINT_TOKENS[arm]
    manifest = {
        "status": status,
        "model_path": (
            f"/checkpoints/mini_a5/{token}/global_step_120/actor/huggingface"
        ),
        "job_type": "fixture",
    }
    (run_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return run_dir


def _write_base(root: Path) -> Path:
    path = root / "base_report.json"
    path.write_text(
        json.dumps({"schema_version": "fixture-base", "base": BASE_TABLE}, indent=2),
        encoding="utf-8",
    )
    return path


def _write_f8(root: Path, *, schema: str = F8_SCHEMA_VERSION) -> tuple[Path, dict]:
    payload = {
        "schema_version": schema,
        "branch_determination": {"branch_fired": "branch_2"},
        "primary_endpoint": {
            "template_id": "coordinate_register_twenty_point_x_v02",
            "n_pairs": 600,
            "lenient_pair_correct": {
                "cp_minus_member": -0.01,
                "decision_rule_outcome": "NOT MOVED",
            },
            "contract_strict_strict_pair_correct": {
                "cp_minus_member": 0.07,
                "decision_rule_outcome": "MOVED",
            },
        },
    }
    path = root / "f8_report.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path, payload


def _make_fixture(
    root: Path,
    *,
    member_status: str = "complete",
    cp_token: str | None = None,
    necessity_drop: str | None = None,
    f8_schema: str = F8_SCHEMA_VERSION,
):
    dirs = {
        "std": _write_arm(root, "std", PLANTED["std"]),
        "member": _write_arm(
            root,
            "member",
            PLANTED["member"],
            status=member_status,
            untagged=MEMBER_UNTAGGED,
        ),
        "necessity": _write_arm(
            root, "necessity", PLANTED["necessity"], drop_pair=necessity_drop
        ),
        "cp": _write_arm(root, "cp", PLANTED["cp"], model_token=cp_token),
    }
    base = _write_base(root)
    f8_path, f8_payload = _write_f8(root, schema=f8_schema)
    return dirs, base, f8_path, f8_payload


def _build(dirs, base, f8_path, **kwargs):
    kwargs.setdefault("bootstrap_draws", 200)
    kwargs.setdefault("expect", "any")
    return build_readout(dirs, base, f8_path, **kwargs)


def _cli_argv(dirs, base, f8_path, output: Path) -> list[str]:
    return [
        "--arm-std", str(dirs["std"]),
        "--arm-member", str(dirs["member"]),
        "--arm-necessity", str(dirs["necessity"]),
        "--arm-cp", str(dirs["cp"]),
        "--base-report", str(base),
        "--f8-report", str(f8_path),
        "--bootstrap-draws", "200",
        "--expect", "any",
        "--output", str(output),
    ]


def test_planted_values_recovered_exactly(tmp_path: Path) -> None:
    dirs, base, f8_path, f8_payload = _make_fixture(tmp_path)
    result = _build(dirs, base, f8_path)
    assert result["schema_version"] == SCHEMA_VERSION  # I15

    arms = result["arms"]
    assert arms["std"]["arm_number"] == 1
    assert arms["std"]["per_task_role"][TEMPLATE_A]["lenient_pair_accuracy"] == 0.25
    assert arms["std"]["per_task_role"][TEMPLATE_B]["lenient_pair_accuracy"] == 0.5
    assert arms["member"]["per_task_role"][TEMPLATE_A]["lenient_pair_accuracy"] == 0.5
    # planted lenient/strict divergence (I7): untagged correct pair
    assert arms["member"]["per_task_role"][TEMPLATE_A]["strict_pair_accuracy"] == 0.25
    assert arms["necessity"]["per_task_role"][TEMPLATE_A]["lenient_pair_accuracy"] == 0.75
    assert arms["necessity"]["per_task_role"][TEMPLATE_B]["lenient_pair_accuracy"] == 1.0
    assert arms["cp"]["per_task_role"][TEMPLATE_B]["lenient_pair_accuracy"] == 0.0

    contrasts = result["registered_contrasts"]
    c1 = contrasts["contrast_1_arm2_minus_arm1"]
    assert (c1["left_arm"], c1["right_arm"]) == ("std", "member")
    cell = c1["per_task_role"][TEMPLATE_A]
    assert cell["lenient_pair_correct"]["right_minus_left"] == 0.25
    assert cell["contract_strict_strict_pair_correct"]["right_minus_left"] == 0.0
    assert cell["lenient_pair_correct"]["mcnemar_b01_left_wrong_right_correct"] == 1
    assert cell["lenient_pair_correct"]["mcnemar_b10_left_correct_right_wrong"] == 0

    c2 = contrasts["contrast_2_arm3_minus_arm2"]
    assert (c2["left_arm"], c2["right_arm"]) == ("member", "necessity")
    cell = c2["per_task_role"][TEMPLATE_A]
    assert cell["lenient_pair_correct"]["right_minus_left"] == 0.25
    assert cell["contract_strict_strict_pair_correct"]["right_minus_left"] == 0.5

    c3 = contrasts["contrast_3_absolute_levels_vs_frozen_base"]
    assert c3["arm1_std_minus_base"][TEMPLATE_A]["arm_minus_base_lenient"] == 0.0
    assert c3["arm1_std_minus_base"][TEMPLATE_A]["arm_minus_base_strict"] == 0.25
    assert c3["arm1_std_minus_base"][TEMPLATE_B]["arm_minus_base_lenient"] == 0.0
    assert c3["arm3_necessity_minus_base"][TEMPLATE_A]["arm_minus_base_lenient"] == 0.5
    assert c3["arm3_necessity_minus_base"][TEMPLATE_B]["arm_minus_base_strict"] == 0.5

    # arm 4 - arm 2 carried verbatim from F8, never recomputed
    carried = result["carried_from_f8_not_re_decided"]
    assert carried["f8_primary_endpoint"] == f8_payload["primary_endpoint"]
    assert carried["f8_branch_fired"] == "branch_2"


def test_both_contracts_reported_for_every_cell_and_roles_never_pooled(
    tmp_path: Path,
) -> None:
    dirs, base, f8_path, _ = _make_fixture(tmp_path)
    result = _build(dirs, base, f8_path)
    for arm_block in result["arms"].values():
        assert set(arm_block["per_task_role"]) == {TEMPLATE_A, TEMPLATE_B}
        for cell in arm_block["per_task_role"].values():
            assert "lenient_pair_accuracy" in cell  # I7
            assert "strict_pair_accuracy" in cell  # I7
        # pooled numbers exist only under the explicitly labeled key (I13)
        assert "pooled_all_roles_NOT_AN_ENDPOINT" in arm_block
    for key in ("contrast_1_arm2_minus_arm1", "contrast_2_arm3_minus_arm2"):
        contrast = result["registered_contrasts"][key]
        assert set(contrast["per_task_role"]) == {TEMPLATE_A, TEMPLATE_B}
        for cell in contrast["per_task_role"].values():
            assert "lenient_pair_correct" in cell  # I7
            assert "contract_strict_strict_pair_correct" in cell  # I7
        assert "pooled_all_roles_NOT_AN_ENDPOINT" in contrast


def test_item_set_mismatch_between_arms_refused(tmp_path: Path) -> None:
    dirs, base, f8_path, _ = _make_fixture(
        tmp_path, necessity_drop=f"{TEMPLATE_A}_p000"
    )
    with pytest.raises(ReadoutRefusal, match="item-set mismatch"):
        _build(dirs, base, f8_path)


def test_missing_run_manifest_refused(tmp_path: Path) -> None:
    dirs, base, f8_path, _ = _make_fixture(tmp_path)
    (dirs["member"] / "run_manifest.json").unlink()
    with pytest.raises(ReadoutRefusal, match="missing run manifest"):
        _build(dirs, base, f8_path)


def test_incomplete_run_status_refused(tmp_path: Path) -> None:
    dirs, base, f8_path, _ = _make_fixture(tmp_path, member_status="running")
    with pytest.raises(ReadoutRefusal, match="partial readouts are prohibited"):
        _build(dirs, base, f8_path)


def test_wrong_arm_label_refused(tmp_path: Path) -> None:
    # cp slot fed a checkpoint whose path carries the member token
    dirs, base, f8_path, _ = _make_fixture(
        tmp_path, cp_token=ARM_CHECKPOINT_TOKENS["member"]
    )
    with pytest.raises(ReadoutRefusal, match="arm label mismatch"):
        _build(dirs, base, f8_path)


def test_registered_shape_enforced_by_default(tmp_path: Path) -> None:
    # registration-specific check: the default expectation refuses anything but
    # the registered R19 shape (3 templates, 600/300/300 pairs)
    dirs, base, f8_path, _ = _make_fixture(tmp_path)
    with pytest.raises(ReadoutRefusal, match="registered R19 shape violated"):
        build_readout(dirs, base, f8_path, bootstrap_draws=200)


def test_wrong_f8_report_schema_refused(tmp_path: Path) -> None:
    dirs, base, f8_path, _ = _make_fixture(
        tmp_path, f8_schema="blind-gains.some-other-report.v1"
    )
    with pytest.raises(ReadoutRefusal, match="F8 report schema mismatch"):
        _build(dirs, base, f8_path)


def test_determinism_two_invocations_byte_identical(tmp_path: Path) -> None:
    dirs, base, f8_path, _ = _make_fixture(tmp_path)
    out1 = tmp_path / "readout_run1.json"
    out2 = tmp_path / "readout_run2.json"
    main(_cli_argv(dirs, base, f8_path, out1))
    main(_cli_argv(dirs, base, f8_path, out2))
    assert out1.read_bytes() == out2.read_bytes()
    payload = json.loads(out1.read_text(encoding="utf-8"))
    assert payload["schema_version"] == SCHEMA_VERSION


def test_refuses_to_overwrite_existing_output(tmp_path: Path) -> None:
    dirs, base, f8_path, _ = _make_fixture(tmp_path)
    out = tmp_path / "readout.json"
    out.write_text("{}", encoding="utf-8")
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        main(_cli_argv(dirs, base, f8_path, out))
