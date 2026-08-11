#!/usr/bin/env python3
"""Registered Track-4 premise-v2 acceptance-gate readout: E1 (difficulty band) + E2 (blind floor).

Governing registration: docs/registered_track4_premise_v2_design_v1.md
  §7 "Acceptance gates (I14) - registered commands and pass criteria" (E1, E2)
  §5 "Easier premise variant - the difficulty lever" (registered branches a-d)
  §3 (fact_read carries no premise fields), §4 (both contracts reported, I7),
  §8 (declared batch composition: types, counts, n_points, template_id)

WHAT THIS INSTRUMENT IS
-----------------------
It reads six banked evaluation cells (three premise-probe cells and three
causal/final cells, at image modes real / gray / no_image), joins every
prediction row to its manifest row on the identity key `pair_id`, and reports
the registered E1 and E2 verdicts PER INTERVENTION TYPE, mechanically.

It reports numbers, the registered verdicts, and the section-5 branch the
registered rule fires (quoting the registration verbatim). It makes no
interpretation and decides nothing the registration leaves to the PI.

DISCIPLINE (binding)
--------------------
I7  Both scoring contracts (lenient `correct_*` / contract-strict
    `strict_correct_*`) are computed and reported separately for every cell and
    every intervention type. They are never merged, averaged, or reduced to one
    number. Where they disagree the disagreement is the reported result.
I13 Every endpoint is per intervention type. NOTHING is pooled across types
    anywhere in this output. Each cell's own `metrics.json` IS pooled across
    intervention types and is therefore NOT the registered endpoint; it is
    carried in provenance by sha256 only, with no value copied out of it.
I10 Adversarial fixtures (tests/test_build_track4_premise_v2_gate_readout.py)
    pass before this instrument is pointed at the real cells.
I15 `schema_version` at the top level of the JSON artifact.

SCORING SOURCE
--------------
The reported numbers come from the per-row verdict fields banked by
`scripts/eval_qwen_vl_fliptrack.py` (`correct_a/b`, `strict_correct_a/b`,
`pair_correct`, `strict_pair_correct`) -- the same cached-prediction discipline
`scripts/build_f2d_template_decomposition.py` uses. No proxy is ever
substituted: a row missing any required field is refused.

Those banked verdicts are then INDEPENDENTLY RE-DERIVED, row by row, with the
frozen repo scorer `src.eval.fliptrack_metrics.pair_score` under the locked
prompt contract (`src.eval.prompt_contract.DEFAULT_PROMPT_CONTRACT`,
contract_id `answer-tags-v1`), and any disagreement refuses the readout. This
is why the decoding lock is checked first: every row must carry
`prompt_contract_id == "answer-tags-v1"`, `prompt_contract_sha256` equal to the
repo contract's sha256, and `parser_version` equal to the repo
`PARSER_VERSION`. A cell scored under a different lock is refused rather than
re-scored under the current one.

`src.eval.fliptrack_metrics.aggregate_pair_metrics` IS reused, per intervention
type, as the authority on the registered accuracy convention: for every type it
is run over that type's own row subset and its `member_accuracy` /
`pair_accuracy` / `strict_member_accuracy` / `strict_pair_accuracy` must equal
the numbers this instrument derives from the banked verdicts, or the readout is
refused. The registered denominator (member accuracy over 2 x n_pairs) therefore
stays owned by the frozen repo module instead of being restated here.

`aggregate_pair_metrics_by_template` is the one function in that module that
does NOT fit: it groups by `template_id`, and in §8 two intervention types share
one template_id, so it would pool exactly the types I13 forbids pooling. The
grouping used here is `intervention_type`.

The scoring core of the module (`pair_score`, `golds_equivalent`) is reused
verbatim for the row-level cross-check and for the equal-gold classification.

REFUSALS (fail closed, all before any accuracy is reported)
-----------------------------------------------------------
  - a cell directory, predictions.jsonl or metrics.json missing/unreadable;
  - metrics.json `image_mode` or any row's `eval_image_mode` not the cell's
    registered mode, or not single-valued within the cell;
  - decoding lock not single-valued or not equal to the repo's frozen contract
    / parser version;
  - any required field absent or of the wrong type on any prediction row
    (including `intervention_type`), or absent on any manifest row;
  - duplicate `pair_id` in any cell or either manifest;
  - any prediction row whose `pair_id` is not in the manifest, or any manifest
    row with no prediction (join must be a bijection);
  - joined field disagreement (intervention_type, template_id, answer_a/b,
    difficulty_knobs.n_points);
  - a banked verdict that the frozen scorer does not reproduce;
  - an intervention type whose `difficulty_knobs.n_points` is missing or not
    single-valued (its E2 premise ceiling would be undefined);
  - an intervention type whose premise-probe rows mix equal-gold and
    differing-gold items (that would merge §4 `premise_stability` with §4
    `premise_transition_accuracy`, which I13 forbids);
  - a type present in the premise-probe manifest but absent from the causal
    manifest (its E2 final criterion would be unevaluable);
  - under `--expect registered` (the default), any deviation from the §8
    declared batch composition; `--expect any` exists for fixtures only;
  - the registration document missing, or any quoted criterion/branch text no
    longer present in it (registration drift);
  - an existing JSON or markdown output (never overwritten).

DETERMINISM
-----------
No timestamps, no random draws, no wall-clock or environment values other than
the git HEAD of --root. Sorted keys, sorted type/pair_id ordering: rerunning
over identical inputs is byte-identical.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT_DEFAULT = Path(__file__).resolve().parents[1]
if str(ROOT_DEFAULT) not in sys.path:
    sys.path.insert(0, str(ROOT_DEFAULT))

from src.eval.fliptrack_metrics import (  # noqa: E402
    aggregate_pair_metrics,
    golds_equivalent,
    pair_score,
)
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT  # noqa: E402
from src.rewards.answer_reward import PARSER_VERSION  # noqa: E402

SCHEMA_VERSION = "blind-gains.track4-premise-v2-gate-readout.v1"
REGISTRATION_RELPATH = "docs/registered_track4_premise_v2_design_v1.md"

# ---------------------------------------------------------------------------
# Registered constants (docs/registered_track4_premise_v2_design_v1.md)
# ---------------------------------------------------------------------------

E1_BAND_LOW = 0.40
E1_BAND_HIGH = 0.60
E1_BAND_CARRIER_TYPE = "chained_premise_easy"

# §7 E2: "final member accuracy <= 0.133 (2x the 1/15 uniform-x chance)"
E2_FINAL_MEMBER_CEILING = 0.133
# §7 E2: "blind premise member accuracy <= 2x 1/(n_points-1)"
E2_PREMISE_CEILING_MULTIPLIER = 2.0

# §8 development batch composition (P1.4: one declared batch, 160 groups)
REGISTERED_COMPOSITION: dict[str, dict[str, Any]] = {
    "chained_premise": {
        "groups": 20,
        "n_points": 20,
        "template_id": "t4v2_coordinate_register_n20_v1",
        "role": "frozen-construction control (anchors against P0.1's 0.275)",
        "has_premise": True,
    },
    "chained_premise_easy": {
        "groups": 40,
        "n_points": 8,
        "template_id": "t4v2_coordinate_register_n8_v1",
        "role": "easier variant carrying the section-5 band",
        "has_premise": True,
    },
    "fact_read": {
        "groups": 20,
        "n_points": 20,
        "template_id": "t4v2_coordinate_register_n20_v1",
        "role": "reading control (no premise)",
        "has_premise": False,
    },
    "premise_transition": {
        "groups": 40,
        "n_points": 20,
        "template_id": "t4v2_coordinate_register_n20_v1",
        "role": "the new construct, reference difficulty",
        "has_premise": True,
    },
    "premise_transition_easy": {
        "groups": 40,
        "n_points": 8,
        "template_id": "t4v2_coordinate_register_n8_v1",
        "role": "new construct x easier lever",
        "has_premise": True,
    },
}

# Verbatim registration text. Every quote below is verified to still be present
# in the registration document (whitespace-normalized) before anything is
# reported; a drifted registration refuses the readout.
QUOTE_E1_READOUT = (
    "Readout: per-intervention-type premise member accuracy (probe run) and final\n"
    "member/pair accuracy (causal run), lenient + strict (I7), no aggregation\n"
    "across types (I13). Pass: `chained_premise_easy` premise member accuracy in\n"
    "[0.40, 0.60] (else §5 branches fire)."
)
QUOTE_E2_CRITERION = (
    "**E2 — blind floor** (1 GPU): repeat both E1 commands with\n"
    "`--image-mode no_image` and `--image-mode gray` (four runs). Pass, per type:\n"
    "blind (no_image and gray) **final** member accuracy ≤ 0.133 (2× the 1/15\n"
    "uniform-x chance) and blind **premise** member accuracy ≤ 2×`1/(n_points−1)`\n"
    "(n=20: ≤ 0.105; n=8: ≤ 0.286), on lenient scoring. Fail ⇒ the failing type is\n"
    "excluded from any training use; the blind-solvable `pair_id`s are reported; no\n"
    "silent regeneration."
)
QUOTE_TARGET_BAND = (
    "**Target band: base premise member accuracy ∈ [0.40, 0.60] on\n"
    "`chained_premise_easy`** (primary carrier; anchor point 0.275 at n=20)."
)
QUOTE_FACT_READ_NO_PREMISE = (
    "`fact_read` items carry no premise fields at all. Half-specified premise\n"
    "metadata fails closed in the loader."
)
QUOTE_GATES_ALL_FOUR = (
    "The track is unusable for training or release reporting until all four gates\n"
    "run and pass."
)

SECTION5_BRANCHES: dict[str, dict[str, str]] = {
    "a": {
        "label": "(a) band hit",
        "condition": "0.40 <= acc <= 0.60",
        "quote": (
            "- **(a) band hit** (0.40 ≤ acc ≤ 0.60): `n=8` is frozen as the Phase-2\n"
            "  curriculum entry difficulty. No further lever moves."
        ),
    },
    "b": {
        "label": "(b) too easy",
        "condition": "acc > 0.60",
        "quote": (
            "- **(b) too easy** (acc > 0.60): one pre-committed step to `n=12`; one fresh\n"
            "  40-group easy tranche built under identical registered constraints from\n"
            "  unused development-bucket scenes; **one** re-measure. No other knob moves."
        ),
    },
    "c": {
        "label": "(c) still too hard",
        "condition": "acc < 0.40",
        "quote": (
            "- **(c) still too hard** (acc < 0.40): one pre-committed step to `n=5` (the\n"
            "  minimum at which the premise remains a genuine 4-distractor search); same\n"
            "  single re-measure discipline."
        ),
    },
    "d": {
        "label": "(d) the single re-measure also misses",
        "condition": "reachable only after the one registered re-measure",
        "quote": (
            "- **(d) the single re-measure also misses:** the label-count lever is declared\n"
            "  insufficient for this construct. Escalate to the PAPER2 §6 premise-first\n"
            "  redesign (simpler premise curriculum or a small verified warm start, which\n"
            "  mandates the SFT+standard-GRPO comparator, I16). The miss is reported as a\n"
            "  result; there is no further iteration on this batch."
        ),
    },
}

# ---------------------------------------------------------------------------
# Cell layout
# ---------------------------------------------------------------------------

PREMISE_FAMILY = "premise"
FINAL_FAMILY = "final"
REAL_MODE = "real"
BLIND_MODES = ("gray", "no_image")

# (cell key, CLI flag, family, registered image mode)
CELL_SPECS: tuple[tuple[str, str, str, str], ...] = (
    ("premise_probe_real", "--probe-real", PREMISE_FAMILY, "real"),
    ("premise_probe_gray", "--probe-gray", PREMISE_FAMILY, "gray"),
    ("premise_probe_no_image", "--probe-no-image", PREMISE_FAMILY, "no_image"),
    ("final_real", "--final-real", FINAL_FAMILY, "real"),
    ("final_gray", "--final-gray", FINAL_FAMILY, "gray"),
    ("final_no_image", "--final-no-image", FINAL_FAMILY, "no_image"),
)
CELL_BY_FAMILY_MODE = {(family, mode): key for key, _flag, family, mode in CELL_SPECS}

REQUIRED_PREDICTION_STR_FIELDS = (
    "pair_id",
    "intervention_type",
    "template_id",
    "eval_image_mode",
    "prompt_contract_id",
    "prompt_contract_sha256",
    "parser_version",
    "answer_a",
    "answer_b",
)
# Strings that must be present and of type str but MAY legitimately be empty
# (a response with no extractable span extracts to "").
REQUIRED_PREDICTION_STR_MAYBE_EMPTY_FIELDS = ("extracted_answer_a", "extracted_answer_b")
REQUIRED_PREDICTION_BOOL_FIELDS = (
    "correct_a",
    "correct_b",
    "strict_correct_a",
    "strict_correct_b",
    "pair_correct",
    "strict_pair_correct",
    "equal_gold_a",
    "equal_gold_b",
)
REQUIRED_PREDICTION_INT_FIELDS = ("match_tier_a", "match_tier_b")
REQUIRED_PREDICTION_PRESENT_FIELDS = ("prediction_a", "prediction_b")

REQUIRED_MANIFEST_STR_FIELDS = (
    "pair_id",
    "intervention_type",
    "template_id",
    "answer_a",
    "answer_b",
)

# Joined fields that must agree between the prediction row and its manifest row.
JOIN_AGREEMENT_FIELDS = ("intervention_type", "template_id", "answer_a", "answer_b")

# Scorer outputs cross-checked against the banked verdicts, row by row.
RESCORE_CHECK_FIELDS = (
    "correct_a",
    "correct_b",
    "strict_correct_a",
    "strict_correct_b",
    "pair_correct",
    "strict_pair_correct",
    "equal_gold_a",
    "equal_gold_b",
    "match_tier_a",
    "match_tier_b",
    "extracted_answer_a",
    "extracted_answer_b",
)

CONTRACTS: dict[str, dict[str, str]] = {
    "lenient": {
        "member_field_a": "correct_a",
        "member_field_b": "correct_b",
        "pair_field": "pair_correct",
        "description": "lenient matcher on the extracted answer span (I7 contract 1)",
    },
    "strict": {
        "member_field_a": "strict_correct_a",
        "member_field_b": "strict_correct_b",
        "pair_field": "strict_pair_correct",
        "description": "contract-strict: lenient match AND answer-tags-v1 satisfied (I7 contract 2)",
    },
}
# §7 E2 names its scoring contract explicitly: "on lenient scoring".
E2_REGISTERED_CONTRACT = "lenient"


class GateReadoutRefusal(RuntimeError):
    """Raised whenever the instrument refuses to produce a readout."""


_MISSING = object()


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _git_head(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _resolve(root: Path, value: str | Path) -> Path:
    candidate = Path(value)
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as error:
        raise GateReadoutRefusal(
            f"input path escapes the analysis root {root}: {value}"
        ) from error
    return resolved


def _relpath(root: Path, path: Path) -> str:
    return str(Path(path).resolve().relative_to(root.resolve()))


def _read_jsonl(path: Path, what: str) -> list[dict[str, Any]]:
    if not path.is_file():
        raise GateReadoutRefusal(f"missing {what}: {path} (fail-closed)")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise GateReadoutRefusal(f"unreadable {what}: {path}: {error}") from error
    rows: list[dict[str, Any]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise GateReadoutRefusal(
                f"malformed JSON in {what} {path} line {lineno}: {error}"
            ) from error
        if not isinstance(row, dict):
            raise GateReadoutRefusal(
                f"{what} {path} line {lineno} is not a JSON object (fail-closed)"
            )
        rows.append(row)
    if not rows:
        raise GateReadoutRefusal(f"{what} {path} contains no rows (fail-closed)")
    return rows


def _read_json(path: Path, what: str) -> dict[str, Any]:
    if not path.is_file():
        raise GateReadoutRefusal(f"missing {what}: {path} (fail-closed)")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GateReadoutRefusal(f"unreadable {what}: {path}: {error}") from error
    if not isinstance(payload, dict):
        raise GateReadoutRefusal(f"{what} {path} is not a JSON object (fail-closed)")
    return payload


def _require_nonempty_str(row: dict[str, Any], field: str, where: str) -> str:
    value = row.get(field, _MISSING)
    if value is _MISSING:
        raise GateReadoutRefusal(f"{where}: required field '{field}' is absent (fail-closed)")
    if value is None:
        raise GateReadoutRefusal(f"{where}: required field '{field}' is null (fail-closed)")
    if not isinstance(value, str):
        raise GateReadoutRefusal(
            f"{where}: required field '{field}' must be a string, got"
            f" {type(value).__name__} (fail-closed; no proxy is substituted)"
        )
    if not value.strip():
        raise GateReadoutRefusal(f"{where}: required field '{field}' is empty (fail-closed)")
    return value


def _require_str(row: dict[str, Any], field: str, where: str) -> str:
    value = row.get(field, _MISSING)
    if value is _MISSING:
        raise GateReadoutRefusal(f"{where}: required field '{field}' is absent (fail-closed)")
    if not isinstance(value, str):
        raise GateReadoutRefusal(
            f"{where}: required field '{field}' must be a string, got"
            f" {type(value).__name__} (fail-closed)"
        )
    return value


def _require_bool(row: dict[str, Any], field: str, where: str) -> bool:
    value = row.get(field, _MISSING)
    if value is _MISSING:
        raise GateReadoutRefusal(f"{where}: required verdict field '{field}' is absent (fail-closed)")
    if not isinstance(value, bool):
        raise GateReadoutRefusal(
            f"{where}: verdict field '{field}' must be a JSON boolean, got"
            f" {type(value).__name__} {value!r} (fail-closed; no proxy is substituted)"
        )
    return value


def _require_int(row: dict[str, Any], field: str, where: str) -> int:
    value = row.get(field, _MISSING)
    if value is _MISSING:
        raise GateReadoutRefusal(f"{where}: required field '{field}' is absent (fail-closed)")
    if isinstance(value, bool) or not isinstance(value, int):
        raise GateReadoutRefusal(
            f"{where}: field '{field}' must be an integer, got"
            f" {type(value).__name__} {value!r} (fail-closed)"
        )
    return value


def _require_n_points(row: dict[str, Any], where: str) -> int:
    knobs = row.get("difficulty_knobs", _MISSING)
    if knobs is _MISSING or knobs is None:
        raise GateReadoutRefusal(
            f"{where}: 'difficulty_knobs' is absent -- the E2 premise ceiling"
            f" 2x1/(n_points-1) would be underivable (fail-closed)"
        )
    if not isinstance(knobs, dict):
        raise GateReadoutRefusal(
            f"{where}: 'difficulty_knobs' must be an object, got {type(knobs).__name__}"
        )
    value = knobs.get("n_points", _MISSING)
    if value is _MISSING or value is None:
        raise GateReadoutRefusal(
            f"{where}: 'difficulty_knobs.n_points' is absent -- the E2 premise"
            f" ceiling 2x1/(n_points-1) would be underivable (fail-closed;"
            f" no proxy such as len(scene_points_a) is substituted)"
        )
    if isinstance(value, bool) or not isinstance(value, int):
        raise GateReadoutRefusal(
            f"{where}: 'difficulty_knobs.n_points' must be an integer, got"
            f" {type(value).__name__} {value!r} (fail-closed)"
        )
    if value < 2:
        raise GateReadoutRefusal(
            f"{where}: 'difficulty_knobs.n_points' = {value} < 2; the premise"
            f" ceiling 2x1/(n_points-1) is undefined (fail-closed)"
        )
    return value


def premise_ceiling(n_points: int) -> float:
    """Registered E2 premise ceiling: 2 x 1/(n_points - 1)."""
    return E2_PREMISE_CEILING_MULTIPLIER * (1.0 / (n_points - 1))


# ---------------------------------------------------------------------------
# Registration verification
# ---------------------------------------------------------------------------


def verify_registration(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise GateReadoutRefusal(
            f"missing registration document {path}; the registered criteria and"
            f" section-5 branches cannot be verified (fail-closed)"
        )
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise GateReadoutRefusal(f"unreadable registration document {path}: {error}") from error
    haystack = _normalize_ws(text)
    quotes = {
        "e1_readout": QUOTE_E1_READOUT,
        "e2_criterion": QUOTE_E2_CRITERION,
        "target_band": QUOTE_TARGET_BAND,
        "fact_read_no_premise": QUOTE_FACT_READ_NO_PREMISE,
        "all_four_gates": QUOTE_GATES_ALL_FOUR,
        **{f"section5_branch_{key}": spec["quote"] for key, spec in SECTION5_BRANCHES.items()},
    }
    for name, quote in sorted(quotes.items()):
        if _normalize_ws(quote) not in haystack:
            raise GateReadoutRefusal(
                f"registration drift: quoted text '{name}' is no longer present in"
                f" {path}; the instrument refuses to report a verdict against a"
                f" registration it cannot verify (fail-closed)"
            )
    return {"quotes_verified": sorted(quotes), "sha256": _sha256_file(path)}


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_manifest(path: Path, family: str) -> dict[str, dict[str, Any]]:
    rows = _read_jsonl(path, f"{family} manifest")
    out: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        where = f"{family} manifest {path} row {index}"
        for field in REQUIRED_MANIFEST_STR_FIELDS:
            _require_nonempty_str(row, field, where)
        pair_id = row["pair_id"]
        _require_n_points(row, f"{where} (pair_id={pair_id})")
        probe = row.get("probe")
        if family == PREMISE_FAMILY:
            if probe != "premise":
                raise GateReadoutRefusal(
                    f"{where} (pair_id={pair_id}): premise-probe manifest row must"
                    f" carry probe == 'premise', got {probe!r}; refusing in case the"
                    f" premise and causal manifests were swapped (fail-closed)"
                )
            for side in ("a", "b"):
                premise_gold = _require_nonempty_str(row, f"premise_answer_{side}", where)
                answer = row[f"answer_{side}"]
                if premise_gold != answer:
                    raise GateReadoutRefusal(
                        f"{where} (pair_id={pair_id}): premise-probe row scores"
                        f" answer_{side}={answer!r} but carries"
                        f" premise_answer_{side}={premise_gold!r}; the probe row must"
                        f" be scored against the premise gold (fail-closed)"
                    )
        else:
            if probe not in (None, ""):
                raise GateReadoutRefusal(
                    f"{where} (pair_id={pair_id}): causal manifest row carries"
                    f" probe={probe!r}; refusing in case the premise and causal"
                    f" manifests were swapped (fail-closed)"
                )
        if pair_id in out:
            raise GateReadoutRefusal(
                f"duplicate pair_id {pair_id!r} in {family} manifest {path} (fail-closed)"
            )
        out[pair_id] = row
    return out


def load_cell(cell_key: str, cell_dir: Path, family: str, mode: str) -> dict[str, Any]:
    if not cell_dir.is_dir():
        raise GateReadoutRefusal(f"cell '{cell_key}': not a directory: {cell_dir} (fail-closed)")
    predictions_path = cell_dir / "predictions.jsonl"
    metrics_path = cell_dir / "metrics.json"
    metrics = _read_json(metrics_path, f"cell '{cell_key}' metrics.json")
    metrics_mode = metrics.get("image_mode")
    if metrics_mode != mode:
        raise GateReadoutRefusal(
            f"cell '{cell_key}': metrics.json image_mode is {metrics_mode!r}, expected"
            f" {mode!r} for this cell slot (fail-closed)"
        )
    rows = _read_jsonl(predictions_path, f"cell '{cell_key}' predictions.jsonl")
    seen: set[str] = set()
    contract_ids: set[str] = set()
    contract_shas: set[str] = set()
    parser_versions: set[str] = set()
    modes: set[str] = set()
    for index, row in enumerate(rows):
        where = f"cell '{cell_key}' predictions row {index}"
        for field in REQUIRED_PREDICTION_STR_FIELDS:
            _require_nonempty_str(row, field, where)
        pair_id = row["pair_id"]
        where = f"cell '{cell_key}' predictions row {index} (pair_id={pair_id})"
        for field in REQUIRED_PREDICTION_PRESENT_FIELDS:
            if field not in row:
                raise GateReadoutRefusal(
                    f"{where}: required field '{field}' is absent (fail-closed)"
                )
        for field in REQUIRED_PREDICTION_STR_MAYBE_EMPTY_FIELDS:
            _require_str(row, field, where)
        for field in REQUIRED_PREDICTION_BOOL_FIELDS:
            _require_bool(row, field, where)
        for field in REQUIRED_PREDICTION_INT_FIELDS:
            _require_int(row, field, where)
        _require_n_points(row, where)
        if pair_id in seen:
            raise GateReadoutRefusal(
                f"duplicate pair_id {pair_id!r} in cell '{cell_key}'"
                f" ({predictions_path}) (fail-closed)"
            )
        seen.add(pair_id)
        contract_ids.add(row["prompt_contract_id"])
        contract_shas.add(row["prompt_contract_sha256"])
        parser_versions.add(row["parser_version"])
        modes.add(row["eval_image_mode"])
    if len(modes) != 1:
        raise GateReadoutRefusal(
            f"cell '{cell_key}': eval_image_mode is not single-valued:"
            f" {sorted(modes)} (fail-closed)"
        )
    if modes != {mode}:
        raise GateReadoutRefusal(
            f"cell '{cell_key}': rows carry eval_image_mode {sorted(modes)}, expected"
            f" {mode!r} for this cell slot (fail-closed)"
        )
    expected_sha = DEFAULT_PROMPT_CONTRACT.sha256
    if contract_ids != {DEFAULT_PROMPT_CONTRACT.contract_id}:
        raise GateReadoutRefusal(
            f"cell '{cell_key}': decoding lock violated -- prompt_contract_id"
            f" {sorted(contract_ids)}, expected"
            f" ['{DEFAULT_PROMPT_CONTRACT.contract_id}'] (fail-closed)"
        )
    if contract_shas != {expected_sha}:
        raise GateReadoutRefusal(
            f"cell '{cell_key}': decoding lock violated -- prompt_contract_sha256"
            f" {sorted(contract_shas)}, expected ['{expected_sha}'] (the repo prompt"
            f" contract has changed since this cell was scored; refusing rather than"
            f" re-scoring under a different lock)"
        )
    if parser_versions != {PARSER_VERSION}:
        raise GateReadoutRefusal(
            f"cell '{cell_key}': decoding lock violated -- parser_version"
            f" {sorted(parser_versions)}, expected ['{PARSER_VERSION}'] (fail-closed)"
        )
    return {
        "cell_key": cell_key,
        "family": family,
        "image_mode": mode,
        "dir": cell_dir,
        "predictions_path": predictions_path,
        "metrics_path": metrics_path,
        "metrics": metrics,
        "rows": rows,
    }


def join_cell(cell: dict[str, Any], manifest: dict[str, dict[str, Any]], manifest_path: Path) -> None:
    """Join predictions to manifest rows on pair_id; refuse unless bijective and consistent."""
    cell_key = cell["cell_key"]
    pred_ids = {row["pair_id"] for row in cell["rows"]}
    manifest_ids = set(manifest)
    unmatched = sorted(pred_ids - manifest_ids)
    if unmatched:
        raise GateReadoutRefusal(
            f"cell '{cell_key}': {len(unmatched)} prediction row(s) have no manifest"
            f" row in {manifest_path}; sample={unmatched[:5]} (fail-closed)"
        )
    missing = sorted(manifest_ids - pred_ids)
    if missing:
        raise GateReadoutRefusal(
            f"cell '{cell_key}': {len(missing)} manifest row(s) in {manifest_path}"
            f" have no prediction; sample={missing[:5]} (incomplete cell, fail-closed)"
        )
    for row in cell["rows"]:
        pair_id = row["pair_id"]
        manifest_row = manifest[pair_id]
        for field in JOIN_AGREEMENT_FIELDS:
            if row[field] != manifest_row[field]:
                raise GateReadoutRefusal(
                    f"cell '{cell_key}' pair_id={pair_id}: joined field '{field}'"
                    f" disagrees -- prediction {row[field]!r} vs manifest"
                    f" {manifest_row[field]!r} (fail-closed)"
                )
        pred_n = row["difficulty_knobs"]["n_points"]
        man_n = manifest_row["difficulty_knobs"]["n_points"]
        if pred_n != man_n:
            raise GateReadoutRefusal(
                f"cell '{cell_key}' pair_id={pair_id}: difficulty_knobs.n_points"
                f" disagrees -- prediction {pred_n} vs manifest {man_n} (fail-closed)"
            )


def verify_banked_scores(cell: dict[str, Any]) -> None:
    """Re-derive every banked verdict with the frozen scorer; refuse on any disagreement."""
    cell_key = cell["cell_key"]
    mismatches: list[str] = []
    for row in cell["rows"]:
        rescored = pair_score(row)
        for field in RESCORE_CHECK_FIELDS:
            banked = row[field]
            derived = rescored[field]
            if isinstance(banked, str) != isinstance(derived, str):
                same = False
            elif isinstance(banked, str):
                same = banked == derived
            else:
                same = bool(banked) == bool(derived) if isinstance(banked, bool) else banked == derived
            if not same:
                mismatches.append(
                    f"pair_id={row['pair_id']} {field}: banked={banked!r}"
                    f" rescored={derived!r}"
                )
    if mismatches:
        raise GateReadoutRefusal(
            f"cell '{cell_key}': {len(mismatches)} banked verdict(s) are not"
            f" reproduced by src.eval.fliptrack_metrics.pair_score under the locked"
            f" contract; sample={mismatches[:5]} (fail-closed)"
        )


# ---------------------------------------------------------------------------
# Per-intervention-type aggregation (I13: never pooled across types)
# ---------------------------------------------------------------------------


def group_rows_by_type(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["intervention_type"], []).append(row)
    return {
        itype: sorted(type_rows, key=lambda r: r["pair_id"])
        for itype, type_rows in sorted(grouped.items())
    }


def aggregate_type(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Member and pair accuracy from banked verdicts, both contracts, never merged (I7)."""
    n_pairs = len(rows)
    if n_pairs == 0:
        raise GateReadoutRefusal("aggregate_type called with zero rows (fail-closed)")
    block: dict[str, Any] = {"n_pairs": n_pairs, "n_members": 2 * n_pairs}
    for contract, spec in sorted(CONTRACTS.items()):
        member_correct = sum(
            int(row[spec["member_field_a"]]) + int(row[spec["member_field_b"]]) for row in rows
        )
        pair_correct = sum(int(row[spec["pair_field"]]) for row in rows)
        block[contract] = {
            "contract": contract,
            "contract_description": spec["description"],
            "member_accuracy": member_correct / (2 * n_pairs),
            "member_correct": member_correct,
            "pair_accuracy": pair_correct / n_pairs,
            "pair_correct": pair_correct,
        }

    # The frozen repo aggregator is the authority on the registered accuracy
    # convention (member accuracy over 2 x n_pairs). Run it over this type's own
    # row subset -- the registered grouping is `intervention_type`, so the subset
    # is what it is handed -- and refuse if this instrument's arithmetic ever
    # diverges from it. Both paths reduce to the same integer numerator over the
    # same denominator, so exact equality is the correct comparison.
    repo = aggregate_pair_metrics(rows)
    if repo["n_pairs"] != float(n_pairs):
        raise GateReadoutRefusal(
            f"src.eval.fliptrack_metrics.aggregate_pair_metrics reports"
            f" n_pairs={repo['n_pairs']!r} for a {n_pairs}-row intervention-type"
            f" subset (fail-closed)"
        )
    for contract, repo_keys in (
        ("lenient", {"member_accuracy": "member_accuracy", "pair_accuracy": "pair_accuracy"}),
        ("strict", {"member_accuracy": "strict_member_accuracy", "pair_accuracy": "strict_pair_accuracy"}),
    ):
        for local_key, repo_key in sorted(repo_keys.items()):
            mine = block[contract][local_key]
            theirs = repo[repo_key]
            if mine != theirs:
                raise GateReadoutRefusal(
                    f"per-type {contract} {local_key} derived from the banked"
                    f" verdicts ({mine!r}) disagrees with"
                    f" src.eval.fliptrack_metrics.aggregate_pair_metrics"
                    f" ('{repo_key}' = {theirs!r}) over the same rows; the"
                    f" registered accuracy convention is owned by that module"
                    f" (fail-closed)"
                )
    block["accuracy_convention_cross_checked_against"] = (
        "src.eval.fliptrack_metrics.aggregate_pair_metrics, run over this"
        " intervention type's own row subset (member accuracy over 2 x n_pairs)"
    )
    return block


