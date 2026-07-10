from __future__ import annotations

import copy
import json

from scripts.compute_gate2 import _exact_package_ready, _json_status, machine_ready
from scripts.compute_recovery_gate1 import compute_recovery_gate


RECOVERY_PASS_INPUT = {
    "scientific_gpu_jobs_an12": 1,
    "scientific_gpu_jobs_an29": 1,
    "stage0_proposal_gate": "conditional",
    "grpo_audit": "pass",
    "grpo_repro_steps": 30,
    "dataset_license_triage": "pass",
    "fliptrack_v01_pairs": 300,
    "fliptrack_v01_real_pair_acc": 0.80,
    "fliptrack_v01_caption_pair_acc": 0.60,
    "artifact_gate_v01": "pass",
    "literature_overlap": "pass",
}


def test_recovery_status_cannot_pass_with_any_failed_sub_gate() -> None:
    baseline = compute_recovery_gate(RECOVERY_PASS_INPUT)
    assert baseline["status"] == "pass"
    for sub_gate in baseline["sub_gates"]:
        candidate = copy.deepcopy(RECOVERY_PASS_INPUT)
        if sub_gate == "scientific_job_an12":
            candidate["scientific_gpu_jobs_an12"] = 0
        elif sub_gate == "scientific_job_an29":
            candidate["scientific_gpu_jobs_an29"] = 0
        elif sub_gate == "stage0_at_least_conditional":
            candidate["stage0_proposal_gate"] = "fail"
        elif sub_gate == "grpo_audit_complete":
            candidate["grpo_audit"] = "fail"
        elif sub_gate == "grpo_reproduction_30_steps":
            candidate["grpo_repro_steps"] = 29
        elif sub_gate == "dataset_license_triage_complete":
            candidate["dataset_license_triage"] = "partial"
        elif sub_gate == "fliptrack_v01_300_pairs":
            candidate["fliptrack_v01_pairs"] = 299
        elif sub_gate == "fliptrack_real_accuracy_target":
            candidate["fliptrack_v01_real_pair_acc"] = 0.79
        elif sub_gate == "fliptrack_caption_accuracy_target":
            candidate["fliptrack_v01_caption_pair_acc"] = 0.61
        elif sub_gate == "artifact_gate_v01_complete":
            candidate["artifact_gate_v01"] = "fail"
        elif sub_gate == "literature_overlap_complete":
            candidate["literature_overlap"] = "fail"
        assert compute_recovery_gate(candidate)["status"] == "fail", sub_gate


def test_gate2_machine_ready_is_and_of_every_check() -> None:
    checks = {f"check_{index}": True for index in range(13)}
    assert machine_ready(checks) is True
    for name in checks:
        candidate = dict(checks)
        candidate[name] = False
        assert machine_ready(candidate) is False


def test_gate_json_status_does_not_treat_fail_string_as_truthy(tmp_path) -> None:
    status_file = tmp_path / "status.json"
    status_file.write_text(json.dumps({"status": "fail"}), encoding="utf-8")
    assert _json_status(status_file) is False
    status_file.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
    assert _json_status(status_file) is True
    status_file.write_text(json.dumps({"status": True}), encoding="utf-8")
    assert _json_status(status_file) is True


def test_gate_json_status_supports_nested_gate_status(tmp_path) -> None:
    status_file = tmp_path / "artifact.json"
    status_file.write_text(json.dumps({"gate": {"status": True}}), encoding="utf-8")
    assert _json_status(status_file, "gate", "status") is True
    assert _json_status(status_file) is False


def test_exact_package_requires_both_caption_cells(tmp_path) -> None:
    summary = tmp_path / "summary.json"
    payload = {
        "status": "automated_pass_human_audit_pending",
        "n_pairs": 1200,
        "cells": {
            "qwen25vl3b": {"caption": {"metrics": {"n_pairs": 1200}}},
            "qwen25vl7b": {"caption": {"metrics": {"n_pairs": 1200}}},
        },
    }
    summary.write_text(json.dumps(payload), encoding="utf-8")
    assert _exact_package_ready(summary) is True
    payload["cells"]["qwen25vl7b"]["caption"]["metrics"]["n_pairs"] = 1199
    summary.write_text(json.dumps(payload), encoding="utf-8")
    assert _exact_package_ready(summary) is False
