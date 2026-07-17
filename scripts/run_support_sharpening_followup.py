#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from PIL import Image

from scripts.run_blind_solvability import _vllm_request
from src.analysis.support_sharpening import (
    registered_followup_schedule,
    registered_sampling_kwargs,
)
from src.eval.blind_solvability import (
    build_conditioned_messages,
    load_caption_map,
    load_geometry_rows,
    score_greedy_item_pilot,
    vllm_multimodal_limits,
)
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT
from src.rewards.answer_reward import PARSER_VERSION
from src.rewards.pilot_reward import PILOT_REWARD_VERSION


SCHEMA_VERSION = "blind-gains.support-sharpening-draw.v1"
CONFIG_SCHEMA_VERSION = "blind-gains.support-sharpening-execution.v2"
ARMS = ("a1_real", "a2_gray", "a2b_noimage", "a3_caption")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            raise ValueError(f"blank JSONL row at {path}:{line_number}")
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"non-object JSONL row at {path}:{line_number}")
        rows.append(row)
    return rows


def _require_file_hash(root: Path, record: dict[str, Any], label: str) -> Path:
    path = (root / str(record.get("path", ""))).resolve()
    if not path.is_file() or sha256(path) != record.get("sha256"):
        raise ValueError(f"{label} is absent or hash-mismatched: {path}")
    return path


def validate_execution_config(config: dict[str, Any], root: Path) -> None:
    if config.get("schema_version") != CONFIG_SCHEMA_VERSION:
        raise ValueError("unsupported support-sharpening execution config")
    expected_schedule = registered_followup_schedule()
    followup = config.get("followup")
    if not isinstance(followup, dict):
        raise ValueError("follow-up config is absent")
    checks = {
        "draw_start": followup.get("draw_index_start_inclusive") == 16,
        "draw_stop": followup.get("draw_index_stop_exclusive") == 80,
        "seed_formula": followup.get("seed_formula") == "20260716 + draw_index",
        "seeds": followup.get("seeds") == [row["seed"] for row in expected_schedule],
        "decoding": followup.get("decoding")
        == {"temperature": 1.0, "top_p": 1.0, "n_per_call": 1, "max_tokens": 2048},
        "original_seed": config.get("original_sampling_seed") == 20260710,
        "prompt": config.get("prompt_contract_sha256")
        == DEFAULT_PROMPT_CONTRACT.sha256,
        "parser": config.get("parser_version") == PARSER_VERSION,
        "reward": config.get("pilot_reward_version") == PILOT_REWARD_VERSION,
        "arms": isinstance(config.get("arms"), dict)
        and tuple(config["arms"].keys()) == ARMS,
    }
    if not all(checks.values()):
        raise ValueError(f"support-sharpening execution contract drift: {checks}")
    _require_file_hash(root, config["source_manifest"], "source manifest")
    _require_file_hash(root, config["format_prompt"], "format prompt")
    model_config = root / str(config["model"]["path"]) / "config.json"
    if not model_config.is_file() or sha256(model_config) != config["model"]["config_sha256"]:
        raise ValueError("frozen base-model config is absent or hash-mismatched")


