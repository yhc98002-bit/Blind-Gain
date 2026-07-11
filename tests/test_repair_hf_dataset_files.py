from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts.repair_hf_dataset_files import install_verified_file


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _pointer(oid: str, size: int) -> str:
    return f"version https://git-lfs.github.com/spec/v1\noid sha256:{oid}\nsize {size}\n"


def test_repair_installs_only_hash_matching_payload_over_expected_pointer(tmp_path: Path) -> None:
    payload = b"verified parquet fixture"
    expected = _sha256(payload)
    source = tmp_path / "source.bin"
    source.write_bytes(payload)
    destination = tmp_path / "target.parquet"
    destination.write_text(_pointer(expected, len(payload)), encoding="utf-8")

    action = install_verified_file(source.as_uri(), destination, expected, len(payload))

    assert action == "installed"
    assert destination.read_bytes() == payload


def test_repair_refuses_unexpected_existing_content(tmp_path: Path) -> None:
    payload = b"expected"
    expected = _sha256(payload)
    source = tmp_path / "source.bin"
    source.write_bytes(payload)
    destination = tmp_path / "target.parquet"
    destination.write_bytes(b"unexpected existing content")

    with pytest.raises(ValueError, match="refusing to replace"):
        install_verified_file(source.as_uri(), destination, expected, len(payload))


def test_repair_keeps_pointer_when_download_hash_is_wrong(tmp_path: Path) -> None:
    payload = b"expected"
    expected = _sha256(payload)
    source = tmp_path / "source.bin"
    source.write_bytes(b"wrong")
    destination = tmp_path / "target.parquet"
    pointer = _pointer(expected, len(payload))
    destination.write_text(pointer, encoding="utf-8")

    with pytest.raises(ValueError, match="download verification failed"):
        install_verified_file(source.as_uri(), destination, expected, len(payload))
    assert destination.read_text(encoding="utf-8") == pointer
