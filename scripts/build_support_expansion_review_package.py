#!/usr/bin/env python3
"""Build the portable 24-candidate support-expansion review package.

Packages the qualitative window on the M10 seed-1 support-sharpening readout:
every item classified `high-confidence support-expansion candidate` in
`reports/support_sharpening_seed1_v2.json` (0/16 base samples, 0/64 registered
follow-up draws, step-100 greedy correct), with the question, the image, the
base's 16 sampled answers, the trained arm's step-100 answer, and the gold
answer. Selection is exhaustive over the 24 qualifying items; no RNG is used.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_human_audit_bundle import (
    _jsonl_bytes,
    _write_bytes,
    _write_deterministic_zip,
    read_jsonl,
    sha256_file,
)
from src.rewards.answer_reward import extract_answer_span

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "blind-gains.support-expansion-review-bundle.v1"
CLASSIFICATION = "high-confidence support-expansion candidate"
ARMS = ("a1_real", "a2_gray", "a2b_noimage", "a3_caption")
EXPECTED_ARM_COUNTS = {"a1_real": 16, "a2_gray": 1, "a2b_noimage": 5, "a3_caption": 2}
ARM_LABELS = {
    "a1_real": "A1 real",
    "a2_gray": "A2 gray",
    "a2b_noimage": "A2b no-image",
    "a3_caption": "A3 caption",
}
CONDITION_NOTES = {
    "real": "the real image was shown",
    "gray": "a gray placeholder replaced the image",
    "none": "no image token was given at all",
    "caption": "a question-blind caption replaced the image",
}

READOUT_PATH = "reports/support_sharpening_seed1_v2.json"
EXEC_CONFIG_PATH = "configs/eval/support_sharpening_v2.json"
READOUT_MANIFEST_PATH = "experiments/manifests/pilot_4arm_seed1_readout_v2.json"
IMAGES_MANIFEST_PATH = "data/geometry3k_caption_images_manifest.jsonl"
GUIDE_PATH = "docs/SUPPORT_EXPANSION_REVIEW_GUIDE.md"

STEP100_AUDITS = {
    "a1_real": "experiments/runs/pilot_geo3k_step100_audit_m2_geo3k_a1_real_seed1_step100_an12_gpu4_20260715T210056Z_20260715T211733Z/audit.json",
    "a2_gray": "experiments/runs/pilot_geo3k_step100_audit_m2_geo3k_a2_gray_seed1_step100_an12_gpu4_20260716T155345Z_20260716T161002Z/audit.json",
    "a2b_noimage": "experiments/runs/pilot_geo3k_step100_audit_m2_geo3k_a2b_noimage_seed1_step100_an12_gpu5_20260715T210056Z_20260715T211906Z/audit.json",
    "a3_caption": "experiments/runs/pilot_geo3k_step100_audit_m2_geo3k_a3_caption_seed1_step100_an12_gpu6_20260715T210056Z_20260715T212255Z/audit.json",
}

VERDICT_VALUES = ("genuine_solve", "guess", "artifact", "unclear")
LEGIBLE_VALUES = ("pass", "fail")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _stream_rows(path: Path, wanted: set[tuple[str, int]]) -> dict[tuple[str, int], dict[str, Any]]:
    """Stream a per-item JSONL file, keeping only rows keyed by (split, row_index)."""
    found: dict[tuple[str, int], dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            key = (str(row.get("split")), int(row.get("row_index")))
            if key in wanted:
                if key in found:
                    raise ValueError(f"duplicate (split,row_index) {key} in {path}")
                found[key] = row
    missing = wanted - set(found)
    if missing:
        raise ValueError(f"{path} is missing rows: {sorted(missing)}")
    return found


def _display_answer(text: str) -> dict[str, Any]:
    span = extract_answer_span(text)
    display = span.span.strip()
    if len(display) > 160:
        display = display[:157] + "..."
    return {
        "display": display,
        "extraction_level": span.extraction_level,
        "extractor_valid": span.extractor_valid,
    }


def collect_items() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    readout = _load_json(ROOT / READOUT_PATH)
    exec_config = _load_json(ROOT / EXEC_CONFIG_PATH)
    manifest = _load_json(ROOT / READOUT_MANIFEST_PATH)

    source_sha256: dict[str, str] = {
        "support_sharpening_readout": sha256_file(ROOT / READOUT_PATH),
        "support_sharpening_exec_config": sha256_file(ROOT / EXEC_CONFIG_PATH),
        "pilot_readout_manifest": sha256_file(ROOT / READOUT_MANIFEST_PATH),
        "geometry3k_images_manifest": sha256_file(ROOT / IMAGES_MANIFEST_PATH),
    }
    source_paths: dict[str, str] = {
        "support_sharpening_readout": READOUT_PATH,
        "support_sharpening_exec_config": EXEC_CONFIG_PATH,
        "pilot_readout_manifest": READOUT_MANIFEST_PATH,
        "geometry3k_images_manifest": IMAGES_MANIFEST_PATH,
    }

    image_index: dict[tuple[str, int], dict[str, str]] = {}
    for row in read_jsonl(ROOT / IMAGES_MANIFEST_PATH):
        key = (str(row["split"]), int(row["row_index"]))
        images = row.get("images")
        if not isinstance(images, list) or len(images) != 1:
            raise ValueError(f"images manifest row {key} must reference exactly one image")
        image_index[key] = {"path": images[0]["path"], "sha256": images[0]["sha256"]}

    items: list[dict[str, Any]] = []
    per_arm_provenance: dict[str, Any] = {}
    for arm in ARMS:
        arm_record = readout["arms"][arm]
        condition = str(arm_record["condition"])
        flagged = [
            row for row in arm_record["items"] if row["classification"] == CLASSIFICATION
        ]
        if len(flagged) != EXPECTED_ARM_COUNTS[arm]:
            raise ValueError(
                f"{arm}: expected {EXPECTED_ARM_COUNTS[arm]} {CLASSIFICATION} items, "
                f"found {len(flagged)}"
            )

        candidate_record = exec_config["arms"][arm]
        candidate_path = ROOT / candidate_record["candidate_path"]
        found_sha = sha256_file(candidate_path)
        if found_sha != candidate_record["candidate_sha256"]:
            raise ValueError(f"candidate hash mismatch for {arm}")
        candidates = {
            row["source_item_fingerprint"]: row for row in read_jsonl(candidate_path)
        }

        baseline_rel = manifest["geo_baselines"][arm]
        audit_rel = STEP100_AUDITS[arm]
        audit = _load_json(ROOT / audit_rel)
        step100_path = Path(audit["output"])
        if not step100_path.is_absolute():
            step100_path = ROOT / step100_path
        step100_sha = sha256_file(step100_path)
        if step100_sha != audit["output_sha256"]:
            raise ValueError(f"step-100 per-item hash mismatch for {arm}")

        wanted = {(str(row["split"]), int(row["row_index"])) for row in flagged}
        baseline_rows = _stream_rows(ROOT / baseline_rel, wanted)
        step100_rows = _stream_rows(step100_path, wanted)

        per_arm_provenance[arm] = {
            "condition": condition,
            "candidate_path": candidate_record["candidate_path"],
            "candidate_sha256": found_sha,
            "baseline_per_item": baseline_rel,
            "baseline_per_item_sha256": sha256_file(ROOT / baseline_rel),
            "step100_audit": audit_rel,
            "step100_audit_sha256": sha256_file(ROOT / audit_rel),
            "step100_per_item": str(step100_path.relative_to(ROOT)),
            "step100_per_item_sha256": step100_sha,
        }

        for flagged_row in sorted(flagged, key=lambda row: (row["split"], row["row_index"])):
            fingerprint = flagged_row["source_item_fingerprint"]
            candidate = candidates.get(fingerprint)
            if candidate is None:
                raise ValueError(f"{arm}: no candidate row for fingerprint {fingerprint}")
            key = (str(flagged_row["split"]), int(flagged_row["row_index"]))
            if (str(candidate["split"]), int(candidate["row_index"])) != key:
                raise ValueError(f"{arm}: candidate/readout identity mismatch at {key}")
            base = baseline_rows[key]
            trained = step100_rows[key]

            gold = str(candidate["ground_truth"])
            if str(base["ground_truth"]) != gold or str(trained["ground_truth"]) != gold:
                raise ValueError(f"{arm}: ground-truth mismatch at {key}")
            if str(base.get("condition")) != condition:
                raise ValueError(f"{arm}: baseline condition mismatch at {key}")
            if int(base["sample_count"]) != 16 or int(base["sample_correct_count"]) != 0:
                raise ValueError(f"{arm}: baseline is not 0-of-16 at {key}")
            if int(flagged_row["extra_correct_count"]) != 0:
                raise ValueError(f"{arm}: follow-up draws are not 0-of-64 at {key}")
            if trained.get("acc_final") is not True or int(trained["global_step"]) != 100:
                raise ValueError(f"{arm}: step-100 greedy is not recorded correct at {key}")
            image_ref = image_index.get(key)
            if image_ref is None:
                raise ValueError(f"{arm}: no image manifest row at {key}")
            if candidate["image_sha256"] != [image_ref["sha256"]] or base["image_sha256"] != [
                image_ref["sha256"]
            ]:
                raise ValueError(f"{arm}: image hash mismatch at {key}")

            sampled_responses = base["sampled_responses"]
            sampled_correct = base["sampled_canonical_correct"]
            if len(sampled_responses) != 16 or len(sampled_correct) != 16:
                raise ValueError(f"{arm}: expected 16 base samples at {key}")
            if any(bool(flag) for flag in sampled_correct):
                raise ValueError(f"{arm}: a base sample is recorded correct at {key}")

            problem = str(candidate["problem"])
            items.append(
                {
                    "item_id": f"{arm}_{key[0]}_{key[1]:04d}",
                    "arm": arm,
                    "arm_label": ARM_LABELS[arm],
                    "condition": condition,
                    "condition_note": CONDITION_NOTES[condition],
                    "split": key[0],
                    "row_index": key[1],
                    "source_item_fingerprint": fingerprint,
                    "question": problem,
                    "question_display": problem.replace("<image>", "", 1).strip(),
                    "ground_truth": gold,
                    "image": {
                        "source_path": image_ref["path"],
                        "sha256": image_ref["sha256"],
                        "package_path": f"images/{image_ref['sha256'][:16]}.png",
                    },
                    "base_step0": {
                        "greedy_response": base["greedy_response"],
                        "greedy_answer": _display_answer(base["greedy_response"]),
                        "greedy_canonical_correct": bool(base["greedy_canonical_correct"]),
                        "sampled_answers": [
                            {
                                "sample_index": index,
                                "answer": _display_answer(response),
                                "canonical_correct": bool(correct),
                                "response": response,
                            }
                            for index, (response, correct) in enumerate(
                                zip(sampled_responses, sampled_correct)
                            )
                        ],
                        "sample_correct_count": 0,
                        "sample_count": 16,
                    },
                    "trained_step100": {
                        "greedy_response": trained["greedy_response"],
                        "extracted_answer": trained["extracted_answer"],
                        "acc_final": True,
                        "global_step": 100,
                    },
                    "followup_draws": {
                        "extra_sample_count": int(flagged_row["extra_sample_count"]),
                        "extra_correct_count": 0,
                        "total_sample_count": int(flagged_row["total_sample_count"]),
                        "total_correct_count": int(flagged_row["total_correct_count"]),
                        "jeffreys_ci95": flagged_row["jeffreys_ci95"],
                    },
                    "classification": CLASSIFICATION,
                    "registered_language": flagged_row["registered_language"],
                    "causal_capability_claim_permitted": False,
                    "selection_rule": candidate["selection_rule"],
                }
            )

    if len(items) != 24:
        raise ValueError(f"expected 24 items, assembled {len(items)}")
    provenance = {
        "paths": source_paths,
        "sha256": source_sha256,
        "arms": per_arm_provenance,
    }
    return items, provenance


def response_sheet_csv(items: list[dict[str, Any]]) -> str:
    lines = ["item_id,arm,condition,split,row_index,trained_answer_verdict,item_legible,note"]
    for item in items:
        lines.append(
            f"{item['item_id']},{item['arm']},{item['condition']},{item['split']},"
            f"{item['row_index']},,,"
        )
    return "\n".join(lines) + "\n"


def _answer_chip(sample: dict[str, Any]) -> str:
    answer = html.escape(sample["answer"]["display"])
    body = html.escape(sample["response"])
    return (
        f"<details class=\"sample\"><summary><span class=\"chip wrong\">"
        f"{sample['sample_index'] + 1}</span> {answer}</summary>"
        f"<pre>{body}</pre></details>"
    )


def render_viewer(items: list[dict[str, Any]]) -> str:
    arm_counts: dict[str, int] = {}
    for item in items:
        arm_counts[item["arm_label"]] = arm_counts.get(item["arm_label"], 0) + 1
    summary = " · ".join(f"{label} {count}" for label, count in arm_counts.items())

    nav_entries = []
    cards = []
    for position, item in enumerate(items, start=1):
        anchor = html.escape(item["item_id"])
        nav_entries.append(
            f"<a href=\"#{anchor}\"><span class=\"navnum\">{position:02d}</span> "
            f"{anchor} <span class=\"navarm\">{html.escape(item['arm_label'])}</span></a>"
        )
        trained = item["trained_step100"]
        base = item["base_step0"]
        chips = "\n".join(_answer_chip(sample) for sample in base["sampled_answers"])
        follow = item["followup_draws"]
        ci = follow["jeffreys_ci95"]
        cards.append(f"""
