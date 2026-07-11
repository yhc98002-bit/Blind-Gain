from __future__ import annotations

import json
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

import src.rewards.pilot_reward as pilot_reward
from src.rewards.pilot_reward import (
    NATIVE_R1V_PATH,
    PILOT_REWARD_VERSION,
    compute_score,
    load_native_r1v,
)


ROOT = Path(__file__).resolve().parents[1]
MULTILINE_CASES = (
    (16, "0.38"),
    (18, "18"),
    (58, "6.71"),
    (61, "2.5"),
    (68, "125"),
    (90, "2"),
    (121, "5"),
    (139, "14.1"),
    (163, "12"),
    (177, "21"),
    (212, "14"),
    (261, "55"),
    (306, "1440"),
    (309, "3"),
)


@pytest.mark.parametrize(("source_row_index", "ground_truth"), MULTILINE_CASES)
def test_known_multiline_answer_cases_receive_full_pilot_reward(
    tmp_path: Path, source_row_index: int, ground_truth: str
) -> None:
    shadow = tmp_path / "shadow.jsonl"
    response = f"<think>case {source_row_index}</think>\n<answer>\n{ground_truth}\n</answer>"

    score = compute_score(
        {"response": response, "ground_truth": ground_truth},
        shadow_log_path=str(shadow),
        require_shadow_log=True,
    )

    assert score["training_reward"] == 1.0
    assert score["accuracy"] == 1.0
    assert score["format"] == 1.0
    row = json.loads(shadow.read_text(encoding="utf-8"))
    assert row["pilot_reward_version"] == PILOT_REWARD_VERSION
    assert row["reward_disagreement_reason"] == "none"


def test_mathruler_precedence_and_string_reason_are_shadow_logged(tmp_path: Path) -> None:
    shadow = tmp_path / "shadow.jsonl"
    score = compute_score(
        {"response": "<answer>94\N{DEGREE SIGN}</answer>", "ground_truth": "94"},
        shadow_log_path=str(shadow),
        require_shadow_log=True,
    )
    assert score["canonical_eval_reward"] == 1.0
    assert score["accuracy"] == 0.0
    assert score["training_reward"] == 0.5
    row = json.loads(shadow.read_text(encoding="utf-8"))
    assert row["reward_disagreement_reason"] == "canonical_correct_mathruler_incorrect"


def test_mathruler_can_receive_credit_when_canonical_equivalence_rejects(tmp_path: Path) -> None:
    shadow = tmp_path / "shadow.jsonl"
    score = compute_score(
        {"response": "<answer>x = 37</answer>", "ground_truth": "37"},
        shadow_log_path=str(shadow),
        require_shadow_log=True,
    )
    assert score["canonical_eval_reward"] == 0.0
    assert score["accuracy"] == 1.0
    assert score["training_reward"] == 1.0
    row = json.loads(shadow.read_text(encoding="utf-8"))
    assert row["reward_disagreement_reason"] == "mathruler_correct_canonical_incorrect"


def test_pilot_reward_requires_shadow_log_when_configured() -> None:
    with pytest.raises(RuntimeError, match="BLIND_GAINS_REWARD_SHADOW_LOG"):
        compute_score(
            {"response": "<answer>1</answer>", "ground_truth": "1"},
            require_shadow_log=True,
        )


def test_native_shadow_calls_the_pinned_easy_r1_reward(tmp_path: Path) -> None:
    response = "<think>work</think><answer>5</answer>"
    native = load_native_r1v().compute_score({"response": response, "ground_truth": "5"})
    pilot = compute_score(
        {"response": response, "ground_truth": "5"},
        shadow_log_path=str(tmp_path / "shadow.jsonl"),
    )
    assert pilot["native_r1v_shadow_reward"] == native["overall"]
    assert pilot["native_r1v_shadow_valid"] == 1.0


def test_hanging_mathruler_is_bounded_and_logged(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def hang_forever(_answer: str, _ground_truth: str) -> bool:
        while True:
            time.sleep(1)

    monkeypatch.setattr(pilot_reward, "grade_answer", hang_forever)
    monkeypatch.setattr(
        pilot_reward,
        "load_native_r1v",
        lambda: SimpleNamespace(compute_score=lambda *_args, **_kwargs: {"overall": 1.0}),
    )
    shadow = tmp_path / "shadow.jsonl"

    started = time.monotonic()
    score = compute_score(
        {"response": "<answer>5</answer>", "ground_truth": "5"},
        shadow_log_path=str(shadow),
        symbolic_grader_timeout_seconds=0.05,
    )

    assert time.monotonic() - started < 1.0
    assert score["accuracy"] == 0.0
    assert score["canonical_eval_reward"] == 1.0
    row = json.loads(shadow.read_text(encoding="utf-8"))
    assert row["mathruler_error"] == "SymbolicGraderTimeout"
    assert row["reward_disagreement_reason"] == "mathruler_error_canonical_correct"


def test_hanging_native_shadow_is_bounded_without_changing_training_reward(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def hang_forever(*_args: object, **_kwargs: object) -> dict[str, float]:
        while True:
            time.sleep(1)

    monkeypatch.setattr(
        pilot_reward,
        "load_native_r1v",
        lambda: SimpleNamespace(compute_score=hang_forever),
    )
    shadow = tmp_path / "shadow.jsonl"

    score = compute_score(
        {"response": "<answer>5</answer>", "ground_truth": "5"},
        shadow_log_path=str(shadow),
        symbolic_grader_timeout_seconds=0.05,
    )

    assert score["training_reward"] == 1.0
    assert score["native_r1v_shadow_reward"] == 0.0
    assert score["native_r1v_shadow_valid"] == 0.0
    row = json.loads(shadow.read_text(encoding="utf-8"))
    assert row["native_r1v_shadow_error"] == "SymbolicGraderTimeout"
    assert row["native_r1v_shadow_valid"] is False


def test_anchor_remains_native_and_all_mechanical_arms_bind_pilot_reward() -> None:
    anchor = yaml.safe_load((ROOT / "configs/train/anchor_a0_recipe_3b_geo3k.yaml").read_text())
    assert anchor["worker"]["reward"]["reward_function"] == (
        str(NATIVE_R1V_PATH) + ":compute_score"
    )
    for path in sorted((ROOT / "configs/train").glob("mech_a*_3b_geo3k.yaml")):
        config = yaml.safe_load(path.read_text())
        reward = config["worker"]["reward"]
        assert reward["reward_function"].endswith("/src/rewards/pilot_reward.py:compute_score")
        assert reward["reward_function_kwargs"] == {
            "format_weight": 0.5,
            "require_shadow_log": True,
            "symbolic_grader_timeout_seconds": 5.0,
        }


def test_pilot_reward_smoke_uses_dev_shm_for_ray_runtime() -> None:
    launcher = (ROOT / "scripts/launch_pilot_reward_smoke.sh").read_text(encoding="utf-8")
    assert 'RAY_TMP_DIR="/dev/shm/bg-ray-${RAY_DIGEST}"' in launcher
    assert 'df -Pk /dev/shm' in launcher
    assert "awk 'NR==2 {print \\$4}'" in launcher
    assert "awk 'NR==2 {print \\\\$4}'" not in launcher
    assert "short_ray_tmp_dir" not in launcher
    assert "gpu_ids: $gpu_ids" in launcher
    assert "tensor_parallel_width: 1" in launcher
    assert "replica_count: 1" in launcher
    assert "synchronous EasyR1/GRPO smoke" in launcher
    assert "rollout is not disaggregated across nodes" in launcher
