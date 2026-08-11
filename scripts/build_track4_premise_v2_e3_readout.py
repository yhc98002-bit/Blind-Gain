#!/usr/bin/env python3
"""Track-4 premise-v2 E3 (caption stress) per-type readout — registered criterion.

docs/registered_track4_premise_v2_design_v1.md section 7, E3:

    Pass, per type: caption member accuracy <= blind-floor threshold + 0.10
    absolute.  Fail => the track is caption-leaky: eval-only until revised.

The endpoint is **per intervention type** (I13 — nothing is pooled across types)
and is reported under **both scoring contracts, never merged** (I7).  The
caption-QA cell's own metrics.json is pooled across types and is therefore NOT
the endpoint; it is carried by sha256 only.

**The one thing the registration leaves open, stated rather than decided.**
"blind-floor threshold" can be read two ways, and this instrument reports both
without choosing:

  (a) *registered-ceiling reading* — the threshold E2 registers for the final
      clause, the literal 0.133 for all five types, giving a 0.233 E3 ceiling.
      This is the reading the section-7 text most directly supports: E2's own
      criterion names 0.133 as "the" blind-floor threshold for final member
      accuracy, and a registered constant cannot be moved by a measurement.
  (b) *measured-floor reading* — the type's own measured blind final member
      accuracy from the E2 cells, plus 0.10.

Where the two readings disagree for a type, the disagreement is the result and
the choice is the PI's.  Intervention type comes from the dev batch's own
manifest_causal_pairs.jsonl `intervention_type` field, never from parsing
pair_id (the type names are prefixes of one another).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "blind-gains.track4-premise-v2-e3-readout.v1"
REGISTERED_FINAL_BLIND_CEILING = 0.133
E3_MARGIN = 0.10


class ReadoutRefusal(RuntimeError):
    """Raised whenever the instrument refuses to produce a readout."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def build_report(
    predictions_path: Path,
    causal_manifest_path: Path,
    *,
    measured_blind_floors: dict[str, float] | None = None,
) -> dict[str, Any]:
    preds = _read_jsonl(predictions_path)
    if not preds:
        raise ReadoutRefusal("prediction file contains no rows")

    types_by_pair: dict[str, str] = {}
    for row in _read_jsonl(causal_manifest_path):
        pid = str(row["pair_id"])
        itype = row.get("intervention_type")
        if not itype:
            raise ReadoutRefusal(f"causal manifest row {pid} carries no intervention_type")
        types_by_pair[pid] = str(itype)
    if not types_by_pair:
        raise ReadoutRefusal("causal manifest contains no rows")

    seen: set[str] = set()
    for row in preds:
        pid = str(row["pair_id"])
        if pid in seen:
            raise ReadoutRefusal(f"duplicate pair_id in predictions: {pid}")
        seen.add(pid)
        if pid not in types_by_pair:
            raise ReadoutRefusal(
                f"prediction pair_id {pid} is not in the causal manifest; the type mapping "
                "would be a guess"
            )
        for key in ("acc_final_a", "acc_final_b", "acc_strict_a", "acc_strict_b"):
            if key not in row:
                raise ReadoutRefusal(f"prediction row {pid} lacks {key}")
        if str(row.get("parser_version")) != "canonical-v2":
            raise ReadoutRefusal(f"row {pid} parser_version={row.get('parser_version')!r}")
        if str(row.get("prompt_contract_id")) != "answer-tags-v1":
            raise ReadoutRefusal(f"row {pid} prompt_contract_id={row.get('prompt_contract_id')!r}")

    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in preds:
        by_type[types_by_pair[str(row["pair_id"])]].append(row)

    per_type: dict[str, Any] = {}
    for itype in sorted(by_type):
        rows = by_type[itype]
        n_pairs = len(rows)
        n_members = 2 * n_pairs
        lenient = sum(bool(r["acc_final_a"]) + bool(r["acc_final_b"]) for r in rows) / n_members
        strict = sum(bool(r["acc_strict_a"]) + bool(r["acc_strict_b"]) for r in rows) / n_members
        pair_lenient = sum(1 for r in rows if r["pair_correct"]) / n_pairs
        pair_strict = sum(1 for r in rows if r["strict_pair_correct"]) / n_pairs
        collapse = sum(1 for r in rows if r.get("collapsed")) / n_pairs

        entry: dict[str, Any] = {
            "n_pairs": n_pairs,
            "n_members": n_members,
            "caption_member_accuracy_lenient": lenient,
            "caption_member_accuracy_strict": strict,
            "caption_pair_accuracy_lenient": pair_lenient,
            "caption_pair_accuracy_strict": pair_strict,
            "collapse_rate": collapse,
            "readings": {},
        }
        reading_a_ceiling = REGISTERED_FINAL_BLIND_CEILING + E3_MARGIN
        entry["readings"]["a_registered_ceiling"] = {
            "blind_floor_threshold": REGISTERED_FINAL_BLIND_CEILING,
            "e3_ceiling": reading_a_ceiling,
            "lenient_verdict": "PASS" if lenient <= reading_a_ceiling else "FAIL",
            "strict_verdict": "PASS" if strict <= reading_a_ceiling else "FAIL",
            "basis": (
                "E2's registered final-clause threshold, the literal 0.133 for all five types, "
                "plus the registered 0.10 margin"
            ),
        }
        if measured_blind_floors is not None:
            if itype not in measured_blind_floors:
                raise ReadoutRefusal(
                    f"measured blind floor not supplied for type {itype}; reading (b) would be "
                    "a guess"
                )
            floor = measured_blind_floors[itype]
            reading_b_ceiling = floor + E3_MARGIN
            entry["readings"]["b_measured_floor"] = {
                "blind_floor_threshold": floor,
                "e3_ceiling": reading_b_ceiling,
                "lenient_verdict": "PASS" if lenient <= reading_b_ceiling else "FAIL",
                "strict_verdict": "PASS" if strict <= reading_b_ceiling else "FAIL",
                "basis": (
                    "the type's own measured blind final member accuracy from the E2 cells, "
                    "plus the registered 0.10 margin"
                ),
            }
            a = entry["readings"]["a_registered_ceiling"]
            b = entry["readings"]["b_measured_floor"]
            entry["readings_agree"] = (
                a["lenient_verdict"] == b["lenient_verdict"]
                and a["strict_verdict"] == b["strict_verdict"]
            )
        per_type[itype] = entry

    contracts_agree = all(
        e["readings"]["a_registered_ceiling"]["lenient_verdict"]
        == e["readings"]["a_registered_ceiling"]["strict_verdict"]
        for e in per_type.values()
    )
    failing_a = sorted(
        t for t, e in per_type.items()
        if "FAIL" in (e["readings"]["a_registered_ceiling"]["lenient_verdict"],
                      e["readings"]["a_registered_ceiling"]["strict_verdict"])
    )

    n_all = sum(e["n_members"] for e in per_type.values())
    pooled = sum(
        e["caption_member_accuracy_lenient"] * e["n_members"] for e in per_type.values()
    ) / n_all

    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "registration": "docs/registered_track4_premise_v2_design_v1.md#7-E3",
        "criterion_text": (
            "Pass, per type: caption member accuracy <= blind-floor threshold + 0.10 absolute. "
            "Fail => the track is caption-leaky: eval-only until revised."
        ),
        "discipline": (
            "Per intervention type only (I13); both scoring contracts reported and never "
            "merged (I7); the cell's own pooled metrics.json is not the endpoint."
        ),
        "open_in_the_registration": (
            "'blind-floor threshold' is not disambiguated in section 7 E3. Both readings are "
            "reported; where they disagree the disagreement is the result and the choice is "
            "the PI's."
        ),
        "margin": E3_MARGIN,
        "per_intervention_type": per_type,
        "summary": {
            "contracts_agree_under_reading_a": contracts_agree,
            "failing_types_under_reading_a": failing_a,
            "n_types": len(per_type),
            "registered_consequence": (
                "Fail => the track is caption-leaky: eval-only until revised."
            ),
        },
        "POOLED_ACROSS_TYPES_NOT_AN_ENDPOINT": {
            "note": "I13: mixes intervention types. Emitted for auditability only.",
            "member_accuracy_lenient": pooled,
        },
        "inputs_sha256": {
            str(predictions_path.name): _sha256(predictions_path),
            str(causal_manifest_path.name): _sha256(causal_manifest_path),
        },
    }

    for key, value in report.items():
        if key == "inputs_sha256":
            continue
        _audit(value, f"/{key}")
    return report


