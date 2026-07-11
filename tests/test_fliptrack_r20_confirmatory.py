from __future__ import annotations

from scripts.build_fliptrack_r20_confirmatory import template_criteria


TEMPLATE = "header_cued_table_code_v02"


def _metrics(value: float) -> dict[str, object]:
    return {"per_template": {TEMPLATE: {"pair_accuracy": value}}}


def test_confirmatory_template_passes_only_all_prefrozen_criteria() -> None:
    cells = {
        "3b_real": _metrics(0.60),
        "7b_real": _metrics(0.80),
        "3b_gray": _metrics(0.01),
        "7b_gray": _metrics(0.00),
        "3b_noise": _metrics(0.00),
        "7b_noise": _metrics(0.00),
        "3b_caption": _metrics(0.02),
        "7b_caption": _metrics(0.03),
    }
    degradation = {
        "mild": _metrics(0.50),
        "medium": _metrics(0.30),
        "severe": _metrics(0.05),
    }

    result = template_criteria(TEMPLATE, cells, degradation)

    assert all(result["checks"].values())
    assert result["automated_outcome"] == "generator-level-pass"


def test_confirmatory_failure_downgrades_without_minting_rescue_batch() -> None:
    cells = {
        "3b_real": _metrics(0.60),
        "7b_real": _metrics(0.80),
        "3b_gray": _metrics(0.00),
        "7b_gray": _metrics(0.00),
        "3b_noise": _metrics(0.00),
        "7b_noise": _metrics(0.00),
        "3b_caption": _metrics(0.02),
        "7b_caption": _metrics(0.16),
    }
    degradation = {
        "mild": _metrics(0.50),
        "medium": _metrics(0.30),
        "severe": _metrics(0.05),
    }

    result = template_criteria(TEMPLATE, cells, degradation)

    assert result["checks"]["7b_caption_at_most_0_15"] is False
    assert result["automated_outcome"] == "downgrade-to-R19-selected"
