#!/usr/bin/env python3
import importlib.util
import json
import shutil
import subprocess
import sys


MODULES = [
    "torch",
    "torchvision",
    "transformers",
    "datasets",
    "modelscope",
    "vllm",
    "verl",
    "accelerate",
    "deepspeed",
    "PIL",
    "matplotlib",
    "numpy",
    "cv2",
]


def run(cmd):
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"ERROR: {exc}"


def main():
    info = {
        "python": sys.version,
        "executable": sys.executable,
        "modules": {name: importlib.util.find_spec(name) is not None for name in MODULES},
        "nvcc": shutil.which("nvcc"),
        "nvidia_smi": shutil.which("nvidia-smi"),
    }
    try:
        import torch

        info.update(
            {
                "torch_version": torch.__version__,
                "cuda_available": torch.cuda.is_available(),
                "cuda_device_count": torch.cuda.device_count(),
                "cuda_version": torch.version.cuda,
            }
        )
    except Exception as exc:
        info["torch_error"] = repr(exc)

    info["nvcc_version"] = run(["nvcc", "--version"]) if info["nvcc"] else "missing"
    info["gpu_query"] = (
        run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,driver_version",
                "--format=csv,noheader,nounits",
            ]
        )
        if info["nvidia_smi"]
        else "missing"
    )
    print(json.dumps(info, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

