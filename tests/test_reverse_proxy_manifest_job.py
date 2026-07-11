from pathlib import Path

import pytest

from scripts.run_reverse_proxy_manifest_job import build_ssh_command


def test_reverse_proxy_command_keeps_download_and_tunnel_on_one_node(tmp_path: Path) -> None:
    command = build_ssh_command(
        "an29",
        17890,
        tmp_path / "run manifest.json",
        tmp_path / "node log.txt",
    )

    assert command[:5] == [
        "ssh",
        "-o",
        "ExitOnForwardFailure=yes",
        "-R",
        "17890:127.0.0.1:7890",
    ]
    assert command[5] == "an29"
    assert "run_manifest_job.py" in command[6]
    assert "'" in command[6]


@pytest.mark.parametrize(("node", "port"), [("login", 17890), ("an12", 0), ("an29", 65536)])
def test_reverse_proxy_command_rejects_invalid_placement(node: str, port: int) -> None:
    with pytest.raises(ValueError):
        build_ssh_command(node, port, Path("manifest.json"), Path("log.txt"))
