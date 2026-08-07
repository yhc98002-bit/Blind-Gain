#!/usr/bin/env python3
"""Single-arm catch-trial invariance (stability) levels for Gate-1 arms.

WHY THIS IS A SEPARATE FILE. The registered catch-stability instrument
``src/eval/catch_stability.py`` is pinned by sha256 in
docs/registered_mini_a5_catch_stability_v1.md (section 3 pins the scorer,
section 5 pins its test file) and is structurally two-arm: ``--cp-scores`` and
``--member-scores`` are both required, the output schema hard-codes
``arms.cp`` / ``arms.member`` / ``cp_vs_member``, and the registration
anticipates no additional arm. Editing that file would break the registered
pins and the byte-stability of the published cp/member outputs
(reports/mini_a5_catch_stability_readout_v1.*). Per
scripts/gate1_endpoint_evals_todo.md: "do not shoehorn a new arm into a
mislabeled cp/member slot" — hence this wrapper.

WHAT IT COMPUTES. Per-arm, per-template LEVELS of the six registered catch
indicators, by importing the arm-agnostic core of the registered scorer
unchanged (``catch_pair_score`` via ``score_rows``, ``aggregate_by_template``,
``INDICATORS``). Both severities are reported and never merged (I7); the
aggregation is per template only, with no pooled slot anywhere in the schema
(I13). The output carries its OWN schema_version (I15) — never the registered
two-arm id, because the shapes differ.

WHAT IT REFUSES (fail-closed):
  - arm labels ``cp`` / ``member`` (reserved for the registered two-arm
    instrument; a new arm can never be scored under those labels, and the
    registered arms are never re-scored here) and any label outside the
    Gate-1 roster (``std``, ``necessity``);
  - a run dir whose run_manifest.json is missing, unreadable, has
    status != "complete", lacks a model_path containing the arm's registered
    checkpoint token, or lacks a data_manifest_hash (incomplete manifest);
  - a run whose recorded data_manifest_hash does not equal the sha256 of the
    catch manifest supplied on the command line;
  - a scored item set that does not exactly match the catch manifest's
    pair_group_uid set, or whose template_id disagrees with the manifest for
    any pair;
  - missing/empty shard files; duplicate pair_group_uid; non-equal-gold rows
    (inherited from the registered core);
  - a non 3x100 template shape unless ``--expect any`` (fixtures only);
  - overwriting an existing output.

WHAT IT DOES NOT COMPUTE. No cross-arm contrast, no bootstrap, no McNemar,
no seeds: the registered cp-vs-member contrast lives solely in
``src/eval/catch_stability.py``, and any contrast involving a Gate-1 arm
would need its own registered instrument and seed derivation first.

Entry points (from the repo root):

    PYTHONPATH=. .venv/bin/python -m src.eval.catch_stability_single_arm \
      --arm-label std \
      --run-dir experiments/runs/mini_a5_catch_std_step120_real_an29_<TS> \
      --output reports/mini_a5_catch_stability_levels_std_v1.json \
      --per-row-output experiments/runs/mini_a5_catch_std_step120_real_an29_<TS>/catch_stability_rows_std.jsonl

and identically with ``--arm-label necessity`` over the necessity run dir.

Adversarial fixtures: tests/test_catch_stability_single_arm.py (a NEW file;
the registered test file is sha-pinned and is not modified).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.eval.catch_stability import (
    INDICATORS,
    SCHEMA_VERSION as TWO_ARM_SCHEMA_VERSION,
    CatchScoreError,
    _read_jsonl_paths,
    _require_registered_shape,
    aggregate_by_template,
    score_rows,
)
from src.eval.prompt_contract import prompt_contract_metadata
from src.rewards.answer_reward import PARSER_VERSION

SCHEMA_VERSION = "blind-gains.mini-a5-catch-stability-single-arm.v1"

# Gate-1 completion arms this wrapper may score. cp/member are RESERVED for
# the registered two-arm instrument and are refused here by name.
ARM_CHECKPOINT_TOKENS = {
    "std": "mini_a5_std_seed1",
    "necessity": "mini_a5_necessity_seed1",
}
ARM_NUMBERS = {"std": 1, "necessity": 3}
RESERVED_TWO_ARM_LABELS = ("cp", "member")

DEFAULT_CATCH_MANIFEST = "data/derived/mini_a5_catch_eval_manifest_v1.jsonl"


class SingleArmRefusal(RuntimeError):
    """Raised whenever this wrapper refuses to produce a readout."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require_allowed_arm_label(arm_label: str) -> str:
    if arm_label in RESERVED_TWO_ARM_LABELS:
        raise SingleArmRefusal(
            f"arm label {arm_label!r} is reserved for the registered two-arm "
            "instrument src/eval/catch_stability.py "
            "(docs/registered_mini_a5_catch_stability_v1.md); this wrapper "
            f"scores only the Gate-1 arms {sorted(ARM_CHECKPOINT_TOKENS)} and "
            "never re-scores or relabels the registered arms (fail-closed)"
        )
    if arm_label not in ARM_CHECKPOINT_TOKENS:
        raise SingleArmRefusal(
            f"unknown arm label {arm_label!r}; allowed: "
            f"{sorted(ARM_CHECKPOINT_TOKENS)} (fail-closed)"
        )
    return arm_label


