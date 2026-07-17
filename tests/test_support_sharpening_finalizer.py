from __future__ import annotations

from pathlib import Path

import pytest

from scripts.finalize_support_sharpening_seed1 import (
    DRAW_SCHEMA_VERSION,
    _validate_draw_contract,
    _validate_run,
)
from src.analysis.support_sharpening import registered_sampling_kwargs
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT
from src.rewards.answer_reward import PARSER_VERSION
from src.rewards.pilot_reward import PILOT_REWARD_VERSION


def test_finalizer_rejects_draw_that_reuses_an_unregistered_decoding_call() -> None:
    row = {
        "schema_version": DRAW_SCHEMA_VERSION,
        "arm": "a1_real",
        "condition": "real",
        "draw_index": 16,
        "decoding": {**registered_sampling_kwargs(16), "n": 16},
        "response": "same text is permitted, but the call contract is not",
        "pilot_accuracy_correct": False,
        "parser_version": PARSER_VERSION,
        "pilot_reward_version": PILOT_REWARD_VERSION,
        "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
        "duplicate_text_responses_retained": True,
    }

    with pytest.raises(ValueError, match="decoding.*False"):
        _validate_draw_contract(row, "a1_real", "real")


def test_finalizer_rejects_manifest_from_a_different_execution_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path
    config_path = root / "configs/eval/support_sharpening_v2.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text('{"arms":{"a1_real":{"condition":"real","candidate_count":1}}}\n')
    run_dir = root / "experiments/runs/fixture"
    run_dir.mkdir(parents=True)
    (run_dir / "draws.jsonl").write_text("{}\n")
    (run_dir / "run_manifest.json").write_text(
        """{
          "status":"complete",
          "exit_code":0,
          "artifacts_exist":true,
          "job_type":"m10_support_sharpening_followup",
          "arm":"a1_real",
          "condition":"real",
          "config_path":"configs/eval/support_sharpening_v2.json",
          "config_hash":"ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
          "candidate_count":1,
          "expected_row_count":64,
          "draw_seeds":{"first":20260732,"last":20260795,"count":64,"formula":"20260716 + draw_index"},
          "decoding":{"temperature":1.0,"top_p":1.0,"n_per_call":1,"max_tokens":2048},
          "expected_artifacts":["experiments/runs/fixture/draws.jsonl"]
        }\n""",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "scripts.finalize_support_sharpening_seed1.ROOT", root
    )

    with pytest.raises(ValueError, match="does not pass"):
        _validate_run(
            {"arms": {"a1_real": {"condition": "real", "candidate_count": 1}}},
            config_path,
            "a1_real",
            run_dir,
        )
