from __future__ import annotations

import json
from pathlib import Path

from scripts.build_generalization_audits import (
    BACKENDS,
    CONDITIONS,
    DATASETS,
    build_payload,
)
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT


def _write_run_metric(
    root: Path, name: str, job_type: str, metric: dict, manifest_fields: dict
) -> Path:
    run = root / name
    run.mkdir()
    metric_path = run / "metrics.json"
    metric_path.write_text(json.dumps(metric) + "\n", encoding="utf-8")
    manifest = {
        "status": "complete",
        "job_type": job_type,
        "expected_artifacts": [str(metric_path)],
        **manifest_fields,
    }
    (run / "run_manifest.json").write_text(
        json.dumps(manifest) + "\n", encoding="utf-8"
    )
    return metric_path


def _fixture(tmp_path: Path) -> tuple[list[Path], list[Path], list[Path]]:
    flip = []
    stage_names = {"internvl3": "InternVL3-9B", "gemma3": "gemma-3-12b-it"}
    for backend in BACKENDS:
        for dataset in DATASETS:
            for condition in CONDITIONS:
                metric = {
                    "backend": backend,
                    "dataset_id": dataset,
                    "condition": condition,
                    "row_count": 1200,
                    "n_pairs": 1200.0,
                    "pair_accuracy": 0.5,
                    "pair_accuracy_ci95_low": 0.45,
                    "pair_accuracy_ci95_high": 0.55,
                    "collapse_rate": 0.1,
                    "parser_version": "canonical-v2",
                    "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
                    "decoding": {"temperature": 0.0, "top_p": 1.0, "n": 1, "max_new_tokens": 384},
                    "per_template": {"template": {"pair_accuracy": 0.5}},
                    "runtime": (
                        {
                            "backend": "internvl3",
                            "generation_callable": True,
                            "generation_shim_applied": True,
                            "generation_config_ready": True,
                            "legacy_cache_only": True,
                            "timm_version": "0.9.12",
                            "use_flash_attn": False,
                        }
                        if backend == "internvl3"
                        else {
                            "backend": "gemma3",
                            "generation_callable": True,
                            "processor_use_fast": False,
                            "torch_version": "2.6.0+cu118",
                        }
                    ),
                }
                flip.append(
                    _write_run_metric(
                        tmp_path,
                        f"flip-{backend}-{dataset}-{condition}",
                        "m11_nonqwen_fliptrack_evaluation",
                        metric,
                        {"model_backend": backend, "dataset_id": dataset, "condition": condition},
                    )
                )
    blind = []
    for backend in BACKENDS:
        for condition in CONDITIONS:
            metric = {
                "backend": backend,
                "condition": condition,
                "n_rows": 4096,
                "acc_final": 0.4,
                "acc_final_ci95_low": 0.38,
                "acc_final_ci95_high": 0.42,
                "acc_strict": 0.35,
                "contract_valid_rate": 0.8,
                "parser_version": "canonical-v2",
                "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
                "decoding": {"temperature": 0.0, "top_p": 1.0, "n": 1, "max_new_tokens": 2048},
                "per_source_category": {"source::category": {"n": 4096, "acc_final": 0.4}},
                "runtime": (
                    {
                        "backend": "internvl3",
                        "generation_callable": True,
                        "generation_shim_applied": True,
                        "generation_config_ready": True,
                        "legacy_cache_only": True,
                        "timm_version": "0.9.12",
                        "use_flash_attn": False,
                    }
                    if backend == "internvl3"
                    else {
                        "backend": "gemma3",
                        "generation_callable": True,
                        "processor_use_fast": False,
                        "torch_version": "2.6.0+cu118",
                    }
                ),
            }
            blind.append(
                _write_run_metric(
                    tmp_path,
                    f"blind-{backend}-{condition}",
                    "m11_nonqwen_blind_sample_evaluation",
                    metric,
                    {"model_backend": backend, "condition": condition},
                )
            )
    stages = []
    for backend in BACKENDS:
        path = tmp_path / f"stage-{backend}.json"
        path.write_text(
            json.dumps(
                {
                    "status": "complete",
                    "job_type": "m11_ephemeral_model_stage",
                    "destination": f"/dev/shm/blind-gains/models/{stage_names[backend]}",
                    "data_manifest_hash": "a" * 64,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        stages.append(path)
    return flip, blind, stages


def test_complete_generalization_matrix_passes(tmp_path: Path) -> None:
    flip, blind, stages = _fixture(tmp_path)

    payload = build_payload(flip, blind, stages)

    assert payload["status"] == "pass"
    assert all(payload["checks"].values())
    assert payload["errors"] == []


def test_missing_fliptrack_cell_fails_matrix(tmp_path: Path) -> None:
    flip, blind, stages = _fixture(tmp_path)

    payload = build_payload(flip[:-1], blind, stages)

    assert payload["status"] == "fail"
    assert payload["checks"]["complete_fliptrack_2x2x3_matrix"] is False