def load_catch_manifest(path: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Return ({pair_group_uid: template_id}, provenance) for the catch manifest."""
    path = Path(path)
    try:
        rows, provenance = _read_jsonl_paths([str(path)])
    except OSError as exc:
        raise SingleArmRefusal(
            f"missing or unreadable catch manifest: {path}: {exc} (fail-closed)"
        ) from exc
    if not rows:
        raise SingleArmRefusal(f"catch manifest has no rows: {path} (fail-closed)")
    uid_to_template: dict[str, str] = {}
    for row in rows:
        uid = row.get("pair_group_uid")
        template = row.get("template_id")
        if not isinstance(uid, str) or not uid:
            raise SingleArmRefusal(
                f"catch manifest row lacks a nonempty pair_group_uid: {path} (fail-closed)"
            )
        if not isinstance(template, str) or not template:
            raise SingleArmRefusal(
                f"catch manifest row {uid!r} lacks a nonempty template_id: {path} (fail-closed)"
            )
        if uid in uid_to_template:
            raise SingleArmRefusal(
                f"duplicate pair_group_uid {uid!r} in catch manifest: {path} (fail-closed)"
            )
        uid_to_template[uid] = template
    return uid_to_template, provenance[0]


def load_arm_run(arm_label: str, run_dir: Path, catch_manifest_sha256: str) -> dict[str, Any]:
    """Load and validate one arm's catch-cell run dir (fail-closed)."""
    run_dir = Path(run_dir)
    manifest_path = run_dir / "run_manifest.json"
    if not manifest_path.is_file():
        raise SingleArmRefusal(
            f"missing run manifest for arm '{arm_label}': {manifest_path} (fail-closed)"
        )
    manifest_bytes = manifest_path.read_bytes()
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SingleArmRefusal(
            f"unreadable run manifest for arm '{arm_label}': {manifest_path}: {exc}"
        ) from exc
    status = manifest.get("status")
    if status != "complete":
        raise SingleArmRefusal(
            f"run manifest for arm '{arm_label}' has status {status!r}, not "
            "'complete' -- partial readouts are prohibited, fail-closed"
        )
    token = ARM_CHECKPOINT_TOKENS[arm_label]
    model_path = str(manifest.get("model_path") or "")
    if token not in model_path:
        raise SingleArmRefusal(
            f"arm label mismatch for arm '{arm_label}': registered checkpoint "
            f"token '{token}' not found in run_manifest model_path "
            f"{model_path!r} (fail-closed)"
        )
    recorded_hash = manifest.get("data_manifest_hash")
    if not isinstance(recorded_hash, str) or not recorded_hash:
        raise SingleArmRefusal(
            f"run manifest for arm '{arm_label}' lacks a data_manifest_hash; "
            "incomplete run manifests are refused (fail-closed)"
        )
    if recorded_hash != catch_manifest_sha256:
        raise SingleArmRefusal(
            f"catch-manifest mismatch for arm '{arm_label}': run_manifest "
            f"data_manifest_hash {recorded_hash} != sha256 "
            f"{catch_manifest_sha256} of the supplied catch manifest (fail-closed)"
        )
    shard_paths = sorted((run_dir / "shards").glob("shard_*.jsonl"))
    if not shard_paths:
        raise SingleArmRefusal(
            f"no shard files for arm '{arm_label}' under "
            f"{run_dir / 'shards'} (fail-closed)"
        )
    rows, scores_provenance = _read_jsonl_paths([str(p) for p in shard_paths])
    if not rows:
        raise SingleArmRefusal(
            f"shard files for arm '{arm_label}' contain no rows (fail-closed)"
        )
    return {
        "run_dir": run_dir,
        "manifest": manifest,
        "manifest_provenance": {
            "path": str(manifest_path),
            "sha256": _sha256_bytes(manifest_bytes),
        },
        "rows": rows,
        "scores_provenance": scores_provenance,
    }


def check_item_set(
    arm_label: str,
    scored: list[dict[str, Any]],
    manifest_uid_to_template: dict[str, str],
) -> None:
    scored_map = {row["pair_group_uid"]: row["template_id"] for row in scored}
    if set(scored_map) != set(manifest_uid_to_template):
        only_manifest = sorted(set(manifest_uid_to_template) - set(scored_map))[:5]
        only_scores = sorted(set(scored_map) - set(manifest_uid_to_template))[:5]
        raise SingleArmRefusal(
            f"item-set mismatch for arm '{arm_label}' vs the catch manifest: "
            f"manifest has {len(manifest_uid_to_template)} pairs, scores have "
            f"{len(scored_map)}; manifest-only sample={only_manifest} "
            f"scores-only sample={only_scores} (fail-closed)"
        )
    for uid in sorted(scored_map):
        if scored_map[uid] != manifest_uid_to_template[uid]:
            raise SingleArmRefusal(
                f"template_id mismatch for pair_group_uid {uid!r} (arm "
                f"'{arm_label}'): scores say {scored_map[uid]!r}, catch "
                f"manifest says {manifest_uid_to_template[uid]!r} (fail-closed)"
            )


def build_single_arm_readout(
    arm_label: str,
    run_dir: Path,
    catch_manifest: Path,
    expect: str = "registered",
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Build the single-arm levels readout. Returns (readout, scored_rows)."""
    require_allowed_arm_label(arm_label)
    manifest_map, catch_manifest_provenance = load_catch_manifest(catch_manifest)
    arm = load_arm_run(arm_label, run_dir, catch_manifest_provenance["sha256"])
    scored = score_rows(arm["rows"])
    check_item_set(arm_label, scored, manifest_map)
    if expect == "registered":
        _require_registered_shape(scored, arm_label)
    # coverage counts, not metrics: no indicator value is ever pooled (I13)
    template_pair_counts: dict[str, int] = {}
    for row in scored:
        template_pair_counts[row["template_id"]] = (
            template_pair_counts.get(row["template_id"], 0) + 1
        )
    readout = {
        "schema_version": SCHEMA_VERSION,
        "endpoint": (
            "Mini-A5 secondary 2 (addendum section 6.2): catch-trial stability — "
            "self-consistency under a non-queried visual change; single-arm "
            "LEVELS readout for a Gate-1 completion arm"
        ),
        "aggregation_rule": "per catch template id only; never pooled across templates (I13)",
        "severity_rule": "every indicator reported lenient and contract-strict (I7)",
        "contrast_note": (
            "levels only: this instrument computes no cross-arm contrast, "
            "bootstrap, McNemar, or seed; the registered cp-vs-member contrast "
            "lives solely in src/eval/catch_stability.py, and any contrast "
            "involving this arm needs its own registered instrument and seeds"
        ),
        "registered_two_arm_instrument": {
            "path": "src/eval/catch_stability.py",
            "schema_version": TWO_ARM_SCHEMA_VERSION,
            "registration": "docs/registered_mini_a5_catch_stability_v1.md",
        },
        "indicator_indices": {
            indicator: index for index, (indicator, _, _) in enumerate(INDICATORS)
        },
        "parser_version": PARSER_VERSION,
        **prompt_contract_metadata(None),
        "arm": {
            "label": arm_label,
            "arm_number": ARM_NUMBERS[arm_label],
            "checkpoint_token": ARM_CHECKPOINT_TOKENS[arm_label],
            "run_dir": str(run_dir),
            "run_id": arm["manifest"].get("run_id"),
            "model_path": arm["manifest"].get("model_path"),
            "run_manifest_status": "complete",
        },
        "inputs": {
            "scores": arm["scores_provenance"],
            "run_manifest": arm["manifest_provenance"],
            "catch_manifest": catch_manifest_provenance,
        },
        "checks": {
            "arm_label_allowed": True,
            "arm_token_in_model_path": True,
            "run_manifest_status_complete": True,
            "run_manifest_data_manifest_hash_matches_catch_manifest": True,
            "item_set_matches_catch_manifest": True,
            "template_ids_match_catch_manifest": True,
            "n_pairs_scored": len(scored),
            "template_pair_counts": template_pair_counts,
            "expectation_mode": expect,
        },
        "levels": aggregate_by_template(scored),
        "automatic_branch_assignment": False,
    }
    return readout, scored


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--arm-label",
        required=True,
        help="Gate-1 arm to score: 'std' or 'necessity' (cp/member are refused)",
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="catch-cell run dir (must contain run_manifest.json and shards/shard_*.jsonl)",
    )
    parser.add_argument(
        "--catch-manifest",
        type=Path,
        default=Path(DEFAULT_CATCH_MANIFEST),
        help="catch eval manifest the run must match (default: registered manifest, from repo root)",
    )
    parser.add_argument("--output", type=Path, required=True, help="readout JSON path")
    parser.add_argument(
        "--per-row-output", type=Path, default=None, help="optional per-row scored jsonl"
    )
    parser.add_argument(
        "--expect", choices=("registered", "any"), default="registered",
        help="registered: require 3 templates x 100 pairs (default); any is for fixtures only",
    )
    args = parser.parse_args(argv)

    partial = Path(f"{args.output}.partial")
    if args.output.exists() or partial.exists():
        raise SingleArmRefusal(
            f"refusing to overwrite existing readout: {args.output} (fail-closed)"
        )
    if args.per_row_output is not None and args.per_row_output.exists():
        raise SingleArmRefusal(
            f"refusing to overwrite existing per-row output: {args.per_row_output} (fail-closed)"
        )
    readout, scored = build_single_arm_readout(
        args.arm_label, args.run_dir, args.catch_manifest, expect=args.expect
    )
    if args.per_row_output is not None:
        args.per_row_output.parent.mkdir(parents=True, exist_ok=True)
        with args.per_row_output.open("w", encoding="utf-8") as handle:
            for row in scored:
                handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    partial.write_text(
        json.dumps(readout, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(partial, args.output)
    for template, block in readout["levels"]["per_template"].items():
        summary = "  ".join(
            f"{indicator}={block[indicator]['count']}/{block['n_pairs']}"
            for indicator, _, _ in INDICATORS
        )
        print(f"{args.arm_label:<10} {template}  {summary}")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
