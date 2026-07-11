from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.inventory_dataset_checkout import inventory_checkout


def _checkout(tmp_path: Path) -> Path:
    root = tmp_path / "dataset"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "fixture@example.com"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Fixture"], check=True)
    return root


def test_dataset_inventory_excludes_git_metadata_and_is_stable(tmp_path: Path) -> None:
    root = _checkout(tmp_path)
    (root / "data.json").write_text('{"value": 1}\n', encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "data.json"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)

    first = inventory_checkout(root)
    (root / ".git" / "untracked-metadata").write_text("ignored", encoding="utf-8")
    second = inventory_checkout(root)

    assert first["status"] == "pass"
    assert first["tree_sha256"] == second["tree_sha256"]
    assert first["file_count"] == 1


def test_dataset_inventory_rejects_unresolved_lfs_pointer(tmp_path: Path) -> None:
    root = _checkout(tmp_path)
    (root / "large.bin").write_text(
        "version https://git-lfs.github.com/spec/v1\n"
        "oid sha256:" + "a" * 64 + "\nsize 123\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "-C", str(root), "add", "large.bin"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "pointer"], check=True)

    result = inventory_checkout(root)

    assert result["status"] == "fail"
    assert result["unresolved_lfs_pointers"] == ["large.bin"]


def test_modelscope_clone_launcher_detaches_from_login_shell() -> None:
    root = Path(__file__).resolve().parents[1]
    launcher = (root / "scripts/launch_modelscope_dataset_clone.sh").read_text(encoding="utf-8")

    assert "nohup setsid --wait" in launcher
