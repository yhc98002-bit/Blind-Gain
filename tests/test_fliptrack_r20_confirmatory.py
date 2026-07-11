from __future__ import annotations

from pathlib import Path

from scripts.build_fliptrack_r20_confirmatory import render_markdown, template_criteria


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


def test_rendered_status_is_machine_auditable_without_human_pending_marker() -> None:
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
    package = {
        "generator_level_outcome": "generator-level-pass",
        "interpretation_rule": "frozen rule",
        "release_manifest": "data/r20.jsonl",
        "release_manifest_sha256": "a" * 64,
        "lint_json": "reports/lint.json",
        "attacker_json": "reports/attacker.json",
        "template_results": {TEMPLATE: template_criteria(TEMPLATE, cells, degradation)},
    }

    rendered = render_markdown(package, Path("reports/r20.json"))
    status = rendered.split("Status:\n", 1)[1].split("\n\n", 1)[0]

    assert "pending" not in status.lower()
    assert "- Machine status JSON: `reports/r20.json`." in status
    assert "human contact-sheet audit is separate" in rendered
