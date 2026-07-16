from __future__ import annotations

from scripts.build_mini_a5_smoke_registration_marker import (
    document_contains_registered_hashes,
)


def test_document_hash_binding_requires_every_hash() -> None:
    hashes = {"a": "a" * 64, "b": "b" * 64}
    assert document_contains_registered_hashes("\n".join(hashes.values()), hashes)


def test_adversarial_stale_or_omitted_hash_fails_binding() -> None:
    hashes = {"a": "a" * 64, "b": "b" * 64}
    assert document_contains_registered_hashes("a" * 64, hashes) is False
