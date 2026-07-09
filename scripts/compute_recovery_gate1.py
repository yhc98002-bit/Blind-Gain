#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def compute_recovery_gate(inputs: dict[str, Any]) -> dict[str, Any]:
    sub_gates = {
        "scientific_job_an12": int(inputs.get("scientific_gpu_jobs_an12", 0)) >= 1,
        "scientific_job_an29": int(inputs.get("scientific_gpu_jobs_an29", 0)) >= 1,
        "stage0_at_least_conditional": inputs.get("stage0_proposal_gate") in {"conditional", "pass"},
        "grpo_audit_complete": inputs.get("grpo_audit") == "pass",
        "grpo_reproduction_30_steps": int(inputs.get("grpo_repro_steps", 0)) >= 30,
        "dataset_license_triage_complete": inputs.get("dataset_license_triage") == "pass",
        "fliptrack_v01_300_pairs": int(inputs.get("fliptrack_v01_pairs", 0)) >= 300,
        "fliptrack_real_accuracy_target": float(inputs.get("fliptrack_v01_real_pair_acc") or 0.0) >= 0.80,
        "fliptrack_caption_accuracy_target": float(inputs.get("fliptrack_v01_caption_pair_acc") or 1.0) <= 0.60,
        "artifact_gate_v01_complete": inputs.get("artifact_gate_v01") == "pass",
        "literature_overlap_complete": inputs.get("literature_overlap") == "pass",
    }
    status = "pass" if all(sub_gates.values()) else "fail"
    output = dict(inputs)
    output["status"] = status
    output["sub_gates"] = sub_gates
    output["failed_sub_gates"] = [name for name, passed in sub_gates.items() if not passed]
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="reports/recovery_gate1_inputs.json")
    parser.add_argument("--output", default="reports/recovery_gate1.json")
    args = parser.parse_args()
    inputs = json.loads(Path(args.input).read_text(encoding="utf-8"))
    output = compute_recovery_gate(inputs)
    Path(args.output).write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": output["status"], "failed_sub_gates": output["failed_sub_gates"]}, sort_keys=True))


if __name__ == "__main__":
    main()
