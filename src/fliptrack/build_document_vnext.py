from __future__ import annotations

import argparse
import hashlib
import json
import random
import string
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from src.fliptrack.build_v02 import _font, _save_rendered_pair, write_contact_sheets
from src.fliptrack.schema import stable_id, write_jsonl


SCHEMA_VERSION = "blind-gains.document-vnext-calibration.v1"
TEMPLATE_ID = "dense_control_register_code_v01"
CODE_FIELDS = ("auth_code", "batch_code", "route_code")
FIELD_LABELS = {
    "auth_code": "AUTH",
    "batch_code": "BATCH",
    "route_code": "ROUTE",
}
CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _unique_code(rng: random.Random, used: set[str]) -> str:
    while True:
        value = "".join(rng.choice(CODE_CHARS) for _ in range(5))
        if value not in used:
            used.add(value)
            return value


def _replacement_code(rng: random.Random, source: str, used: set[str]) -> str:
    positions = list(range(len(source)))
    rng.shuffle(positions)
    for position in positions:
        choices = [character for character in CODE_CHARS if character != source[position]]
        rng.shuffle(choices)
        for character in choices:
            candidate = source[:position] + character + source[position + 1 :]
            if candidate not in used:
                return candidate
    raise RuntimeError(f"could not create a unique one-character counterfactual for {source}")


