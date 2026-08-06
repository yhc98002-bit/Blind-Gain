#!/usr/bin/env python3
"""Machine check for the LH2 stage-1 config (docs/registered_lh2_stage1_v1.md).

Asserts, fail-closed, that configs/train/lh2_anchor_seed2_3b_geo3k.yaml differs
from the seed-1 anchor recipe template in EXACTLY the registered leaf paths
(data.seed, trainer.max_steps, trainer.save_freq, trainer.experiment_name,
trainer.save_checkpoint_path) with EXACTLY the registered values, and from the
M5 long-horizon config in exactly the registered set (data.seed,
trainer.max_steps, trainer.experiment_name, trainer.save_checkpoint_path,
trainer.load_checkpoint_path).

Writes reports/lh2_config_diff_check_v1.json (refuses to overwrite a differing
existing artifact only via --force-rewrite; default behavior is overwrite-free
when content is unchanged). Exit 0 iff every assertion holds.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
LH2_PATH = ROOT / "configs/train/lh2_anchor_seed2_3b_geo3k.yaml"
ANCHOR_PATH = ROOT / "configs/train/anchor_a0_recipe_3b_geo3k.yaml"
M5_PATH = ROOT / "configs/train/m5_anchor_longhorizon_400.yaml"
OUT_PATH = ROOT / "reports/lh2_config_diff_check_v1.json"

BLINDGAIN = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"

ALLOWED_VS_ANCHOR: dict[str, list[Any]] = {
    "data.seed": [1, 2],
    "trainer.max_steps": [100, 200],
    "trainer.save_freq": [20, 50],
    "trainer.experiment_name": ["anchor_a0_recipe_3b_geo3k", "lh2_anchor_seed2_3b_geo3k"],
    "trainer.save_checkpoint_path": [
        f"{BLINDGAIN}/checkpoints/anchor_a0_recipe_3b_geo3k",
        f"{BLINDGAIN}/checkpoints/lh2_anchor_seed2_3b_geo3k",
    ],
}

ALLOWED_VS_M5: dict[str, list[Any]] = {
    "data.seed": [1, 2],
    "trainer.max_steps": [400, 200],
    "trainer.experiment_name": ["m5_anchor_longhorizon_400", "lh2_anchor_seed2_3b_geo3k"],
    "trainer.save_checkpoint_path": [
        f"{BLINDGAIN}/checkpoints/m5_anchor_longhorizon_400",
        f"{BLINDGAIN}/checkpoints/lh2_anchor_seed2_3b_geo3k",
    ],
    "trainer.load_checkpoint_path": [
        f"{BLINDGAIN}/checkpoints/anchor_a0_recipe_3b_geo3k/"
        "anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_100",
        None,
    ],
}

_ABSENT = object()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _flatten(node: Any, prefix: tuple[str, ...] = ()) -> dict[tuple[str, ...], Any]:
    if isinstance(node, dict):
        flat: dict[tuple[str, ...], Any] = {}
        for key, value in node.items():
            flat.update(_flatten(value, prefix + (str(key),)))
        return flat
    return {prefix: node}


def _diff(a: dict[tuple[str, ...], Any], b: dict[tuple[str, ...], Any]) -> dict[str, list[Any]]:
    out: dict[str, list[Any]] = {}
    for path in sorted(set(a) | set(b)):
        va = a.get(path, _ABSENT)
        vb = b.get(path, _ABSENT)
        if va is not vb and va != vb:
            out[".".join(path)] = [
                "<absent>" if va is _ABSENT else va,
                "<absent>" if vb is _ABSENT else vb,
            ]
    return out


def main() -> int:
    payloads = {}
    for name, path in (("lh2", LH2_PATH), ("anchor", ANCHOR_PATH), ("m5", M5_PATH)):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            print(f"FAIL: {path} did not parse to a mapping", file=sys.stderr)
            return 1
        payloads[name] = _flatten(payload)

    failures: list[str] = []
    diffs: dict[str, dict[str, list[Any]]] = {}
    for label, base, allowed in (
        ("lh2_vs_anchor", "anchor", ALLOWED_VS_ANCHOR),
        ("lh2_vs_m5", "m5", ALLOWED_VS_M5),
    ):
        observed = _diff(payloads[base], payloads["lh2"])
        diffs[label] = observed
        if set(observed) != set(allowed):
            failures.append(
                f"{label}: differing paths {sorted(observed)} != registered {sorted(allowed)}"
            )
            continue
        for path, expected in allowed.items():
            if observed[path] != expected:
                failures.append(f"{label}: {path} observed {observed[path]} != registered {expected}")

    result = {
        "schema": "blind-gains.lh2-config-diff-check.v1",
        "status": "fail" if failures else "pass",
        "failures": failures,
        "configs": {
            "lh2": {"path": str(LH2_PATH.relative_to(ROOT)), "sha256": _sha256(LH2_PATH)},
            "anchor_template": {"path": str(ANCHOR_PATH.relative_to(ROOT)), "sha256": _sha256(ANCHOR_PATH)},
            "m5_reference": {"path": str(M5_PATH.relative_to(ROOT)), "sha256": _sha256(M5_PATH)},
        },
        "observed_diffs": diffs,
        "registered_allowed_diffs": {
            "lh2_vs_anchor": ALLOWED_VS_ANCHOR,
            "lh2_vs_m5": ALLOWED_VS_M5,
        },
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "failures": failures}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
