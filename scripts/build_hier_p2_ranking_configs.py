#!/usr/bin/env python3
"""Emit the HB P2.1 candidate-ranking configs — one per hier_v1 registry
(7 cells × l3/l2 = 14), each carrying the four P2.1 models. Every pin is
computed from disk at emission time; the processor / prompt-contract /
scoring blocks are copied verbatim from the registered Mini-A5 ranking
config so the ranking instrument's semantics are unchanged. The 3B
processor block serves all four models: every processor artifact
(tokenizer.json, vocab.json, merges.txt, tokenizer_config.json,
preprocessor_config.json) is byte-identical between the 3B and 7B
checkpoints (verified 2026-08-16, shas recorded per config).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "configs/eval/mini_a5_visual_evidence_ranking_v1.json"
BUILD_REPORT = ROOT / "reports/hier_v1_dev_build_v1.json"

MODELS = {
    "base3b": ("artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct", 0),
    "base7b": ("artifacts/models/Qwen/Qwen2.5-VL-7B-Instruct", 0),
    "mini_a5_std_step120": (
        "checkpoints/mini_a5/mini_a5_std_seed1/global_step_120/actor/huggingface", 120),
    "mini_a5_cp_step120": (
        "checkpoints/mini_a5/mini_a5_cp_seed1/global_step_120/actor/huggingface", 120),
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    build = json.loads(BUILD_REPORT.read_text(encoding="utf-8"))
    models = {
        key: {
            "path": path,
            "global_step": step,
            "model_index_sha256": sha256_file(
                ROOT / path / "model.safetensors.index.json"),
        }
        for key, (path, step) in MODELS.items()
    }
    emitted = []
    for cell_key, cell in sorted(build["cells"].items()):
        family, cell_name = cell_key.split("/")
        for layer in ("l3", "l2"):
            registry = cell["candidate_registries"][layer]
            manifest = cell["manifests"][layer]
            config = {
                "schema_version": "blind-gains.hier-p2-ranking.v1",
                "scope": (
                    f"HB P2.1 candidate-ranking readout for {cell_key} {layer} "
                    "(registered_hier_benchmark_v1.md §7 + A2; causal rows "
                    "only — invariance ranking is the catch-stability "
                    "instrument's job). Processor/prompt-contract/scoring "
                    "blocks byte-identical to "
                    "configs/eval/mini_a5_visual_evidence_ranking_v1.json; "
                    "the 3B processor serves all four models — every "
                    "processor artifact is byte-identical between the 3B and "
                    "7B checkpoints (verified at emission)."
                ),
                "candidate_registry": {
                    "path": registry["path"],
                    "sha256": sha256_file(ROOT / registry["path"]),
                    "pair_count": registry["rows"],
                    "source_manifest_sha256": manifest["sha256"],
                    "max_candidates": 16,
                    "selection_uses_model_outputs": False,
                },
                "processor": template["processor"],
                "prompt_contract": template["prompt_contract"],
                "models": models,
                "conditions": ["real"],
                "scoring": template["scoring"],
            }
            if config["candidate_registry"]["sha256"] != registry["sha256"]:
                raise AssertionError(
                    f"{registry['path']}: on-disk sha != build-report sha")
            out = ROOT / f"configs/eval/hier_p2_ranking_v1_{family}_{cell_name}_{layer}.json"
            if out.exists():
                raise FileExistsError(out)
            out.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
            emitted.append(str(out.relative_to(ROOT)))
    print(json.dumps({"emitted": emitted, "n": len(emitted)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
