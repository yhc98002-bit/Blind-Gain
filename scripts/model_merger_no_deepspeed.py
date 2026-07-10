#!/usr/bin/env python3
"""Run EasyR1's merger when DeepSpeed is installed but CUDA_HOME is absent."""

from __future__ import annotations

import runpy
from pathlib import Path

import accelerate.utils.other as accelerate_other


def main() -> None:
    accelerate_other.is_deepspeed_available = lambda: False
    merger = Path(__file__).resolve().parents[1] / "artifacts" / "repos" / "EasyR1" / "scripts" / "model_merger.py"
    runpy.run_path(str(merger), run_name="__main__")


if __name__ == "__main__":
    main()
