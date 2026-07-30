#!/usr/bin/env python3
"""Render reports/e1c_blind_columns_v1.md from the json payload."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
SRC = ROOT / "reports/e1c_blind_columns_v1.json"
OUT = ROOT / "reports/e1c_blind_columns_v1.md"


def num(value, digits=4):
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "true" if value else "false"
    return f"{value:.{digits}f}"


def ci(block, key, digits=4):
    low = block.get(f"{key}_ci95_low")
    high = block.get(f"{key}_ci95_high")
    if low is None or high is None:
        return ""
    return f"[{low:.{digits}f}, {high:.{digits}f}]"


def est(block, key, digits=4):
    """Point estimate plus interval, collapsed to a single 'n/a' when undefined."""
    point = num(block.get(key), digits)
    interval = ci(block, key, digits)
    if point == "n/a" and not interval:
        return "n/a"
    return f"{point} {interval}".strip()


def label(row):
    return row["subset"] + (" **(underpowered)**" if row.get("underpowered_subset") else "")


def main() -> None:
    payload = json.loads(SRC.read_text(encoding="utf-8"))
    lines: list[str] = []
    add = lines.append

    add("# E1c: blind columns for the five benchmarks that had none")
    add("")
    add(f"- Schema: `{payload['schema_version']}`")
    add(f"- Generated: {payload['generated_utc']}")
    add(f"- Source of truth: `reports/e1c_blind_columns_v1.json`")
    add("")
    add(payload["purpose"])
    add("")
    add("This takes the F0 visual-necessity audit from 2 benchmarks (MMStar, MathVista) to 7.")
    add("")

    add("## Method")
    add("")
    method = payload["method"]
    add(f"- naive retention = `{method['naive_retention']}`")
    add(f"- corrected retention = `{method['corrected_retention']}`")
    add("- null rule (unchanged from `reports/chance_corrected_retention_v1.json`):")
    for key, value in method["null_rule"].items():
        add(f"  - {key}: {value}")
    add(f"- null aggregation: {method['null_aggregation']}")
    boot = method["bootstrap"]
    add(
        f"- bootstrap: {boot['reps']} reps, seed {boot['seed']}, unit={boot['unit']}, "
        f"paired={boot['paired']}, CI={boot['ci']}"
    )
    add(f"- {method['mixed_benchmark_rule']}")
    add(f"- {method['undefined_denominator']}")
    add(f"- {method['underpowered_subsets']}")
    add("")
    add(f"**Blind integrity.** {payload['blind_integrity']}")
    add("")
    add("## HallusionBench null: which rule was applied")
    add("")
    add(payload["hallusionbench_null_decision"])
    add("")
    add("**Prompt mirroring.** The blind prompt is the with-image prompt minus the image messages:")
    for key, value in payload["prompt_mirroring"].items():
        add(f"- `{key}`: {value}")
    add("")

    add("## Format composition of each benchmark")
    add("")
    add("| Benchmark | Model | Format counts |")
    add("| --- | --- | --- |")
    for benchmark, per_model in payload["format_counts"].items():
        for model, counts in per_model.items():
            pretty = ", ".join(f"`{k}`={v}" for k, v in counts.items())
            add(f"| {benchmark} | {model} | {pretty} |")
    add("")

    add("## Whole-benchmark naive retention (null ignored)")
    add("")
    add("| Benchmark | Model | n | with-image acc_final | blind acc_final | naive retention (95% CI) |")
    add("| --- | --- | --- | --- | --- | --- |")
    for row in payload["reference_naive_whole_benchmark"]:
        lenient = row["lenient_acc_final"]
        add(
            f"| {row['benchmark']} | {row['model']} | {row['n']} | "
            f"{num(lenient['with_image_acc'])} | {num(lenient['blind_acc'])} | "
            f"{est(lenient, 'naive_retention')} |"
        )
    add("")

    add("## Format-split rows (lenient, `acc_final`)")
    add("")
    add(
        "| Benchmark | Model | Subset | k | n | null | with-image | blind | naive retention (95% CI) "
        "| corrected retention (95% CI) | denom<=0 frac |"
    )
    add("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for row in payload["rows"]:
        lenient = row["lenient_acc_final"]
        add(
            f"| {row['benchmark']} | {row['model']} | {label(row)} | "
            f"{row['k'] if row['k'] is not None else 'mixed'} | {row['n']} | {num(row['null'], 4)} | "
            f"{num(lenient['with_image_acc'])} | {num(lenient['blind_acc'])} | "
            f"{est(lenient, 'naive_retention')} | "
            f"{est(lenient, 'corrected_retention')} | "
            f"{num(lenient['boot_denominator_nonpositive_frac'], 3)} |"
        )
    add("")

    add("## Format-split rows (strict, `acc_strict`)")
    add("")
    add(f"{payload['method']['strict_caveat']}")
    add("")
    add(
        "| Benchmark | Model | Subset | n | null | with-image | blind | naive retention (95% CI) "
        "| corrected retention (95% CI) | denom crosses zero |"
    )
    add("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for row in payload["rows"]:
        strict = row["strict_acc_strict"]
        add(
            f"| {row['benchmark']} | {row['model']} | {label(row)} | {row['n']} | "
            f"{num(row['null'], 4)} | {num(strict['with_image_acc'])} | {num(strict['blind_acc'])} | "
            f"{est(strict, 'naive_retention')} | "
            f"{est(strict, 'corrected_retention')} | "
            f"{num(strict['denominator_crosses_zero'])} |"
        )
    add("")

    add("## Not computed")
    add("")
    for entry in payload["not_computed"]:
        head = f"- **{entry['benchmark']} / {entry['model']} / {entry['subset']}**"
        if "n" in entry:
            head += f" (n={entry['n']})"
        add(f"{head}: {entry['reason']}")
    add("")

    add("## Provenance")
    add("")
    add("| Benchmark | Model | Blind run id | Blind config | with-image run (source of the paired column) |")
    add("| --- | --- | --- | --- | --- |")
    for entry in payload["provenance"]:
        add(
            f"| {entry['benchmark']} | {entry['model']} | `{entry['blind_run_id']}` | "
            f"`{entry['blind_config']}` | `{entry['with_image_run']}` |"
        )
    add("")
    add("All blind cells: node/GPU, seed, git hash, config hash, data manifest hash, exit code, and "
        "`image_removed` flag are recorded per cell in the `provenance` block of the json, and in each "
        "run's `run_manifest.json`.")
    add("")
    add("### Input artifact digests")
    add("")
    add("| Artifact | sha256 | bytes |")
    add("| --- | --- | --- |")
    for key, value in payload["inputs"].items():
        add(f"| `{key}` | `{value['sha256'][:16]}...` | {value['bytes']} |")
    add("")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", OUT, f"({len(lines)} lines)")


if __name__ == "__main__":
    main()
