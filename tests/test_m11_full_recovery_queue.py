from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.run_m11_full_recovery_queue import (
    EXPECTED_M2_ARMS,
    initial_recovery_state,
    m2_priority_gate_status,
    validate_smoke_evidence,
)
from scripts.run_m11_generalization_queue import BACKENDS, CONDITIONS
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _runtime(backend: str) -> dict:
    if backend == "internvl3":
        return {
            "backend": "internvl3",
            "generation_callable": True,
            "generation_shim_applied": True,
            "generation_config_ready": True,
            "legacy_cache_only": True,
            "timm_version": "0.9.12",
            "use_flash_attn": False,
        }
    return {
        "backend": "gemma3",
        "generation_callable": True,
        "processor_use_fast": False,
        "torch_version": "2.6.0+cu118",
    }


def _config(tmp_path: Path) -> dict:
    records = []
    for backend in BACKENDS:
        for condition in CONDITIONS:
            run = tmp_path / "runs" / f"{backend}-{condition}"
            run.mkdir(parents=True)
            prediction = run / "predictions.jsonl"
            metrics = run / "metrics.json"
            manifest = run / "run_manifest.json"
            prediction.write_text(json.dumps({"pair_id": "fixture"}) + "\n", encoding="utf-8")
            metrics.write_text(
                json.dumps(
                    {
                        "row_count": 1,
                        "parser_version": "canonical-v2",
                        "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
                        "runtime": _runtime(backend),
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            manifest.write_text(
                json.dumps(
                    {
                        "job_type": "m11_nonqwen_fliptrack_evaluation",
                        "status": "complete",
                        "exit_code": 0,
                        "model_backend": backend,
                        "dataset_id": "r19",
                        "condition": condition,
                        "limit": 1,
                        "max_new_tokens": 384,
                        "decoding": {"temperature": 0.0, "top_p": 1.0, "n": 1},
                        "expected_artifacts": [str(prediction), str(metrics)],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            records.append(
                {
                    "cell_id": f"smoke_{backend}_r19_{condition}",
                    "backend": backend,
                    "condition": condition,
                    "run_manifest": str(manifest.relative_to(tmp_path)),
                    "run_manifest_sha256": _hash(manifest),
                    "metrics": str(metrics.relative_to(tmp_path)),
                    "metrics_sha256": _hash(metrics),
                    "predictions": str(prediction.relative_to(tmp_path)),
                    "predictions_sha256": _hash(prediction),
                }
            )
    return {
        "models": {
            backend: {"python": ".venv-m11/bin/python"} for backend in BACKENDS
        },
        "conditions": list(CONDITIONS),
        "smoke_limit": 1,
        "smoke_evidence": records,
        "m2_priority_gate": [
            {"arm": arm, "marker": f"markers/{arm}.json"}
            for arm in sorted(EXPECTED_M2_ARMS)
        ],
    }


def test_six_hash_pinned_smoke_cells_initialize_full_only_state(tmp_path: Path) -> None:
    config = _config(tmp_path)

    audit = validate_smoke_evidence(config, tmp_path)
    state = initial_recovery_state(config, audit)

    assert len(audit) == 6
    assert len(state["cells"]) == 18
    assert all(not key.startswith("smoke_") for key in state["cells"])
    assert state["status"] == "waiting_m2_priority"


def test_smoke_artifact_mutation_after_registration_fails_closed(tmp_path: Path) -> None:
    config = _config(tmp_path)
    target = tmp_path / config["smoke_evidence"][0]["predictions"]
    target.write_text('{"pair_id":"mutated"}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="hash mismatch"):
        validate_smoke_evidence(config, tmp_path)


def test_hash_valid_but_wrong_smoke_identity_fails_closed(tmp_path: Path) -> None:
    config = _config(tmp_path)
    record = config["smoke_evidence"][0]
    manifest = tmp_path / record["run_manifest"]
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["condition"] = "caption"
    manifest.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    record["run_manifest_sha256"] = _hash(manifest)

    with pytest.raises(ValueError, match="invalid smoke evidence"):
        validate_smoke_evidence(config, tmp_path)


def test_missing_m2_markers_keep_full_queue_closed(tmp_path: Path) -> None:
    config = _config(tmp_path)

    ready, evidence = m2_priority_gate_status(config, tmp_path)

    assert ready is False
    assert set(evidence) == EXPECTED_M2_ARMS
    assert all(item["exists"] is False for item in evidence.values())


def test_all_valid_step100_markers_open_m2_priority_gate(tmp_path: Path) -> None:
    config = _config(tmp_path)
    for item in config["m2_priority_gate"]:
        path = tmp_path / item["marker"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "schema_version": "blind-gains.pilot-step-eval-marker.v1",
                    "status": "complete",
                    "global_step": 100,
                    "checks": {"fixture": True},
                }
            )
            + "\n",
            encoding="utf-8",
        )

    ready, evidence = m2_priority_gate_status(config, tmp_path)

    assert ready is True
    assert all(item["exists"] for item in evidence.values())


def test_malformed_existing_m2_marker_fails_instead_of_waiting(tmp_path: Path) -> None:
    config = _config(tmp_path)
    item = config["m2_priority_gate"][0]
    path = tmp_path / item["marker"]
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "blind-gains.pilot-step-eval-marker.v1",
                "status": "complete",
                "global_step": 60,
                "checks": {"fixture": True},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid M2 priority marker"):
        m2_priority_gate_status(config, tmp_path)


def test_launcher_is_login_only_and_pins_m2_priority_gate() -> None:
    root = Path(__file__).resolve().parents[1]
    launcher = (root / "scripts/launch_m11_full_recovery_queue.sh").read_text(
        encoding="utf-8"
    )

    assert 'job_type: "m11_generalization_full_recovery_queue"' in launcher
    assert 'node: "login"' in launcher
    assert 'gpu_allocation: []' in launcher
    assert "--preflight-only" in launcher
    assert "waits for all four M2 step-100 evaluation markers" in launcher
    assert "critical M11 recovery code or config differs from HEAD" in launcher
