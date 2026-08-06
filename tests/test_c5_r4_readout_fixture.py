"""Adversarial fixtures for scripts/build_c5_r4_readout.py (I10).

Every fixture is synthetic and small enough to hand-verify. Each test targets
a failure mode a naive readout silently commits:

  a. planted matched/crossed gains and TrainShare recovered exactly, with
     poisoned train-split rows (overlapping row_index, inverted correctness)
     that would corrupt every planted value if the test-split filter leaked;
  b. the two scoring contracts (canonical / strict) are planted with
     different values, computed separately, and never merged;
  c. an unstable A1 denominator under ONE contract -> that contract's
     TrainShare is `undefined-unstable-denominator` with no ratio computed,
     while the other contract's TrainShare is still recovered (contract
     independence);
  d. an item present in one cell but missing in another -> hard failure,
     never silent dropping, no outputs written;
  e. a run manifest with status != complete is refused before any estimand;
  f. two runs at the registered seed 20260730 produce byte-identical JSON,
     markdown, and joined-items artifacts;
  g. --partial is verify-only: exit 0 on the two base cells alone, every
     estimand refused, and NO accuracy or performance value in any output.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_c5_r4_readout.py"

MODELS = ("base", "a1_real", "a2_gray")
TESTS = ("real", "gray")
CELLS = tuple(f"{model}:{test}" for model in MODELS for test in TESTS)
DRAWS = 200
SEED = 20260730
N_TEST = 40
N_TRAIN_POISON = 20

# Planted (canonical_correct_count, strict_correct_count) out of 40 test rows.
# Deliberately different per contract so a merge is detectable.
PLANTED_COUNTS = {
    "base:real": (8, 4),
    "a1_real:real": (24, 16),
    "a2_gray:real": (16, 10),
    "base:gray": (4, 2),
    "a1_real:gray": (6, 4),
    "a2_gray:gray": (20, 12),
}
# Hand-checked planted estimands (prefix-positional correctness):
#   canonical: matched A1 = 16/40 = 0.4, matched A2 = 16/40 = 0.4,
#              crossed A2 = 8/40 = 0.2, TrainShare = 0.2/0.4 = 0.5,
#              descriptive A1-gray diff = 2/40 = 0.05;
#              A1 denominator 0.4 vs 2*SE ~ 0.157 -> stable.
#   strict:    matched A1 = 12/40 = 0.3, matched A2 = 10/40 = 0.25,
#              crossed A2 = 6/40 = 0.15, TrainShare = 0.15/0.3 = 0.5,
#              descriptive A1-gray diff = 2/40 = 0.05;
#              A1 denominator 0.3 vs 2*SE ~ 0.147 -> stable.
PLANTED = {
    "canonical": {
        "cell_acc": {cell: c / N_TEST for cell, (c, _) in PLANTED_COUNTS.items()},
        "matched_a1": 0.4,
        "matched_a2": 0.4,
        "crossed_a2": 0.2,
        "trainshare": 0.5,
        "descriptive_a1_gray": 0.05,
    },
    "strict": {
        "cell_acc": {cell: s / N_TEST for cell, (_, s) in PLANTED_COUNTS.items()},
        "matched_a1": 0.3,
        "matched_a2": 0.25,
        "crossed_a2": 0.15,
        "trainshare": 0.5,
        "descriptive_a1_gray": 0.05,
    },
}
# Unstable variant: a1_real:real canonical correct set = {2..10} (9 items):
# contributions vs base:real (correct {0..7}) are +1 x3 (8,9,10), -1 x2 (0,1),
# 0 x35 -> mean 1/40 = 0.025, 2 * paired SE ~ 0.113 -> UNSTABLE. Strict is
# untouched (prefix 16 vs 4 -> 0.3, stable).
UNSTABLE_A1_CANONICAL_SET = frozenset(range(2, 11))

MODEL_REVISIONS = {
    "base": "fixture/base-model",
    "a1_real": "fixture/checkpoints/c5_a1_real_fixture/global_step_100",
    "a2_gray": "fixture/checkpoints/c5_a2_gray_fixture/global_step_100",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _row(
    test: str,
    idx: int,
    *,
    split: str,
    canonical: bool,
    strict: bool,
    poison: bool = False,
) -> dict:
    return {
        "schema_version": "fixture.c5.v1",
        "split": split,
        "qid": None,
        "row_index": idx,
        "condition": test,
        "greedy_canonical_correct": canonical,
        "greedy_acc_strict": strict,
        "ground_truth": "poison" if poison else f"gt-{idx}",
        "problem": "poison problem" if poison else f"problem {idx}",
        "image_sha256": ["ff" * 32] if poison else [("%02x" % idx) * 32],
        "decoding": {
            "greedy": {"n": 1, "temperature": 0.0, "top_p": 1.0},
            "sampled": {"n": 16, "temperature": 1.0, "top_p": 1.0},
            "seed": 20260710,
            "max_tokens": 64,
        },
        "prompt_contract_sha256": "c" * 64,
        "format_prompt_sha256": "a" * 64,
        "source_manifest_sha256": "d" * 64,
        "train_filter_sha256": "b" * 64,
        "parser_version": "fixture-parser",
        "scoring_mode": "fixture-scoring",
    }


def _manifest(run_dir: Path, model: str, test: str, status: str = "complete") -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "run_id": run_dir.name,
                "job_type": "fixture_eval",
                "status": status,
                "condition": test,
                "node": "fixture",
                "git_hash": "0" * 40,
                "config_hash": "f" * 64,
                "model_revision": MODEL_REVISIONS[model],
                "seed": 20260710,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _build_fixture(root: Path, *, canonical_sets: dict[str, frozenset] = {}) -> None:
    """Write six fixture cells under root/runs/{model}_{test}.

    Test rows: prefix-positional correctness from PLANTED_COUNTS, overridden
    per cell by canonical_sets (explicit canonical-correct index sets).
    Train rows: N_TRAIN_POISON poisoned rows per cell with row_index
    OVERLAPPING the test range (0..) and inverted extreme correctness (all
    correct in base cells, all wrong in arm cells) plus different content, so
    any leak of the test-split filter corrupts every planted estimand, breaks
    row_index uniqueness, and breaks content identity -- loudly.
    """
    for cell in CELLS:
        model, _, test = cell.partition(":")
        canonical_count, strict_count = PLANTED_COUNTS[cell]
        canonical_set = canonical_sets.get(cell, frozenset(range(canonical_count)))
        rows = [
            _row(
                test,
                idx,
                split="test",
                canonical=idx in canonical_set,
                strict=idx < strict_count,
            )
            for idx in range(N_TEST)
        ]
        base_cell = model == "base"
        rows.extend(
            _row(
                test,
                idx,
                split="train",
                canonical=base_cell,
                strict=base_cell,
                poison=True,
            )
            for idx in range(N_TRAIN_POISON)
        )
        run_dir = root / f"runs/{model}_{test}"
        _manifest(run_dir, model, test)
        _write_jsonl(run_dir / "per_item.jsonl", rows)


def _cli(
    root: Path,
    *,
    cells: tuple[str, ...] = CELLS,
    partial: bool = False,
    json_name: str = "out.json",
    md_name: str = "out.md",
    artifact_dir: str | None = "reports/artifacts",
) -> list[str]:
    args = [
        sys.executable,
        str(SCRIPT),
        "--root", str(root),
        "--json-output", f"reports/{json_name}",
        "--markdown-output", f"reports/{md_name}",
        "--bootstrap-draws", str(DRAWS),
        "--bootstrap-seed", str(SEED),
        "--expected-test-rows", str(N_TEST),
    ]
    for cell in cells:
        model, _, test = cell.partition(":")
        args.extend(["--cell", f"{cell}=runs/{model}_{test}"])
    if partial:
        args.append("--partial")
    elif artifact_dir is not None:
        args.extend(["--artifact-dir", artifact_dir])
    return args


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True)


def _run_full(root: Path, **kwargs) -> dict:
    result = _run(_cli(root, **kwargs))
    assert result.returncode == 0, result.stderr
    return json.loads((root / "reports/out.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# a. planted estimands recovered exactly (train poison ignored)
# --------------------------------------------------------------------------

def test_planted_estimands_recovered_exactly(tmp_path: Path) -> None:
    _build_fixture(tmp_path)
    payload = _run_full(tmp_path)
    assert payload["status"] == "complete"

    for contract, planted in PLANTED.items():
        block = payload["estimands"][contract]
        for cell in CELLS:
            summary = block["cell_accuracy"][cell]
            assert summary["n"] == N_TEST
            assert abs(summary["estimate"] - planted["cell_acc"][cell]) < 1e-12
            assert summary["ci95"] is not None
            assert summary["seed_tag"].startswith("one seed")
        assert abs(
            block["matched_gain"]["a1_real"]["estimate"] - planted["matched_a1"]
        ) < 1e-12
        assert abs(
            block["matched_gain"]["a2_gray"]["estimate"] - planted["matched_a2"]
        ) < 1e-12
        assert abs(
            block["crossed_gain"]["a2_gray"]["estimate"] - planted["crossed_a2"]
        ) < 1e-12
        descriptive = block["a1_tested_gray_descriptive"]
        assert descriptive["label"] == "descriptive"
        assert abs(
            descriptive["crossed_difference"]["estimate"]
            - planted["descriptive_a1_gray"]
        ) < 1e-12
        trainshare = block["crossed_recovery_trainshare"]["a2_gray"]
        assert trainshare["status"] == "stable"
        assert trainshare["denominator"]["stable"] is True
        assert abs(trainshare["ratio"]["estimate"] - planted["trainshare"]) < 1e-12
        assert trainshare["ratio"]["ci95"] is not None

    # Train poison never leaks: provenance counts 40 test + 20 train per cell.
    for cell in CELLS:
        row = payload["provenance"]["cells"][cell]
        assert row["test_row_count"] == N_TEST
        assert row["train_row_count"] == N_TRAIN_POISON
    assert payload["checks"]["test_rows_per_cell"] == {
        cell: N_TEST for cell in CELLS
    }

    # Joined-items artifact: 6 cells x 40 items, sha256 recorded.
    joined = tmp_path / "reports/artifacts/c5_joined_items.jsonl"
    assert joined.is_file()
    joined_rows = joined.read_text(encoding="utf-8").splitlines()
    assert len(joined_rows) == 6 * N_TEST
    assert payload["joined_items_sha256"] == _sha256(joined)

    # Cross-scale anchor is a static descriptive quote, labeled cross-scale.
    anchor = payload["cross_scale_anchor"]
    assert "cross-scale" in anchor["label"]
    assert anchor["pilot_pooled_crossed_trainshare_a2_gray"]["estimate"] == 0.487


# --------------------------------------------------------------------------
# b. both contracts computed, never merged
# --------------------------------------------------------------------------

def test_contracts_computed_separately_and_never_merged(tmp_path: Path) -> None:
    _build_fixture(tmp_path)
    payload = _run_full(tmp_path)

    canonical = payload["estimands"]["canonical"]
    strict = payload["estimands"]["strict"]
    assert canonical["field"] == "greedy_canonical_correct"
    assert strict["field"] == "greedy_acc_strict"
    # The planted values differ per contract, so a silent merge is detectable.
    assert abs(canonical["matched_gain"]["a1_real"]["estimate"] - 0.4) < 1e-12
    assert abs(strict["matched_gain"]["a1_real"]["estimate"] - 0.3) < 1e-12
    assert abs(canonical["matched_gain"]["a2_gray"]["estimate"] - 0.4) < 1e-12
    assert abs(strict["matched_gain"]["a2_gray"]["estimate"] - 0.25) < 1e-12
    for cell in CELLS:
        assert (
            canonical["cell_accuracy"][cell]["estimate"]
            != strict["cell_accuracy"][cell]["estimate"]
        )
    assert payload["checks"]["contracts_never_merged"] is True

    markdown = (tmp_path / "reports/out.md").read_text(encoding="utf-8")
    assert "Contract: canonical (`greedy_canonical_correct`)" in markdown
    assert "Contract: strict (`greedy_acc_strict`)" in markdown


# --------------------------------------------------------------------------
# c. unstable A1 denominator under one contract only
# --------------------------------------------------------------------------

def test_unstable_canonical_denominator_excludes_recovery(tmp_path: Path) -> None:
    _build_fixture(
        tmp_path,
        canonical_sets={"a1_real:real": UNSTABLE_A1_CANONICAL_SET},
    )
    payload = _run_full(tmp_path)

    canonical = payload["estimands"]["canonical"]["crossed_recovery_trainshare"][
        "a2_gray"
    ]
    assert canonical["status"] == "undefined-unstable-denominator"
    assert "ratio" not in canonical
    assert canonical["denominator"]["stable"] is False
    assert abs(canonical["denominator"]["estimate"] - 1 / 40) < 1e-12
    assert (
        canonical["denominator"]["estimate"]
        < 2 * canonical["denominator"]["paired_se"]
    )
    # The gain analysis is untouched: matched gain A1 is still reported.
    assert abs(
        payload["estimands"]["canonical"]["matched_gain"]["a1_real"]["estimate"]
        - 1 / 40
    ) < 1e-12

    # Contract independence: strict TrainShare is still recovered exactly.
    strict = payload["estimands"]["strict"]["crossed_recovery_trainshare"]["a2_gray"]
    assert strict["status"] == "stable"
    assert abs(strict["ratio"]["estimate"] - 0.5) < 1e-12

    markdown = (tmp_path / "reports/out.md").read_text(encoding="utf-8")
    assert "undefined-unstable-denominator" in markdown


# --------------------------------------------------------------------------
# d. item missing in one cell -> loud failure, no outputs
# --------------------------------------------------------------------------

def test_missing_item_fails_loudly(tmp_path: Path) -> None:
    _build_fixture(tmp_path)
    per_item = tmp_path / "runs/a2_gray_real/per_item.jsonl"
    kept = [
        line
        for line in per_item.read_text(encoding="utf-8").splitlines()
        if not (
            json.loads(line)["split"] == "test"
            and json.loads(line)["row_index"] == N_TEST - 1
        )
    ]
    per_item.write_text("".join(line + "\n" for line in kept), encoding="utf-8")

    # The dropped row makes the per-cell count gate fire first (39 != 40);
    # relax the expectation to reach the cross-cell identity gate.
    args = _cli(tmp_path)
    args[args.index("--expected-test-rows") + 1] = str(N_TEST)
    result = _run(args)
    assert result.returncode != 0
    assert "expected 40 test rows, found 39" in result.stderr
    assert not (tmp_path / "reports/out.json").exists()
    assert not (tmp_path / "reports/out.md").exists()

    # Same fixture, per-cell count of 39 planted everywhere EXCEPT the gate
    # must still catch the cross-cell mismatch: drop row 39 from every cell
    # except a2_gray:real's already-dropped -> instead check identity gate by
    # removing a DIFFERENT row from another cell so counts match (39 vs 39)
    # but the sets differ.
    other = tmp_path / "runs/base_real/per_item.jsonl"
    kept_other = [
        line
        for line in other.read_text(encoding="utf-8").splitlines()
        if not (
            json.loads(line)["split"] == "test"
            and json.loads(line)["row_index"] == 0
        )
    ]
    other.write_text(
        "".join(line + "\n" for line in kept_other), encoding="utf-8"
    )
    for cell in CELLS:
        if cell in ("a2_gray:real", "base:real"):
            continue
        model, _, test = cell.partition(":")
        path = tmp_path / f"runs/{model}_{test}/per_item.jsonl"
        kept_cell = [
            line
            for line in path.read_text(encoding="utf-8").splitlines()
            if not (
                json.loads(line)["split"] == "test"
                and json.loads(line)["row_index"] == 0
            )
        ]
        path.write_text(
            "".join(line + "\n" for line in kept_cell), encoding="utf-8"
        )
    args = _cli(tmp_path)
    args[args.index("--expected-test-rows") + 1] = str(N_TEST - 1)
    result = _run(args)
    assert result.returncode != 0
    assert "item-identity gate failed" in result.stderr
    assert "a2_gray:real" in result.stderr
    assert not (tmp_path / "reports/out.json").exists()


# --------------------------------------------------------------------------
# e. incomplete run manifest refused before any estimand
# --------------------------------------------------------------------------

def test_incomplete_manifest_refused(tmp_path: Path) -> None:
    _build_fixture(tmp_path)
    manifest = tmp_path / "runs/a1_real_real/run_manifest.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["status"] = "running"
    manifest.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

    result = _run(_cli(tmp_path))
    assert result.returncode != 0
    assert "readiness gate failed" in result.stderr
    assert "'running'" in result.stderr
    assert not (tmp_path / "reports/out.json").exists()
    assert not (tmp_path / "reports/artifacts").exists()


# --------------------------------------------------------------------------
# f. determinism at the registered seed 20260730
# --------------------------------------------------------------------------

def test_two_runs_at_registered_seed_are_byte_identical(tmp_path: Path) -> None:
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    _build_fixture(root_a)
    shutil.copytree(root_a, root_b)
    payload_a = _run_full(root_a)
    payload_b = _run_full(root_b)
    assert payload_a == payload_b
    assert (root_a / "reports/out.json").read_bytes() == (
        root_b / "reports/out.json"
    ).read_bytes()
    assert (root_a / "reports/out.md").read_bytes() == (
        root_b / "reports/out.md"
    ).read_bytes()
    assert (root_a / "reports/artifacts/c5_joined_items.jsonl").read_bytes() == (
        root_b / "reports/artifacts/c5_joined_items.jsonl"
    ).read_bytes()


# --------------------------------------------------------------------------
# g. partial mode is verify-only: no accuracy value anywhere
# --------------------------------------------------------------------------

def test_partial_mode_verifies_and_refuses_all_estimands(tmp_path: Path) -> None:
    _build_fixture(tmp_path)
    result = _run(
        _cli(tmp_path, cells=("base:real", "base:gray"), partial=True)
    )
    assert result.returncode == 0, result.stderr
    raw = (tmp_path / "reports/out.json").read_text(encoding="utf-8")
    payload = json.loads(raw)
    assert payload["status"] == "partial-verify-only"
    assert "estimands" not in payload
    assert "cross_scale_anchor" not in payload
    assert payload["checks"]["partial_refuses_all_estimands"] is True
    assert payload["checks"]["manifests_complete"] is True
    assert payload["checks"]["item_identity_exact"] is True
    assert payload["checks"]["test_rows_per_cell"] == {
        "base:real": N_TEST,
        "base:gray": N_TEST,
    }
    refused = set(payload["partial_mode"]["refused_estimands"])
    assert {
        "cell_accuracy",
        "matched_gain_a1_real",
        "matched_gain_a2_gray",
        "crossed_gain_a2_gray",
        "crossed_recovery_trainshare_a2_gray",
    } <= refused
    # No accuracy or performance value appears anywhere in either output.
    assert '"estimate"' not in raw
    assert "cell_accuracy" not in json.dumps(
        {k: v for k, v in payload.items() if k != "partial_mode"}
    )
    markdown = (tmp_path / "reports/out.md").read_text(encoding="utf-8")
    assert "PARTIAL" in markdown
    assert "No accuracy or performance value" in markdown
    assert "Acc (95% CI)" not in markdown

    # --partial with --artifact-dir is a usage error.
    bad = _cli(
        tmp_path,
        cells=("base:real", "base:gray"),
        partial=True,
        json_name="bad.json",
        md_name="bad.md",
    )
    bad.extend(["--artifact-dir", "reports/bad_artifacts"])
    result = _run(bad)
    assert result.returncode != 0
    assert "--partial forbids --artifact-dir" in result.stderr

    # Full mode without the arm cells is a usage error pointing at --partial.
    result = _run(
        _cli(
            tmp_path,
            cells=("base:real", "base:gray"),
            json_name="bad2.json",
            md_name="bad2.md",
        )
    )
    assert result.returncode != 0
    assert "full mode requires all six cells" in result.stderr
    assert "--partial" in result.stderr


# --------------------------------------------------------------------------
# registered defaults are pinned in the CLI
# --------------------------------------------------------------------------

def test_registered_defaults_are_pinned() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("build_c5_r4_readout", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.REGISTERED_BOOTSTRAP_DRAWS == 5000
    assert module.REGISTERED_BOOTSTRAP_SEED == 20260730
    assert module.REGISTERED_TEST_ROWS == 601
    assert module.REGISTERED_DECODING_SEED == 20260710
    assert module.REGISTERED_SOURCE_MANIFEST_SHA256 == (
        "0ac91fb836f39776acd5137ccd5cca7259d4ad0a836347be60f96f535d00f639"
    )
    assert module.REGISTERED_TRAIN_FILTER_SHA256 == (
        "8631d015ee8593669b46cc707b9fe1fb3690391520bccf416b64bbb2306ff7d1"
    )
    assert module.REGISTERED_FORMAT_PROMPT_SHA256 == (
        "f1b62cb8332bdbec38efc8689aff6e9ce65174c0db8967937307880f95f58fca"
    )
    assert module.REGISTERED_PROMPT_CONTRACT_SHA256 == (
        "7ac39f53a2a824490fc5ee22671a888d2d79d55e1d8351919006d7d71c7a8f3f"
    )
    assert module.REGISTERED_BASE_MODEL_PATH == (
        "artifacts/models/Qwen/Qwen2.5-VL-7B-Instruct"
    )
    assert module.CONTRACTS == {
        "canonical": "greedy_canonical_correct",
        "strict": "greedy_acc_strict",
    }
