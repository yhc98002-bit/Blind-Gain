#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.eval.image_conditions import materialize_image
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT, format_question
from src.eval.visual_evidence_ranking import (
    RESULT_SCHEMA_VERSION,
    SCORER_VERSION,
    completion_logprob_from_logits,
    score_pair_from_candidates,
)


ROOT = Path(__file__).resolve().parents[1]
CONDITIONS = {"real", "gray", "no_image", "mismatched_real", "twin_counterfactual"}


def select_source_image(
    row: dict[str, Any],
    side: str,
    condition: str,
    image_override: dict[str, Any] | None,
) -> str:
    if condition == "twin_counterfactual":
        twin = "b" if side == "a" else "a"
        return str(row[f"image_{twin}_path"])
    if condition == "mismatched_real":
        if image_override is None:
            raise ValueError("mismatched_real requires an image override map")
        entry = image_override["per_pair"][str(row["pair_id"])]
        override_path = str(entry[side])
        if override_path == str(row[f"image_{side}_path"]):
            raise ValueError(
                f"override equals own image for pair {row['pair_id']}"
            )
        return override_path
    return str(row[f"image_{side}_path"])


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def _processor_artifact_sha256(path: Path, names: list[str]) -> str:
    items = []
    for name in sorted(names):
        file_path = path / name
        if not file_path.is_file() or Path(name).name != name:
            raise ValueError(f"invalid processor artifact member: {name}")
        items.append({"name": name, "sha256": _sha256(file_path)})
    encoded = json.dumps(items, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _messages(question: str, condition: str, image_path: str | None) -> list[dict[str, Any]]:
    text_item = {"type": "text", "text": format_question(question)}
    if condition == "no_image":
        content = [text_item]
    else:
        if not image_path:
            raise ValueError("an image path is required outside no_image")
        content = [{"type": "image", "image": image_path}, text_item]
    return [{"role": "user", "content": content}]


def _score_side(
    *,
    model: Any,
    processor: Any,
    process_vision_info: Any,
    row: dict[str, Any],
    side: str,
    condition: str,
    image_override: dict[str, Any] | None,
    cache_dir: Path,
    batch_size: int,
) -> tuple[dict[str, float], dict[str, float], dict[str, int]]:
    source_image = _resolve(select_source_image(row, side, condition, image_override))
    if condition in {"real", "mismatched_real", "twin_counterfactual"}:
        image_path = str(source_image)
    elif condition == "gray":
        image_path = materialize_image(
            str(source_image), "gray", cache_dir, noise_seed=0
        )
    else:
        image_path = None
    messages = _messages(str(row["question"]), condition, image_path)
    prompt = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    if condition == "no_image":
        image_inputs = None
        video_inputs = None
        prompt_inputs = processor(
            text=[prompt], padding=True, return_tensors="pt"
        )
    else:
        image_inputs, video_inputs = process_vision_info(messages)
        prompt_inputs = processor(
            text=[prompt],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
    prompt_length = int(prompt_inputs["attention_mask"][0].sum().item())
    prompt_ids = prompt_inputs["input_ids"][0, :prompt_length].tolist()

    mean_scores: dict[str, float] = {}
    raw_scores: dict[str, float] = {}
    token_counts: dict[str, int] = {}
    candidates = list(row["candidates"])
    for start in range(0, len(candidates), batch_size):
        batch = candidates[start : start + batch_size]
        full_texts = [prompt + str(item["verbalization"]) for item in batch]
        if condition == "no_image":
            inputs = processor(
                text=full_texts, padding=True, return_tensors="pt"
            )
        else:
            assert image_inputs is not None
            repeated_images = list(image_inputs) * len(batch)
            repeated_videos = list(video_inputs) * len(batch) if video_inputs else None
            inputs = processor(
                text=full_texts,
                images=repeated_images,
                videos=repeated_videos,
                padding=True,
                return_tensors="pt",
            )
        inputs = inputs.to(model.device)
        import torch

        with torch.inference_mode():
            logits = model(**inputs, use_cache=False).logits
        for index, item in enumerate(batch):
            sequence_length = int(inputs["attention_mask"][index].sum().item())
            observed_prefix = inputs["input_ids"][index, :prompt_length].tolist()
            if observed_prefix != prompt_ids:
                raise ValueError(
                    f"prompt is not an exact token prefix for candidate {item['candidate_id']}"
                )
            mean, raw_sum, token_count = completion_logprob_from_logits(
                logits[index], inputs["input_ids"][index], prompt_length, sequence_length
            )
            candidate_id = str(item["candidate_id"])
            mean_scores[candidate_id] = mean
            raw_scores[candidate_id] = raw_sum
            token_counts[candidate_id] = token_count
        del logits, inputs
    return mean_scores, raw_scores, token_counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--model-key", required=True)
    parser.add_argument("--condition", choices=sorted(CONDITIONS), required=True)
    parser.add_argument("--image-override-map", default=None)
    parser.add_argument("--output", required=True)
    parser.add_argument("--cache-dir", required=True)
    parser.add_argument("--num-shards", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    if args.num_shards < 1 or not 0 <= args.shard_index < args.num_shards:
        raise ValueError("invalid shard specification")

    config_path = _resolve(args.config)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    image_override = None
    image_override_sha256 = None
    if args.condition == "mismatched_real":
        if not args.image_override_map:
            raise ValueError("mismatched_real requires --image-override-map")
        override_path = _resolve(args.image_override_map)
        image_override_sha256 = _sha256(override_path)
        expected_override = config.get("image_override_map") or {}
        if str(expected_override.get("path")) != str(args.image_override_map):
            raise ValueError("override map path differs from configuration")
        if str(expected_override.get("sha256")) != image_override_sha256:
            raise ValueError("override map hash differs from configuration")
        image_override = json.loads(override_path.read_text(encoding="utf-8"))
    elif args.image_override_map:
        raise ValueError("--image-override-map is only valid for mismatched_real")
    model_spec = config["models"].get(args.model_key)
    if not isinstance(model_spec, dict):
        raise ValueError(f"unknown model key: {args.model_key}")
    registry_path = _resolve(config["candidate_registry"]["path"])
    if _sha256(registry_path) != config["candidate_registry"]["sha256"]:
        raise ValueError("frozen candidate-registry hash mismatch")
    model_path = _resolve(model_spec["path"])
    index_path = model_path / "model.safetensors.index.json"
    if _sha256(index_path) != model_spec["model_index_sha256"]:
        raise ValueError("model index hash mismatch")
    processor_path = _resolve(config["processor"]["path"])
    if _processor_artifact_sha256(
        processor_path, list(config["processor"]["artifact_files"])
    ) != config["processor"]["artifact_sha256"]:
        raise ValueError("frozen processor/tokenizer artifact hash mismatch")
    if DEFAULT_PROMPT_CONTRACT.sha256 != config["prompt_contract"]["sha256"]:
        raise ValueError("prompt contract hash mismatch")

    output = _resolve(args.output)
    partial = Path(f"{output}.partial")
    if output.exists() or partial.exists():
        raise FileExistsError(f"refusing to overwrite ranking output: {output}")
    rows = [
        json.loads(line)
        for index, line in enumerate(registry_path.read_text(encoding="utf-8").splitlines())
        if index % args.num_shards == args.shard_index
    ]
    if args.limit is not None:
        rows = rows[: args.limit]
    if not rows:
        raise ValueError("ranking shard is empty")

    import torch
    from qwen_vl_utils import process_vision_info
    from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

    processor = AutoProcessor.from_pretrained(processor_path, trust_remote_code=True)
    processor.tokenizer.padding_side = "right"
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
        attn_implementation="sdpa",
    )
    model.eval()
    cache_dir = _resolve(args.cache_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    with partial.open("x", encoding="utf-8") as handle:
        for row in rows:
            scores_a, raw_a, counts_a = _score_side(
                model=model,
                processor=processor,
                process_vision_info=process_vision_info,
                row=row,
                side="a",
                condition=args.condition,
                image_override=image_override,
                cache_dir=cache_dir,
                batch_size=int(config["scoring"]["candidate_batch_size"]),
            )
            scores_b, raw_b, counts_b = _score_side(
                model=model,
                processor=processor,
                process_vision_info=process_vision_info,
                row=row,
                side="b",
                condition=args.condition,
                image_override=image_override,
                cache_dir=cache_dir,
                batch_size=int(config["scoring"]["candidate_batch_size"]),
            )
            metrics = score_pair_from_candidates(row, scores_a, scores_b, raw_a, raw_b)
            result = {
                "schema_version": RESULT_SCHEMA_VERSION,
                "scorer_version": SCORER_VERSION,
                "pair_id": row["pair_id"],
                "source_pair_id": row.get("source_pair_id"),
                "template_id": row["template_id"],
                "template_label": row["template_label"],
                "category": row.get("category"),
                "model_key": args.model_key,
                "global_step": model_spec["global_step"],
                "condition": args.condition,
                "candidate_set_sha256": row["candidate_set_sha256"],
                **(
                    {
                        "image_override_map_sha256": image_override_sha256,
                        "mismatched_source_pair_id": image_override["per_pair"][
                            str(row["pair_id"])
                        ]["source_pair_id"],
                    }
                    if image_override is not None
                    else {}
                ),
                "candidate_count": row["candidate_count"],
                "candidate_scores_a": scores_a,
                "candidate_scores_b": scores_b,
                "candidate_raw_sum_scores_a": raw_a,
                "candidate_raw_sum_scores_b": raw_b,
                "candidate_token_counts_a": counts_a,
                "candidate_token_counts_b": counts_b,
                **metrics,
            }
            handle.write(json.dumps(result, sort_keys=True, ensure_ascii=True) + "\n")
            handle.flush()
    os.replace(partial, output)
    print(
        json.dumps(
            {
                "status": "complete",
                "rows": len(rows),
                "output": str(output),
                "output_sha256": _sha256(output),
                "model_key": args.model_key,
                "condition": args.condition,
                "scorer_version": SCORER_VERSION,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
