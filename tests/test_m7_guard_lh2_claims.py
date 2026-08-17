"""Adversarial fixtures for the guard's LH2 plain-text claim support
(claim-format unification, 2026-08-17): the exact 3-line LH2 shape counts as
occupied on its filename-derived GPU regardless of age; everything else keeps
the fail-closed refusal."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "m7_gpu_occupancy_guard", ROOT / "scripts/m7_gpu_occupancy_guard.py")
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)

LH2_BODY = "lh2_seed2_seg1_an12_20260816T172233Z\npid pending\n1786900953\n"
PATH = "/dev/shm/blind-gains/gpu_claims/an12_gpu2.claim"


def test_lh2_plaintext_parses_and_derives_gpu_from_filename():
    payload = GUARD.parse_lh2_plaintext_claim(PATH, LH2_BODY)
    assert payload == {"claim_format": "lh2_plaintext", "gpu": 2,
                       "run_id": "lh2_seed2_seg1_an12_20260816T172233Z",
                       "pid": None, "always_occupied": True}


@pytest.mark.parametrize("body", [
    "just one line",
    "run_id\npid pending\nnot-an-epoch",
    "run id with spaces\npid pending\n1786900953",
    "run_id\npid maybe\n1786900953",
    "run_id\npid pending\n1786900953\nfourth line",
])
def test_non_lh2_bodies_stay_unparseable(body):
    assert GUARD.parse_lh2_plaintext_claim(PATH, body) is None


def test_bad_filename_stays_unparseable():
    assert GUARD.parse_lh2_plaintext_claim("/anywhere/notaclaim.txt", LH2_BODY) is None


def test_lh2_claim_counts_occupied_even_when_old():
    payload = GUARD.parse_lh2_plaintext_claim(PATH, LH2_BODY)
    # mtime 10 hours ago: far beyond CLAIM_FRESH_SECONDS, pid absent — the
    # age-based release must NOT apply to an LH2 trainer claim.
    occupied = GUARD.evaluate_claims(
        now_epoch=1_786_900_953.0,
        claims=[{"path": PATH, "mtime": 1_786_900_953.0 - 36_000,
                 "payload": payload}],
        pid_alive={})
    assert 2 in occupied and "always occupied" in occupied[2][0]


def test_lh2_claim_blocks_only_its_own_gpu():
    payload = GUARD.parse_lh2_plaintext_claim(PATH, LH2_BODY)
    occupied = GUARD.evaluate_claims(
        now_epoch=0.0,
        claims=[{"path": PATH, "mtime": -36_000.0, "payload": payload}],
        pid_alive={})
    assert set(occupied) == {2}


def test_unparseable_claim_still_fails_closed():
    with pytest.raises(GUARD.ClaimIndeterminate):
        GUARD.evaluate_claims(
            now_epoch=0.0,
            claims=[{"path": PATH, "mtime": 0.0, "payload": None}],
            pid_alive={})
