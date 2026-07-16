from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_launcher_uses_durable_tmux_session_not_bare_background_nohup() -> None:
    source = (ROOT / "scripts" / "launch_virl39k_decon_hash_text.sh").read_text(
        encoding="utf-8"
    )

    assert 'tmux new-session -d -s "${RUN_ID}"' in source
    assert 'tmux list-panes -t "${RUN_ID}"' in source
    assert "nohup" not in source


def test_launcher_registers_full_layer1_and_fail_closed_manifest_fields() -> None:
    source = (ROOT / "scripts" / "launch_virl39k_decon_hash_text.sh").read_text(
        encoding="utf-8"
    )

    for input_name in (
        "MMSTAR_TSV",
        "MATHVISTA_TSV",
        "BLINK_TSV",
        "MMVP_TSV",
        "HALLUSION_TSV",
        "MATHVERSE_TSV",
        "MMMU_TSV",
    ):
        assert f'"${{{input_name}}}"' in source
    for field in (
        "git_hash",
        "config_hash",
        "data_manifest_hash",
        "gpu_allocation",
        "tensor_parallel_width",
        "replica_count",
        "placement_justification",
        "expected_artifacts",
    ):
        assert field in source
    assert "scripts/storage_guard.py --tier S" in source
