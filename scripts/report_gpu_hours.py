#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


def _timestamp(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def summarize_gpu_hours(
    records: Iterable[dict[str, Any]],
    *,
    max_gap_seconds: float = 900.0,
    active_utilization_pct: float = 5.0,
    occupied_memory_mib: float = 1024.0,
) -> dict[str, Any]:
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[(str(record["node"]), int(record["gpu_index"]))].append(record)

    by_node_raw: dict[str, dict[str, float | int | str | None]] = defaultdict(
        lambda: {
            "sample_count": 0,
            "observed_seconds": 0.0,
            "active_seconds": 0.0,
            "occupied_seconds": 0.0,
            "utilization_equivalent_seconds": 0.0,
            "omitted_gap_count": 0,
            "first_timestamp": None,
            "last_timestamp": None,
        }
    )
    per_gpu: list[dict[str, Any]] = []
    for (node, gpu_index), samples in sorted(grouped.items()):
        samples.sort(key=lambda item: _timestamp(str(item["ts"])))
        observed = active = occupied = utilization_equivalent = 0.0
        omitted = 0
        for current, following in zip(samples, samples[1:]):
            seconds = (
                _timestamp(str(following["ts"])) - _timestamp(str(current["ts"]))
            ).total_seconds()
            if seconds <= 0 or seconds > max_gap_seconds:
                omitted += 1
                continue
            observed += seconds
            utilization = max(0.0, min(100.0, float(current["util_gpu_pct"])))
            utilization_equivalent += seconds * utilization / 100.0
            if utilization >= active_utilization_pct:
                active += seconds
            if float(current["memory_used_mib"]) >= occupied_memory_mib:
                occupied += seconds

        first = str(samples[0]["ts"])
        last = str(samples[-1]["ts"])
        record = {
            "node": node,
            "gpu_index": gpu_index,
            "sample_count": len(samples),
            "first_timestamp": first,
            "last_timestamp": last,
            "observed_gpu_hours": observed / 3600.0,
            "active_gpu_hours": active / 3600.0,
            "occupied_gpu_hours": occupied / 3600.0,
            "utilization_equivalent_gpu_hours": utilization_equivalent / 3600.0,
            "mean_utilization_pct_over_observed": (
                100.0 * utilization_equivalent / observed if observed else None
            ),
            "omitted_gap_count": omitted,
        }
        per_gpu.append(record)

        node_record = by_node_raw[node]
        node_record["sample_count"] = int(node_record["sample_count"]) + len(samples)
        node_record["observed_seconds"] = float(node_record["observed_seconds"]) + observed
        node_record["active_seconds"] = float(node_record["active_seconds"]) + active
        node_record["occupied_seconds"] = float(node_record["occupied_seconds"]) + occupied
        node_record["utilization_equivalent_seconds"] = (
            float(node_record["utilization_equivalent_seconds"]) + utilization_equivalent
        )
        node_record["omitted_gap_count"] = int(node_record["omitted_gap_count"]) + omitted
        node_record["first_timestamp"] = min(
            filter(None, [node_record["first_timestamp"], first])
        )
        node_record["last_timestamp"] = max(
            filter(None, [node_record["last_timestamp"], last])
        )

    by_node: dict[str, dict[str, Any]] = {}
    for node, raw in sorted(by_node_raw.items()):
        observed = float(raw.pop("observed_seconds"))
        active = float(raw.pop("active_seconds"))
        occupied = float(raw.pop("occupied_seconds"))
        utilization_equivalent = float(raw.pop("utilization_equivalent_seconds"))
        by_node[node] = {
            **raw,
            "observed_gpu_hours": observed / 3600.0,
            "active_gpu_hours": active / 3600.0,
            "occupied_gpu_hours": occupied / 3600.0,
            "utilization_equivalent_gpu_hours": utilization_equivalent / 3600.0,
            "mean_utilization_pct_over_observed": (
                100.0 * utilization_equivalent / observed if observed else None
            ),
        }

    return {
        "schema_version": "blind-gains.gpu-hours-utilization.v1",
        "status": "pass",
        "gate": False,
        "attribution": "all processes; foreign and project jobs are not separated",
        "parameters": {
            "max_gap_seconds": max_gap_seconds,
            "active_utilization_pct": active_utilization_pct,
            "occupied_memory_mib": occupied_memory_mib,
        },
        "by_node": by_node,
        "per_gpu": per_gpu,
    }


def _read_jsonl(paths: list[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as error:
                    raise ValueError(f"invalid JSONL at {path}:{line_number}: {error}") from error
    return records


def render_markdown(payload: dict[str, Any], inputs: list[Path]) -> str:
    lines = [
        "# GPU-Hours Utilization Report",
        "",
        "Status:",
        "- Telemetry has been integrated as a utilization report only; it is not a compute gate.",
        "- Foreign processes are treated as normal and are included because process ownership cannot be reconstructed from `nvidia-smi` samples.",
        "",
        "Evidence:",
        f"- Inputs: {', '.join(f'`{path}`' for path in inputs)}.",
        "- Machine status JSON: `reports/gpu_hours_utilization.json`.",
        "- Intervals longer than 15 minutes are omitted instead of imputed.",
        "- Active GPU-hours use sampled GPU utilization >=5%; occupied GPU-hours use memory >=1,024 MiB.",
        "",
        "| Node | Samples | Coverage | Observed GPU-h | Active GPU-h | Occupied GPU-h | Util.-equiv. GPU-h | Mean util. | Omitted gaps |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for node, record in payload["by_node"].items():
        mean = record["mean_utilization_pct_over_observed"]
        lines.append(
            f"| {node} | {record['sample_count']:,} | {record['first_timestamp']} to {record['last_timestamp']} | "
            f"{record['observed_gpu_hours']:.2f} | {record['active_gpu_hours']:.2f} | "
            f"{record['occupied_gpu_hours']:.2f} | {record['utilization_equivalent_gpu_hours']:.2f} | "
            f"{mean:.2f}% | {record['omitted_gap_count']} |"
        )
    lines += [
        "",
        "Problems:",
        "- Utilization telemetry does not identify process owners, commands, or scientific value; it must not be used to infer project-only efficiency.",
        "- A short high-utilization job between samples may be missed.",
        "",
        "Decision:",
        "- Remove per-GPU idle violations from `scripts/compute_gate2.py`; retain this descriptive accounting alongside run manifests.",
        "",
        "Next actions:",
        "- Continue collection and publish a new versioned report for the pilot window rather than rewriting this snapshot.",
        "",
    ]
    return "\n".join(lines)


def _write_new(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--json-output", type=Path, default=Path("reports/gpu_hours_utilization.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("reports/gpu_hours_utilization.md"))
    args = parser.parse_args()
    for output in (args.json_output, args.markdown_output):
        if output.exists():
            raise FileExistsError(f"refusing to overwrite utilization report: {output}")
    payload = summarize_gpu_hours(_read_jsonl(args.inputs))
    _write_new(args.json_output, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    _write_new(args.markdown_output, render_markdown(payload, args.inputs))
    print(json.dumps({"status": "pass", "by_node": payload["by_node"]}, sort_keys=True))


if __name__ == "__main__":
    main()