def load_bound_inputs(
    config: dict[str, Any], arm: str, root: Path
) -> tuple[list[dict[str, Any]], dict[tuple[str, int], dict[str, Any]], dict[str, str] | None]:
    if arm not in ARMS:
        raise ValueError(f"unregistered support-sharpening arm: {arm}")
    arm_config = config["arms"][arm]
    candidate_path = _require_file_hash(
        root,
        {"path": arm_config["candidate_path"], "sha256": arm_config["candidate_sha256"]},
        f"{arm} candidates",
    )
    baseline_path = _require_file_hash(
        root,
        {"path": arm_config["baseline_path"], "sha256": arm_config["baseline_sha256"]},
        f"{arm} baseline",
    )
    candidates = sorted(
        read_jsonl(candidate_path), key=lambda row: (str(row["split"]), int(row["row_index"]))
    )
    if len(candidates) != arm_config["candidate_count"]:
        raise ValueError(f"{arm} candidate count drift")
    if len({(row["split"], row["row_index"]) for row in candidates}) != len(candidates):
        raise ValueError(f"{arm} candidate identities are not unique")

    baseline_rows = read_jsonl(baseline_path)
    baseline = {(str(row["split"]), int(row["row_index"])): row for row in baseline_rows}
    if len(baseline) != len(baseline_rows):
        raise ValueError(f"{arm} baseline identities are not unique")
    source_path = root / config["source_manifest"]["path"]
    source_rows = load_geometry_rows(source_path, ("test",))
    source = {(str(row["split"]), int(row["row_index"])): row for row in source_rows}

    for candidate in candidates:
        identity = (str(candidate["split"]), int(candidate["row_index"]))
        base = baseline.get(identity)
        item = source.get(identity)
        checks = {
            "candidate_schema": candidate.get("schema_version")
            == "blind-gains.support-sharpening.v1",
            "arm": candidate.get("arm") == arm,
            "condition": candidate.get("condition") == arm_config["condition"],
            "source_present": item is not None,
            "baseline_present": base is not None,
            "baseline_condition": base is not None
            and base.get("condition") == arm_config["condition"],
            "initial_floor": base is not None
            and base.get("sample_count") == 16
            and base.get("sample_correct_count") == 0,
            "original_seed": base is not None
            and base.get("decoding", {}).get("seed") == config["original_sampling_seed"],
            "problem": item is not None and candidate.get("problem") == item.get("problem"),
            "answer": item is not None and candidate.get("ground_truth") == item.get("answer"),
            "images": item is not None
            and candidate.get("image_sha256")
            == [image["sha256"] for image in item.get("images", [])],
        }
        if not all(checks.values()):
            raise ValueError(f"candidate/source binding failed for {arm}:{identity}: {checks}")

    captions = None
    if arm_config["condition"] == "caption":
        caption_records = config["caption_store"]["shards"]
        caption_paths = [
            _require_file_hash(root, record, f"caption shard {index}")
            for index, record in enumerate(caption_records)
        ]
        captions = load_caption_map(caption_paths)
        required = {
            image["sha256"]
            for candidate in candidates
            for image in source[(candidate["split"], candidate["row_index"])].get("images", [])
        }
        if not required <= captions.keys():
            raise ValueError("frozen caption store misses a support-sharpening image")
    return candidates, source, captions


def expected_draw_identities(candidates: list[dict[str, Any]]) -> list[tuple[int, int]]:
    return [
        (registered["draw_index"], int(candidate["row_index"]))
        for registered in registered_followup_schedule()
        for candidate in candidates
    ]