<section class="card" id="{anchor}">
  <header>
    <h2>{position:02d} / 24 &mdash; <code>{anchor}</code></h2>
    <span class="badge">{html.escape(item['arm_label'])}</span>
    <span class="meta">condition: {html.escape(item['condition'])} &mdash; {html.escape(item['condition_note'])}</span>
    <span class="meta">geo3k {html.escape(item['split'])} row {item['row_index']}</span>
  </header>
  <p class="question">{html.escape(item['question_display'])}</p>
  <p class="mathnote">Math notation is shown as raw LaTeX source; read it as written.</p>
  <div class="itembody">
    <figure>
      <a href="package/{html.escape(item['image']['package_path'])}" target="_blank" rel="noopener">
        <img src="package/{html.escape(item['image']['package_path'])}" alt="item image" loading="lazy">
      </a>
      <figcaption>Click the image to open it at full resolution.</figcaption>
    </figure>
    <div class="answers">
      <div class="row gold"><span class="label">Gold answer</span><span class="value">{html.escape(item['ground_truth'])}</span></div>
      <div class="row trained"><span class="label">Trained arm, step-100 greedy</span><span class="value correct">{html.escape(str(trained['extracted_answer']))}</span></div>
      <details class="fullresp"><summary>Full step-100 response</summary><pre>{html.escape(trained['greedy_response'])}</pre></details>
      <div class="row"><span class="label">Base greedy (step 0, same condition)</span><span class="value">{html.escape(base['greedy_answer']['display'])}</span></div>
      <details class="fullresp"><summary>Full base greedy response</summary><pre>{html.escape(base['greedy_response'])}</pre></details>
      <div class="row stats"><span class="label">Base sampled support</span><span class="value">0 / 16 correct; follow-up 0 / {follow['extra_sample_count']} registered draws; total 0 / {follow['total_sample_count']}; Jeffreys 95% [{ci[0]:.7f}, {ci[1]:.7f}]</span></div>
      <h3>Base's 16 sampled answers (temperature 1.0; every one recorded incorrect)</h3>
      <div class="samples">
{chips}
      </div>
    </div>
  </div>
