"""Adversarial fixtures for scripts/build_m7_r3_readout.py (I10).

Every fixture is synthetic and small enough to hand-verify. Each test targets
a failure mode a naive readout silently commits:

  a. planted positive / negative rank correlation across fake strata ->
     rho_gain and rho_recovery recover the sign exactly (+1 / -1);
  b. a stratum whose A1 gain is positive but below two paired standard
     errors -> recovery is `undefined-unstable-denominator`, EXCLUDED from
     rho_recovery, but its gain row is PRESENT;
  c. a constant q_bar vector -> tied_spearman returns None, the point
     estimate is `undefined-constant-rank-vector`, every bootstrap draw is
     counted as undefined (never replaced with zero), and the interval is
     labeled `unstable` (> 5% undefined);
  d. an item present at step 0 but missing at step 100 -> hard failure,
     never silent dropping;
  e. stratum eligibility is a pure sample-count rule: 29 items ->
     descriptive-small-n, 30 -> eligible; and the recount assertion fails
     loudly on a wrong expectation;
  f. two runs at seed 20260716 on identical inputs produce byte-identical
     JSON and markdown;
  g. a run manifest with status != complete is refused before any estimand
     is computed (the live-data readiness gate).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_m7_r3_readout.py"

ARMS = ("a1_real", "a2_gray", "a2b_noimage", "a3_caption")
BLIND_ARMS = ("a2_gray", "a2b_noimage", "a3_caption")
CONDITIONS = {
    "a1_real": "real",
    "a2_gray": "gray",
    "a2b_noimage": "none",
    "a3_caption": "caption",
}
DRAWS = 200
SEED = 20260716


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


# --------------------------------------------------------------------------
# Fixture builders
# --------------------------------------------------------------------------
#
# Main fixture ("planted"): six joint strata, one category, sources s1..s6.
#   s1..s5: 30 items each (eligible); s6: 29 items (descriptive-small-n).
#   q_i is constant within each stratum:
#     s1 0.1, s2 0.2, s3 0.3, s4 0.4, s5 0.5, s6 0.15  (all arms).
#   A1: strata s1..s4 and s6: every item flips wrong -> correct
#       (gain 1.0, paired SE 0 -> stable denominator).
#       s5: 15 items +1, 13 items -1, 2 items 0 -> mean 2/30 = 0.0667,
#       paired SE ~0.179, 2*SE ~0.358 > mean -> UNSTABLE denominator.
#   Blind-arm step-100 flip counts (acc0 all False):
#     a2_gray     s1..s6: 0, 3, 6,  9, 12, 1   -> gain increases with q_bar
#     a2b_noimage s1..s6: 12, 9, 6, 3,  0, 2   -> gain decreases with q_bar
#     a3_caption  s1..s6: 0, 3, 6,  9, 12, 1   -> same as a2_gray
#   Hand-computed rank statistics over the five eligible strata:
#     rho_gain[a2_gray] = +1, rho_gain[a2b_noimage] = -1, rho_gain[a3] = +1.
#   Recovery uses only the four STABLE eligible strata (s1..s4), where
#   gain[A1,s] = 1 so recovery == blind gain:
#     rho_recovery[a2_gray] = +1, rho_recovery[a2b_noimage] = -1.
#   M10 candidates: sample_correct_count is 4 everywhere except the three
#   flipped s2 items of a2_gray, which are 0 -> exactly 3 candidates for
#   a2_gray and 0 for every other arm.

PLANTED_Q = {"s1": 0.1, "s2": 0.2, "s3": 0.3, "s4": 0.4, "s5": 0.5, "s6": 0.15}
PLANTED_N = {"s1": 30, "s2": 30, "s3": 30, "s4": 30, "s5": 30, "s6": 29}
PLANTED_FLIPS = {
    "a2_gray": {"s1": 0, "s2": 3, "s3": 6, "s4": 9, "s5": 12, "s6": 1},
    "a2b_noimage": {"s1": 12, "s2": 9, "s3": 6, "s4": 3, "s5": 0, "s6": 2},
    "a3_caption": {"s1": 0, "s2": 3, "s3": 6, "s4": 9, "s5": 12, "s6": 1},
}


def _item_ids(sources: dict[str, int]) -> list[tuple[str, str, int]]:
    items: list[tuple[str, str, int]] = []
    index = 0
    for source in sorted(sources):
        for position in range(sources[source]):
            items.append((source, f"q-{source}-{position:03d}", index))
            index += 1
    return items


def _manifest(run_dir: Path, arm: str, step: str, status: str = "complete") -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "run_id": run_dir.name,
                "job_type": f"fixture_{step}_eval",
                "status": status,
                "condition": CONDITIONS[arm],
                "node": "fixture",
                "git_hash": "0" * 40,
                "config_hash": "f" * 64,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _per_item_row(
    arm: str,
    qid: str,
    row_index: int,
    *,
    q: float,
    correct: bool,
    count: int = 4,
    step0: bool = True,
) -> dict:
    row = {
        "schema_version": "blind-gains.blind-solvability-pilot.v1",
        "qid": qid,
        "row_index": row_index,
        "split": "train",
        "condition": CONDITIONS[arm],
        "greedy_canonical_correct": correct,
        "problem": f"problem {qid}",
        "ground_truth": "42",
        "image_sha256": "e" * 64,
        "source_manifest_sha256": "d" * 64,
        "prompt_contract_sha256": "c" * 64,
        "parser_version": "fixture-parser",
        "pilot_reward_version": "fixture-reward",
        "decoding": {"sampled": {"temperature": 1.0}, "max_tokens": 16},
    }
    if step0:
        row.update(
            {
                "q_i": q,
                "p_i_jeffreys": q / 5.0,
                "sample_count": 16,
                "sample_correct_count": count,
            }
        )
    return row


def _build_fixture(
    root: Path,
    *,
    sources_n: dict[str, int],
    q_of: dict[str, float],
    flips: dict[str, dict[str, int]],
    a1_gain_plan: dict[str, str],
    zero_count_items: set[tuple[str, str]] = frozenset(),
) -> dict[str, str]:
    """Write a heldout manifest plus eight fixture runs under `root`.

    a1_gain_plan maps source -> 'all_gain' (every item flips wrong->correct)
    or 'unstable' (15 items +1, 13 items -1, 2 items 0).
    zero_count_items: {(arm, qid)} whose step-0 sample_correct_count is 0.
    Returns CLI values for --step0/--step100.
    """
    items = _item_ids(sources_n)
    heldout_rows = [
        {
            "schema_version": "fixture-heldout.v1",
            "split": "train",
            "qid": qid,
            "row_index": row_index,
            "problem": f"problem {qid}",
            "answer": "42",
            "images": [f"images/{qid}.png"],
            "metadata": {"source": source, "category": "cat", "image_sha256": ["e" * 64]},
        }
        for source, qid, row_index in items
    ]
    _write_jsonl(root / "data/heldout.jsonl", heldout_rows)

    runs: dict[str, str] = {}
    for arm in ARMS:
        step0_rows: list[dict] = []
        step100_rows: list[dict] = []
        for source, qid, row_index in items:
            q = q_of[source]
            count = 0 if (arm, qid) in zero_count_items else 4
            if arm == "a1_real":
                plan = a1_gain_plan[source]
                position = int(qid.rsplit("-", 1)[1])
                if plan == "all_gain":
                    acc0, acc100 = False, True
                elif plan == "unstable":
                    if position < 15:
                        acc0, acc100 = False, True  # +1
                    elif position < 28:
                        acc0, acc100 = True, False  # -1
                    else:
                        acc0, acc100 = False, False  # 0
                else:
                    raise AssertionError(plan)
            else:
                position = int(qid.rsplit("-", 1)[1])
                acc0 = False
                acc100 = position < flips[arm][source]
            step0_rows.append(
                _per_item_row(arm, qid, row_index, q=q, correct=acc0, count=count)
            )
            step100_rows.append(
                _per_item_row(arm, qid, row_index, q=q, correct=acc100, step0=False)
            )
        step0_dir = root / f"runs/{arm}_step0"
        step100_dir = root / f"runs/{arm}_step100"
        _manifest(step0_dir, arm, "step0")
        _manifest(step100_dir, arm, "step100")
        _write_jsonl(step0_dir / "per_item.jsonl", step0_rows)
        _write_jsonl(step100_dir / "per_item.jsonl", step100_rows)
        runs[arm] = (f"runs/{arm}_step0", f"runs/{arm}_step100")
    return runs


def _build_planted(root: Path) -> None:
    _build_fixture(
        root,
        sources_n=PLANTED_N,
        q_of=PLANTED_Q,
        flips=PLANTED_FLIPS,
        a1_gain_plan={
            "s1": "all_gain",
            "s2": "all_gain",
            "s3": "all_gain",
            "s4": "all_gain",
            "s5": "unstable",
            "s6": "all_gain",
        },
        zero_count_items={
            ("a2_gray", f"q-s2-{position:03d}") for position in range(3)
        },
    )


def _build_constant_q(root: Path) -> None:
    """Three eligible strata, q_i = 0.25 everywhere -> constant q_bar vector."""
    _build_fixture(
        root,
        sources_n={"t1": 30, "t2": 30, "t3": 30},
        q_of={"t1": 0.25, "t2": 0.25, "t3": 0.25},
        flips={
            "a2_gray": {"t1": 0, "t2": 3, "t3": 6},
            "a2b_noimage": {"t1": 6, "t2": 3, "t3": 0},
            "a3_caption": {"t1": 0, "t2": 3, "t3": 6},
        },
        a1_gain_plan={"t1": "all_gain", "t2": "all_gain", "t3": "all_gain"},
    )


def _cli(
    root: Path,
    *,
    partial: bool = False,
    expected_eligible: int,
    expected_small_n: int,
    expected_rows: int,
    json_name: str = "out.json",
    md_name: str = "out.md",
) -> list[str]:
    args = [
        sys.executable,
        str(SCRIPT),
        "--root", str(root),
        "--heldout", "data/heldout.jsonl",
        "--json-output", f"reports/{json_name}",
        "--markdown-output", f"reports/{md_name}",
        "--bootstrap-draws", str(DRAWS),
        "--bootstrap-seed", str(SEED),
        "--expected-heldout-sha256", _sha256(root / "data/heldout.jsonl"),
        "--expected-heldout-rows", str(expected_rows),
        "--expected-eligible-strata", str(expected_eligible),
        "--expected-small-n-strata", str(expected_small_n),
    ]
    for arm in ARMS:
        args.extend(["--step0", f"{arm}=runs/{arm}_step0"])
    if partial:
        args.append("--partial")
    else:
        for arm in ARMS:
            args.extend(["--step100", f"{arm}=runs/{arm}_step100"])
        args.extend(["--artifact-dir", "reports/artifacts"])
    return args


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True)


def _run_planted(root: Path, **kwargs) -> dict:
    result = _run(
        _cli(root, expected_eligible=5, expected_small_n=1, expected_rows=179, **kwargs)
    )
    assert result.returncode == 0, result.stderr
    return json.loads((root / "reports/out.json").read_text(encoding="utf-8"))


def _stratum_row(payload: dict, source: str) -> dict:
    rows = [row for row in payload["stratum_table"] if row["source"] == source]
    assert len(rows) == 1, f"expected exactly one stratum row for {source}"
    return rows[0]


# --------------------------------------------------------------------------
# a. planted sign recovery
# --------------------------------------------------------------------------

def test_planted_rank_correlations_recover_the_sign(tmp_path: Path) -> None:
    _build_planted(tmp_path)
    payload = _run_planted(tmp_path)
    stats = payload["rank_statistics"]

    assert abs(stats["a2_gray"]["rho_gain"]["estimate"] - 1.0) < 1e-9
    assert abs(stats["a3_caption"]["rho_gain"]["estimate"] - 1.0) < 1e-9
    assert abs(stats["a2b_noimage"]["rho_gain"]["estimate"] + 1.0) < 1e-9
    assert stats["a2_gray"]["rho_gain"]["direction_holds"] is True
    assert stats["a2b_noimage"]["rho_gain"]["direction_holds"] is False

    assert abs(stats["a2_gray"]["rho_recovery"]["estimate"] - 1.0) < 1e-9
    assert abs(stats["a2b_noimage"]["rho_recovery"]["estimate"] + 1.0) < 1e-9
    assert stats["a2_gray"]["rho_recovery"]["direction_holds"] is True
    assert stats["a2b_noimage"]["rho_recovery"]["direction_holds"] is False

    for arm in BLIND_ARMS:
        assert stats[arm]["rho_gain"]["n_strata"] == 5
        bootstrap = stats[arm]["rho_gain"]["bootstrap"]
        assert bootstrap["draws"] == DRAWS
        assert bootstrap["undefined_draw_count"] == 0
        assert bootstrap["interval_label"] == "stable"
        assert bootstrap["ci95"] is not None

    # Hand-computed stratum quantities: q_bar constant within stratum; the
    # a2_gray gain in s4 is 9/30 = 0.3 exactly.
    s4 = _stratum_row(payload, "s4")
    assert abs(s4["q_bar"]["a2_gray"] - 0.4) < 1e-12
    assert abs(s4["gain"]["a2_gray"]["estimate"] - 0.3) < 1e-12
    assert s4["gain"]["a1_real"]["estimate"] == 1.0

    # M10: exactly the three planted 0/16 flipped items, all in a2_gray.
    support = payload["support_sharpening"]["arms"]
    assert support["a2_gray"]["candidate_count"] == 3
    assert support["a1_real"]["candidate_count"] == 0
    assert support["a2b_noimage"]["candidate_count"] == 0
    assert support["a3_caption"]["candidate_count"] == 0


# --------------------------------------------------------------------------
# b. unstable A1 denominator
# --------------------------------------------------------------------------

def test_unstable_a1_denominator_excluded_from_recovery_only(tmp_path: Path) -> None:
    _build_planted(tmp_path)
    payload = _run_planted(tmp_path)

    s5 = _stratum_row(payload, "s5")
    assert s5["eligible"] is True
    # A1 gain mean 2/30 is positive but far below two paired SEs.
    assert abs(s5["a1_denominator"]["estimate"] - 2 / 30) < 1e-12
    assert s5["a1_denominator"]["estimate"] > 0
    assert (
        s5["a1_denominator"]["estimate"]
        < 2 * s5["a1_denominator"]["paired_se"]
    )
    assert s5["a1_denominator"]["stable"] is False
    # PRESENT in the gain table...
    assert abs(s5["gain"]["a2_gray"]["estimate"] - 0.4) < 1e-12
    # ...but recovery is undefined and EXCLUDED from rho_recovery.
    for arm in BLIND_ARMS:
        assert s5["recovery"][arm] == {"status": "undefined-unstable-denominator"}
    for arm in BLIND_ARMS:
        recovery = payload["rank_statistics"][arm]["rho_recovery"]
        assert recovery["n_strata"] == 5
        assert recovery["n_recovery_strata"] == 4
        assert recovery["excluded_unstable_strata"] == ["s5||cat"]
        assert "s5||cat" not in recovery["recovery_strata"]

    # A stable stratum's recovery is the plain ratio: a2_gray s4 = 0.3 / 1.0.
    s4 = _stratum_row(payload, "s4")
    assert s4["recovery"]["a2_gray"]["status"] == "stable"
    assert abs(s4["recovery"]["a2_gray"]["estimate"] - 0.3) < 1e-12


# --------------------------------------------------------------------------
# c. constant q_bar vector -> undefined draws counted, interval unstable
# --------------------------------------------------------------------------

def test_constant_q_bar_yields_undefined_and_unstable_interval(tmp_path: Path) -> None:
    _build_constant_q(tmp_path)
    result = _run(
        _cli(tmp_path, expected_eligible=3, expected_small_n=0, expected_rows=90)
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads((tmp_path / "reports/out.json").read_text(encoding="utf-8"))
    for arm in BLIND_ARMS:
        for statistic in ("rho_gain", "rho_recovery"):
            stat = payload["rank_statistics"][arm][statistic]
            assert stat["estimate"] is None
            assert stat["status"] == "undefined-constant-rank-vector"
            bootstrap = stat["bootstrap"]
            # Every draw has a constant q_bar rank vector: all undefined,
            # counted rather than replaced with zero, and > 5% -> unstable.
            assert bootstrap["undefined_draw_count"] == DRAWS
            assert bootstrap["defined_draw_count"] == 0
            assert bootstrap["undefined_fraction"] == 1.0
            assert bootstrap["ci95"] is None
            assert bootstrap["interval_label"] == "unstable"


# --------------------------------------------------------------------------
# d. missing step-100 item -> hard failure
# --------------------------------------------------------------------------

def test_item_missing_at_step100_fails_loudly(tmp_path: Path) -> None:
    _build_planted(tmp_path)
    per_item = tmp_path / "runs/a2_gray_step100/per_item.jsonl"
    lines = per_item.read_text(encoding="utf-8").splitlines(keepends=True)
    per_item.write_text("".join(lines[:-1]), encoding="utf-8")

    result = _run(
        _cli(tmp_path, expected_eligible=5, expected_small_n=1, expected_rows=179)
    )
    assert result.returncode != 0
    assert "pairing" in result.stderr
    assert "missing at step 100" in result.stderr
    assert not (tmp_path / "reports/out.json").exists()


# --------------------------------------------------------------------------
# e. eligibility is a pure sample-count rule; recount assertion is hard
# --------------------------------------------------------------------------

def test_stratum_eligibility_threshold_and_recount_assertion(tmp_path: Path) -> None:
    _build_planted(tmp_path)
    payload = _run_planted(tmp_path)

    s6 = _stratum_row(payload, "s6")  # 29 items
    assert s6["n"] == 29
    assert s6["eligible"] is False
    assert s6["label"] == "descriptive-small-n"
    s1 = _stratum_row(payload, "s1")  # 30 items
    assert s1["n"] == 30
    assert s1["eligible"] is True
    assert s1["label"] == "eligible"
    assert payload["strata"]["eligible_count"] == 5
    assert payload["strata"]["small_n_count"] == 1

    # The recount assertion fails loudly on a wrong expectation.
    wrong = _cli(tmp_path, expected_eligible=4, expected_small_n=2,
                 expected_rows=179, json_name="wrong.json", md_name="wrong.md")
    result = _run(wrong)
    assert result.returncode != 0
    assert "stratum eligibility recount mismatch" in result.stderr


# --------------------------------------------------------------------------
# f. determinism at seed 20260716
# --------------------------------------------------------------------------

def test_two_runs_at_registered_seed_are_byte_identical(tmp_path: Path) -> None:
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    _build_planted(root_a)
    shutil.copytree(root_a, root_b)
    payload_a = _run_planted(root_a)
    payload_b = _run_planted(root_b)
    assert payload_a == payload_b
    bytes_a = (root_a / "reports/out.json").read_bytes()
    bytes_b = (root_b / "reports/out.json").read_bytes()
    assert bytes_a == bytes_b
    assert (root_a / "reports/out.md").read_bytes() == (
        root_b / "reports/out.md"
    ).read_bytes()


# --------------------------------------------------------------------------
# g. readiness gate on incomplete runs; partial mode refuses estimands
# --------------------------------------------------------------------------

def test_incomplete_run_manifest_is_refused(tmp_path: Path) -> None:
    _build_planted(tmp_path)
    manifest = tmp_path / "runs/a2_gray_step0/run_manifest.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["status"] = "running"
    manifest.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

    result = _run(
        _cli(tmp_path, expected_eligible=5, expected_small_n=1, expected_rows=179)
    )
    assert result.returncode != 0
    assert "readiness gate failed" in result.stderr
    assert "'running'" in result.stderr


def test_partial_mode_computes_step0_only_and_refuses_estimands(
    tmp_path: Path,
) -> None:
    _build_planted(tmp_path)
    result = _run(
        _cli(
            tmp_path,
            partial=True,
            expected_eligible=5,
            expected_small_n=1,
            expected_rows=179,
        )
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads((tmp_path / "reports/out.json").read_text(encoding="utf-8"))
    assert payload["status"] == "partial-step0-only"
    # Step-0 quantities are present; corpus q_bar is the hand-computed mean:
    # (30 * (0.1+0.2+0.3+0.4+0.5) + 29 * 0.15) / 179.
    expected_q_bar = (30 * 1.5 + 29 * 0.15) / 179
    for arm in ARMS:
        corpus_arm = payload["corpus"]["arms"][arm]
        assert abs(corpus_arm["q_bar"] - expected_q_bar) < 1e-12
        assert "acc_final_step0" in corpus_arm
        assert "gain" not in corpus_arm
        assert "acc_final_step100" not in corpus_arm
    # Every downstream estimand is refused, not silently zeroed.
    assert "rank_statistics" not in payload
    assert "support_sharpening" not in payload
    assert "aggregate_recovery" not in payload["corpus"]
    assert "geometry3k_anchor_comparison" not in payload["corpus"]
    for row in payload["stratum_table"]:
        assert "gain" not in row
        assert "recovery" not in row
    refused = set(payload["partial_mode"]["refused_estimands"])
    assert {"gain", "recovery", "rho_gain", "rho_recovery"} <= refused

    markdown = (tmp_path / "reports/out.md").read_text(encoding="utf-8")
    assert "PARTIAL" in markdown

    # --partial with --step100 is a usage error.
    bad = _cli(
        tmp_path,
        partial=True,
        expected_eligible=5,
        expected_small_n=1,
        expected_rows=179,
        json_name="bad.json",
        md_name="bad.md",
    )
    for arm in ARMS:
        bad.extend(["--step100", f"{arm}=runs/{arm}_step100"])
    result = _run(bad)
    assert result.returncode != 0
    assert "--partial forbids --step100" in result.stderr


# --------------------------------------------------------------------------
# registered defaults are pinned in the CLI
# --------------------------------------------------------------------------

def test_registered_defaults_are_pinned() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("build_m7_r3_readout", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.REGISTERED_BOOTSTRAP_DRAWS == 5000
    assert module.REGISTERED_BOOTSTRAP_SEED == 20260716
    assert module.REGISTERED_ELIGIBLE_STRATA == 22
    assert module.REGISTERED_SMALL_N_STRATA == 38
    assert module.REGISTERED_HELDOUT_ROWS == 4239
    assert module.REGISTERED_HELDOUT_SHA256 == (
        "50f3b85c11c4046ef2512c544faec04286648688bb6d47548995f18cab40716c"
    )
    assert module.GEO3K_ANCHORS == {"a2_gray": 0.0789, "a2b_noimage": 0.1184}
    assert module.ELIGIBILITY_THRESHOLD == 30
    assert module.UNSTABLE_UNDEFINED_FRACTION == 0.05
