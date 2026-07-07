#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from modelscope import snapshot_download

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.model_registry import ModelArtifact, append_artifact, sha256_tree


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--revision", default="master")
    parser.add_argument("--local-dir", required=True)
    parser.add_argument("--license", default="VERIFY")
    parser.add_argument("--redistribution", default="VERIFY")
    parser.add_argument("--registry", default="experiments/manifests/model_registry.jsonl")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    local_dir = Path(args.local_dir)
    local_dir.parent.mkdir(parents=True, exist_ok=True)
    path = snapshot_download(args.model_id, revision=args.revision, local_dir=str(local_dir))
    digest = sha256_tree(path)
    append_artifact(
        ModelArtifact(
            name=args.model_id,
            source="ModelScope",
            source_url=f"https://modelscope.cn/models/{args.model_id}",
            revision=args.revision,
            license=args.license,
            local_path=str(path),
            redistribution=args.redistribution,
            sha256=digest,
            notes=args.notes,
        ),
        args.registry,
    )
    print(path)


if __name__ == "__main__":
    main()