</section>""")

    nav = "\n".join(nav_entries)
    body = "\n".join(cards)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Blind Gains Support-Expansion Candidate Review</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #1f2925; --muted: #5f6b66; --line: #cbd2ce; --surface: #ffffff;
      --canvas: #f3f5f3; --accent: #087f5b; --accent-dark: #056044;
      --danger: #b42318; --danger-soft: #fff1f0; --success: #157347;
      --success-soft: #edf8f2; --radius: 4px;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; background: var(--canvas); color: var(--ink); font-size: 15px;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
    }}
    .page {{ max-width: 1180px; margin: 0 auto; padding: 24px 20px 80px; }}
    h1 {{ font-size: 22px; margin: 0 0 4px; }}
    .subtitle {{ color: var(--muted); margin: 0 0 18px; }}
    .notice {{
      background: var(--surface); border: 1px solid var(--line); border-left: 4px solid var(--accent);
      border-radius: var(--radius); padding: 12px 16px; margin-bottom: 18px;
    }}
    nav.index {{
      background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius);
      padding: 12px 16px; margin-bottom: 24px; display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 4px 16px;
    }}
    nav.index a {{ color: var(--accent-dark); text-decoration: none; font-size: 13.5px; }}
    nav.index a:hover {{ text-decoration: underline; }}
    .navnum {{ color: var(--muted); font-variant-numeric: tabular-nums; }}
    .navarm {{ color: var(--muted); }}
    .card {{
      background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius);
      padding: 18px 20px; margin-bottom: 26px;
    }}
    .card header {{ display: flex; flex-wrap: wrap; align-items: baseline; gap: 10px; margin-bottom: 8px; }}
    .card h2 {{ font-size: 16px; margin: 0; }}
    .badge {{
      background: var(--accent); color: #fff; border-radius: var(--radius);
      padding: 2px 8px; font-size: 12.5px; font-weight: 650;
    }}
    .meta {{ color: var(--muted); font-size: 13px; }}
    .question {{ font-size: 15.5px; margin: 6px 0 2px; }}
    .mathnote {{ color: var(--muted); font-size: 12.5px; margin: 0 0 12px; }}
    .itembody {{ display: flex; flex-wrap: wrap; gap: 20px; }}
    figure {{ margin: 0; flex: 0 1 420px; }}
    figure img {{ max-width: 100%; border: 1px solid var(--line); border-radius: var(--radius); background: #fff; }}
    figcaption {{ color: var(--muted); font-size: 12.5px; margin-top: 4px; }}
    .answers {{ flex: 1 1 460px; min-width: 320px; }}
    .row {{ display: flex; gap: 10px; align-items: baseline; margin-bottom: 6px; }}
    .row .label {{ flex: 0 0 250px; color: var(--muted); font-size: 13px; }}
    .row .value {{ font-weight: 650; overflow-wrap: anywhere; }}
    .row.gold .value {{ color: var(--accent-dark); }}
    .value.correct {{ color: var(--success); }}
    .row.stats .value {{ font-weight: 400; font-size: 13.5px; }}
    h3 {{ font-size: 13.5px; margin: 14px 0 6px; color: var(--muted); font-weight: 650; }}
    .samples {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 6px; }}
    details.sample, details.fullresp {{
      border: 1px solid var(--line); border-radius: var(--radius); background: #fbfcfb; padding: 4px 8px;
    }}
    details.fullresp {{ margin: 2px 0 10px; }}
    details summary {{ cursor: pointer; font-size: 13.5px; overflow-wrap: anywhere; }}
    details pre {{
      white-space: pre-wrap; overflow-wrap: anywhere; font-size: 12.5px;
      background: #f6f8f7; border-radius: var(--radius); padding: 8px; margin: 6px 0 2px;
      max-height: 340px; overflow-y: auto;
    }}
    .chip {{
      display: inline-block; min-width: 22px; text-align: center; border-radius: var(--radius);
      font-size: 12px; font-weight: 650; padding: 1px 4px; margin-right: 4px;
    }}
    .chip.wrong {{ background: var(--danger-soft); color: var(--danger); }}
    code {{ font-size: 13px; }}
  </style>
</head>
<body>
<div class="page">
  <h1>Blind Gains Support-Expansion Candidate Review</h1>
  <p class="subtitle">24 conservative candidates &mdash; {summary}. Reviewer decisions go in <code>response_sheet.csv</code>; see <code>REVIEW_GUIDE.md</code>.</p>
  <div class="notice">
    Every item below is a geo3k test item where the frozen base produced <strong>0 correct answers in 16 samples</strong>
    under the arm's input condition and <strong>0 in 64 additional registered draws</strong>, while the trained arm's
    step-100 greedy answer is recorded correct. These are <em>support-expansion candidates</em> under the registered
    non-causal language; this review decides per-item whether the trained answer is a genuine solve, a guess, or an
    artifact, and whether the item is legible. No aggregate acceptance decision is made here.
  </div>
  <nav class="index">
{nav}
  </nav>
{body}
</div>
</body>
</html>
"""


