from __future__ import annotations

from pathlib import Path

import pytest

import scripts.measure_storage_usage as msu
from scripts.measure_storage_usage import _parse_project_listing, _parse_project_quota_kib


def _lustre_stub(used_bytes: int):
    def stub(root: Path, timeout_seconds: int) -> dict[str, object]:
        return {
            "measurement": "stubbed Lustre project quota",
            "used_bytes": used_bytes,
            "project_id": 1,
            "project_file_count": 2,
            "components": {"lustre_project_id:1": used_bytes},
        }

    return stub


def test_snapshot_status_is_fail_when_over_soft_quota(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """I10 fixture for the 2026-08-12..16 incident: the snapshot carried
    free_bytes: -461684596736 with status:"pass". Over-quota must self-report
    as "fail" (a valid measurement of a failing state), never "pass"."""
    monkeypatch.setattr(msu, "DEFAULT_SHARED_QUOTA_BYTES", 1000)
    monkeypatch.setattr(msu, "_measure_lustre_project", _lustre_stub(1500))

    payload = msu.measure(tmp_path, workers=1, timeout_seconds=5)

    assert payload["status"] == "fail"
    assert payload["free_bytes"] == -500
    assert payload["used_bytes"] == 1500


def test_snapshot_status_is_pass_at_or_under_soft_quota(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(msu, "DEFAULT_SHARED_QUOTA_BYTES", 1000)
    monkeypatch.setattr(msu, "_measure_lustre_project", _lustre_stub(800))

    payload = msu.measure(tmp_path, workers=1, timeout_seconds=5)

    assert payload["status"] == "pass"
    assert payload["free_bytes"] == 200


def test_project_quota_parser_handles_wrapped_filesystem_row(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    listing = f"2228473301 P {root}\n"
    quota = f"""Disk quotas for prj 2228473301 (pid 2228473301):
     Filesystem  kbytes   quota   limit   grace   files   quota   limit   grace
{root}
                1225350212       0       0       -  714982       0       0       -
pid 2228473301 is using default block quota setting
"""

    assert _parse_project_listing(listing, root) == 2228473301
    assert _parse_project_quota_kib(quota, root) == (1_225_350_212, 714_982)


def test_project_quota_parser_rejects_unrelated_or_ambiguous_rows(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    with pytest.raises(RuntimeError, match="one positive Lustre project ID"):
        _parse_project_listing(f"1 P {root}\n2 P {root}\n", root)
    with pytest.raises(RuntimeError, match="quota row"):
        _parse_project_quota_kib(
            f"{root}\nnot-a-number 0 0 - 1 0 0 -\n",
            root,
        )
