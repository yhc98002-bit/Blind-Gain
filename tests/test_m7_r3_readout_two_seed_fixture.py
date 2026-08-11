"""Adversarial fixtures for the REGISTERED TWO-SEED R3 readout (I10).

Target: scripts/build_m7_r3_readout.py --step100-seed2 (schema
`blind-gains.m7-r3-readout.v2`). Every fixture is synthetic and hand-verifiable;
no test in this file touches a real M7 run directory.

The registered estimand under test (docs/registered_m7_amendment_v1.md:52-53):

    "gain[b,s] is the mean across the two fixed M7 seeds of
     Acc_final(step_final) - Acc_final(step_0) on paired held-out items."

Step 0 is the shared base model and is never checkpointed
(docs/registered_m7_seed_scope_v1.md:62-64, docs/registered_pilot_seed23_v1.md:19),
so one step-0 cell per arm serves both seeds and the estimand reduces per item to
`(acc100_seed1 + acc100_seed2) / 2 - acc0`.

Failure modes each test targets:

  a. the seed mean is taken at the ITEM level, not by averaging per-seed
     statistics: the planted fixture is built so that rho_gain[a2_gray] is
     -1 at seed 1, +1 at seed 2, and +1 on the registered two-seed mean, and
     every two-seed stratum gain is asserted against an exact hand-computed
     fraction;
  b. items are NOT stacked across seeds: n stays 179 at corpus level and 30 per
     eligible stratum, and q_bar is bit-identical to the one-seed readout;
  c. a run directory whose own manifest disagrees with its CLI (arm, seed) key
     is refused -- seed mislabel, arm mislabel, and a step-0 cell that names a
     seeded training checkpoint;
  d. an incomplete seed-2 arm set (1, 2 or 3 arms) is refused: recovery divides
     a two-seed blind gain by a two-seed A1 gain and no mixed-seed form is
     registered;
  e. an item set that differs across seeds is refused by the cross-seed pairing
     gate ("preserving item identity across step 0, all arms, and both seeds",
     docs/registered_m7_amendment_v1.md:71-73);
  f. a seed-2 run manifest with status != complete is refused before any
     estimand;
  g. determinism: two two-seed runs at seed 20260716 are byte-identical;
  h. REGRESSION: the seed-1 code path is unchanged. The planted seed-1 fixture
     output is pinned to sha256 goldens produced by
     scripts/build_m7_r3_readout.py BEFORE the two-seed extension
     (script sha256 b1b1ab4858968b8926ff636d8e81db25c58cbd216dd41dbead39fd8dea84b8af);
  i. M10 support-sharpening candidate lists are per seed and never merged: no
     union/intersection rule is registered (docs/registered_extensions_v1.md:142).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_m7_r3_readout.py"

# Reuse the seed-1 fixture module's builders by path so the seed-1 regression
# golden below is produced by exactly the bytes the committed seed-1 suite uses.
# Loading under a private module name keeps pytest from collecting it twice.
_SEED1_FIXTURE_PATH = Path(__file__).resolve().parent / "test_m7_r3_readout_fixture.py"
_spec = importlib.util.spec_from_file_location(
    "_m7_r3_seed1_fixture", _SEED1_FIXTURE_PATH
)
seed1_fixture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(seed1_fixture)

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
SEEDS = (1, 2)

SCHEMA_V1 = "blind-gains.m7-r3-readout.v1"
SCHEMA_V2 = "blind-gains.m7-r3-readout.v2"
TAG_V1 = "one seed (seed 1)"
TAG_V2 = "two seeds (seeds 1, 2; registered two-seed mean)"

# Goldens for the seed-1 planted fixture, produced by the pre-extension script
# (scripts/build_m7_r3_readout.py at sha256 b1b1ab48...) on 2026-08-11. They pin
# the claim "the seed-1 code path still produces identical results" to bytes.
SEED1_GOLDEN_JSON_SHA256 = (
    "d103d2bcb6454a29d27eb0e1235f3f0070cc604ab0de7e196cfb4bcae7641c81"
)
SEED1_GOLDEN_MD_SHA256 = (
    "bac41283aebb152cfb916fba88a70a5e91760d3bb4c905327aba70b144390679"
)

BASE_MODEL_PATH = "artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct"


def _checkpoint_path(arm: str, seed: int, step: int = 100) -> str:
    return (
        f"checkpoints/m7/m7_virl_{arm}_seed{seed}/global_step_{step}/"
        "actor/huggingface"
    )


# --------------------------------------------------------------------------
# Two-seed planted fixture
# --------------------------------------------------------------------------
#
# Six joint strata, one category, sources s1..s6; s1..s5 have 30 items
# (eligible), s6 has 29 (descriptive-small-n); 179 rows in total.
# q_i is constant within stratum: s1 0.1, s2 0.2, s3 0.3, s4 0.4, s5 0.5,
# s6 0.15 -- identical for both seeds, because q_i comes from the SHARED
# step-0 cells.
#
# A1 is identical at both seeds (s1..s4, s6 every item flips wrong->correct;
# s5 is the engineered unstable denominator: 15 items +1, 13 items -1, 2 items
# 0 -> mean 2/30, far below two paired SEs). The two-seed A1 vector therefore
# equals the seed-1 A1 vector item for item, which keeps the registered
# stability structure hand-checkable.
#
# Blind-arm step-100 flip counts (acc0 is False everywhere, so a stratum's gain
# is flips / n and the two-seed stratum gain is (flips_s1 + flips_s2) / (2n)):
#
#              s1   s2   s3   s4   s5      per-seed rho_gain
#   a2_gray  seed1  12    9    6    3    0        -1  (strictly decreasing)
#            seed2   0    7   14   21   28        +1  (strictly increasing)
#            SUM    12   16   20   24   28        +1  <- REGISTERED two-seed
#
#   a2b      seed1  12    9    6    3    0        -1
#            seed2  16   12    8    4    0        -1
#            SUM    28   21   14    7    0        -1
#
#   a3       seed1   0    3    6    9   12        +1
#            seed2   0    3    6    9   12        +1   (seeds identical:
#            SUM     0    6   12   18   24        +1    the control arm)
#
# a2_gray is the load-bearing arm: the registered two-seed verdict (+1) has the
# OPPOSITE SIGN to seed 1 alone (-1). A readout that averaged per-seed rho
# values would report 0; one that read seed 1 only would report a failed
# direction. Only a per-item seed mean gives +1.

TWO_SEED_Q = {"s1": 0.1, "s2": 0.2, "s3": 0.3, "s4": 0.4, "s5": 0.5, "s6": 0.15}
TWO_SEED_N = {"s1": 30, "s2": 30, "s3": 30, "s4": 30, "s5": 30, "s6": 29}
TWO_SEED_A1_PLAN = {
    "s1": "all_gain",
    "s2": "all_gain",
    "s3": "all_gain",
    "s4": "all_gain",
    "s5": "unstable",
    "s6": "all_gain",
}
TWO_SEED_FLIPS = {
    1: {
        "a2_gray": {"s1": 12, "s2": 9, "s3": 6, "s4": 3, "s5": 0, "s6": 2},
        "a2b_noimage": {"s1": 12, "s2": 9, "s3": 6, "s4": 3, "s5": 0, "s6": 2},
        "a3_caption": {"s1": 0, "s2": 3, "s3": 6, "s4": 9, "s5": 12, "s6": 1},
    },
    2: {
        "a2_gray": {"s1": 0, "s2": 7, "s3": 14, "s4": 21, "s5": 28, "s6": 1},
        "a2b_noimage": {"s1": 16, "s2": 12, "s3": 8, "s4": 4, "s5": 0, "s6": 1},
        "a3_caption": {"s1": 0, "s2": 3, "s3": 6, "s4": 9, "s5": 12, "s6": 1},
    },
}
# M10: base 0/16 items planted only in a2_gray. s1 positions 0,1 flip at seed 1
# (12 flips) but not at seed 2 (0 flips); s2 positions 0,1,2 flip at both
# (9 and 7 flips). Hand count: a2_gray seed 1 -> 5 candidates, seed 2 -> 3.
TWO_SEED_ZERO_COUNT = {("a2_gray", "q-s1-000"), ("a2_gray", "q-s1-001")} | {
    ("a2_gray", f"q-s2-{position:03d}") for position in range(3)
}

ELIGIBLE_SOURCES = ("s1", "s2", "s3", "s4", "s5")
CORPUS_ROWS = 179


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest(
    run_dir: Path,
    arm: str,
    step: str,
    *,
    status: str = "complete",
    model_path: str,
) -> None:
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
                "model_path": model_path,
                "model_revision": "fixture@" + "9" * 40,
                # The real manifests' `seed` field is the fixed intervention /
                # decoding seed, NOT data.seed; the fixture mirrors that so the
                # label gate cannot accidentally start trusting it.
                "seed": 20260710,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def build_two_seed_fixture(
    root: Path,
    *,
    sources_n: dict[str, int] = TWO_SEED_N,
    q_of: dict[str, float] = TWO_SEED_Q,
    flips_by_seed: dict[int, dict[str, dict[str, int]]] = TWO_SEED_FLIPS,
    a1_plan: dict[str, str] = TWO_SEED_A1_PLAN,
    zero_count_items: set[tuple[str, str]] = TWO_SEED_ZERO_COUNT,
) -> None:
    """Write a held-out manifest plus 12 fixture runs (4 arms x step0 + 2 seeds)."""
    items = seed1_fixture._item_ids(sources_n)
    heldout_rows = [
        {
            "schema_version": "fixture-heldout.v1",
            "split": "train",
            "qid": qid,
            "row_index": row_index,
            "problem": f"problem {qid}",
            "answer": "42",
            "images": [f"images/{qid}.png"],
            "metadata": {
                "source": source,
                "category": "cat",
                "image_sha256": ["e" * 64],
            },
        }
        for source, qid, row_index in items
    ]
    seed1_fixture._write_jsonl(root / "data/heldout.jsonl", heldout_rows)

    for arm in ARMS:
        step0_rows: list[dict] = []
        per_seed_rows: dict[int, list[dict]] = {seed: [] for seed in SEEDS}
        for source, qid, row_index in items:
            q = q_of[source]
            count = 0 if (arm, qid) in zero_count_items else 4
            position = int(qid.rsplit("-", 1)[1])
            if arm == "a1_real":
                plan = a1_plan[source]
                if plan == "all_gain":
                    acc0, acc100 = False, True
                elif plan == "unstable":
                    if position < 15:
                        acc0, acc100 = False, True
                    elif position < 28:
                        acc0, acc100 = True, False
                    else:
                        acc0, acc100 = False, False
                else:
                    raise AssertionError(plan)
                acc100_of_seed = {seed: acc100 for seed in SEEDS}
            else:
                acc0 = False
                acc100_of_seed = {
                    seed: position < flips_by_seed[seed][arm][source]
                    for seed in SEEDS
                }
            step0_rows.append(
                seed1_fixture._per_item_row(
                    arm, qid, row_index, q=q, correct=acc0, count=count
                )
            )
            for seed in SEEDS:
                per_seed_rows[seed].append(
                    seed1_fixture._per_item_row(
                        arm,
                        qid,
                        row_index,
                        q=q,
                        correct=acc100_of_seed[seed],
                        step0=False,
                    )
                )
        step0_dir = root / f"runs/{arm}_step0"
        _manifest(step0_dir, arm, "step0", model_path=BASE_MODEL_PATH)
        seed1_fixture._write_jsonl(step0_dir / "per_item.jsonl", step0_rows)
        for seed in SEEDS:
            run_dir = root / f"runs/{arm}_step100_seed{seed}"
            _manifest(
                run_dir,
                arm,
                f"step100_seed{seed}",
                model_path=_checkpoint_path(arm, seed),
            )
            seed1_fixture._write_jsonl(
                run_dir / "per_item.jsonl", per_seed_rows[seed]
            )


def _cli_two_seed(
    root: Path,
    *,
    seed2_arms: tuple[str, ...] = ARMS,
    json_name: str = "out.json",
    md_name: str = "out.md",
    artifact_dir: str = "reports/artifacts",
    expected_eligible: int = 5,
    expected_small_n: int = 1,
    expected_rows: int = CORPUS_ROWS,
    seed2_dir_of=None,
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
        "--artifact-dir", artifact_dir,
    ]
    for arm in ARMS:
        args.extend(["--step0", f"{arm}=runs/{arm}_step0"])
        args.extend(["--step100", f"{arm}=runs/{arm}_step100_seed1"])
    for arm in seed2_arms:
        value = (
            seed2_dir_of(arm)
            if seed2_dir_of is not None
            else f"runs/{arm}_step100_seed2"
        )
        args.extend(["--step100-seed2", f"{arm}={value}"])
    return args


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True)


def _run_two_seed(root: Path, **kwargs) -> dict:
    result = _run(_cli_two_seed(root, **kwargs))
    assert result.returncode == 0, result.stderr
    name = kwargs.get("json_name", "out.json")
    return json.loads((root / f"reports/{name}").read_text(encoding="utf-8"))


def _stratum_row(payload: dict, source: str) -> dict:
    rows = [row for row in payload["stratum_table"] if row["source"] == source]
    assert len(rows) == 1, f"expected exactly one stratum row for {source}"
    return rows[0]


def _two_seed_gain(arm: str, source: str) -> float:
    """Hand-computed registered estimand for a blind arm (acc0 is False)."""
    total = sum(TWO_SEED_FLIPS[seed][arm][source] for seed in SEEDS)
    return total / (len(SEEDS) * TWO_SEED_N[source])


# --------------------------------------------------------------------------
# a. the registered two-seed estimand, recovered EXACTLY
# --------------------------------------------------------------------------

def test_two_seed_estimand_matches_hand_computed_values(tmp_path: Path) -> None:
    build_two_seed_fixture(tmp_path)
    payload = _run_two_seed(tmp_path)

    # I15: a two-seed payload carries its own schema version, and the scope tag
    # is present and true rather than dropped.
    assert payload["schema_version"] == SCHEMA_V2
    assert payload["seed_scope"]["tag"] == TAG_V2
    assert payload["seed_scope"]["seeds"] == [1, 2]
    assert payload["seed_scope"]["seed_mean_is_taken"].startswith("per item")
    assert "one seed" not in payload["seed_scope"]["tag"]

    # Every eligible stratum's two-seed gain equals (f1 + f2) / (2n) exactly.
    for source in ELIGIBLE_SOURCES:
        row = _stratum_row(payload, source)
        for arm in BLIND_ARMS:
            expected = _two_seed_gain(arm, source)
            assert abs(row["gain"][arm]["estimate"] - expected) < 1e-12, (
                source,
                arm,
            )
        # A1 is identical at both seeds, so the registered structure is intact.
        if source == "s5":
            assert abs(row["gain"]["a1_real"]["estimate"] - 2 / 30) < 1e-12
            assert row["a1_denominator"]["stable"] is False
        else:
            assert row["gain"]["a1_real"]["estimate"] == 1.0
            assert row["a1_denominator"]["stable"] is True

    # Spot value: a2_gray in s4 is (3 + 21) / 60 = 0.4 exactly, and because the
    # A1 denominator there is 1.0 the recovery is the same number.
    s4 = _stratum_row(payload, "s4")
    assert abs(s4["gain"]["a2_gray"]["estimate"] - 24 / 60) < 1e-12
    assert abs(s4["q_bar"]["a2_gray"] - 0.4) < 1e-12
    assert s4["recovery"]["a2_gray"]["status"] == "stable"
    assert abs(s4["recovery"]["a2_gray"]["estimate"] - 24 / 60) < 1e-12

    # Unstable A1 stratum still publishes its gain and is excluded from
    # recovery only -- unchanged by the second seed.
    s5 = _stratum_row(payload, "s5")
    assert s5["eligible"] is True
    for arm in BLIND_ARMS:
        assert s5["recovery"][arm] == {"status": "undefined-unstable-denominator"}

    # Registered rank statistics, on the two-seed mean.
    stats = payload["rank_statistics"]
    assert abs(stats["a2_gray"]["rho_gain"]["estimate"] - 1.0) < 1e-9
    assert abs(stats["a3_caption"]["rho_gain"]["estimate"] - 1.0) < 1e-9
    assert abs(stats["a2b_noimage"]["rho_gain"]["estimate"] + 1.0) < 1e-9
    assert abs(stats["a2_gray"]["rho_recovery"]["estimate"] - 1.0) < 1e-9
    assert abs(stats["a2b_noimage"]["rho_recovery"]["estimate"] + 1.0) < 1e-9
    for arm in BLIND_ARMS:
        assert stats[arm]["rho_gain"]["n_strata"] == 5
        assert stats[arm]["rho_recovery"]["n_recovery_strata"] == 4
        assert stats[arm]["rho_recovery"]["excluded_unstable_strata"] == ["s5||cat"]

    # Corpus aggregate: 4,239-style two-point contrast over 179 items.
    #   a1  gain = (4*30 + 2 + 29) / 179            = 151/179
    #   a2  gain = (32 + 71) / (2*179)              = 103/358
    #   recovery = (103/358) / (151/179)            = 103/302
    corpus = payload["corpus"]
    assert abs(corpus["arms"]["a1_real"]["gain"]["estimate"] - 151 / 179) < 1e-12
    assert abs(corpus["arms"]["a2_gray"]["gain"]["estimate"] - 103 / 358) < 1e-12
    assert abs(corpus["arms"]["a2b_noimage"]["gain"]["estimate"] - 73 / 358) < 1e-12
    assert abs(corpus["arms"]["a3_caption"]["gain"]["estimate"] - 62 / 358) < 1e-12
    assert corpus["a1_denominator"]["stable"] is True
    assert (
        abs(corpus["aggregate_recovery"]["a2_gray"]["estimate"] - 103 / 302) < 1e-12
    )
    assert (
        abs(corpus["aggregate_recovery"]["a2b_noimage"]["estimate"] - 73 / 302)
        < 1e-12
    )


# --------------------------------------------------------------------------
# a'. the seed mean is taken PER ITEM, not by averaging per-seed statistics
# --------------------------------------------------------------------------

def test_seed_mean_is_per_item_and_can_flip_the_seed1_sign(tmp_path: Path) -> None:
    build_two_seed_fixture(tmp_path)
    payload = _run_two_seed(tmp_path)

    dispersion = payload["seed_dispersion"]
    per_seed = dispersion["per_seed"]

    # Planted disagreement: seed 1 alone gives -1, seed 2 alone gives +1.
    assert abs(per_seed["seed1"]["rank_statistics"]["a2_gray"]["rho_gain"] + 1.0) < 1e-9
    assert abs(per_seed["seed2"]["rank_statistics"]["a2_gray"]["rho_gain"] - 1.0) < 1e-9
    # The REGISTERED number is the two-seed mean, and it is +1: neither the
    # seed-1 value (-1) nor the mean of the two per-seed rho values (0) is it.
    assert abs(payload["rank_statistics"]["a2_gray"]["rho_gain"]["estimate"] - 1.0) < 1e-9
    mean_of_per_seed_rho = (
        per_seed["seed1"]["rank_statistics"]["a2_gray"]["rho_gain"]
        + per_seed["seed2"]["rank_statistics"]["a2_gray"]["rho_gain"]
    ) / 2
    assert abs(mean_of_per_seed_rho) < 1e-9
    assert (
        abs(
            payload["rank_statistics"]["a2_gray"]["rho_gain"]["estimate"]
            - mean_of_per_seed_rho
        )
        > 0.5
    )

    # Per-seed corpus gains are the plain one-seed numbers: 32/179 and 71/179.
    assert abs(per_seed["seed1"]["corpus"]["a2_gray"]["gain"] - 32 / 179) < 1e-12
    assert abs(per_seed["seed2"]["corpus"]["a2_gray"]["gain"] - 71 / 179) < 1e-12
    assert abs(dispersion["differences"]["corpus_gain"]["a2_gray"] + 39 / 179) < 1e-12
    assert abs(dispersion["differences"]["rho_gain"]["a2_gray"] + 2.0) < 1e-9

    # Dispersion is DESCRIPTIVE: no interval, no test, no seed-level claim, and
    # every per-seed block carries its own honest one-seed tag.
    assert dispersion["inference_permitted"] is False
    assert dispersion["n_seeds"] == 2
    assert per_seed["seed1"]["scope_tag"] == "one seed (seed 1)"
    assert per_seed["seed2"]["scope_tag"] == "one seed (seed 2)"
    for seed_key in ("seed1", "seed2"):
        blob = json.dumps(per_seed[seed_key])
        assert "ci95" not in blob
        assert "p_value" not in blob
        assert "significant" not in blob

    # NO registered branch keys on seed disagreement: the direction verdict is
    # read off the two-seed mean and fires exactly as it would with one seed.
    gain_stat = payload["rank_statistics"]["a2_gray"]["rho_gain"]
    assert gain_stat["status"] == "computed"
    assert gain_stat["direction_registered"] == "rho_gain > 0"
    assert gain_stat["direction_holds"] is True
    assert payload["rank_statistics"]["a2b_noimage"]["rho_gain"]["direction_holds"] is False
    assert payload["status"] == "complete"
    payload_text = json.dumps(payload)
    for forbidden in (
        "seed_disagreement",
        "seeds_disagree",
        "seed_conflict",
        "seed_level_ci",
        "seed_p_value",
    ):
        assert forbidden not in payload_text


# --------------------------------------------------------------------------
# b. items are never stacked across seeds; q_bar is seed-free
# --------------------------------------------------------------------------

def test_two_seed_readout_does_not_pool_items_across_seeds(tmp_path: Path) -> None:
    build_two_seed_fixture(tmp_path)
    two_seed = _run_two_seed(tmp_path)
    one_seed_args = _cli_two_seed(
        tmp_path,
        seed2_arms=(),
        json_name="one_seed.json",
        md_name="one_seed.md",
        artifact_dir="reports/artifacts_one_seed",
    )
    result = _run(one_seed_args)
    assert result.returncode == 0, result.stderr
    one_seed = json.loads(
        (tmp_path / "reports/one_seed.json").read_text(encoding="utf-8")
    )

    # n is the item count, not the item-seed count.
    for arm in ARMS:
        assert two_seed["corpus"]["arms"][arm]["n"] == CORPUS_ROWS
        assert one_seed["corpus"]["arms"][arm]["n"] == CORPUS_ROWS
        assert two_seed["corpus"]["arms"][arm]["gain"]["n"] == CORPUS_ROWS
    for source in ELIGIBLE_SOURCES:
        row = _stratum_row(two_seed, source)
        assert row["n"] == TWO_SEED_N[source]
        for arm in ARMS:
            assert row["gain"][arm]["n"] == TWO_SEED_N[source]
    assert two_seed["strata"] == one_seed["strata"]

    # q_bar comes from the shared step-0 cells and is bit-identical.
    for arm in ARMS:
        assert (
            two_seed["corpus"]["arms"][arm]["q_bar"]
            == one_seed["corpus"]["arms"][arm]["q_bar"]
        )
        assert (
            two_seed["corpus"]["arms"][arm]["acc_final_step0"]
            == one_seed["corpus"]["arms"][arm]["acc_final_step0"]
        )
    for source in list(TWO_SEED_N):
        assert (
            _stratum_row(two_seed, source)["q_bar"]
            == _stratum_row(one_seed, source)["q_bar"]
        )

    # The one-seed sibling really is the seed-1 readout, tag and schema intact.
    assert one_seed["schema_version"] == SCHEMA_V1
    assert one_seed["seed_scope"]["tag"] == TAG_V1
    assert "seed_dispersion" not in one_seed
    # ... and the blind arms are still three separate arms in both payloads
    # (docs/registered_m7_amendment_v1.md:107).
    assert set(two_seed["rank_statistics"]) == set(BLIND_ARMS)
    assert set(two_seed["corpus"]["aggregate_recovery"]) == set(BLIND_ARMS)
    assert len(two_seed["stratum_table"]) == len(TWO_SEED_N)
    assert set(two_seed["descriptive_views"]) == {"source_only", "category_only"}


# --------------------------------------------------------------------------
# c. a run dir whose manifest disagrees with its CLI (arm, seed) key
# --------------------------------------------------------------------------

def _rewrite_manifest(path: Path, **updates) -> None:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest.update(updates)
    path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")


def test_seed_mislabelled_run_is_refused(tmp_path: Path) -> None:
    build_two_seed_fixture(tmp_path)
    # The a2_gray seed-2 run now claims to be the seed-1 checkpoint.
    _rewrite_manifest(
        tmp_path / "runs/a2_gray_step100_seed2/run_manifest.json",
        model_path=_checkpoint_path("a2_gray", 1),
    )
    result = _run(_cli_two_seed(tmp_path))
    assert result.returncode != 0
    assert "arm/seed label gate failed" in result.stderr
    assert "CLI key says seed 2 but the run's own checkpoint says seed 1" in result.stderr
    assert not (tmp_path / "reports/out.json").exists()
    assert not (tmp_path / "reports/out.md").exists()


def test_arm_mislabelled_run_is_refused(tmp_path: Path) -> None:
    build_two_seed_fixture(tmp_path)
    _rewrite_manifest(
        tmp_path / "runs/a3_caption_step100_seed2/run_manifest.json",
        model_path=_checkpoint_path("a2_gray", 2),
    )
    result = _run(_cli_two_seed(tmp_path))
    assert result.returncode != 0
    assert "arm/seed label gate failed" in result.stderr
    assert "the run's own checkpoint says arm 'a2_gray'" in result.stderr
    assert not (tmp_path / "reports/out.json").exists()


def test_unlabelled_step100_run_is_refused(tmp_path: Path) -> None:
    build_two_seed_fixture(tmp_path)
    _rewrite_manifest(
        tmp_path / "runs/a1_real_step100_seed2/run_manifest.json",
        model_path="checkpoints/somewhere/else",
    )
    result = _run(_cli_two_seed(tmp_path))
    assert result.returncode != 0
    assert "cannot be verified against the CLI key" in result.stderr
    assert not (tmp_path / "reports/out.json").exists()


def test_step0_cell_naming_a_seeded_checkpoint_is_refused(tmp_path: Path) -> None:
    """step_0 is the shared base model and is never checkpointed."""
    build_two_seed_fixture(tmp_path)
    _rewrite_manifest(
        tmp_path / "runs/a1_real_step0/run_manifest.json",
        model_path=_checkpoint_path("a1_real", 1, step=0),
    )
    result = _run(_cli_two_seed(tmp_path))
    assert result.returncode != 0
    assert "arm/seed label gate failed" in result.stderr
    assert "step 0 is the shared frozen base model" in result.stderr
    assert not (tmp_path / "reports/out.json").exists()


def test_wrong_target_step_checkpoint_is_refused(tmp_path: Path) -> None:
    build_two_seed_fixture(tmp_path)
    _rewrite_manifest(
        tmp_path / "runs/a2b_noimage_step100_seed2/run_manifest.json",
        model_path=_checkpoint_path("a2b_noimage", 2, step=80),
    )
    result = _run(_cli_two_seed(tmp_path))
    assert result.returncode != 0
    assert "not the registered final step 100" in result.stderr
    assert not (tmp_path / "reports/out.json").exists()


# --------------------------------------------------------------------------
# d. an incomplete seed-2 arm set is refused
# --------------------------------------------------------------------------

def test_incomplete_seed2_arm_set_is_refused(tmp_path: Path) -> None:
    build_two_seed_fixture(tmp_path)
    for count in (1, 2, 3):
        subset = ARMS[:count]
        result = _run(
            _cli_two_seed(
                tmp_path,
                seed2_arms=subset,
                json_name=f"partial_{count}.json",
                md_name=f"partial_{count}.md",
                artifact_dir=f"reports/artifacts_{count}",
            )
        )
        assert result.returncode != 0, subset
        assert "--step100-seed2 missing for arms" in result.stderr
        assert "mixed-seed denominator has no registered definition" in result.stderr
        assert not (tmp_path / f"reports/partial_{count}.json").exists()
        assert not (tmp_path / f"reports/artifacts_{count}").exists()


def test_seed2_reusing_the_seed1_run_dir_is_refused(tmp_path: Path) -> None:
    build_two_seed_fixture(tmp_path)
    result = _run(
        _cli_two_seed(
            tmp_path, seed2_dir_of=lambda arm: f"runs/{arm}_step100_seed1"
        )
    )
    assert result.returncode != 0
    assert "repeats the seed-1 run directory" in result.stderr
    assert not (tmp_path / "reports/out.json").exists()


def test_partial_mode_forbids_seed2(tmp_path: Path) -> None:
    build_two_seed_fixture(tmp_path)
    args = [
        sys.executable,
        str(SCRIPT),
        "--root", str(tmp_path),
        "--heldout", "data/heldout.jsonl",
        "--json-output", "reports/partial.json",
        "--markdown-output", "reports/partial.md",
        "--bootstrap-draws", str(DRAWS),
        "--bootstrap-seed", str(SEED),
        "--expected-heldout-sha256", _sha256(tmp_path / "data/heldout.jsonl"),
        "--expected-heldout-rows", str(CORPUS_ROWS),
        "--expected-eligible-strata", "5",
        "--expected-small-n-strata", "1",
        "--partial",
    ]
    for arm in ARMS:
        args.extend(["--step0", f"{arm}=runs/{arm}_step0"])
        args.extend(["--step100-seed2", f"{arm}=runs/{arm}_step100_seed2"])
    result = _run(args)
    assert result.returncode != 0
    assert "--partial forbids --step100-seed2" in result.stderr
    assert not (tmp_path / "reports/partial.json").exists()


# --------------------------------------------------------------------------
# e. item identity must hold across step 0, all arms, AND both seeds
# --------------------------------------------------------------------------

def test_cross_seed_item_set_mismatch_is_refused(tmp_path: Path) -> None:
    build_two_seed_fixture(tmp_path)
    per_item = tmp_path / "runs/a2_gray_step100_seed2/per_item.jsonl"
    lines = per_item.read_text(encoding="utf-8").splitlines(keepends=True)
    per_item.write_text("".join(lines[:-1]), encoding="utf-8")

    result = _run(_cli_two_seed(tmp_path))
    assert result.returncode != 0
    assert "cross-seed pairing gate failed" in result.stderr
    assert "missing at step 100 seed 2" in result.stderr
    assert "item set differs from seed 1" in result.stderr
    assert not (tmp_path / "reports/out.json").exists()


def test_seed1_only_pairing_gate_still_fires_in_two_seed_mode(tmp_path: Path) -> None:
    build_two_seed_fixture(tmp_path)
    per_item = tmp_path / "runs/a3_caption_step100_seed1/per_item.jsonl"
    lines = per_item.read_text(encoding="utf-8").splitlines(keepends=True)
    per_item.write_text("".join(lines[:-1]), encoding="utf-8")

    result = _run(_cli_two_seed(tmp_path))
    assert result.returncode != 0
    assert "pairing" in result.stderr
    assert "missing at step 100" in result.stderr
    assert not (tmp_path / "reports/out.json").exists()


# --------------------------------------------------------------------------
# f. an incomplete seed-2 run manifest is refused before any estimand
# --------------------------------------------------------------------------

def test_incomplete_seed2_manifest_is_refused(tmp_path: Path) -> None:
    build_two_seed_fixture(tmp_path)
    _rewrite_manifest(
        tmp_path / "runs/a2b_noimage_step100_seed2/run_manifest.json",
        status="running",
    )
    result = _run(_cli_two_seed(tmp_path))
    assert result.returncode != 0
    assert "readiness gate failed" in result.stderr
    assert "'running'" in result.stderr
    assert "step100_seed2" in result.stderr
    assert not (tmp_path / "reports/out.json").exists()


def test_failed_seed2_manifest_is_refused(tmp_path: Path) -> None:
    build_two_seed_fixture(tmp_path)
    _rewrite_manifest(
        tmp_path / "runs/a2_gray_step100_seed2/run_manifest.json", status="fail"
    )
    result = _run(_cli_two_seed(tmp_path))
    assert result.returncode != 0
    assert "readiness gate failed" in result.stderr
    assert "'fail'" in result.stderr
    assert not (tmp_path / "reports/out.json").exists()


# --------------------------------------------------------------------------
# g. determinism at the registered bootstrap seed
# --------------------------------------------------------------------------

def test_two_seed_runs_at_registered_seed_are_byte_identical(tmp_path: Path) -> None:
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    build_two_seed_fixture(root_a)
    shutil.copytree(root_a, root_b)
    payload_a = _run_two_seed(root_a)
    payload_b = _run_two_seed(root_b)
    assert payload_a == payload_b
    assert (root_a / "reports/out.json").read_bytes() == (
        root_b / "reports/out.json"
    ).read_bytes()
    assert (root_a / "reports/out.md").read_bytes() == (
        root_b / "reports/out.md"
    ).read_bytes()
    assert payload_a["bootstrap"]["seed"] == SEED
    assert payload_a["checks"]["bootstrap_seed_registered_20260716"] is True


# --------------------------------------------------------------------------
# h. REGRESSION: the seed-1 code path is unchanged, to the byte
# --------------------------------------------------------------------------

def test_seed1_path_is_byte_identical_to_the_pre_extension_golden(
    tmp_path: Path,
) -> None:
    """The seed-1 planted fixture must still hash to the pre-extension goldens.

    The goldens were produced by scripts/build_m7_r3_readout.py at sha256
    b1b1ab4858968b8926ff636d8e81db25c58cbd216dd41dbead39fd8dea84b8af, i.e.
    before --step100-seed2 existed. Any drift in the seed-1 arithmetic, in a
    bootstrap stream label, in the "one seed (seed 1)" tag, or in the markdown
    layout moves these hashes.
    """
    seed1_fixture.SCRIPT = SCRIPT
    seed1_fixture._build_planted(tmp_path)
    result = _run(
        seed1_fixture._cli(
            tmp_path, expected_eligible=5, expected_small_n=1, expected_rows=179
        )
    )
    assert result.returncode == 0, result.stderr
    assert _sha256(tmp_path / "reports/out.json") == SEED1_GOLDEN_JSON_SHA256
    assert _sha256(tmp_path / "reports/out.md") == SEED1_GOLDEN_MD_SHA256

    payload = json.loads((tmp_path / "reports/out.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == SCHEMA_V1
    assert payload["seed_scope"]["tag"] == TAG_V1
    assert payload["seed_scope"]["between_seed_dispersion"].startswith("unmeasured")
    # No two-seed machinery leaks into a one-seed payload.
    assert "seed_dispersion" not in payload
    assert "seeds" not in payload["seed_scope"]
    for key in (
        "seeds_present",
        "cross_seed_item_identity_exact",
        "arm_seed_labels_match_cli_keys",
        "seed_mean_taken_per_item",
    ):
        assert key not in payload["checks"]
    for arm in ARMS:
        assert set(payload["provenance"]["runs"][arm]) == {"step0", "step100"}
        assert "per_seed" not in payload["support_sharpening"]["arms"][arm]

    markdown = (tmp_path / "reports/out.md").read_text(encoding="utf-8")
    assert markdown.startswith("# M7 R3 Readout V1\n")
    assert f"## Corpus aggregate ({TAG_V1})" in markdown
    assert f"## Rank statistics ({TAG_V1})" in markdown
    assert TAG_V2 not in markdown


# --------------------------------------------------------------------------
# i. per-seed M10 candidates are published separately and never merged
# --------------------------------------------------------------------------

def test_per_seed_m10_candidates_are_not_merged(tmp_path: Path) -> None:
    build_two_seed_fixture(tmp_path)
    payload = _run_two_seed(tmp_path)
    support = payload["support_sharpening"]

    assert support["merged_across_seeds"] is False
    assert support["causal_capability_claim_permitted"] is False

    # Hand count: a2_gray has five 0/16 items planted. s1 positions 0,1 flip at
    # seed 1 (12 flips) but not at seed 2 (0 flips); s2 positions 0,1,2 flip at
    # both seeds (9 and 7 flips).
    a2 = support["arms"]["a2_gray"]["per_seed"]
    assert a2["seed1"]["candidate_count"] == 5
    assert a2["seed2"]["candidate_count"] == 3
    assert a2["seed1"]["candidate_artifact"] != a2["seed2"]["candidate_artifact"]
    assert a2["seed1"]["candidate_artifact"].endswith(
        "support_candidates_a2_gray_seed1.jsonl"
    )
    assert a2["seed2"]["candidate_artifact"].endswith(
        "support_candidates_a2_gray_seed2.jsonl"
    )
    for arm in ("a1_real", "a2b_noimage", "a3_caption"):
        for seed_key in ("seed1", "seed2"):
            assert support["arms"][arm]["per_seed"][seed_key]["candidate_count"] == 0
    # Both per-seed files exist on disk with distinct content hashes.
    artifacts = tmp_path / "reports/artifacts"
    assert (artifacts / "support_candidates_a2_gray_seed1.jsonl").is_file()
    assert (artifacts / "support_candidates_a2_gray_seed2.jsonl").is_file()
    assert a2["seed1"]["candidate_sha256"] != a2["seed2"]["candidate_sha256"]
    # No merged/union artifact was written.
    assert not (artifacts / "support_candidates_a2_gray.jsonl").exists()


# --------------------------------------------------------------------------
# provenance: both seeds are recorded, step 0 is marked shared
# --------------------------------------------------------------------------

def test_provenance_carries_a_seed_axis_and_the_step0_reuse_note(
    tmp_path: Path,
) -> None:
    build_two_seed_fixture(tmp_path)
    payload = _run_two_seed(tmp_path)
    provenance = payload["provenance"]

    assert provenance["seeds"] == [1, 2]
    for arm in ARMS:
        runs = provenance["runs"][arm]
        assert set(runs) == {"step0", "step100_seed1", "step100_seed2"}
        assert runs["step0"]["shared_across_seeds"] is True
        assert runs["step0"]["training_seed"] is None
        for seed in SEEDS:
            record = runs[f"step100_seed{seed}"]
            assert record["training_seed"] == seed
            assert record["shared_across_seeds"] is False
            assert record["checkpoint_model_path"] == _checkpoint_path(arm, seed)
            assert record["per_item_sha256"]
        # both seeds' per_item files are distinct artifacts for the blind arms
        # whose flip plans differ
        if arm in ("a2_gray", "a2b_noimage"):
            assert (
                runs["step100_seed1"]["per_item_sha256"]
                != runs["step100_seed2"]["per_item_sha256"]
            )
    assert "shared base model" in provenance["step0_reuse"]["registered_basis"][0]
    assert provenance["arm_seed_label_gate"]["arms"]["a1_real"]["step0"][
        "is_seeded_training_checkpoint"
    ] is False


# --------------------------------------------------------------------------
# markdown: the tag is corrected, never dropped
# --------------------------------------------------------------------------

def test_two_seed_markdown_tags_every_estimand_section(tmp_path: Path) -> None:
    build_two_seed_fixture(tmp_path)
    _run_two_seed(tmp_path)
    markdown = (tmp_path / "reports/out.md").read_text(encoding="utf-8")

    assert markdown.startswith("# M7 R3 Readout V2 (registered two-seed estimator)\n")
    for heading in (
        f"## Corpus aggregate ({TAG_V2})",
        f"## Registered joint strata: gains ({TAG_V2})",
        f"## Registered joint strata: recovery ({TAG_V2})",
        f"## Rank statistics ({TAG_V2})",
        f"## Geometry3K anchor comparison ({TAG_V2}; informed comparison)",
    ):
        assert heading in markdown, heading
    # The tag is corrected, not dropped: no estimand heading is untagged and the
    # false "one seed" wording never appears on a two-seed number.
    assert "## Corpus aggregate\n" not in markdown
    assert "## Rank statistics\n" not in markdown
    assert f"({TAG_V1})" not in markdown
    # Descriptive dispersion is present and labelled; pooling discipline holds.
    assert "## Seed dispersion (descriptive only)" in markdown
    assert "descriptive only" in markdown
    assert "informed" in markdown
    assert "M10 language remains non-causal" in markdown
    # PI flag on the one registered sentence a two-seed readout contradicts.
    assert "PI sign-off flag" in markdown


# --------------------------------------------------------------------------
# registered defaults are pinned, for both schema versions
# --------------------------------------------------------------------------

def test_two_seed_registered_defaults_are_pinned() -> None:
    spec = importlib.util.spec_from_file_location("build_m7_r3_readout", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # v1 pins are untouched.
    assert module.SCHEMA_VERSION == SCHEMA_V1
    assert module.REGISTERED_BOOTSTRAP_DRAWS == 5000
    assert module.REGISTERED_BOOTSTRAP_SEED == 20260716
    assert module.REGISTERED_ELIGIBLE_STRATA == 22
    assert module.REGISTERED_SMALL_N_STRATA == 38
    assert module.REGISTERED_HELDOUT_ROWS == 4239
    assert module.ELIGIBILITY_THRESHOLD == 30
    assert module.UNSTABLE_UNDEFINED_FRACTION == 0.05
    assert module.GEO3K_ANCHORS == {"a2_gray": 0.0789, "a2b_noimage": 0.1184}
    assert module.SEED_SCOPE_TAG == TAG_V1

    # v2 additions.
    assert module.SCHEMA_VERSION_TWO_SEED == SCHEMA_V2
    assert module.REGISTERED_SEEDS == (1, 2)
    assert module.TWO_SEED_SCOPE_TAG == TAG_V2
    assert module.SEED_LABELS == {1: "step100", 2: "step100_seed2"}
    assert module.PROVENANCE_SEED_LABELS == {1: "step100_seed1", 2: "step100_seed2"}
    assert module.TARGET_STEP == 100
    # The one-seed and two-seed scope blocks are distinct and neither is empty.
    one = module._seed_scope_block((1,))
    two = module._seed_scope_block((1, 2))
    assert one["tag"] == TAG_V1 and two["tag"] == TAG_V2
    assert "one seed" not in two["tag"]
    assert "PI sign-off flag" in two["tag_provenance"]
    # An unregistered seed set is refused outright.
    try:
        module._seed_scope_block((1, 2, 3))
    except ValueError as error:
        assert "unregistered seed set" in str(error)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError for an unregistered seed set")
