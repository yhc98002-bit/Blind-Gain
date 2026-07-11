from __future__ import annotations

import json
import hashlib
from pathlib import Path

from src.fliptrack.build_r20 import (
    FROZEN_INPUT_HASHES,
    FROZEN_INPUT_SNAPSHOTS,
    FROZEN_SNAPSHOT_SOURCE_COMMITS,
    ROOT,
    build_r20,
    verify_frozen_inputs,
)


def test_frozen_r20_inputs_match_recorded_hashes() -> None:
    observed = verify_frozen_inputs()
    assert len(observed) == 6


def test_mutable_metric_module_resolves_to_exact_historical_snapshot() -> None:
    logical = "src/eval/fliptrack_metrics.py"
    snapshot = ROOT / FROZEN_INPUT_SNAPSHOTS[logical]
    mutable = ROOT / logical

    assert FROZEN_SNAPSHOT_SOURCE_COMMITS[logical] == (
        "4058924530ee70b98a9d1ce3a6b448a8fe2baa70"
    )
    assert snapshot.read_bytes() != mutable.read_bytes()
    assert hashlib.sha256(snapshot.read_bytes()).hexdigest() == FROZEN_INPUT_HASHES[logical]


def test_r20_builder_is_one_shot_and_preserves_declared_counts(tmp_path: Path) -> None:
    r19 = tmp_path / "r19.jsonl"
    r19.write_text('{"pair_id":"old-pair"}\n', encoding="utf-8")
    manifest = tmp_path / "r20.jsonl"
    metadata = tmp_path / "r20.json"
    contacts = tmp_path / "contacts"
    counts = {
        "header_cued_table_code_v02": 1,
        "coordinate_register_twenty_point_x_v02": 2,
        "starred_series_value_nine_v07": 1,
    }

    payload = build_r20(
        out_dir=tmp_path / "source",
        manifest=manifest,
        contact_sheet_dir=contacts,
        metadata_output=metadata,
        r19_source_manifest=r19,
        template_counts=counts,
        seeds={"document": 101, "geometry": 202, "chart": 303},
    )

    assert payload["status"] == "pass"
    assert payload["template_counts"] == counts
    assert payload["selection_applied"] is False
    assert len(manifest.read_text(encoding="utf-8").splitlines()) == 4
    assert len(list(contacts.glob("*.png"))) == 3
    try:
        build_r20(
            out_dir=tmp_path / "source",
            manifest=manifest,
            contact_sheet_dir=contacts,
            metadata_output=metadata,
            r19_source_manifest=r19,
            template_counts=counts,
            seeds={"document": 101, "geometry": 202, "chart": 303},
        )
    except FileExistsError:
        pass
    else:
        raise AssertionError("R20 builder overwrote its one-shot output")

    stored = json.loads(metadata.read_text(encoding="utf-8"))
    assert "we do not mint R21" in stored["interpretation_rule"]
