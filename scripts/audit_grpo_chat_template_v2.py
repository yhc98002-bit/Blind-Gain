#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Template
from PIL import Image


SCHEMA_VERSION = "blind-gains.grpo-chat-template-audit.v2"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_rows(path: Path, count_per_split: int) -> list[dict[str, Any]]:
    selected: dict[str, list[dict[str, Any]]] = {"train": [], "test": []}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            split = str(row.get("split"))
            if split in selected and len(selected[split]) < count_per_split:
                selected[split].append(row)
            if all(len(rows) == count_per_split for rows in selected.values()):
                break
    if any(len(rows) != count_per_split for rows in selected.values()):
        raise ValueError(f"expected {count_per_split} rows for each train/test split")
    return [*selected["train"], *selected["test"]]


def build_messages(row: dict[str, Any], format_prompt: str) -> list[dict[str, Any]]:
    prompt = Template(format_prompt.strip()).render(content=str(row["problem"]))
    parts = prompt.split("<image>")
    images = list(row.get("images", []))
    if len(parts) - 1 != len(images):
        raise ValueError(
            f"row {(row.get('split'), row.get('row_index'))} has "
            f"{len(parts) - 1} image markers and {len(images)} images"
        )
    content: list[dict[str, str]] = []
    for index, part in enumerate(parts):
        if index:
            content.append({"type": "image"})
        if part:
            content.append({"type": "text", "text": part})
    return [{"role": "user", "content": content}]


def _image_path(image: Any) -> Path:
    if isinstance(image, str):
        return Path(image)
    if isinstance(image, dict) and isinstance(image.get("path"), str):
        return Path(image["path"])
    raise TypeError(f"unsupported image reference: {image!r}")


def _process_image(path: Path, min_pixels: int | None, max_pixels: int | None) -> Image.Image:
    image = Image.open(path)
    image.load()
    if max_pixels is not None and image.width * image.height > max_pixels:
        factor = math.sqrt(max_pixels / (image.width * image.height))
        image = image.resize((int(image.width * factor), int(image.height * factor)))
    if min_pixels is not None and image.width * image.height < min_pixels:
        factor = math.sqrt(min_pixels / (image.width * image.height))
        image = image.resize((int(image.width * factor), int(image.height * factor)))
    return image.convert("RGB")


def audit_rendered_rows(
    *,
    processor: Any,
    rows: list[dict[str, Any]],
    format_prompt: str,
    min_pixels: int | None,
    max_pixels: int | None,
    max_prompt_length: int,
    load_images: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, bool]]:
    records: list[dict[str, Any]] = []
    for row in rows:
        messages = build_messages(row, format_prompt)
        rendered = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=False,
        )
        image_paths = [_image_path(image) for image in row.get("images", [])]
        images = (
            [_process_image(path, min_pixels, max_pixels) for path in image_paths]
            if load_images
            else [str(path) for path in image_paths]
        )
        inputs = processor(
            images=images,
            text=[rendered],
            add_special_tokens=False,
            return_tensors="pt",
        )
        prompt_tokens = int(inputs["input_ids"].shape[-1])
        records.append(
            {
                "split": str(row["split"]),
                "row_index": int(row["row_index"]),
                "problem": str(row["problem"]),
                "ground_truth": str(row["answer"]),
                "image_paths": [str(path) for path in image_paths],
                "image_sha256": [
                    _sha256(path) if load_images or path.is_file() else None
                    for path in image_paths
                ],
                "source_image_count": len(image_paths),
                "rendered_vision_marker_count": rendered.count("<|vision_start|>"),
                "rendered_prompt": rendered,
                "rendered_prompt_sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
                "rendered_prompt_chars": len(rendered),
                "prompt_tokens": prompt_tokens,
                "within_max_prompt_length": prompt_tokens <= max_prompt_length,
                "has_think_contract": "<think>" in rendered and "</think>" in rendered,
                "has_answer_contract": "<answer>" in rendered and "</answer>" in rendered,
                "has_generation_prompt": rendered.rstrip().endswith("assistant"),
            }
        )
    checks = {
        "exact_8_train_8_test": len(records) == 16
        and sum(row["split"] == "train" for row in records) == 8
        and sum(row["split"] == "test" for row in records) == 8,
        "all_item_identities_unique": len(
            {(row["split"], row["row_index"]) for row in records}
        )
        == len(records),
        "image_markers_match_source_images": all(
            row["rendered_vision_marker_count"] == row["source_image_count"]
            for row in records
        ),
        "think_contract_present": all(row["has_think_contract"] for row in records),
        "answer_contract_present": all(row["has_answer_contract"] for row in records),
        "generation_prompt_present": all(row["has_generation_prompt"] for row in records),
        "all_prompts_within_configured_limit": all(
            row["within_max_prompt_length"] for row in records
        ),
    }
    return records, checks


