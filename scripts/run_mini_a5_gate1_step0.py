#!/usr/bin/env python3
"""Step-0 base-model reward diagnostic for the Gate-1 completion arms.

Mirrors scripts/run_mini_a5_step0.py on the per-member v2 sample schema
(scripts/build_mini_a5_gate1_smoke_inputs.py): necessity pseudo-pairs draw
their members i.i.d., so each member carries its own question, template,
rendering, and answer. Zero optimizer steps; 5 temperature-1 rollouts per
member; both the member reward and the CP joint diagnostic are computed with
the registered reward implementation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jinja2 import Template
from PIL import Image

from scripts.run_blind_solvability import _vllm_request
from src.rewards.answer_reward import PARSER_VERSION
from src.rewards.cp_grpo_reward import (
    CP_REWARD_VERSION,
    compute_member_score,
    compute_score,
)
from src.rewards.pilot_reward import PILOT_REWARD_VERSION


SCHEMA_VERSION = "blind-gains.mini-a5-gate1-step0-row.v1"
SAMPLE_SCHEMA_VERSION = "blind-gains.mini-a5-gate1-step0-pair.v2"
EXPECTED_PAIRS = 192
ROLLOUT_N = 5
MAX_TOKENS = 2048
TEMPERATURE = 1.0
TOP_P = 1.0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_sample(path: Path, arm: str) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        pairs = [json.loads(line) for line in handle if line.strip()]
    if len(pairs) != EXPECTED_PAIRS:
        raise ValueError(
            f"gate1 step-0 sample must contain exactly {EXPECTED_PAIRS} pseudo-pairs"
        )
    uids = [str(pair.get("pair_group_uid", "")) for pair in pairs]
    if len(uids) != len(set(uids)) or not all(uids):
        raise ValueError("gate1 step-0 sample uids must be unique and nonempty")
    for pair in pairs:
        if pair.get("schema_version") != SAMPLE_SCHEMA_VERSION:
            raise ValueError(f"sample schema is not {SAMPLE_SCHEMA_VERSION}")
        if pair.get("arm") != arm:
            raise ValueError(f"sample arm {pair.get('arm')!r} != requested {arm!r}")
        for member in ("a", "b"):
            for field in (
                f"question_{member}",
                f"answer_{member}",
                f"image_{member}_path",
                f"image_{member}_sha256",
                f"template_id_{member}",
                f"category_{member}",
                f"source_qid_{member}",
            ):
                if not str(pair.get(field, "")):
                    raise ValueError(f"{pair['pair_group_uid']}: missing {field}")
    return pairs


def pair_reward_inputs(
    pair: dict[str, Any], responses_a: list[str], responses_b: list[str]
) -> list[dict[str, Any]]:
    if len(responses_a) != ROLLOUT_N or len(responses_b) != ROLLOUT_N:
        raise ValueError(f"each pseudo-pair member requires exactly {ROLLOUT_N} responses")
    rows: list[dict[str, Any]] = []
    for member, responses in (("a", responses_a), ("b", responses_b)):
        for rollout_index, response in enumerate(responses):
            rows.append(
                {
                    "response": response,
                    "ground_truth": str(pair[f"answer_{member}"]),
                    "pair_group_uid": str(pair["pair_group_uid"]),
                    "pair_member": member,
                    "pair_rollout_index": rollout_index,
                }
            )
    return rows


def _messages(question: str, image_path: str, format_template: Template) -> list[dict[str, Any]]:
    return [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image_path},
                {"type": "text", "text": format_template.render(content=question).strip()},
            ],
        }
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=("std", "necessity"), required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--model-revision", required=True)
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument("--format-prompt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch-pairs", type=int, default=2)
    parser.add_argument("--max-model-len", type=int, default=8192)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.72)
    parser.add_argument("--seed", type=int, default=20260716)
    args = parser.parse_args()
    if args.batch_pairs < 1:
        raise ValueError("batch-pairs must be positive")

    pairs = load_sample(args.sample, args.arm)
    sample_sha256 = sha256_file(args.sample)
    format_prompt_sha256 = sha256_file(args.format_prompt)
    format_template = Template(args.format_prompt.read_text(encoding="utf-8").strip())
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite step-0 output: {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.touch(exist_ok=False)

    from transformers import AutoProcessor
    from vllm import LLM, SamplingParams

    processor = AutoProcessor.from_pretrained(
        args.model_path, trust_remote_code=True, local_files_only=True
    )
    llm = LLM(
        model=str(args.model_path),
        trust_remote_code=True,
        tensor_parallel_size=1,
        dtype="bfloat16",
        max_model_len=args.max_model_len,
        gpu_memory_utilization=args.gpu_memory_utilization,
        limit_mm_per_prompt={"image": 1, "video": 0},
    )
    sampling = SamplingParams(
        temperature=TEMPERATURE,
        top_p=TOP_P,
        n=ROLLOUT_N,
        max_tokens=MAX_TOKENS,
        seed=args.seed,
    )

    with args.output.open("a", encoding="utf-8") as handle:
        for start in range(0, len(pairs), args.batch_pairs):
            batch = pairs[start : start + args.batch_pairs]
            requests: list[dict[str, Any]] = []
            opened_images: list[Image.Image] = []
            for pair in batch:
                for member in ("a", "b"):
                    image_path = str(pair[f"image_{member}_path"])
                    request, opened = _vllm_request(
                        processor,
                        _messages(
                            str(pair[f"question_{member}"]),
                            image_path,
                            format_template,
                        ),
                        [image_path],
                    )
                    requests.append(request)
                    opened_images.extend(opened)
            try:
                outputs = llm.generate(requests, sampling, use_tqdm=False)
            finally:
                for image in opened_images:
                    image.close()

            for offset, pair in enumerate(batch):
                responses_a = [item.text.strip() for item in outputs[offset * 2].outputs]
                responses_b = [item.text.strip() for item in outputs[offset * 2 + 1].outputs]
                reward_inputs = pair_reward_inputs(pair, responses_a, responses_b)
                cp_scores = compute_score(reward_inputs)
                member_scores = compute_member_score(reward_inputs)
                for reward_input, cp_score, member_score in zip(
                    reward_inputs, cp_scores, member_scores, strict=True
                ):
                    member = str(reward_input["pair_member"])
                    row = {
                        "schema_version": SCHEMA_VERSION,
                        "arm": args.arm,
                        "pair_group_uid": str(pair["pair_group_uid"]),
                        "pair_member": member,
                        "pair_rollout_index": int(reward_input["pair_rollout_index"]),
                        "template_id": str(pair[f"template_id_{member}"]),
                        "category": str(pair[f"category_{member}"]),
                        "question": str(pair[f"question_{member}"]),
                        "source_qid": str(pair[f"source_qid_{member}"]),
                        "ground_truth": str(reward_input["ground_truth"]),
                        "image_sha256": str(pair[f"image_{member}_sha256"]),
                        "response": str(reward_input["response"]),
                        "member_reward": float(member_score["overall"]),
                        "cp_joint_reward": float(cp_score["overall"]),
                        "contract_valid": float(member_score["format"]),
                        "canonical_eval_reward": float(
                            member_score["canonical_eval_reward"]
                        ),
                        "reward_disagreement": float(
                            member_score["reward_disagreement"]
                        ),
                        "reward_disagreement_reason_code": float(
                            member_score["reward_disagreement_reason_code"]
                        ),
                        "sample_manifest_sha256": sample_sha256,
                        "format_prompt_sha256": format_prompt_sha256,
                        "model_revision": args.model_revision,
                        "seed": args.seed,
                        "rollout_n": ROLLOUT_N,
                        "temperature": TEMPERATURE,
                        "top_p": TOP_P,
                        "max_tokens": MAX_TOKENS,
                        "parser_version": PARSER_VERSION,
                        "pilot_reward_version": PILOT_REWARD_VERSION,
                        "cp_reward_version": CP_REWARD_VERSION,
                    }
                    handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
                handle.flush()
            print(
                json.dumps(
                    {
                        "arm": args.arm,
                        "processed_pairs": min(start + len(batch), len(pairs)),
                        "total_pairs": len(pairs),
                    }
                ),
                flush=True,
            )


if __name__ == "__main__":
    main()
