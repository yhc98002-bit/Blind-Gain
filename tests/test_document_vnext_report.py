from pathlib import Path

from scripts.build_document_vnext_report import build_payload, render_report


def _metadata() -> dict:
    return {
        "n_pairs": 100,
        "iteration_policy": "one declared batch; no regeneration or threshold change in this round",
        "selection_applied": False,
        "regeneration_applied": False,
        "target_7b_real_pair_accuracy": [0.5, 0.9],
        "template_id": "dense",
        "seed": 7,
        "manifest": "manifest.jsonl",
        "manifest_sha256": "a" * 64,
    }


def _cell(pair_accuracy: float) -> dict:
    return {
        "n_pairs": 100,
        "pair_accuracy": pair_accuracy,
        "member_accuracy": pair_accuracy,
        "collapse_rate": 0.0,
    }


def test_document_report_calls_saturated_7b_cell_too_easy(tmp_path: Path) -> None:
    paths = {}
    metrics = {
        "qwen25vl3b_real": _cell(0.7),
        "qwen25vl7b_real": _cell(1.0),
        "qwen25vl7b_caption": _cell(0.2),
    }
    for name in metrics:
        path = tmp_path / f"{name}.json"
        path.write_text("{}\n", encoding="utf-8")
        paths[name] = path

    payload = build_payload(_metadata(), metrics, paths)
    report = render_report(payload, Path("report.json"))

    assert payload["status"] == "complete"
    assert payload["calibration_verdict"] == "too-easy"
    assert "Do not generate a second L11 batch" in report
    assert "not a PI gate declaration" in report


def test_document_report_rejects_selection_or_missing_pairs(tmp_path: Path) -> None:
    metadata = _metadata()
    metadata["selection_applied"] = True
    metrics = {name: _cell(0.7) for name in (
        "qwen25vl3b_real",
        "qwen25vl7b_real",
        "qwen25vl7b_caption",
    )}
    paths = {}
    for name in metrics:
        path = tmp_path / f"{name}.json"
        path.write_text("{}\n", encoding="utf-8")
        paths[name] = path

    import pytest

    with pytest.raises(ValueError, match="selection"):
        build_payload(metadata, metrics, paths)
    metadata["selection_applied"] = False
    metrics["qwen25vl3b_real"]["n_pairs"] = 99
    with pytest.raises(ValueError, match="100 pairs"):
        build_payload(metadata, metrics, paths)
