from pathlib import Path


def test_pytest_scope_excludes_downloaded_upstream_repositories() -> None:
    config = Path("pytest.ini").read_text(encoding="utf-8")
    assert "testpaths = tests" in config