def validate_resume_prefix(
    partial: Path, candidates: list[dict[str, Any]], arm: str, condition: str
) -> list[dict[str, Any]]:
    if not partial.exists():
        return []
    rows = read_jsonl(partial)
    expected = expected_draw_identities(candidates)
    if len(rows) > len(expected):
        raise ValueError("support-sharpening partial is longer than the registered run")
    candidate_by_index = {int(row["row_index"]): row for row in candidates}
    for position, (row, identity) in enumerate(zip(rows, expected), 1):
        draw_index, row_index = identity
        candidate = candidate_by_index[row_index]
        expected_fields = {
            "schema_version": SCHEMA_VERSION,
            "arm": arm,
            "condition": condition,
            "row_index": row_index,
            "draw_index": draw_index,
            "seed": 20260716 + draw_index,
            "source_item_fingerprint": candidate["source_item_fingerprint"],
            "parser_version": PARSER_VERSION,
            "pilot_reward_version": PILOT_REWARD_VERSION,
            "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
        }
        for key, value in expected_fields.items():
            if row.get(key) != value:
                raise ValueError(
                    f"support-sharpening resume mismatch at row {position} for {key}"
                )
        if row.get("decoding") != registered_sampling_kwargs(draw_index):
            raise ValueError(f"support-sharpening decoding mismatch at row {position}")
        if not isinstance(row.get("response"), str) or not isinstance(
            row.get("pilot_accuracy_correct"), bool
        ):
            raise ValueError(f"support-sharpening score payload invalid at row {position}")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--arm", choices=ARMS, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--request-batch-size", type=int, default=8)
    parser.add_argument("--max-model-len", type=int, default=8192)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.72)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite follow-up output: {args.output}")
    if args.request_batch_size < 1:
        raise ValueError("request batch size must be positive")

    root = Path(__file__).resolve().parents[1]
    config = json.loads(args.config.read_text(encoding="utf-8"))
    validate_execution_config(config, root)
    candidates, source, captions = load_bound_inputs(config, args.arm, root)
    condition = config["arms"][args.arm]["condition"]
    partial = Path(f"{args.output}.partial")
    resumed = validate_resume_prefix(partial, candidates, args.arm, condition)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    if not partial.exists():
        partial.touch(exist_ok=False)
    total_rows = len(candidates) * len(registered_followup_schedule())
    if len(resumed) == total_rows:
        os.replace(partial, args.output)
        return

    from transformers import AutoProcessor
    from vllm import LLM, SamplingParams

    model_path = root / config["model"]["path"]
    processor = AutoProcessor.from_pretrained(
        model_path, trust_remote_code=True, local_files_only=True
    )
    max_images = max(
        len(source[(candidate["split"], candidate["row_index"])].get("images", []))
        for candidate in candidates
    )
    llm = LLM(
        model=str(model_path),
        trust_remote_code=True,
        tensor_parallel_size=1,
        dtype="bfloat16",
        max_model_len=args.max_model_len,
        gpu_memory_utilization=args.gpu_memory_utilization,
        limit_mm_per_prompt=vllm_multimodal_limits(condition, max_images=max_images),
    )
    format_prompt = (root / config["format_prompt"]["path"]).read_text(encoding="utf-8")
    start_position = len(resumed)
    candidate_count = len(candidates)

    with partial.open("a", encoding="utf-8") as handle:
        for registered in registered_followup_schedule():
            draw_index = registered["draw_index"]
            draw_start = (draw_index - 16) * candidate_count
            if start_position >= draw_start + candidate_count:
                continue
            first_candidate = max(0, start_position - draw_start)
            sampling_kwargs = registered_sampling_kwargs(draw_index)
            sampling = SamplingParams(**sampling_kwargs)
            for batch_start in range(first_candidate, candidate_count, args.request_batch_size):
                batch = candidates[batch_start : batch_start + args.request_batch_size]
                requests = []
                opened_images: list[Image.Image] = []
                for candidate in batch:
                    item = source[(candidate["split"], candidate["row_index"])]
                    messages, image_paths = build_conditioned_messages(
                        item,
                        format_prompt,
                        condition,
                        args.cache_dir,
                        captions=captions,
                        noise_seed=config["original_sampling_seed"],
                    )
                    request, opened = _vllm_request(processor, messages, image_paths)
                    requests.append(request)
                    opened_images.extend(opened)
                try:
                    outputs = llm.generate(requests, sampling, use_tqdm=False)
                finally:
                    for image in opened_images:
                        image.close()
                if len(outputs) != len(batch) or any(len(output.outputs) != 1 for output in outputs):
                    raise RuntimeError("vLLM did not return one output per registered draw")
                for candidate, generated in zip(batch, outputs):
                    response = generated.outputs[0].text.strip()
                    scored = score_greedy_item_pilot(
                        str(candidate["ground_truth"]),
                        response,
                        DEFAULT_PROMPT_CONTRACT,
                    )
                    row = {
                        "schema_version": SCHEMA_VERSION,
                        "arm": args.arm,
                        "condition": condition,
                        "split": candidate["split"],
                        "row_index": candidate["row_index"],
                        "source_item_fingerprint": candidate["source_item_fingerprint"],
                        "draw_index": draw_index,
                        "seed": registered["seed"],
                        "decoding": sampling_kwargs,
                        "response": response,
                        "pilot_accuracy_correct": bool(scored["pilot_accuracy_reward"] > 0.5),
                        "duplicate_text_responses_retained": True,
                        **scored,
                    }
                    handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                    start_position += 1
                print(
                    json.dumps(
                        {
                            "arm": args.arm,
                            "draw_index": draw_index,
                            "seed": registered["seed"],
                            "processed_rows": start_position,
                            "total_rows": total_rows,
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
    if start_position != total_rows:
        raise RuntimeError(f"follow-up row count mismatch: {start_position} != {total_rows}")
    os.replace(partial, args.output)


if __name__ == "__main__":
    main()
