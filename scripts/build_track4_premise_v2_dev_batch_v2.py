#!/usr/bin/env python3
"""Track-4 premise-construct v2 — dev batch v2 (one-shot regeneration,
dispatch 2026-08-16 item 4; registered in docs/registered_hier_benchmark_v1.md
§8 and docs/registered_track4_premise_v2_design_v1.md §5 branch (c)).

Regenerates the five E2-failing intervention types in ONE one-shot batch under
two registered changes, and nothing else:

1. **Answer-balance constraint** (registered_hier_benchmark_v1.md §8): per
   intervention type, over all causal-pair member golds (both sides pooled),
   no final-answer value exceeds a 0.10 share. Enforced by deterministic
   constrained resampling: a candidate group is accepted only if both its
   member golds stay under the per-value ceiling floor(0.10 * 2N); rejected
   attempts advance the attempt counter exactly like v1's geometric
   rejections. The blind constant-answer attacker is thereby bounded at 0.10
   member accuracy, 25% under E2's registered 0.133 ceiling.
2. **Branch (c), executed**: the easy variant steps to n_points = 5 — "the
   minimum at which the premise remains a genuine 4-distractor search" —
   for `chained_premise_easy` (primary carrier) and `premise_transition_easy`
   (secondary). The n=20 types keep n=20.

Everything else is v1's frozen machinery, imported and reused: geometry
builders, renderer, invariance construction, schema-v2 group assembly, split
enforcement (development bucket only), attacker-release packaging, frozen-B1
disjointness. The v1 batch and builder are untouched; this driver overrides
the v1 module's declared knobs IN MEMORY only, and records every override in
the build report.

One-shot declared batch: 160 groups, no acceptance iteration. CPU only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import socket
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image

import scripts.build_track4_premise_v2_dev_batch as v1
from src.train.intervention_group_schema import validate_batch_v2

ROOT = v1.ROOT
BATCH_SEED_V2 = 20260816
BALANCE_CAP = 0.10  # registered_hier_benchmark_v1.md §8

N_POINTS_V2 = {
    "premise_transition": 20,
    "premise_transition_easy": 5,   # branch (c)
    "chained_premise_easy": 5,      # branch (c), primary carrier
    "chained_premise": 20,
    "fact_read": 20,
}
TEMPLATES_V2 = {
    20: "t4v2_coordinate_register_n20_v1",
    5: "t4v2_coordinate_register_n5_v1",
}
COUNTS_V2 = dict(v1.COUNTS)  # unchanged: 40/40/40/20/20


def apply_v1_overrides() -> dict[str, Any]:
    """Point the v1 module's declared knobs at the v2 values (in memory only).

    The v1 builder reads BATCH_SEED / N_POINTS / TEMPLATES as module globals;
    overriding them here reuses its frozen geometry and rendering code paths
    byte-for-byte while the v1 script on disk stays untouched.
    """
    overrides = {
        "BATCH_SEED": (v1.BATCH_SEED, BATCH_SEED_V2),
        "N_POINTS": (dict(v1.N_POINTS), dict(N_POINTS_V2)),
        "TEMPLATES": (dict(v1.TEMPLATES), dict(TEMPLATES_V2)),
    }
    v1.BATCH_SEED = BATCH_SEED_V2
    v1.N_POINTS = dict(N_POINTS_V2)
    v1.TEMPLATES = dict(TEMPLATES_V2)
    return {name: {"v1": old, "v2": new} for name, (old, new) in overrides.items()}


def member_gold_counts(rows: list[dict[str, Any]]) -> dict[str, Counter]:
    """Pooled member-gold distribution per intervention type (both sides)."""
    counts: dict[str, Counter] = {}
    for row in rows:
        c = counts.setdefault(row["intervention_type"], Counter())
        c[str(row["answer_a"])] += 1
        c[str(row["answer_b"])] += 1
    return counts


def balance_report(rows: list[dict[str, Any]], cap: float = BALANCE_CAP) -> dict[str, Any]:
    """Registered balance check: per type, max pooled member-gold share <= cap.

    This is the verifier surface the I10 fixture exercises: a skewed batch
    fails it, the pre-constraint v1 batch fails it, a v2 batch passes it.
    """
    report: dict[str, Any] = {}
    for itype, counter in member_gold_counts(rows).items():
        total = sum(counter.values())
        top_value, top_count = counter.most_common(1)[0]
        share = top_count / total
        report[itype] = {
            "n_member_golds": total,
            "answer_support_k": len(counter),
            "max_share_value": top_value,
            "max_share": share,
            "cap": cap,
            "pass": share <= cap,
        }
    report["all_pass"] = all(v["pass"] for k, v in report.items() if k != "all_pass")
    return report


def build_batch_balanced(out_dir: Path) -> dict[str, Any]:
    """v1.build_batch with the balance predicate applied at geometry-accept
    time (before any image is rendered or written)."""
    groups: list[dict[str, Any]] = []
    causal_rows: list[dict[str, Any]] = []
    inv_rows: list[dict[str, Any]] = []
    attempts_by_type: dict[str, int] = {}
    balance_rejections: dict[str, int] = {}
    built_index = 0
    for intervention, count in COUNTS_V2.items():
        ceiling = int(BALANCE_CAP * 2 * count)  # floor(0.10 * 2N) per gold value
        gold_counts: Counter = Counter()
        built = 0
        attempt = 0
        cap_attempts = count * 3000
        while built < count:
            attempt += 1
            if attempt > cap_attempts:
                raise RuntimeError(
                    f"{intervention}: exhausted {cap_attempts} attempts at item {built} "
                    f"(balance rejections: {balance_rejections.get(intervention, 0)})"
                )
            rng = random.Random(v1.attempt_seed(intervention, attempt))
            geometry = v1.build_group_geometry(intervention, rng)
            if geometry is None:
                continue
            gold_a, gold_b = str(geometry["gold_a"]), str(geometry["gold_b"])
            projected = gold_counts.copy()
            projected[gold_a] += 1
            projected[gold_b] += 1
            if max(projected.values()) > ceiling:
                balance_rejections[intervention] = balance_rejections.get(intervention, 0) + 1
                continue
            invariance = v1.build_invariance_geometry(geometry, rng, prefer_style_twin=built_index % 2 == 0)
            result = v1.materialize_group(out_dir=out_dir, geometry=geometry,
                                          invariance=invariance, rng=rng)
            for row in (result["causal_row"], result["invariance_row"]):
                row["provenance"]["generator"] = "scripts.build_track4_premise_v2_dev_batch_v2"
            gold_counts = projected
            groups.append(result["group"])
            causal_rows.append(result["causal_row"])
            inv_rows.append(result["invariance_row"])
            built += 1
            built_index += 1
        attempts_by_type[intervention] = attempt

    gray_path = out_dir / "gray_1400x1240.png"
    Image.new("RGB", (1400, 1240), (127, 127, 127)).save(gray_path, format="PNG",
                                                         optimize=False, compress_level=9)
    gray_sha = hashlib.sha256(gray_path.read_bytes()).hexdigest()

    by_type: dict[str, list[dict[str, Any]]] = {}
    for g in groups:
        by_type.setdefault(g["intervention_type"], []).append(g)
    for itype, gs in by_type.items():
        for i, g in enumerate(gs):
            donor = gs[(i + 1) % len(gs)]
            for m in g["members"]:
                if m.get("condition") == "mismatched_real":
                    m["image_path"] = donor["original"]["image_path"]
                    m["image_sha256"] = donor["original"]["image_sha256"]
                    m["mismatched_source_group"] = donor["group_uid"]
                if m.get("condition") == "gray":
                    m["image_path"] = str(gray_path)
                    m["image_sha256"] = gray_sha

    validate_batch_v2(groups, require_measured=False)

    return {
        "groups": groups,
        "causal_rows": causal_rows,
        "invariance_rows": inv_rows,
        "attempts_by_type": attempts_by_type,
        "balance_rejections": balance_rejections,
        "gray_sha256": gray_sha,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=ROOT / "data/track4_premise_v2_dev_v2")
    parser.add_argument("--report", type=Path,
                        default=ROOT / "reports/track4_premise_v2_dev_v2_build_v1.json")
    args = parser.parse_args()
    manifest_path = args.out_dir / "manifest_causal_pairs.jsonl"
    if manifest_path.exists() or args.report.exists():
        raise FileExistsError("refusing to overwrite the declared Track-4 dev_v2 batch")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    overrides = apply_v1_overrides()

    result = build_batch_balanced(args.out_dir)
    groups, causal_rows, inv_rows = result["groups"], result["causal_rows"], result["invariance_rows"]
    n_expected = sum(COUNTS_V2.values())
    if not (len(groups) == len(causal_rows) == len(inv_rows) == n_expected):
        raise AssertionError(f"declared batch size mismatch: {len(groups)}")

    balance = balance_report(causal_rows)
    if not balance["all_pass"]:
        raise AssertionError(f"registered balance constraint violated: {balance}")

    probe_rows = [v1.premise_probe_row(r) for r in causal_rows if r["premise_question"]]
    n_probe_expected = sum(c for t, c in COUNTS_V2.items() if t != "fact_read")
    if len(probe_rows) != n_probe_expected:
        raise AssertionError(f"premise probe rows: {len(probe_rows)} != {n_probe_expected}")

    hashes = {
        "manifest_causal_pairs.jsonl": v1.write_jsonl(manifest_path, causal_rows),
        "manifest_invariance_pairs.jsonl": v1.write_jsonl(
            args.out_dir / "manifest_invariance_pairs.jsonl", inv_rows),
        "manifest_premise_probe.jsonl": v1.write_jsonl(
            args.out_dir / "manifest_premise_probe.jsonl", probe_rows),
        "groups_v2.jsonl": v1.write_jsonl(args.out_dir / "groups_v2.jsonl", groups),
    }

    release_dir = args.out_dir / "attacker_release"
    release_dir.mkdir(exist_ok=True)
    release_rows, key_rows = [], []
    for row in causal_rows:
        swapped = bool(row["provenance"]["semantic_side_assignment_swapped"])
        members, key_members = [], []
        for side in ("a", "b"):
            member_id = f"{row['pair_id']}_{side}"
            rel = Path(row[f"image_{side}_path"]).relative_to(args.out_dir)
            members.append({"member_id": member_id, "image_path": f"../{rel}"})
            semantic = {"a": "b", "b": "a"}[side] if swapped else side
            key_members.append({"member_id": member_id, "source_side": semantic})
        release_rows.append({"pair_id": row["pair_id"], "members": members})
        key_rows.append({"pair_id": row["pair_id"], "template_id": row["template_id"],
                         "members": key_members})
    hashes["attacker_release/manifest.jsonl"] = v1.write_jsonl(release_dir / "manifest.jsonl", release_rows)
    hashes["attacker_key.jsonl"] = v1.write_jsonl(args.out_dir / "attacker_key.jsonl", key_rows)

    # disjointness: frozen B1 images AND every v1 scene program
    b1_manifest = ROOT / "data/b1_geometry_track_v1/manifest.jsonl"
    b1_shas: set[str] = set()
    if b1_manifest.exists():
        for line in b1_manifest.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                b1_shas.update({r.get("image_a_sha256"), r.get("image_b_sha256")})
    new_shas = {r[k] for r in causal_rows + inv_rows for k in ("image_a_sha256", "image_b_sha256")}
    b1_collisions = sorted(new_shas & b1_shas)

    v1_manifest = ROOT / "data/track4_premise_v2_dev_v1/manifest_causal_pairs.jsonl"
    v1_spids: set[str] = set()
    if v1_manifest.exists():
        for line in v1_manifest.read_text().splitlines():
            if line.strip():
                v1_spids.add(json.loads(line)["scene_program_id"])
    spid_collisions = sorted({r["scene_program_id"] for r in causal_rows} & v1_spids)

    per_type = {t: {"groups": c, "n_points": N_POINTS_V2[t], "template_id": TEMPLATES_V2[N_POINTS_V2[t]]}
                for t, c in COUNTS_V2.items()}
    git_hash = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True).stdout.strip()
    report = {
        "schema_version": "blind-gains.track4-premise-v2-dev-build.v2",
        "registrations": [
            "docs/registered_hier_benchmark_v1.md (§8 balance constraint)",
            "docs/registered_track4_premise_v2_design_v1.md (§5 branch (c) n=5)",
        ],
        "batch_seed": BATCH_SEED_V2,
        "v1_knob_overrides": overrides,
        "balance_constraint": {"cap": BALANCE_CAP, "scope": "pooled causal member golds per type"},
        "balance_report": balance,
        "balance_rejections": result["balance_rejections"],
        "declared_groups": len(groups),
        "per_intervention": per_type,
        "premise_probe_rows": len(probe_rows),
        "attempts_by_type": result["attempts_by_type"],
        "split_rule": "unchanged from v1 (development bucket only, enforced)",
        "b1_image_sha_collisions": b1_collisions,
        "v1_scene_program_collisions": spid_collisions,
        "gray_control_sha256": result["gray_sha256"],
        "file_sha256": hashes,
        "out_dir": str(args.out_dir.relative_to(ROOT)),
        "node": socket.gethostname(),
        "git_hash": git_hash,
        "command": " ".join(sys.argv),
        "one_shot": "declared regeneration batch; no acceptance iteration",
    }
    if b1_collisions:
        raise AssertionError(f"frozen-B1 image collision: {b1_collisions[:4]}")
    if spid_collisions:
        raise AssertionError(f"v1 scene-program collision: {spid_collisions[:4]}")
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in
                      ("declared_groups", "balance_report", "balance_rejections",
                       "attempts_by_type", "file_sha256")}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
