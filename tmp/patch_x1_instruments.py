#!/usr/bin/env python3
"""Extend the ranking scorer, cell launcher, and open-form evaluator with the
two registered X1 image conditions (mismatched_real, twin_counterfactual) and
script-level no-image open-form support. Existing condition code paths are
byte-identical; SCORER_VERSION is unchanged."""
from pathlib import Path
import sys

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")

PATCHES = [
    # --- ranking scorer -----------------------------------------------------
    (
        ROOT / "scripts/eval_qwen_vl_visual_evidence_ranking.py",
        'CONDITIONS = {"real", "gray", "no_image"}\n',
        'CONDITIONS = {"real", "gray", "no_image", "mismatched_real", "twin_counterfactual"}\n'
        "\n"
        "\n"
        "def select_source_image(\n"
        "    row: dict[str, Any],\n"
        "    side: str,\n"
        "    condition: str,\n"
        "    image_override: dict[str, Any] | None,\n"
        ") -> str:\n"
        '    if condition == "twin_counterfactual":\n'
        '        twin = "b" if side == "a" else "a"\n'
        '        return str(row[f"image_{twin}_path"])\n'
        '    if condition == "mismatched_real":\n'
        "        if image_override is None:\n"
        '            raise ValueError("mismatched_real requires an image override map")\n'
        '        entry = image_override["per_pair"][str(row["pair_id"])]\n'
        "        override_path = str(entry[side])\n"
        '        if override_path == str(row[f"image_{side}_path"]):\n'
        "            raise ValueError(\n"
        '                f"override equals own image for pair {row[\'pair_id\']}"\n'
        "            )\n"
        "        return override_path\n"
        '    return str(row[f"image_{side}_path"])\n',
    ),
    (
        ROOT / "scripts/eval_qwen_vl_visual_evidence_ranking.py",
        """    row: dict[str, Any],
    side: str,
    condition: str,
    cache_dir: Path,
    batch_size: int,
""",
        """    row: dict[str, Any],
    side: str,
    condition: str,
    image_override: dict[str, Any] | None,
    cache_dir: Path,
    batch_size: int,
""",
    ),
    (
        ROOT / "scripts/eval_qwen_vl_visual_evidence_ranking.py",
        """    source_image = _resolve(str(row[f"image_{side}_path"]))
    if condition == "real":
        image_path = str(source_image)
""",
        """    source_image = _resolve(select_source_image(row, side, condition, image_override))
    if condition in {"real", "mismatched_real", "twin_counterfactual"}:
        image_path = str(source_image)
""",
    ),
    (
        ROOT / "scripts/eval_qwen_vl_visual_evidence_ranking.py",
        """    parser.add_argument("--condition", choices=sorted(CONDITIONS), required=True)
    parser.add_argument("--output", required=True)
""",
        """    parser.add_argument("--condition", choices=sorted(CONDITIONS), required=True)
    parser.add_argument("--image-override-map", default=None)
    parser.add_argument("--output", required=True)
""",
    ),
    (
        ROOT / "scripts/eval_qwen_vl_visual_evidence_ranking.py",
        """    config_path = _resolve(args.config)
    config = json.loads(config_path.read_text(encoding="utf-8"))
""",
        """    config_path = _resolve(args.config)
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
""",
    ),
    (
        ROOT / "scripts/eval_qwen_vl_visual_evidence_ranking.py",
        """                side="a",
                condition=args.condition,
                cache_dir=cache_dir,
""",
        """                side="a",
                condition=args.condition,
                image_override=image_override,
                cache_dir=cache_dir,
""",
    ),
    (
        ROOT / "scripts/eval_qwen_vl_visual_evidence_ranking.py",
        """                side="b",
                condition=args.condition,
                cache_dir=cache_dir,
""",
        """                side="b",
                condition=args.condition,
                image_override=image_override,
                cache_dir=cache_dir,
""",
    ),
    (
        ROOT / "scripts/eval_qwen_vl_visual_evidence_ranking.py",
        """                "candidate_set_sha256": row["candidate_set_sha256"],
""",
        """                "candidate_set_sha256": row["candidate_set_sha256"],
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
""",
    ),
    # --- cell launcher ------------------------------------------------------
    (
        ROOT / "scripts/launch_visual_evidence_ranking_cell.sh",
        '[[ "${CONDITION}" =~ ^(real|gray|no_image)$ ]] || { echo "unsupported condition" >&2; exit 2; }\n',
        '[[ "${CONDITION}" =~ ^(real|gray|no_image|mismatched_real|twin_counterfactual)$ ]] || { echo "unsupported condition" >&2; exit 2; }\n',
    ),
    (
        ROOT / "scripts/launch_visual_evidence_ranking_cell.sh",
        'cat > "${RUN_DIR}/worker.sh" <<EOF\n',
        'OVERRIDE_ARG=""\n'
        'if [[ "${CONDITION}" == "mismatched_real" ]]; then\n'
        '  [[ -n "${RANKING_OVERRIDE_MAP:-}" && -f "${RANKING_OVERRIDE_MAP}" ]] || { echo "mismatched_real requires RANKING_OVERRIDE_MAP" >&2; exit 2; }\n'
        "  OVERRIDE_ARG=\"--image-override-map '${RANKING_OVERRIDE_MAP}'\"\n"
        "fi\n"
        'cat > "${RUN_DIR}/worker.sh" <<EOF\n',
    ),
    (
        ROOT / "scripts/launch_visual_evidence_ranking_cell.sh",
        "    --condition '${CONDITION}' \\\n",
        "    --condition '${CONDITION}' ${OVERRIDE_ARG} \\\n",
    ),
    # --- open-form evaluator ------------------------------------------------
    (
        ROOT / "scripts/eval_qwen_vl_fliptrack.py",
        'def main() -> None:\n',
        'def generate_text_only(model, processor, question: str, max_new_tokens: int) -> str:\n'
        "    messages = [\n"
        "        {\n"
        '            "role": "user",\n'
        '            "content": [\n'
        '                {"type": "text", "text": format_question(question)},\n'
        "            ],\n"
        "        }\n"
        "    ]\n"
        "    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)\n"
        '    inputs = processor(text=[text], padding=True, return_tensors="pt").to(model.device)\n'
        "    with torch.inference_mode():\n"
        "        out = model.generate(**inputs, do_sample=False, max_new_tokens=max_new_tokens)\n"
        '    out = out[:, inputs["input_ids"].shape[1] :]\n'
        "    return processor.batch_decode(out, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0].strip()\n"
        "\n"
        "\n"
        "def main() -> None:\n",
    ),
    (
        ROOT / "scripts/eval_qwen_vl_fliptrack.py",
        '    parser.add_argument("--image-mode", choices=IMAGE_MODES, default="real")\n',
        '    parser.add_argument(\n'
        '        "--image-mode",\n'
        '        choices=tuple(IMAGE_MODES) + ("no_image", "mismatched_real", "twin_counterfactual"),\n'
        '        default="real",\n'
        "    )\n"
        '    parser.add_argument("--image-override-map", default=None)\n',
    ),
    (
        ROOT / "scripts/eval_qwen_vl_fliptrack.py",
        "    set_seed(args.seed)\n",
        "    set_seed(args.seed)\n"
        "    image_override = None\n"
        "    image_override_sha256 = None\n"
        '    if args.image_mode == "mismatched_real":\n'
        "        if not args.image_override_map:\n"
        '            raise ValueError("mismatched_real requires --image-override-map")\n'
        "        override_path = Path(args.image_override_map)\n"
        "        import hashlib as _hashlib\n"
        "        image_override_sha256 = _hashlib.sha256(override_path.read_bytes()).hexdigest()\n"
        '        image_override = json.loads(override_path.read_text(encoding="utf-8"))\n'
        "    elif args.image_override_map:\n"
        '        raise ValueError("--image-override-map is only valid for mismatched_real")\n',
    ),
    (
        ROOT / "scripts/eval_qwen_vl_fliptrack.py",
        """            row["eval_image_mode"] = args.image_mode
            condition_key = str(row["pair_id"]) if args.image_mode == "noise" else None
            image_a = materialize_image(
                row["image_a_path"], args.image_mode, cache_dir, args.noise_seed, condition_key=condition_key
            )
            image_b = materialize_image(
                row["image_b_path"], args.image_mode, cache_dir, args.noise_seed, condition_key=condition_key
            )
            row["eval_image_a_path"] = image_a
            row["eval_image_b_path"] = image_b
            row["noise_pair_shared"] = args.image_mode == "noise"
            row["prediction_a"] = generate(model, processor, image_a, row["question"], args.max_new_tokens)
            row["prediction_b"] = generate(model, processor, image_b, row["question"], args.max_new_tokens)
""",
        """            row["eval_image_mode"] = args.image_mode
            source_a = row["image_a_path"]
            source_b = row["image_b_path"]
            materialize_mode = args.image_mode
            if args.image_mode == "twin_counterfactual":
                source_a, source_b = row["image_b_path"], row["image_a_path"]
                materialize_mode = "real"
            elif args.image_mode == "mismatched_real":
                entry = image_override["per_pair"][str(row["pair_id"])]
                if str(entry["a"]) == str(row["image_a_path"]) or str(entry["b"]) == str(row["image_b_path"]):
                    raise ValueError(f"override equals own image for pair {row['pair_id']}")
                source_a, source_b = entry["a"], entry["b"]
                row["mismatched_source_pair_id"] = entry["source_pair_id"]
                row["image_override_map_sha256"] = image_override_sha256
                materialize_mode = "real"
            if args.image_mode == "no_image":
                row["eval_image_a_path"] = None
                row["eval_image_b_path"] = None
                row["noise_pair_shared"] = False
                row["prediction_a"] = generate_text_only(model, processor, row["question"], args.max_new_tokens)
                row["prediction_b"] = generate_text_only(model, processor, row["question"], args.max_new_tokens)
            else:
                condition_key = str(row["pair_id"]) if materialize_mode == "noise" else None
                image_a = materialize_image(
                    source_a, materialize_mode, cache_dir, args.noise_seed, condition_key=condition_key
                )
                image_b = materialize_image(
                    source_b, materialize_mode, cache_dir, args.noise_seed, condition_key=condition_key
                )
                row["eval_image_a_path"] = image_a
                row["eval_image_b_path"] = image_b
                row["noise_pair_shared"] = materialize_mode == "noise"
                row["prediction_a"] = generate(model, processor, image_a, row["question"], args.max_new_tokens)
                row["prediction_b"] = generate(model, processor, image_b, row["question"], args.max_new_tokens)
""",
    ),
]


def main() -> int:
    for path, old, new in PATCHES:
        text = path.read_text(encoding="utf-8")
        if new in text:
            print(f"already patched: {path.name} ({old[:40]!r}...)")
            continue
        count = text.count(old)
        if count != 1:
            print(f"ABORT: {path.name}: expected 1 match, found {count} for {old[:60]!r}")
            return 1
        path.write_text(text.replace(old, new), encoding="utf-8")
        print(f"patched: {path.name} ({old[:40]!r}...)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
