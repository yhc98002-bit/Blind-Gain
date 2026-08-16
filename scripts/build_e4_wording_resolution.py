#!/usr/bin/env python3
"""E4 wording resolution (dispatch 2026-08-16 item 3; criterion untouched).

The registration's prose criterion reads "every attacker's side-prediction
accuracy 95% bootstrap CI includes 0.5", but the instrument folds the
statistic to max(AUC, 1-AUC) before taking percentiles, so the recorded
interval lives on [0.5, 1] by construction and can never include 0.5. The PI
decision (EXPERIMENT_TODO PART 5, 2026-08-16): recompute UNfolded
per-attacker AUC CIs from the attacker outputs and evaluate the registered
sentence literally, per attacker; the folded statistics remain as descriptive
columns and the operative folded gate criterion is NOT modified.

This builder consumes:
  --v1  the sealed v1 gate report (folded aggregates; the file of record)
  --v2  the re-run report carrying `directed_oof_auc_unfolded_ci_95`
        (same registered inputs, same seed; folded and unfolded intervals are
        quantiles of the same bootstrap draws)
and emits reports/track4_premise_v2_e4_wording_resolution_v1.{json,md}.

Reproduction check (hard): every folded field in v2 must reproduce v1 —
exactly for the CPU attackers (frequency_stat, metadata), and to 1e-9 for
dinov2 (GPU inference). Any violation is reported and the literal verdicts
are marked non-evaluable; the builder then exits 1.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

FOLDED_FIELDS = (
    "directed_oof_auc",
    "gate_statistic",
    "pair_bootstrap_ci_95",
    "fold_train_auc",
    "fold_direction",
    "n_members",
    "n_pairs",
    "n_splits",
)
EXACT_ATTACKERS = {"frequency_stat", "metadata"}
DINO_TOLERANCE = 1e-9


def _scopes(entry: dict) -> list[tuple[str, dict]]:
    return [("pooled", entry["pooled"]), *sorted(entry["per_template"].items())]


def _max_delta(a, b) -> float:
    if isinstance(a, list):
        return max((_max_delta(x, y) for x, y in zip(a, b)), default=0.0)
    if isinstance(a, (int, float)):
        return abs(float(a) - float(b))
    return 0.0 if a == b else float("inf")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v1", type=Path, required=True)
    parser.add_argument("--v2", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    v1 = json.loads(args.v1.read_text(encoding="utf-8"))
    v2 = json.loads(args.v2.read_text(encoding="utf-8"))

    reproduction: list[dict] = []
    rows: list[dict] = []
    ok = True
    for attacker in sorted(v1["attacks"]):
        entry_v1 = v1["attacks"][attacker]
        entry_v2 = v2["attacks"].get(attacker)
        if entry_v1 is None or entry_v2 is None:
            reproduction.append({"attacker": attacker, "status": "missing", "ok": False})
            ok = False
            continue
        for (scope, r1), (_, r2) in zip(_scopes(entry_v1), _scopes(entry_v2)):
            deltas = {field: _max_delta(r1[field], r2[field]) for field in FOLDED_FIELDS}
            worst = max(deltas.values())
            tolerance = 0.0 if attacker in EXACT_ATTACKERS else DINO_TOLERANCE
            row_ok = worst <= tolerance
            ok = ok and row_ok
            reproduction.append(
                {
                    "attacker": attacker,
                    "scope": scope,
                    "max_abs_delta_folded_fields": worst,
                    "tolerance": tolerance,
                    "ok": row_ok,
                }
            )
            unfolded = r2["directed_oof_auc_unfolded_ci_95"]
            rows.append(
                {
                    "attacker": attacker,
                    "scope": scope,
                    "directed_oof_auc": r2["directed_oof_auc"],
                    "unfolded_ci_95": unfolded,
                    "ci_includes_0_5_literal": bool(unfolded[0] <= 0.5 <= unfolded[1]),
                    "folded_gate_statistic_descriptive": r1["gate_statistic"],
                    "folded_ci_95_descriptive": r1["pair_bootstrap_ci_95"],
                }
            )

    per_attacker_literal = {
        attacker: all(
            row["ci_includes_0_5_literal"] for row in rows if row["attacker"] == attacker
        )
        for attacker in sorted({row["attacker"] for row in rows})
    }
    payload = {
        "schema_version": "blind-gains.e4-wording-resolution.v1",
        "title": "E4 attacker gate — literal 'CI includes 0.5' evaluation on unfolded CIs",
        "criterion_note": (
            "The operative registered gate remains the folded one the instrument "
            "implements (point <= 0.55, folded CI upper <= 0.62); it is not "
            "modified here and its verdict is unchanged from v1."
        ),
        "v1_report": str(args.v1),
        "v2_report": str(args.v2),
        "v1_gate_verdict_unchanged": v1["gate"],
        "reproduction_check": {"ok": ok, "rows": reproduction},
        "literal_criterion_rows": rows,
        "per_attacker_literal_verdict": per_attacker_literal,
        "all_attackers_literal_pass": all(per_attacker_literal.values()) if per_attacker_literal else False,
    }
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# E4 wording resolution — unfolded per-attacker AUC CIs (v1 criterion untouched)",
        "",
        f"v1 (folded, file of record): `{args.v1}` · v2 re-run: `{args.v2}`",
        "",
        f"Reproduction check: {'PASS' if ok else 'FAIL'} (CPU attackers exact; dinov2 tolerance 1e-9).",
        "",
        "| attacker | scope | unfolded directed OOF AUC | unfolded 95% CI | CI includes 0.5 (literal) | folded stat (descriptive) | folded CI (descriptive) |",
        "|---|---|---:|---|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {attacker} | {scope} | {auc:.6f} | [{lo:.6f}, {hi:.6f}] | {verdict} | {folded:.6f} | [{flo:.6f}, {fhi:.6f}] |".format(
                attacker=row["attacker"],
                scope=row["scope"],
                auc=row["directed_oof_auc"],
                lo=row["unfolded_ci_95"][0],
                hi=row["unfolded_ci_95"][1],
                verdict="yes" if row["ci_includes_0_5_literal"] else "**no**",
                folded=row["folded_gate_statistic_descriptive"],
                flo=row["folded_ci_95_descriptive"][0],
                fhi=row["folded_ci_95_descriptive"][1],
            )
        )
    lines += [
        "",
        "Per-attacker literal verdict: "
        + "; ".join(f"{k}: {'pass' if v else 'FAIL'}" for k, v in per_attacker_literal.items()),
        "",
        payload["criterion_note"],
    ]
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"reproduction_ok": ok, "per_attacker_literal_verdict": per_attacker_literal}, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