def classify_equal_gold(itype: str, rows: list[dict[str, Any]], manifest: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Classify a premise-probe type as a transition read or a stability read (section 4)."""
    equal_ids: list[str] = []
    differing_ids: list[str] = []
    for row in rows:
        manifest_row = manifest[row["pair_id"]]
        equal = golds_equivalent(
            manifest_row["premise_answer_a"], manifest_row["premise_answer_b"]
        )
        if equal != bool(row["equal_gold_a"]) or equal != bool(row["equal_gold_b"]):
            raise GateReadoutRefusal(
                f"intervention_type '{itype}' pair_id={row['pair_id']}: manifest"
                f" premise golds are {'equal' if equal else 'differing'} but the row"
                f" banks equal_gold_a={row['equal_gold_a']},"
                f" equal_gold_b={row['equal_gold_b']} (fail-closed)"
            )
        (equal_ids if equal else differing_ids).append(row["pair_id"])
    if equal_ids and differing_ids:
        raise GateReadoutRefusal(
            f"intervention_type '{itype}': premise-probe rows mix equal-gold"
            f" ({len(equal_ids)}) and differing-gold ({len(differing_ids)}) items;"
            f" pooling them would merge section-4 `premise_stability` with"
            f" `premise_transition_accuracy`, which I13 forbids (fail-closed)"
        )
    if differing_ids:
        semantics = "premise_transition_accuracy (section 4: differing premise golds, discriminative two-gold branch)"
    else:
        semantics = "premise_stability (section 4: equal premise golds, invariance reading)"
    return {
        "n_equal_gold": len(equal_ids),
        "n_differing_gold": len(differing_ids),
        "premise_pair_accuracy_semantics": semantics,
    }


def blind_solvable_pair_ids(rows: list[dict[str, Any]], contract: str) -> dict[str, Any]:
    spec = CONTRACTS[contract]
    any_member = sorted(
        row["pair_id"]
        for row in rows
        if row[spec["member_field_a"]] or row[spec["member_field_b"]]
    )
    both_members = sorted(row["pair_id"] for row in rows if row[spec["pair_field"]])
    return {
        "scoring_contract": contract,
        "n_any_member_correct": len(any_member),
        "any_member_correct": any_member,
        "n_both_members_correct": len(both_members),
        "both_members_correct": both_members,
    }


# ---------------------------------------------------------------------------
# Composition checks
# ---------------------------------------------------------------------------


def check_composition(
    probe_by_type: dict[str, list[dict[str, Any]]],
    causal_by_type: dict[str, list[dict[str, Any]]],
    n_points_by_type: dict[str, int],
    template_by_type: dict[str, str],
    expect: str,
) -> None:
    probe_only = sorted(set(probe_by_type) - set(causal_by_type))
    if probe_only:
        raise GateReadoutRefusal(
            f"intervention type(s) {probe_only} appear in the premise-probe manifest"
            f" but not in the causal manifest; their E2 final-member criterion would"
            f" be unevaluable (fail-closed)"
        )
    if expect == "any":
        return
    expected_types = sorted(REGISTERED_COMPOSITION)
    if sorted(causal_by_type) != expected_types:
        raise GateReadoutRefusal(
            f"section-8 composition violated: causal manifest intervention types"
            f" {sorted(causal_by_type)}, registered {expected_types}"
            f" (--expect any is for fixtures only)"
        )
    expected_probe = sorted(k for k, v in REGISTERED_COMPOSITION.items() if v["has_premise"])
    if sorted(probe_by_type) != expected_probe:
        raise GateReadoutRefusal(
            f"section-8 composition violated: premise-probe manifest intervention"
            f" types {sorted(probe_by_type)}, registered {expected_probe}"
            f" (--expect any is for fixtures only)"
        )
    for itype in expected_types:
        spec = REGISTERED_COMPOSITION[itype]
        n_groups = len(causal_by_type[itype])
        if n_groups != spec["groups"]:
            raise GateReadoutRefusal(
                f"section-8 composition violated: type '{itype}' has {n_groups}"
                f" causal groups, registered {spec['groups']}"
                f" (--expect any is for fixtures only)"
            )
        if n_points_by_type[itype] != spec["n_points"]:
            raise GateReadoutRefusal(
                f"section-8 composition violated: type '{itype}' has n_points"
                f" {n_points_by_type[itype]}, registered {spec['n_points']}"
                f" (--expect any is for fixtures only)"
            )
        if template_by_type[itype] != spec["template_id"]:
            raise GateReadoutRefusal(
                f"section-8 composition violated: type '{itype}' has template_id"
                f" {template_by_type[itype]!r}, registered {spec['template_id']!r}"
                f" (--expect any is for fixtures only)"
            )
        if spec["has_premise"]:
            if itype not in probe_by_type:
                raise GateReadoutRefusal(
                    f"section-8 composition violated: premise type '{itype}' is absent"
                    f" from the premise-probe manifest (fail-closed)"
                )
            n_probe = len(probe_by_type[itype])
            if n_probe != spec["groups"]:
                raise GateReadoutRefusal(
                    f"section-8 composition violated: type '{itype}' has {n_probe}"
                    f" premise-probe rows, registered {spec['groups']}"
                    f" (--expect any is for fixtures only)"
                )


def single_valued_by_type(
    cells: dict[str, dict[str, Any]], field_getter, field_label: str
) -> dict[str, Any]:
    values: dict[str, set[Any]] = {}
    for cell in cells.values():
        for row in cell["rows"]:
            values.setdefault(row["intervention_type"], set()).add(field_getter(row))
    out: dict[str, Any] = {}
    for itype in sorted(values):
        seen = values[itype]
        if len(seen) != 1:
            raise GateReadoutRefusal(
                f"intervention_type '{itype}': {field_label} is not single-valued"
                f" across the cells: {sorted(seen)}; the registered per-type reading"
                f" is undefined (fail-closed)"
            )
        out[itype] = next(iter(seen))
    return out


# ---------------------------------------------------------------------------
# Registered verdicts
# ---------------------------------------------------------------------------


def section5_branch_for(accuracy: float) -> str:
    if E1_BAND_LOW <= accuracy <= E1_BAND_HIGH:
        return "a"
    if accuracy > E1_BAND_HIGH:
        return "b"
    return "c"


def build_e1(
    probe_real_by_type: dict[str, list[dict[str, Any]]],
    final_real_by_type: dict[str, list[dict[str, Any]]],
    premise_semantics: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    per_type: dict[str, Any] = {}
    for itype in sorted(set(probe_real_by_type) | set(final_real_by_type)):
        premise_rows = probe_real_by_type.get(itype)
        final_rows = final_real_by_type.get(itype)
        entry: dict[str, Any] = {
            "premise_member_and_pair_accuracy": None,
            "premise_absent_reason": None,
            "final_member_and_pair_accuracy": None,
        }
        if premise_rows is None:
            entry["premise_absent_reason"] = (
                "no premise-probe rows for this intervention type; the registration"
                " (section 3) states: " + QUOTE_FACT_READ_NO_PREMISE.replace("\n", " ")
            )
        else:
            entry["premise_member_and_pair_accuracy"] = {
                **aggregate_type(premise_rows),
                **premise_semantics[itype],
            }
        if final_rows is not None:
            entry["final_member_and_pair_accuracy"] = aggregate_type(final_rows)
        per_type[itype] = entry

    verdicts: dict[str, Any] = {}
    carrier_rows = probe_real_by_type.get(E1_BAND_CARRIER_TYPE)
    if carrier_rows is None:
        raise GateReadoutRefusal(
            f"E1 band carrier type '{E1_BAND_CARRIER_TYPE}' has no premise-probe rows"
            f" in the real-image cell; the registered pass criterion is unevaluable"
            f" (fail-closed)"
        )
    carrier = aggregate_type(carrier_rows)
    for contract in sorted(CONTRACTS):
        accuracy = carrier[contract]["member_accuracy"]
        in_band = E1_BAND_LOW <= accuracy <= E1_BAND_HIGH
        branch = section5_branch_for(accuracy)
        verdicts[contract] = {
            "intervention_type": E1_BAND_CARRIER_TYPE,
            "metric": "premise member accuracy (premise-probe cell, image mode real)",
            "scoring_contract": contract,
            "value": accuracy,
            "n_pairs": carrier["n_pairs"],
            "n_members": carrier["n_members"],
            "member_correct": carrier[contract]["member_correct"],
            "band_low": E1_BAND_LOW,
            "band_high": E1_BAND_HIGH,
            "band_interval": f"[{E1_BAND_LOW:.2f}, {E1_BAND_HIGH:.2f}] (inclusive both ends)",
            "in_band": in_band,
            "verdict": "PASS" if in_band else "FAIL",
            "section5_branch_fired": {
                "branch": branch,
                "label": SECTION5_BRANCHES[branch]["label"],
                "condition": SECTION5_BRANCHES[branch]["condition"],
                "registration_quote": SECTION5_BRANCHES[branch]["quote"],
            },
        }
    lenient_pass = verdicts["lenient"]["verdict"] == "PASS"
    strict_pass = verdicts["strict"]["verdict"] == "PASS"
    return {
        "gate": "E1 - difficulty band",
        "registration_quote_readout_and_pass": QUOTE_E1_READOUT,
        "registration_quote_target_band": QUOTE_TARGET_BAND,
        "band_carrier_intervention_type": E1_BAND_CARRIER_TYPE,
        "image_mode": REAL_MODE,
        "per_intervention_type": per_type,
        "verdict_by_scoring_contract_never_merged_I7": verdicts,
        "contracts_agree": lenient_pass == strict_pass,
        "contract_not_named_by_registration": (
            "Section 7 E1 states the pass criterion as 'premise member accuracy in"
            " [0.40, 0.60]' and requires 'lenient + strict (I7)' without naming which"
            " contract carries the band (contrast section 7 E2, which says 'on lenient"
            " scoring'). This instrument therefore reports the verdict separately under"
            " each contract and does not choose between them; if they disagree, the"
            " disagreement is the result and the choice is the PI's."
        ),
        "branch_d_not_fireable_here": {
            "reason": (
                "Section-5 branch (d) is defined on 'the single re-measure' and cannot"
                " be fired by a first measurement; it is quoted for completeness only."
            ),
            "registration_quote": SECTION5_BRANCHES["d"]["quote"],
        },
    }


def build_e2(
    probe_blind_by_type: dict[str, dict[str, list[dict[str, Any]]]],
    final_blind_by_type: dict[str, dict[str, list[dict[str, Any]]]],
    n_points_by_type: dict[str, int],
    premise_semantics: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    all_types = sorted(
        set().union(*[set(v) for v in final_blind_by_type.values()])
    )
    per_type: dict[str, Any] = {}
    failing: list[str] = []
    passing: list[str] = []
    for itype in all_types:
        n_points = n_points_by_type[itype]
        has_premise = all(itype in probe_blind_by_type[mode] for mode in BLIND_MODES)
        partial_premise = any(itype in probe_blind_by_type[mode] for mode in BLIND_MODES)
        if partial_premise and not has_premise:
            raise GateReadoutRefusal(
                f"intervention_type '{itype}': premise-probe rows exist for only some"
                f" blind modes; E2 requires both no_image and gray (fail-closed)"
            )
        ceiling = premise_ceiling(n_points) if has_premise else None
        cells_block: dict[str, Any] = {}
        criteria_block: dict[str, Any] = {}
        failing_criteria: list[str] = []
        for mode in BLIND_MODES:
            final_rows = final_blind_by_type[mode].get(itype)
            if final_rows is None:
                raise GateReadoutRefusal(
                    f"intervention_type '{itype}': no rows in the blind final cell"
                    f" (image mode {mode}); the E2 final criterion is unevaluable"
                    f" (fail-closed)"
                )
            final_block = aggregate_type(final_rows)
            final_value = final_block[E2_REGISTERED_CONTRACT]["member_accuracy"]
            final_ok = final_value <= E2_FINAL_MEMBER_CEILING
            if not final_ok:
                failing_criteria.append(f"{mode}:final_member_accuracy")
            mode_cells: dict[str, Any] = {"final": final_block}
            mode_criteria: dict[str, Any] = {
                "final_member_accuracy": {
                    "value": final_value,
                    "ceiling": E2_FINAL_MEMBER_CEILING,
                    "ceiling_source": "registered literal 0.133 (2x the 1/15 uniform-x chance)",
                    "comparison": "value <= ceiling",
                    "ok": final_ok,
                },
            }
            if has_premise:
                premise_rows = probe_blind_by_type[mode][itype]
                premise_block = {
                    **aggregate_type(premise_rows),
                    **premise_semantics[itype],
                }
                premise_value = premise_block[E2_REGISTERED_CONTRACT]["member_accuracy"]
                premise_ok = premise_value <= ceiling
                if not premise_ok:
                    failing_criteria.append(f"{mode}:premise_member_accuracy")
                mode_cells["premise"] = premise_block
                mode_criteria["premise_member_accuracy"] = {
                    "value": premise_value,
                    "ceiling": ceiling,
                    "ceiling_source": (
                        f"2 x 1/(n_points - 1) with n_points = {n_points} from this"
                        f" type's own difficulty_knobs.n_points"
                    ),
                    "comparison": "value <= ceiling",
                    "ok": premise_ok,
                }
            else:
                mode_cells["premise"] = None
                mode_criteria["premise_member_accuracy"] = None
            cells_block[mode] = mode_cells
            criteria_block[mode] = mode_criteria
        verdict = "PASS" if not failing_criteria else "FAIL"
        entry: dict[str, Any] = {
            "n_points": n_points,
            "n_points_source": "difficulty_knobs.n_points (single-valued within the type)",
            "premise_member_accuracy_ceiling": ceiling,
            "premise_criterion_applicable": has_premise,
            "premise_absent_reason": None
            if has_premise
            else (
                "this type carries no premise clause and is absent from the"
                " premise-probe manifest by registered design; section 3: "
                + QUOTE_FACT_READ_NO_PREMISE.replace("\n", " ")
            ),
            "final_member_accuracy_ceiling": E2_FINAL_MEMBER_CEILING,
            "scoring_contract_of_record": E2_REGISTERED_CONTRACT,
            "blind_cells": cells_block,
            "criteria": criteria_block,
            "failing_criteria": failing_criteria,
            "verdict": verdict,
        }
        if verdict == "FAIL":
            failing.append(itype)
            entry["registered_consequence"] = {
                "training_use": "EXCLUDED",
                "registration_quote": QUOTE_E2_CRITERION,
                "statement": (
                    "Registered consequence, applied mechanically: 'Fail => the failing"
                    " type is excluded from any training use; the blind-solvable"
                    " `pair_id`s are reported; no silent regeneration.'"
                ),
            }
            solvable: dict[str, Any] = {}
            for mode in BLIND_MODES:
                solvable[mode] = {
                    "final": blind_solvable_pair_ids(
                        final_blind_by_type[mode][itype], E2_REGISTERED_CONTRACT
                    ),
                    "premise": blind_solvable_pair_ids(
                        probe_blind_by_type[mode][itype], E2_REGISTERED_CONTRACT
                    )
                    if has_premise
                    else None,
                }
            entry["blind_solvable_pair_ids"] = solvable
        else:
            passing.append(itype)
            entry["registered_consequence"] = {
                "training_use": (
                    "not excluded by E2; E3 (caption stress) and E4 (attacker check)"
                    " are not read by this instrument"
                ),
                "registration_quote": QUOTE_GATES_ALL_FOUR,
            }
        per_type[itype] = entry

    strict_secondary: dict[str, Any] = {}
    for itype in all_types:
        strict_secondary[itype] = {
            mode: {
                "final_member_accuracy_strict": per_type[itype]["blind_cells"][mode]["final"][
                    "strict"
                ]["member_accuracy"],
                "premise_member_accuracy_strict": (
                    per_type[itype]["blind_cells"][mode]["premise"]["strict"]["member_accuracy"]
                    if per_type[itype]["blind_cells"][mode]["premise"] is not None
                    else None
                ),
            }
            for mode in BLIND_MODES
        }

    return {
        "gate": "E2 - blind floor",
        "registration_quote": QUOTE_E2_CRITERION,
        "blind_image_modes": list(BLIND_MODES),
        "scoring_contract_of_record": E2_REGISTERED_CONTRACT,
        "scoring_contract_note": (
            "Section 7 E2 names its contract: 'on lenient scoring'. The strict"
            " contract is computed and reported for every cell (I7) but is never"
            " merged into the E2 criterion; see"
            " strict_contract_reported_separately_NOT_A_CRITERION."
        ),
        "final_member_accuracy_ceiling": E2_FINAL_MEMBER_CEILING,
        "premise_ceiling_rule": "2 x 1/(n_points - 1), derived per type from that type's own difficulty_knobs.n_points",
        "per_intervention_type": per_type,
        "failing_types": failing,
        "passing_types": passing,
        "strict_contract_reported_separately_NOT_A_CRITERION": strict_secondary,
    }


# ---------------------------------------------------------------------------
# Payload
# ---------------------------------------------------------------------------


def build_payload(
    root: Path,
    cell_dirs: dict[str, Path],
    probe_manifest_path: Path,
    causal_manifest_path: Path,
    registration_path: Path,
    expect: str,
) -> dict[str, Any]:
    registration = verify_registration(registration_path)

    probe_manifest = load_manifest(probe_manifest_path, PREMISE_FAMILY)
    causal_manifest = load_manifest(causal_manifest_path, FINAL_FAMILY)

    cells: dict[str, dict[str, Any]] = {}
    for cell_key, _flag, family, mode in CELL_SPECS:
        cell = load_cell(cell_key, cell_dirs[cell_key], family, mode)
        manifest = probe_manifest if family == PREMISE_FAMILY else causal_manifest
        manifest_path = probe_manifest_path if family == PREMISE_FAMILY else causal_manifest_path
        join_cell(cell, manifest, manifest_path)
        verify_banked_scores(cell)
        cells[cell_key] = cell

    n_points_by_type = single_valued_by_type(
        cells, lambda row: row["difficulty_knobs"]["n_points"], "difficulty_knobs.n_points"
    )
    template_by_type = single_valued_by_type(cells, lambda row: row["template_id"], "template_id")

    by_type: dict[str, dict[str, list[dict[str, Any]]]] = {
        cell_key: group_rows_by_type(cell["rows"]) for cell_key, cell in cells.items()
    }

    check_composition(
        by_type["premise_probe_real"],
        by_type["final_real"],
        n_points_by_type,
        template_by_type,
        expect,
    )

    premise_semantics: dict[str, dict[str, Any]] = {}
    for cell_key, _flag, family, _mode in CELL_SPECS:
        if family != PREMISE_FAMILY:
            continue
        for itype, rows in by_type[cell_key].items():
            block = classify_equal_gold(itype, rows, probe_manifest)
            previous = premise_semantics.get(itype)
            if previous is not None and previous != block:
                raise GateReadoutRefusal(
                    f"intervention_type '{itype}': premise gold structure differs"
                    f" between premise-probe cells ({previous} vs {block}) (fail-closed)"
                )
            premise_semantics[itype] = block

    e1 = build_e1(
        by_type["premise_probe_real"], by_type["final_real"], premise_semantics
    )
    e2 = build_e2(
        {mode: by_type[CELL_BY_FAMILY_MODE[(PREMISE_FAMILY, mode)]] for mode in BLIND_MODES},
        {mode: by_type[CELL_BY_FAMILY_MODE[(FINAL_FAMILY, mode)]] for mode in BLIND_MODES},
        n_points_by_type,
        premise_semantics,
    )

    provenance_cells: dict[str, Any] = {}
    for cell_key, _flag, family, mode in CELL_SPECS:
        cell = cells[cell_key]
        provenance_cells[cell_key] = {
            "family": family,
            "image_mode": mode,
            "dir": _relpath(root, cell["dir"]),
            "predictions_path": _relpath(root, cell["predictions_path"]),
            "predictions_sha256": _sha256_file(cell["predictions_path"]),
            "n_rows": len(cell["rows"]),
            "rows_by_intervention_type": {
                itype: len(rows) for itype, rows in sorted(by_type[cell_key].items())
            },
            "metrics_path": _relpath(root, cell["metrics_path"]),
            "metrics_sha256": _sha256_file(cell["metrics_path"]),
            "metrics_note": (
                "this cell's metrics.json is POOLED across intervention types and is"
                " NOT the registered endpoint; it is carried here by sha256 only and"
                " no value is copied out of it (I13)"
            ),
            "metrics_decoding_lock": {
                "image_mode": cell["metrics"].get("image_mode"),
                "seed": cell["metrics"].get("seed"),
                "noise_seed": cell["metrics"].get("noise_seed"),
                "max_new_tokens": cell["metrics"].get("max_new_tokens"),
                "prompt_contract_id": cell["metrics"].get("prompt_contract_id"),
                "prompt_contract_sha256": cell["metrics"].get("prompt_contract_sha256"),
                "parser_version": cell["metrics"].get("parser_version"),
            },
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "title": (
            "Track-4 premise-v2 acceptance gates E1 (difficulty band) and E2 (blind"
            " floor): registered per-intervention-type readout"
        ),
        "governing_document": REGISTRATION_RELPATH,
        "governing_sections": [
            "section 7 - Acceptance gates (I14): E1 readout and pass criterion, E2 pass criterion and consequence",
            "section 5 - Easier premise variant: registered branches (a)-(d)",
            "section 4 - both contracts reported (I7); stability vs transition never aggregated (I13)",
            "section 3 - fact_read carries no premise fields",
            "section 8 - declared batch composition",
        ],
        "instrument": {
            "path": "scripts/build_track4_premise_v2_gate_readout.py",
            "reported_numbers_source": (
                "per-row verdict fields banked by scripts/eval_qwen_vl_fliptrack.py"
                " (correct_a/b, strict_correct_a/b, pair_correct, strict_pair_correct)"
            ),
            "independent_rescore_check": (
                "every banked verdict re-derived row by row with"
                " src.eval.fliptrack_metrics.pair_score under"
                " src.eval.prompt_contract.DEFAULT_PROMPT_CONTRACT; any disagreement"
                " refuses the readout"
            ),
            "equal_gold_classifier": "src.eval.fliptrack_metrics.golds_equivalent",
            "aggregation_cross_check": (
                "for every intervention type,"
                " src.eval.fliptrack_metrics.aggregate_pair_metrics is run over that"
                " type's own row subset and must reproduce this instrument's member"
                " and pair accuracies under both contracts; any disagreement refuses"
                " the readout, so the registered denominator stays owned by the frozen"
                " repo module"
            ),
            "aggregation_grouping": (
                "intervention_type; aggregate_pair_metrics_by_template is deliberately"
                " NOT used because it groups by template_id and two registered types"
                " share one template_id (that would pool what I13 forbids pooling)"
            ),
            "expectation_mode": expect,
            "decides_nothing": (
                "This instrument reports the registered verdicts mechanically and names"
                " the section-5 branch the registered rule fires. It does not"
                " editorialize and does not decide anything the registration leaves to"
                " the PI."
            ),
        },
        "decoding_lock": {
            "prompt_contract_id": DEFAULT_PROMPT_CONTRACT.contract_id,
            "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
            "parser_version": PARSER_VERSION,
            "single_valued_across_all_six_cells": True,
        },
        "invariants": {
            "I7": (
                "lenient and contract-strict contracts computed and reported separately"
                " for every cell and every intervention type; never merged"
            ),
            "I13": (
                "every reported endpoint is per intervention type; nothing is pooled"
                " across types anywhere in this output; each cell's own pooled"
                " metrics.json is carried by sha256 only"
            ),
            "I15": "schema_version carried at top level",
        },
        "gates_read_here": ["E1", "E2"],
        "gates_not_read_here": {
            "E3": "caption stress - not read by this instrument",
            "E4": "attacker check - not read by this instrument",
            "registration_quote": QUOTE_GATES_ALL_FOUR,
        },
        "e1_difficulty_band": e1,
        "e2_blind_floor": e2,
        "per_intervention_type_n_points": n_points_by_type,
        "per_intervention_type_template_id": template_by_type,
        "provenance": {
            "root": str(root),
            "git_head": _git_head(root),
            "registration": {
                "path": _relpath(root, registration_path),
                "sha256": registration["sha256"],
                "quotes_verified": registration["quotes_verified"],
            },
            "manifests": {
                "premise_probe": {
                    "path": _relpath(root, probe_manifest_path),
                    "sha256": _sha256_file(probe_manifest_path),
                    "n_rows": len(probe_manifest),
                },
                "causal_pairs": {
                    "path": _relpath(root, causal_manifest_path),
                    "sha256": _sha256_file(causal_manifest_path),
                    "n_rows": len(causal_manifest),
                },
            },
            "cells": provenance_cells,
        },
    }


# ---------------------------------------------------------------------------
# Markdown twin
# ---------------------------------------------------------------------------


def _fmt(value: Any, digits: int = 6) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _quote_block(text: str) -> list[str]:
    return ["> " + line if line else ">" for line in text.split("\n")]


def render_markdown(payload: dict[str, Any], json_relpath: str) -> str:
    lines: list[str] = [
        "# Track-4 premise-v2 acceptance gates E1 + E2 - registered readout",
        "",
        f"Governing registration: `{payload['governing_document']}`"
        f" (sha256 `{payload['provenance']['registration']['sha256']}`).",
        "",
        f"Machine artifact: `{json_relpath}` (`{payload['schema_version']}`).",
        "",
        "This report states the registered verdicts and the section-5 branch the"
        " registered rule fires. It contains no interpretation; every choice the"
        " registration leaves open is left open here.",
        "",
        "Discipline: both scoring contracts are reported separately and never merged"
        " (I7); every endpoint is per intervention type and nothing is pooled across"
        " types (I13). Each cell's own `metrics.json` is pooled across types and is"
        " NOT the registered endpoint; it is carried by sha256 only.",
        "",
        "## E1 - difficulty band",
        "",
        "Registered readout and pass criterion:",
        "",
    ]
    e1 = payload["e1_difficulty_band"]
    lines.extend(_quote_block(e1["registration_quote_readout_and_pass"]))
    lines.extend(
        [
            "",
            "### Per-intervention-type accuracy, real images",
            "",
            "| type | premise n | premise member acc (lenient) | premise member acc (strict) |"
            " premise pair acc (lenient) | final n | final member acc (lenient) |"
            " final member acc (strict) | final pair acc (lenient) | final pair acc (strict) |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for itype in sorted(e1["per_intervention_type"]):
        entry = e1["per_intervention_type"][itype]
        premise = entry["premise_member_and_pair_accuracy"]
        final = entry["final_member_and_pair_accuracy"]
        row = [
            f"`{itype}`",
            _fmt(premise["n_pairs"]) if premise else "n/a",
            _fmt(premise["lenient"]["member_accuracy"]) if premise else "n/a",
            _fmt(premise["strict"]["member_accuracy"]) if premise else "n/a",
            _fmt(premise["lenient"]["pair_accuracy"]) if premise else "n/a",
            _fmt(final["n_pairs"]) if final else "n/a",
            _fmt(final["lenient"]["member_accuracy"]) if final else "n/a",
            _fmt(final["strict"]["member_accuracy"]) if final else "n/a",
            _fmt(final["lenient"]["pair_accuracy"]) if final else "n/a",
            _fmt(final["strict"]["pair_accuracy"]) if final else "n/a",
        ]
        lines.append("| " + " | ".join(row) + " |")
    lines.extend(
        [
            "",
            "Premise pair accuracy semantics per type (section 4; stability and"
            " transition are never aggregated with each other):",
            "",
        ]
    )
    for itype in sorted(e1["per_intervention_type"]):
        premise = e1["per_intervention_type"][itype]["premise_member_and_pair_accuracy"]
        if premise is None:
            reason = e1["per_intervention_type"][itype]["premise_absent_reason"]
            lines.append(f"- `{itype}`: no premise rows - {reason}")
        else:
            lines.append(f"- `{itype}`: {premise['premise_pair_accuracy_semantics']}")
    lines.extend(
        [
            "",
            f"### Registered pass criterion on `{e1['band_carrier_intervention_type']}`",
            "",
            "| contract | premise member accuracy | registered band | in band | verdict |"
            " section-5 branch fired |",
            "|---|---:|---|---|---|---|",
        ]
    )
    for contract in sorted(e1["verdict_by_scoring_contract_never_merged_I7"]):
        block = e1["verdict_by_scoring_contract_never_merged_I7"][contract]
        lines.append(
            f"| {contract} | {_fmt(block['value'])} | {block['band_interval']} |"
            f" {'yes' if block['in_band'] else 'no'} | **{block['verdict']}** |"
            f" {block['section5_branch_fired']['branch']}"
            f" {block['section5_branch_fired']['label']} |"
        )
    lines.extend(["", f"Contracts agree: {'yes' if e1['contracts_agree'] else 'NO'}.", ""])
    lines.append(e1["contract_not_named_by_registration"])
    lines.append("")
    fired = {
        block["section5_branch_fired"]["branch"]
        for block in e1["verdict_by_scoring_contract_never_merged_I7"].values()
    }
    for branch in sorted(fired):
        block = SECTION5_BRANCHES[branch]
        lines.extend([f"Section-5 branch {block['label']} - registered text:", ""])
        lines.extend(_quote_block(block["quote"]))
        lines.append("")
    lines.extend(
        [
            e1["branch_d_not_fireable_here"]["reason"],
            "",
            "## E2 - blind floor",
            "",
            "Registered pass criterion and consequence:",
            "",
        ]
    )
    e2 = payload["e2_blind_floor"]
    lines.extend(_quote_block(e2["registration_quote"]))
    lines.extend(
        [
            "",
            f"Contract of record for E2: **{e2['scoring_contract_of_record']}**"
            f" ({e2['scoring_contract_note']})",
            "",
            "| type | n_points | premise ceiling 2/(n_points-1) | mode |"
            " blind final member acc | <= 0.133 | blind premise member acc |"
            " <= ceiling | type verdict |",
            "|---|---:|---:|---|---:|---|---:|---|---|",
        ]
    )
    for itype in sorted(e2["per_intervention_type"]):
        entry = e2["per_intervention_type"][itype]
        for mode in BLIND_MODES:
            criteria = entry["criteria"][mode]
            final_c = criteria["final_member_accuracy"]
            premise_c = criteria["premise_member_accuracy"]
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{itype}`",
                        str(entry["n_points"]),
                        _fmt(entry["premise_member_accuracy_ceiling"]),
                        mode,
                        _fmt(final_c["value"]),
                        "ok" if final_c["ok"] else "**OVER**",
                        _fmt(premise_c["value"]) if premise_c else "n/a",
                        ("ok" if premise_c["ok"] else "**OVER**") if premise_c else "n/a",
                        f"**{entry['verdict']}**",
                    ]
                )
                + " |"
            )
    lines.append("")
    for itype in sorted(e2["per_intervention_type"]):
        entry = e2["per_intervention_type"][itype]
        if entry["premise_criterion_applicable"]:
            continue
        lines.append(f"- `{itype}`: {entry['premise_absent_reason']}")
    lines.extend(
        [
            "",
            f"E2 passing types: {', '.join('`' + t + '`' for t in e2['passing_types']) or 'none'}.",
            f"E2 failing types: {', '.join('`' + t + '`' for t in e2['failing_types']) or 'none'}.",
            "",
        ]
    )
    if e2["failing_types"]:
        lines.extend(
            [
                "### Failing types - registered consequence and blind-solvable"
                " `pair_id`s",
                "",
            ]
        )
        for itype in e2["failing_types"]:
            entry = e2["per_intervention_type"][itype]
            lines.extend(
                [
                    f"#### `{itype}` - FAIL",
                    "",
                    f"Failing criteria: {', '.join(entry['failing_criteria'])}.",
                    "",
                    f"Training use: **{entry['registered_consequence']['training_use']}**"
                    f" - {entry['registered_consequence']['statement']}",
                    "",
                ]
            )
            for mode in BLIND_MODES:
                for kind in ("final", "premise"):
                    block = entry["blind_solvable_pair_ids"][mode][kind]
                    if block is None:
                        continue
                    lines.extend(
                        [
                            f"Blind-solvable `pair_id`s, {mode} / {kind}"
                            f" ({block['scoring_contract']} scoring):",
                            "",
                            f"- any member correct (n={block['n_any_member_correct']}):"
                            f" {', '.join('`' + p + '`' for p in block['any_member_correct']) or 'none'}",
                            f"- both members correct (n={block['n_both_members_correct']}):"
                            f" {', '.join('`' + p + '`' for p in block['both_members_correct']) or 'none'}",
                            "",
                        ]
                    )
    lines.extend(
        [
            "### Strict contract on the blind cells (reported separately, NOT an E2"
            " criterion)",
            "",
            "| type | mode | final member acc (strict) | premise member acc (strict) |",
            "|---|---|---:|---:|",
        ]
    )
    strict = e2["strict_contract_reported_separately_NOT_A_CRITERION"]
    for itype in sorted(strict):
        for mode in BLIND_MODES:
            block = strict[itype][mode]
            lines.append(
                f"| `{itype}` | {mode} | {_fmt(block['final_member_accuracy_strict'])} |"
                f" {_fmt(block['premise_member_accuracy_strict'])} |"
            )
    lines.extend(
        [
            "",
            "## Gates not read here",
            "",
            f"- E3: {payload['gates_not_read_here']['E3']}",
            f"- E4: {payload['gates_not_read_here']['E4']}",
            "",
        ]
    )
    lines.extend(_quote_block(QUOTE_GATES_ALL_FOUR))
    lines.extend(
        [
            "",
            "## Provenance",
            "",
            f"- root: `{payload['provenance']['root']}`",
            "- git HEAD: "
            + (
                f"`{payload['provenance']['git_head']}`"
                if payload["provenance"]["git_head"]
                else "not recorded (root is not a git repository)"
            ),
            f"- decoding lock: prompt contract"
            f" `{payload['decoding_lock']['prompt_contract_id']}`"
            f" (sha256 `{payload['decoding_lock']['prompt_contract_sha256']}`),"
            f" parser `{payload['decoding_lock']['parser_version']}`",
            f"- premise-probe manifest:"
            f" `{payload['provenance']['manifests']['premise_probe']['path']}`"
            f" sha256 `{payload['provenance']['manifests']['premise_probe']['sha256']}`"
            f" ({payload['provenance']['manifests']['premise_probe']['n_rows']} rows)",
            f"- causal-pairs manifest:"
            f" `{payload['provenance']['manifests']['causal_pairs']['path']}`"
            f" sha256 `{payload['provenance']['manifests']['causal_pairs']['sha256']}`"
            f" ({payload['provenance']['manifests']['causal_pairs']['n_rows']} rows)",
            "",
            "| cell | image mode | rows | predictions sha256 | metrics sha256 (pooled,"
            " NOT the endpoint) |",
            "|---|---|---:|---|---|",
        ]
    )
    for cell_key, _flag, _family, _mode in CELL_SPECS:
        cell = payload["provenance"]["cells"][cell_key]
        lines.append(
            f"| `{cell_key}` | {cell['image_mode']} | {cell['n_rows']} |"
            f" `{cell['predictions_sha256']}` | `{cell['metrics_sha256']}` |"
        )
    lines.append("")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Registered Track-4 premise-v2 acceptance-gate readout (E1 difficulty"
            " band, E2 blind floor). Per intervention type, both contracts, never"
            " pooled."
        )
    )
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    for cell_key, flag, _family, mode in CELL_SPECS:
        parser.add_argument(
            flag,
            dest=cell_key,
            required=True,
            help=f"cell directory for {cell_key} (image mode {mode})",
        )
    parser.add_argument("--probe-manifest", required=True)
    parser.add_argument("--causal-manifest", required=True)
    parser.add_argument(
        "--registration",
        default=REGISTRATION_RELPATH,
        help="registration document whose quoted criteria are verified",
    )
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--markdown-output", required=True)
    parser.add_argument(
        "--expect",
        choices=("registered", "any"),
        default="registered",
        help="'registered' enforces the section-8 batch composition; 'any' is for fixtures only",
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    try:
        cell_dirs = {
            cell_key: _resolve(root, getattr(args, cell_key))
            for cell_key, _flag, _family, _mode in CELL_SPECS
        }
        probe_manifest_path = _resolve(root, args.probe_manifest)
        causal_manifest_path = _resolve(root, args.causal_manifest)
        registration_path = _resolve(root, args.registration)
        json_output = _resolve(root, args.json_output)
        markdown_output = _resolve(root, args.markdown_output)
        if json_output.exists() or markdown_output.exists():
            raise GateReadoutRefusal(
                f"refusing to overwrite existing readout artifacts:"
                f" {json_output} / {markdown_output}"
            )
        payload = build_payload(
            root,
            cell_dirs,
            probe_manifest_path,
            causal_manifest_path,
            registration_path,
            args.expect,
        )
        markdown = render_markdown(payload, _relpath(root, json_output))
        json_output.parent.mkdir(parents=True, exist_ok=True)
        markdown_output.parent.mkdir(parents=True, exist_ok=True)
        if json_output.exists() or markdown_output.exists():
            raise GateReadoutRefusal(
                f"refusing to overwrite existing readout artifacts:"
                f" {json_output} / {markdown_output}"
            )
        json_output.write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        markdown_output.write_text(markdown, encoding="utf-8")
    except GateReadoutRefusal as error:
        print(f"REFUSED: {error}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "schema_version": payload["schema_version"],
                "json": _relpath(root, json_output),
                "markdown": _relpath(root, markdown_output),
                "e1_verdict_lenient": payload["e1_difficulty_band"][
                    "verdict_by_scoring_contract_never_merged_I7"
                ]["lenient"]["verdict"],
                "e1_verdict_strict": payload["e1_difficulty_band"][
                    "verdict_by_scoring_contract_never_merged_I7"
                ]["strict"]["verdict"],
                "e2_failing_types": payload["e2_blind_floor"]["failing_types"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