def _audit(node: Any, path: str) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if "pooled" in str(key).lower() and "NOT_AN_ENDPOINT" not in str(key):
                raise ReadoutRefusal(f"pooled key without NOT_AN_ENDPOINT label at {path}/{key}")
            _audit(value, f"{path}/{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            _audit(value, f"{path}[{i}]")


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# Track-4 premise-v2 — E3 caption stress, per-type readout", ""]
    lines.append(f"Registration: `{report['registration']}`.")
    lines.append("")
    lines.append("> " + report["criterion_text"])
    lines.append("")
    lines.append(report["open_in_the_registration"])
    lines.append("")
    lines.append(
        "| type | n pairs | caption member acc (lenient) | (strict) | ceiling (a) 0.133+0.10 | "
        "verdict (a) | ceiling (b) measured+0.10 | verdict (b) |"
    )
    lines.append("|---|---:|---:|---:|---:|---|---:|---|")
    for itype in sorted(report["per_intervention_type"]):
        e = report["per_intervention_type"][itype]
        a = e["readings"]["a_registered_ceiling"]
        b = e["readings"].get("b_measured_floor")
        lines.append(
            f"| `{itype}` | {e['n_pairs']} | {e['caption_member_accuracy_lenient']:.4f} | "
            f"{e['caption_member_accuracy_strict']:.4f} | {a['e3_ceiling']:.4f} | "
            f"**{a['lenient_verdict']}** / **{a['strict_verdict']}** | "
            + (f"{b['e3_ceiling']:.4f} | **{b['lenient_verdict']}** / **{b['strict_verdict']}** |"
               if b else "n/a | n/a |")
        )
    lines.append("")
    summary = report["summary"]
    if summary["failing_types_under_reading_a"]:
        lines.append(
            "Failing types under reading (a): "
            + ", ".join(f"`{t}`" for t in summary["failing_types_under_reading_a"])
            + f". Registered consequence: {summary['registered_consequence']}"
        )
    else:
        lines.append(
            "**No type fails under reading (a).** The track is not caption-leaky by the "
            "registered criterion."
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--causal-manifest", type=Path, required=True)
    parser.add_argument(
        "--measured-blind-floors",
        type=Path,
        default=None,
        help="JSON {intervention_type: measured blind final member accuracy} for reading (b)",
    )
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, default=None)
    args = parser.parse_args()

    floors = None
    if args.measured_blind_floors is not None:
        floors = {
            str(k): float(v)
            for k, v in json.loads(args.measured_blind_floors.read_text(encoding="utf-8")).items()
        }

    report = build_report(
        args.predictions, args.causal_manifest, measured_blind_floors=floors
    )

    for out, payload in (
        (args.json_output, json.dumps(report, indent=2, sort_keys=True) + "\n"),
        (args.markdown_output, render_markdown(report) if args.markdown_output else None),
    ):
        if out is None:
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        partial = Path(f"{out}.partial")
        if out.exists() or partial.exists():
            raise FileExistsError(f"refusing to overwrite E3 readout: {out}")
        partial.write_text(payload, encoding="utf-8")
        os.replace(partial, out)
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
