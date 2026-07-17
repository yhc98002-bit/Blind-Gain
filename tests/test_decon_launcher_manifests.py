from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _source(name: str) -> str:
    return (ROOT / "scripts" / name).read_text(encoding="utf-8")


def test_embedding_launchers_accept_explicit_dataset_label_and_record_placement() -> None:
    for name in ("launch_decon_embeddings.sh", "launch_decon_embedding_compare.sh"):
        source = _source(name)
        assert "[DATA_LABEL]" in source
        assert "data_manifest: $data_label" in source
        assert "gpu_ids: [$gpu]" in source
        assert "tensor_parallel_width: 1" in source
        assert "replica_count: 1" in source
        assert "placement_justification:" in source


def test_ocr_launchers_record_cpu_only_placement_without_fake_gpu_ids() -> None:
    for name in ("launch_decon_ocr.sh", "launch_decon_ocr_compare.sh"):
        source = _source(name)
        assert "gpu_ids: []" in source
        assert "tensor_parallel_width: 0" in source
        assert "replica_count: 0" in source
        assert "placement_justification:" in source
    assert "[DATA_LABEL]" in _source("launch_decon_ocr_compare.sh")
    assert "data_manifest: $data_label" in _source("launch_decon_ocr_compare.sh")


def test_ocr_extractor_launcher_supports_login_without_ssh_and_sets_pythonpath() -> None:
    source = _source("launch_decon_ocr.sh")

    assert 'if [[ "${NODE}" == "login" ]]' in source
    assert 'tmux new-session -d -s "${RUN_ID}"' in source
    assert 'tmux list-panes -t "${RUN_ID}"' in source
    assert "PYTHONPATH=. OMP_NUM_THREADS=2" in source
