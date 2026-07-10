#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATASET_ROOT="artifacts/hf_home/datasets/hiyouga___geometry3k/default/0.0.0/fd21e533e1e50d0662a2bf7b223e60511bd5f8b7"
OUTPUT_DIR="data/geometry3k_caption_images"
MANIFEST="data/geometry3k_caption_images_manifest.jsonl"
SUMMARY="experiments/manifests/geometry3k_caption_export.json"

cd "${ROOT}"
PYTHONPATH=. .venv/bin/python -m src.data.geometry3k_export \
  --dataset-root "${DATASET_ROOT}" \
  --output-dir "${OUTPUT_DIR}" \
  --manifest "${MANIFEST}" \
  --summary "${SUMMARY}"
