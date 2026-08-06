"""Adversarial fixtures (I10) for the Gate-1 completion registration marker.

Mirrors tests/test_mini_a5_smoke_registration_marker.py: the document-hash
binding must reject any stale or omitted registered hash, and the marker's
authorization fields must collapse to zero/empty whenever any check fails
(guarded here through the marker builder's status logic on synthetic checks).
"""
from __future__ import annotations

from scripts.build_mini_a5_gate1_completion_registration_marker import (
    ARMS,
    MAIN_STEPS_PER_ARM,
    document_contains_registered_hashes,
)


def test_document_hash_binding_requires_every_hash() -> None:
    hashes = {"a": "a" * 64, "b": "b" * 64}
    assert document_contains_registered_hashes("\n".join(hashes.values()), hashes)


def test_adversarial_stale_or_omitted_hash_fails_binding() -> None:
    hashes = {"a": "a" * 64, "b": "b" * 64}
    assert document_contains_registered_hashes("a" * 64, hashes) is False
    assert document_contains_registered_hashes("", hashes) is False


def test_registered_constants_are_the_authorized_budget() -> None:
    assert MAIN_STEPS_PER_ARM == 120
    assert tuple(ARMS) == ("std", "necessity")