def build_package(output_zip: Path, bundle_name: str) -> dict[str, Any]:
    if output_zip.exists():
        raise FileExistsError(f"refusing to overwrite bundle: {output_zip}")
    guide = ROOT / GUIDE_PATH
    if not guide.is_file():
        raise FileNotFoundError(guide)

    items, provenance = collect_items()
    provenance["paths"]["reviewer_guide"] = GUIDE_PATH
    provenance["sha256"]["reviewer_guide"] = sha256_file(guide)

    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="support_expansion_review_", dir=output_zip.parent
    ) as temporary:
        root = Path(temporary)
        _write_bytes(root, PurePosixPath("package/items.jsonl"), _jsonl_bytes(items))
        _write_bytes(
            root,
            PurePosixPath("support_expansion_viewer.html"),
            render_viewer(items).encode("utf-8"),
        )
        _write_bytes(
            root,
            PurePosixPath("response_sheet.csv"),
            response_sheet_csv(items).encode("utf-8"),
        )
        _write_bytes(root, PurePosixPath("REVIEW_GUIDE.md"), guide.read_bytes())

        copied: dict[str, str] = {}
        for item in items:
            package_path = item["image"]["package_path"]
            if package_path in copied:
                if copied[package_path] != item["image"]["sha256"]:
                    raise ValueError(f"conflicting hashes for {package_path}")
                continue
            source = ROOT / item["image"]["source_path"]
            data = source.read_bytes()
            if hashlib.sha256(data).hexdigest() != item["image"]["sha256"]:
                raise ValueError(f"image hash mismatch for {source}")
            _write_bytes(root, PurePosixPath("package") / package_path, data)
            copied[package_path] = item["image"]["sha256"]

        readme = f"""Blind Gains portable support-expansion review: {bundle_name}

1. Extract this ZIP on the reviewing computer.
2. Read REVIEW_GUIDE.md.
3. Open support_expansion_viewer.html in Chromium or Firefox.
4. Work through all 24 items in order; the index at the top links to each item.
5. For every item, record trained_answer_verdict and item_legible in response_sheet.csv,
   with a short note for anything that is not genuine_solve / pass.
6. Return the completed response_sheet.csv.

This package contains all 24 high-confidence support-expansion candidates from the
frozen M10 seed-1 readout (A1 real 16, A2 gray 1, A2b no-image 5, A3 caption 2).
Keep the package and the completed response sheet within the research team.
"""
        _write_bytes(root, PurePosixPath("README.txt"), readme.encode("utf-8"))

        file_hashes = {
            path.relative_to(root).as_posix(): sha256_file(path)
            for path in sorted(item for item in root.rglob("*") if item.is_file())
        }
        arm_counts = {arm: EXPECTED_ARM_COUNTS[arm] for arm in ARMS}
        metadata = {
            "schema_version": SCHEMA_VERSION,
            "selection": {
                "strategy": "all_high_confidence_support_expansion_candidates_in_seed1_v2_readout",
                "classification_filter": CLASSIFICATION,
                "rng": "none; selection is exhaustive over the 24 qualifying items",
                "ordering": "arm (a1_real, a2_gray, a2b_noimage, a3_caption), then split, then row_index",
                "item_count": len(items),
                "arm_counts": arm_counts,
                "item_ids": [item["item_id"] for item in items],
            },
            "review_contract": {
                "decisions_per_item": 2,
                "decision_ids": ["trained_answer_verdict", "item_legible"],
                "trained_answer_verdict_values": list(VERDICT_VALUES),
                "item_legible_values": list(LEGIBLE_VALUES),
                "response_sheet": "response_sheet.csv",
            },
            "registered_language": [
                "mass sharpening within observed support",
                "not observed in the base K-sample set",
            ],
            "causal_capability_claim_permitted": False,
            "source_paths": provenance["paths"],
            "source_sha256": provenance["sha256"],
            "arm_provenance": provenance["arms"],
            "copied_image_count": len(copied),
            "bundled_file_sha256": file_hashes,
        }
        _write_bytes(
            root,
            PurePosixPath("bundle_manifest.json"),
            (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        )
        _write_deterministic_zip(root, output_zip, bundle_name)

    return {
        "output_zip": str(output_zip.resolve()),
        "output_sha256": sha256_file(output_zip),
        "output_bytes": output_zip.stat().st_size,
        "item_count": len(items),
        "image_count": len(copied),
        "arm_counts": arm_counts,
        "source_sha256": provenance["sha256"],
        "arm_provenance": provenance["arms"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-zip",
        type=Path,
        default=ROOT / "reports/human_packages/blind_gains_support_expansion_24_review_20260804_v1.zip",
    )
    parser.add_argument(
        "--bundle-name", default="blind_gains_support_expansion_24_review_20260804_v1"
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=ROOT / "reports/support_expansion_review_bundle_v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_package(args.output_zip, args.bundle_name)
    report = {
        "schema_version": SCHEMA_VERSION,
        "status": "pass",
        "scientific_gate_decision": None,
        "human_review_outcome": "pending",
        **result,
    }
    if args.report_json.exists():
        raise FileExistsError(f"refusing to overwrite report: {args.report_json}")
    args.report_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
