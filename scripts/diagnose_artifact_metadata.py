#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from src.fliptrack.artifact_attackers import (
    METADATA_FEATURE_NAMES,
    _metadata_features,
    build_packaged_member_table,
    univariate_feature_diagnosis,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-dir", required=True)
    parser.add_argument("--key-file", required=True)
    parser.add_argument("--template", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite metadata diagnosis: {args.output}")
    paths, labels, _, templates = build_packaged_member_table(args.release_dir, args.key_file)
    selected = np.asarray(templates) == args.template
    if not selected.any():
        raise ValueError(f"template is absent from package: {args.template}")
    features = np.stack(
        [_metadata_features(path) for path, keep in zip(paths, selected) if keep]
    )
    result = {
        "schema_version": "blind-gains.artifact-metadata-diagnosis.v1",
        "release_dir": args.release_dir,
        "template": args.template,
        "n_members": int(selected.sum()),
        "features": univariate_feature_diagnosis(
            features,
            labels[selected],
            METADATA_FEATURE_NAMES,
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"template": args.template, "n_members": int(selected.sum())}, sort_keys=True))


if __name__ == "__main__":
    main()