def _render_register(records: list[dict[str, str]]) -> Image.Image:
    width, height = 1600, 1120
    image = Image.new("RGB", (width, height), (244, 246, 245))
    draw = ImageDraw.Draw(image)
    draw.rectangle((28, 26, width - 28, height - 26), fill="white", outline=(168, 172, 174), width=2)
    draw.text(
        (width // 2, 58),
        "Regional Dispatch Control Register",
        anchor="mm",
        font=_font(25, True),
        fill=(24, 27, 29),
    )
    draw.text(
        (48, 96),
        "Cycle 11 / Sheet 04     Internal verification copy     Read across by record ID and field header",
        font=_font(14),
        fill=(66, 70, 74),
    )

    left, top = 44, 142
    row_height = 46
    widths = [210, 112, 146, 146, 146, 164, 486]
    headers = ["RECORD ID", "ZONE", "AUTH", "BATCH", "ROUTE", "STATUS", "REFERENCE NOTE"]
    keys = ["record_id", "zone", "auth_code", "batch_code", "route_code", "status", "note"]
    x_positions = [left]
    for cell_width in widths:
        x_positions.append(x_positions[-1] + cell_width)

    draw.rectangle(
        (x_positions[2], top - 34, x_positions[5], top),
        fill=(211, 218, 223),
        outline=(105, 111, 116),
        width=1,
    )
    draw.text(
        ((x_positions[2] + x_positions[5]) // 2, top - 17),
        "CONTROL CODES",
        anchor="mm",
        font=_font(13, True),
        fill=(34, 38, 41),
    )
    for column, header in enumerate(headers):
        draw.rectangle(
            (x_positions[column], top, x_positions[column + 1], top + row_height),
            fill=(222, 227, 231),
            outline=(105, 111, 116),
            width=1,
        )
        draw.text(
            ((x_positions[column] + x_positions[column + 1]) // 2, top + row_height // 2),
            header,
            anchor="mm",
            font=_font(13, True),
            fill=(28, 31, 34),
        )

    for row_index, record in enumerate(records):
        y0 = top + (row_index + 1) * row_height
        fill = (252, 253, 253) if row_index % 2 == 0 else (239, 243, 245)
        for column, key in enumerate(keys):
            draw.rectangle(
                (x_positions[column], y0, x_positions[column + 1], y0 + row_height),
                fill=fill,
                outline=(151, 155, 158),
                width=1,
            )
            anchor = "lm" if key == "note" else "mm"
            x = x_positions[column] + 12 if key == "note" else (
                x_positions[column] + x_positions[column + 1]
            ) // 2
            draw.text(
                (x, y0 + row_height // 2),
                record[key],
                anchor=anchor,
                font=_font(14, key in {"record_id", *CODE_FIELDS}),
                fill=(20, 23, 25),
            )
    draw.text(
        (48, 1048),
        "Codes are independent fields. Similar strings in adjacent rows are not cross-references.",
        font=_font(13),
        fill=(72, 76, 80),
    )
    return image


def generate_document_vnext_pairs(
    out_dir: Path, n_pairs: int, seed: int
) -> list[dict[str, Any]]:
    rows = []
    statuses = ("READY", "HOLD", "VERIFY", "ROUTED")
    notes = (
        "dock scan matched manifest",
        "manual seal review logged",
        "secondary routing check",
        "carrier handoff recorded",
        "weight variance cleared",
        "dispatch window confirmed",
    )
    for index in range(n_pairs):
        pair_seed = seed + index * 104729
        rng = random.Random(pair_seed)
        used_codes: set[str] = set()
        record_ids = rng.sample(range(10000, 99999), 18)
        records_a = [
            {
                "record_id": f"RC-{record_id}-{rng.choice(string.ascii_uppercase)}",
                "zone": f"Z-{rng.randint(1, 28):02d}",
                "auth_code": _unique_code(rng, used_codes),
                "batch_code": _unique_code(rng, used_codes),
                "route_code": _unique_code(rng, used_codes),
                "status": rng.choice(statuses),
                "note": rng.choice(notes),
            }
            for record_id in record_ids
        ]
        target_row = rng.randrange(len(records_a))
        target_field = rng.choice(CODE_FIELDS)
        records_b = [dict(record) for record in records_a]
        answer_a = records_a[target_row][target_field]
        answer_b = _replacement_code(rng, answer_a, used_codes)
        records_b[target_row][target_field] = answer_b
        record_id = records_a[target_row]["record_id"]
        pair_id = "doc_vnext_" + stable_id(
            pair_seed, record_id, target_field, answer_a, answer_b
        )
        rows.append(
            _save_rendered_pair(
                out_dir=out_dir,
                pair_id=pair_id,
                image_a=_render_register(records_a),
                image_b=_render_register(records_b),
                question=(
                    f"In the row for record {record_id}, what is the "
                    f"{FIELD_LABELS[target_field]} code?"
                ),
                answer_a=answer_a,
                answer_b=answer_b,
                category="document_dense_row_column_binding",
                template_id=TEMPLATE_ID,
                provenance={
                    "generator": "src.fliptrack.build_document_vnext",
                    "pair_seed": pair_seed,
                    "visual_operation": "record_id_localization_then_code_header_binding",
                    "calibration_round": "L11-one-shot-v1",
                    "selection_applied": False,
                    "regeneration_applied": False,
                },
                verifier_results={
                    "exact_by_construction": True,
                    "row_count": len(records_a),
                    "target_row": target_row,
                    "target_field": target_field,
                    "target_record_id": record_id,
                    "target_row_highlighted": False,
                    "target_cell_highlighted": False,
                    "answer_hamming_distance": 1,
                    "only_semantic_change": "one character in one target code",
                },
                swap_sides=rng.random() < 0.5,
            )
        )
    return rows


def build_declared_batch(
    *,
    config_path: Path,
    out_dir: Path,
    manifest_path: Path,
    contact_sheet_dir: Path,
    metadata_path: Path,
) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported document calibration config")
    if config.get("template_id") != TEMPLATE_ID:
        raise ValueError("document calibration template ID drift")
    n_pairs = int(config["n_pairs"])
    seed = int(config["seed"])
    if n_pairs != 100:
        raise ValueError("L11 calibration requires exactly one declared 100-pair batch")
    for path in (out_dir, manifest_path, contact_sheet_dir, metadata_path):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite declared document calibration artifact: {path}")
    rows = generate_document_vnext_pairs(out_dir, n_pairs, seed)
    write_jsonl(manifest_path, rows)
    sheets = write_contact_sheets(rows, contact_sheet_dir, n_per_template=20)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": "pass",
        "n_pairs": len(rows),
        "seed": seed,
        "template_id": TEMPLATE_ID,
        "selection_applied": False,
        "regeneration_applied": False,
        "threshold_change_applied": False,
        "iteration_policy": config["iteration_policy"],
        "target_7b_real_pair_accuracy": config["target_7b_real_pair_accuracy"],
        "evaluation_cells": config["evaluation_cells"],
        "config": str(config_path),
        "config_sha256": _sha256(config_path),
        "manifest": str(manifest_path),
        "manifest_sha256": _sha256(manifest_path),
        "contact_sheets": [str(path) for path in sheets],
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/data/fliptrack_document_vnext_calibration_v1.json"),
    )
    parser.add_argument(
        "--out-dir", type=Path, default=Path("data/fliptrack_document_vnext_calibration_source")
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/fliptrack_document_vnext_calibration_manifest.jsonl"),
    )
    parser.add_argument(
        "--contact-sheet-dir",
        type=Path,
        default=Path("reports/contact_sheets/fliptrack_document_vnext_calibration"),
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=Path("data/fliptrack_document_vnext_calibration.json"),
    )
    args = parser.parse_args()
    payload = build_declared_batch(
        config_path=args.config,
        out_dir=args.out_dir,
        manifest_path=args.manifest,
        contact_sheet_dir=args.contact_sheet_dir,
        metadata_path=args.metadata,
    )
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
