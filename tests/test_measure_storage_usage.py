from __future__ import annotations

from pathlib import Path

import pytest

from scripts.measure_storage_usage import _parse_project_listing, _parse_project_quota_kib


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