def build_audit(
    *,
    config_path: Path,
    manifest_path: Path,
    model_path: Path,
) -> dict[str, Any]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    data = config["data"]
    configured_prompt = Path(str(data["format_prompt"])).resolve()
    format_prompt = configured_prompt.read_text(encoding="utf-8")
    rows = _read_rows(manifest_path, 8)
    from transformers import AutoProcessor

    processor = AutoProcessor.from_pretrained(
        model_path,
        trust_remote_code=True,
        local_files_only=True,
    )
    records, checks = audit_rendered_rows(
        processor=processor,
        rows=rows,
        format_prompt=format_prompt,
        min_pixels=data.get("min_pixels"),
        max_pixels=data.get("max_pixels"),
        max_prompt_length=int(data["max_prompt_length"]),
    )
    config_checks = {
        "config_uses_problem_prompt_key": data.get("prompt_key") == "problem",
        "config_uses_images_key": data.get("image_key") == "images",
        "config_format_prompt_exists": configured_prompt.is_file(),
        "config_has_no_chat_template_override": data.get("override_chat_template") is None,
    }
    checks = {**config_checks, **checks}
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "config": str(config_path),
        "config_sha256": _sha256(config_path),
        "source_manifest": str(manifest_path),
        "source_manifest_sha256": _sha256(manifest_path),
        "model_path": str(model_path),
        "format_prompt": str(configured_prompt),
        "format_prompt_sha256": _sha256(configured_prompt),
        "processor_chat_template_sha256": hashlib.sha256(
            str(processor.chat_template).encode("utf-8")
        ).hexdigest(),
        "max_prompt_length": int(data["max_prompt_length"]),
        "min_pixels": data.get("min_pixels"),
        "max_pixels": data.get("max_pixels"),
        "rows": records,
    }


def render_report(payload: dict[str, Any], machine_path: Path) -> str:
    if payload.get("status") != "pass":
        raise ValueError("refusing to publish chat-template report from failed checks")
    train = [row for row in payload["rows"] if row["split"] == "train"]
    test = [row for row in payload["rows"] if row["split"] == "test"]
    lines = [
        "# GRPO Chat Template Audit V2",
        "",
        "Status:",
        "- `pass` for the dedicated 8-train/8-test rendered-prompt audit.",
        "- This is an implementation audit, not a published-reproduction or PI gate verdict.",
        "- The predecessor `reports/grpo_chat_template_audit.md` remains unchanged and is superseded by this version.",
        "",
        "Evidence:",
        f"- Machine artifact: `{machine_path}`; all `{len(payload['checks'])}` checks true.",
        f"- Config SHA256: `{payload['config_sha256']}`.",
        f"- Source manifest SHA256: `{payload['source_manifest_sha256']}`.",
        f"- r1v format prompt SHA256: `{payload['format_prompt_sha256']}`.",
        f"- Qwen processor chat-template SHA256: `{payload['processor_chat_template_sha256']}`.",
        f"- Prompt-token ranges: train `{min(row['prompt_tokens'] for row in train)}-{max(row['prompt_tokens'] for row in train)}`; test `{min(row['prompt_tokens'] for row in test)}-{max(row['prompt_tokens'] for row in test)}`; configured maximum `{payload['max_prompt_length']}`.",
        "- Every source image has exactly one rendered Qwen vision marker, and every prompt contains the registered think/answer contract plus assistant generation prompt.",
        "",
        "Problems:",
        "- This sample proves deterministic rendering and contract wiring for 16 fixed rows; the full-corpus image-grid audit is reported separately in `reports/easyr1_image_grid_audit_v1.md`.",
        "- Prompt rendering does not establish reward-parser equivalence; `reports/parser_agreement_audit_v2.md` retains the below-0.95 native/canonical warning.",
        "",
        "Decision:",
        "- Pin the resolved r1v and Qwen chat-template hashes for the engineering anchor and pilot configs.",
        "- Treat any future template/hash change as a new evaluation contract.",
        "",
        "Next actions:",
        "- Stamp both hashes in future training/evaluation manifests and retain rendered samples for any new model family.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    for output in (args.output_json, args.output_md):
        if output.exists():
            raise FileExistsError(f"refusing to overwrite chat-template audit: {output}")
    payload = build_audit(
        config_path=args.config,
        manifest_path=args.manifest,
        model_path=args.model_path,
    )
    if payload["status"] != "pass":
        raise RuntimeError(json.dumps(payload["checks"], sort_keys=True))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output_json.with_name(f".{args.output_json.name}.partial.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, args.output_json)
    args.output_md.write_text(render_report(payload, args.output_json), encoding="utf-8")
    print(args.output_md)


if __name__ == "__main__":
    main()
