#!/usr/bin/env python3
"""X1 open-form truncation guard (docs/EXPERIMENT_TODO.md, X1 ADDED clause).

Per open-form condition, sample 50 items deterministically (10 per model,
sorted by pair_id, seed 20260724), tokenize both member predictions with the
frozen base processor tokenizer, and flag a row truncated when either side
reaches the 32-token cap without closing the answer contract. Any condition
with > 0.5% truncated rows triggers a full 128-token version-superseding
rerun of every open-form cell.
"""
from __future__ import annotations

import datetime as dt
import glob
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
CONDITIONS = ("real", "gray", "no_image", "mismatched_real", "twin_counterfactual")
MODELS = ("base", "a1_step100", "a2_step100", "a2b_step100", "a3_step100")
CAP = 32
SEED = 20260724
PER_MODEL = 10
OUTPUT = ROOT / "reports/x1_openform_truncation_guard_v1.json"

from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained(
    str(ROOT / "artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct"), trust_remote_code=True
)


def cell_rows(model: str, condition: str) -> list[dict]:
    pattern = str(
        ROOT / f"experiments/runs/x1_openform_{model}_{condition}_an12_*/run_manifest.json"
    )
    for manifest_path in sorted(glob.glob(pattern)):
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        if manifest.get("status") == "complete" and manifest.get("exit_code") == 0:
            predictions = Path(manifest_path).parent / "predictions.jsonl"
            return [
                json.loads(line)
                for line in predictions.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
    raise RuntimeError(f"no complete cell for {model}/{condition}")


def truncated(prediction: str) -> tuple[bool, int]:
    tokens = len(tokenizer(prediction, add_special_tokens=False).input_ids)
    return (tokens >= CAP and "</answer>" not in prediction), tokens


rng = np.random.default_rng(SEED)
result: dict = {
    "schema_version": "blind-gains.x1-openform-truncation-guard.v1",
    "cap_tokens": CAP,
    "sample_per_condition": PER_MODEL * len(MODELS),
    "seed": SEED,
    "threshold_fraction": 0.005,
    "checked_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "conditions": {},
}
any_trigger = False
for condition in CONDITIONS:
    rows_flagged = 0
    max_tokens_seen = 0
    sampled = 0
    examples: list[dict] = []
    for model in MODELS:
        rows = sorted(cell_rows(model, condition), key=lambda r: str(r["pair_id"]))
        indices = rng.choice(len(rows), size=PER_MODEL, replace=False)
        for index in sorted(int(i) for i in indices):
            row = rows[index]
            flag_a, tokens_a = truncated(str(row["prediction_a"]))
            flag_b, tokens_b = truncated(str(row["prediction_b"]))
            max_tokens_seen = max(max_tokens_seen, tokens_a, tokens_b)
            sampled += 1
            if flag_a or flag_b:
                rows_flagged += 1
                if len(examples) < 5:
                    examples.append(
                        {
                            "model": model,
                            "pair_id": row["pair_id"],
                            "tokens_a": tokens_a,
                            "tokens_b": tokens_b,
                        }
                    )
    fraction = rows_flagged / sampled
    trigger = fraction > 0.005
    any_trigger = any_trigger or trigger
    result["conditions"][condition] = {
        "sampled_rows": sampled,
        "truncated_rows": rows_flagged,
        "truncated_fraction": fraction,
        "max_emitted_tokens_seen": max_tokens_seen,
        "trigger_128_rerun": trigger,
        "examples": examples,
    }

result["any_condition_triggers_rerun"] = any_trigger
result["verdict"] = (
    "rerun_all_openform_cells_at_128_tokens_version_superseding"
    if any_trigger
    else "32_token_budget_stands"
)
OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
print(json.dumps({"verdict": result["verdict"], "output_sha256": digest,
                  "per_condition": {c: v["truncated_rows"] for c, v in result["conditions"].items()}}))
