#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModel, AutoTokenizer

from src.decon.core import embedding_entities, read_jsonl


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def image_embeddings(entities: list[tuple[str, str]], model_name: str, batch_size: int) -> np.ndarray:
    processor = AutoImageProcessor.from_pretrained(model_name, local_files_only=True)
    model = AutoModel.from_pretrained(model_name, local_files_only=True).to("cuda").eval()
    outputs = []
    with torch.inference_mode():
        for start in range(0, len(entities), batch_size):
            images = [Image.open(path).convert("RGB") for _, path in entities[start : start + batch_size]]
            inputs = processor(images=images, return_tensors="pt").to("cuda")
            features = model(**inputs).last_hidden_state[:, 0].float()
            features = torch.nn.functional.normalize(features, dim=1)
            outputs.append(features.cpu().numpy().astype(np.float16))
            for image in images:
                image.close()
    return np.concatenate(outputs)


def text_embeddings(entities: list[tuple[str, str]], model_name: str, batch_size: int) -> np.ndarray:
    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
    model = AutoModel.from_pretrained(model_name, local_files_only=True).to("cuda").eval()
    outputs = []
    with torch.inference_mode():
        for start in range(0, len(entities), batch_size):
            texts = [text for _, text in entities[start : start + batch_size]]
            inputs = tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors="pt").to("cuda")
            features = model(**inputs).last_hidden_state[:, 0].float()
            features = torch.nn.functional.normalize(features, dim=1)
            outputs.append(features.cpu().numpy().astype(np.float16))
    return np.concatenate(outputs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("image", "text"), required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--inputs", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metadata-output", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()
    if args.output.exists() or args.metadata_output.exists():
        raise FileExistsError("refusing to overwrite decontamination embeddings")
    records = [row for path in args.inputs for row in read_jsonl(path)]
    entities = embedding_entities(records, args.kind)
    features = (
        image_embeddings(entities, args.model, args.batch_size)
        if args.kind == "image"
        else text_embeddings(entities, args.model, args.batch_size)
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    identifiers = np.asarray([identifier for identifier, _ in entities], dtype=str)
    np.savez_compressed(args.output, identifiers=identifiers, features=features)
    metadata = {
        "schema_version": "blind-gains.decon-embeddings.v1",
        "kind": args.kind,
        "model": args.model,
        "batch_size": args.batch_size,
        "n_entities": len(entities),
        "dimensions": int(features.shape[1]),
        "dtype": str(features.dtype),
        "input_files": [str(path) for path in args.inputs],
        "input_sha256": {str(path): _sha256(path) for path in args.inputs},
        "output": str(args.output),
        "output_sha256": _sha256(args.output),
    }
    args.metadata_output.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"kind": args.kind, "n_entities": len(entities), "dimensions": features.shape[1]}))


if __name__ == "__main__":
    main()
