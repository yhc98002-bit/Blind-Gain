#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any


EXPECTED_VERSIONS = {
    "torch": "2.6.0+cu118",
    "torchvision": "0.21.0+cu118",
    "transformers": "4.56.2",
    "accelerate": "1.14.0",
    "timm": "0.9.12",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate_runtime(
    versions: dict[str, str],
    *,
    cuda_runtime: str | None,
    mask_combinators_available: bool,
    gemma_importable: bool,
) -> dict[str, bool]:
    return {
        "exact_pinned_versions": versions == EXPECTED_VERSIONS,
        "cuda_runtime_is_11_8": cuda_runtime == "11.8",
        "torch_mask_combinators_available": mask_combinators_available,
        "gemma3_conditional_generation_importable": gemma_importable,
    }


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite M11 runtime audit: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requirements", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    import accelerate
    import timm
    import torch
    import torchvision
    import transformers

    try:
        from torch.nn.attention.flex_attention import or_masks  # noqa: F401

        mask_combinators_available = True
    except (ImportError, AttributeError):
        mask_combinators_available = False
    try:
        from transformers import Gemma3ForConditionalGeneration  # noqa: F401

        gemma_importable = True
    except ImportError:
        gemma_importable = False

    versions = {
        "torch": torch.__version__,
        "torchvision": torchvision.__version__,
        "transformers": transformers.__version__,
        "accelerate": accelerate.__version__,
        "timm": timm.__version__,
    }
    checks = evaluate_runtime(
        versions,
        cuda_runtime=torch.version.cuda,
        mask_combinators_available=mask_combinators_available,
        gemma_importable=gemma_importable,
    )
    payload = {
        "schema_version": "blind-gains.m11-runtime-audit.v1",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "versions": versions,
        "cuda_runtime": torch.version.cuda,
        "python_executable": sys.executable,
        "requirements": str(args.requirements),
        "requirements_sha256": sha256(args.requirements),
        "freeze": str(args.freeze),
        "freeze_sha256": sha256(args.freeze),
    }
    atomic_json(args.output, payload)
    print(json.dumps(payload, sort_keys=True))
    raise SystemExit(0 if payload["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
