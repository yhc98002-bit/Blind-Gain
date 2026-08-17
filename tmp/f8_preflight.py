#!/usr/bin/env python3
"""Non-evaluative preflight for the Mini-A5 F8 endpoint evaluation.

Reads NO prediction file, NO metric file, instantiates NO model.
Only: checkpoint file inventory + index JSON parse, manifest sha256,
image existence on disk, and free/used image-path counts.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")

CKPTS = {
    "cp": ROOT / "checkpoints/mini_a5/mini_a5_cp_seed1/global_step_120/actor/huggingface",
    "member": ROOT / "checkpoints/mini_a5/mini_a5_same_data_seed1/global_step_120/actor/huggingface",
}

MANIFESTS = {
    "r19_locked": (
        ROOT
        / "experiments/runs/caption_qa_pair_build_fliptrack_v02r19_qwen25vl3b_384_20260710T140200Z/shards/captions_shard_0.jsonl",
        "e1dde98451e1c7473906637c029713ab4f95ab4f7c915bd035f697953bf2ffb2",
    ),
    "r20": (
        ROOT / "data/fliptrack_r20_source_manifest.jsonl",
        "20222e60201b4e116b4520f1aad8bd749bf49185a0a414087c1a8fe22dbf2ef3",
    ),
    "chart_v08": (
        ROOT / "data/fliptrack_chart_v08_calibration_v1_manifest.jsonl",
        "d90f3f13c1f3304669c8ca6c717ae58eaa7cfe4e785fab3bae8520e15065c292",
    ),
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_ckpt(name: str, path: Path) -> dict:
    out: dict = {"arm": name, "path": str(path), "exists": path.is_dir()}
    if not out["exists"]:
        return out
    files = sorted(x.name for x in path.iterdir() if x.is_file())
    out["files"] = files
    idx = path / "model.safetensors.index.json"
    out["index_present"] = idx.is_file()
    if out["index_present"]:
        try:
            data = json.loads(idx.read_text(encoding="utf-8"))
            out["index_parses"] = True
            wm = data.get("weight_map", {})
            out["index_tensor_count"] = len(wm)
            out["index_total_size_bytes"] = data.get("metadata", {}).get("total_size")
            shards = sorted(set(wm.values()))
            out["index_shards"] = shards
            missing = [s for s in shards if not (path / s).is_file()]
            out["missing_shard_files"] = missing
            out["shard_bytes_on_disk"] = sum(
                (path / s).stat().st_size for s in shards if (path / s).is_file()
            )
        except Exception as exc:  # noqa: BLE001
            out["index_parses"] = False
            out["index_error"] = repr(exc)
    for req in (
        "config.json",
        "generation_config.json",
        "preprocessor_config.json",
        "tokenizer_config.json",
    ):
        out[f"has_{req}"] = (path / req).is_file()
    cfg = path / "config.json"
    if cfg.is_file():
        try:
            c = json.loads(cfg.read_text(encoding="utf-8"))
            out["architectures"] = c.get("architectures")
            out["model_type"] = c.get("model_type")
        except Exception as exc:  # noqa: BLE001
            out["config_error"] = repr(exc)
    if out.get("index_present"):
        out["index_sha256"] = sha256_file(idx)
    return out


def check_manifest(name: str, path: Path, expected: str) -> dict:
    out: dict = {"set": name, "path": str(path), "exists": path.is_file()}
    if not out["exists"]:
        return out
    got = sha256_file(path)
    out["sha256"] = got
    out["sha256_expected"] = expected
    out["sha256_match"] = got == expected
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    out["rows"] = len(rows)
    out["unique_pair_ids"] = len({r["pair_id"] for r in rows})
    tmpl: dict = {}
    for r in rows:
        tmpl[r.get("template_id")] = tmpl.get(r.get("template_id"), 0) + 1
    out["template_counts"] = tmpl
    required = ("pair_id", "question", "image_a_path", "image_b_path", "answer_a", "answer_b")
    out["schema_ok"] = all(all(k in r for k in required) for r in rows)
    missing_imgs = []
    n_imgs = 0
    for r in rows:
        for key in ("image_a_path", "image_b_path"):
            p = Path(r[key])
            if not p.is_absolute():
                p = ROOT / p
            n_imgs += 1
            if not p.is_file():
                missing_imgs.append(str(p))
    out["image_refs"] = n_imgs
    out["missing_images"] = len(missing_imgs)
    out["missing_images_sample"] = missing_imgs[:5]
    return out


def main() -> None:
    result = {
        "checkpoints": [check_ckpt(k, v) for k, v in CKPTS.items()],
        "manifests": [check_manifest(k, p, s) for k, (p, s) in MANIFESTS.items()],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
