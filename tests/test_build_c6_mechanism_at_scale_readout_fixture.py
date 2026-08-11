"""Adversarial fixtures for the C6 mechanism-at-scale readout (I10).

Every test builds SYNTHETIC cells only. Per registration section 9, this suite must pass
before the instrument is pointed at any real C6 run directory.

Coverage (registration section 9, fixture list):
  - planted per-role values recovered exactly under both contracts
  - item-set mismatch between models refused
  - a pair_id present in two models but not the third refused
  - manifest-hash mismatch refused
  - missing run manifest refused; status != complete refused
  - wrong model_revision for a slot refused
  - rows lacking contract_valid / parser_version (the 2026-07-10 schema) refused
  - per-role n_pairs off the registered composition refused
  - R19/R20 rows combined (overlapping pair_id) refused
  - a pooled endpoint emitted without the NOT_AN_ENDPOINT label refused
  - reversed orientation refused
  - two invocations byte-identical
  - refusal to overwrite an existing report
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_c6_mechanism_at_scale_readout import (  # noqa: E402
    ANCHOR_ROLE,
    CANARY_ROLE,
    CELLS,
    READOUT_ROLE,
    ReadoutRefusal,
    SCHEMA_VERSION,
    SEED_TAG,
    build_report,
    render_markdown,
)

# Prediction kinds, verified against src.eval.fliptrack_metrics.pair_score:
#   BOTH         -> pair_correct True,  strict_pair_correct True
#   LENIENT_ONLY -> pair_correct True,  strict_pair_correct False
#   WRONG        -> pair_correct False, strict_pair_correct False
ANSWER_A = "11"
ANSWER_B = "22"
PRED = {
    "BOTH": ("<answer>11</answer>", "<answer>22</answer>"),
    "LENIENT_ONLY": ("11", "22"),
    "WRONG": ("<answer>99</answer>", "<answer>99</answer>"),
}

# Small synthetic composition, 12 pairs per instrument.
FIXTURE_ROLE_N = {ANCHOR_ROLE: 6, CANARY_ROLE: 3, READOUT_ROLE: 3}

FIXTURE_MODELS = {
    "base7b": "fixture/models/base7b",
    "a1real": "fixture/checkpoints/a1real",
    "a2gray": "fixture/checkpoints/a2gray",
}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _row(instrument: str, role: str, index: int, kind: str) -> dict[str, object]:
    pred_a, pred_b = PRED[kind]
    return {
        "pair_id": f"{instrument}_{role}_{index:04d}",
        "template_id": role,
        "answer_a": ANSWER_A,
        "answer_b": ANSWER_B,
        "prediction_a": pred_a,
        "prediction_b": pred_b,
        "contract_valid": True,
        "parser_version": "canonical-v2",
        "prompt_contract_id": "answer-tags-v1",
        "pair_correct": kind in ("BOTH", "LENIENT_ONLY"),
        "strict_pair_correct": kind == "BOTH",
    }


def _plan_to_kinds(n_pairs: int, n_both: int, n_lenient_only: int) -> list[str]:
    assert n_both + n_lenient_only <= n_pairs
    return (
        ["BOTH"] * n_both
        + ["LENIENT_ONLY"] * n_lenient_only
        + ["WRONG"] * (n_pairs - n_both - n_lenient_only)
    )


class Bench:
    """Builds a complete six-cell synthetic C6 workspace under tmp_path."""

    def __init__(self, tmp_path: Path) -> None:
        self.root = tmp_path
        self.pointer_dir = tmp_path / "logs" / "c6_cells"
        self.pointer_dir.mkdir(parents=True)
        self.manifests: dict[str, dict[str, str]] = {}
        for instrument in ("r19", "r20"):
            rel = f"data/fixture_{instrument}_manifest.jsonl"
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = f"fixture instrument {instrument}\n".encode()
            path.write_bytes(payload)
            self.manifests[instrument] = {
                "data_manifest": rel,
                "data_manifest_hash": _sha256_bytes(payload),
            }
        self.registry = {
            "models": dict(FIXTURE_MODELS),
            "instruments": {k: dict(v) for k, v in self.manifests.items()},
            "role_n_pairs": dict(FIXTURE_ROLE_N),
        }

    # -- cell construction --------------------------------------------------
    def write_cell(
        self,
        label: str,
        instrument: str,
        model_slot: str,
        plan: dict[str, tuple[int, int]],
        *,
        role_n: dict[str, int] | None = None,
        model_revision: str | None = None,
        manifest_hash: str | None = None,
        status: str = "complete",
        write_manifest: bool = True,
        strip_contract_fields: bool = False,
        drop_pair_ids: set[str] | None = None,
        extra_rows: list[dict[str, object]] | None = None,
        pair_id_prefix: str | None = None,
    ) -> Path:
        run_dir = self.root / "experiments" / "runs" / f"fixture_{label}"
        (run_dir / "shards").mkdir(parents=True, exist_ok=True)
        (run_dir / "metrics").mkdir(parents=True, exist_ok=True)
        counts = role_n if role_n is not None else FIXTURE_ROLE_N

        rows: list[dict[str, object]] = []
        for role in (ANCHOR_ROLE, CANARY_ROLE, READOUT_ROLE):
            n_pairs = counts[role]
            n_both, n_lenient = plan[role]
            for index, kind in enumerate(_plan_to_kinds(n_pairs, n_both, n_lenient)):
                row = _row(instrument, role, index, kind)
                if pair_id_prefix is not None:
                    row["pair_id"] = f"{pair_id_prefix}_{role}_{index:04d}"
                if strip_contract_fields:
                    row.pop("contract_valid")
                    row.pop("parser_version")
                rows.append(row)
        if drop_pair_ids:
            rows = [r for r in rows if r["pair_id"] not in drop_pair_ids]
        if extra_rows:
            rows.extend(extra_rows)

        for shard in range(4):
            shard_rows = rows[shard::4]
            with (run_dir / "shards" / f"shard_{shard}.jsonl").open("w", encoding="utf-8") as fh:
                for row in shard_rows:
                    fh.write(json.dumps(row, sort_keys=True) + "\n")
            (run_dir / "metrics" / f"shard_{shard}.json").write_text(
                json.dumps({"n_pairs": len(shard_rows)}, sort_keys=True), encoding="utf-8"
            )

        if write_manifest:
            spec = self.manifests[instrument]
            manifest = {
                "run_id": f"fixture_{label}",
                "status": status,
                "expected_shards": 4,
                "performance_values_opened": False,
                "model_revision": model_revision
                if model_revision is not None
                else f"/abs/prefix/{FIXTURE_MODELS[model_slot]}",
                "data_manifest": spec["data_manifest"],
                "data_manifest_hash": manifest_hash
                if manifest_hash is not None
                else spec["data_manifest_hash"],
                "prompt_contract_id": "answer-tags-v1",
                "prompt_contract_sha256": (
                    "7ac39f53a2a824490fc5ee22671a888d2d79d55e1d8351919006d7d71c7a8f3f"
                ),
                "decoding": {"n": 1, "temperature": 0.0, "top_p": 1.0},
                "max_new_tokens": 32,
                "image_mode": "real",
                "seed": 0,
                "node": "fixture",
                "git_hash": "0" * 40,
            }
            (run_dir / "run_manifest.json").write_text(
                json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
            )
        (self.pointer_dir / label).write_text(str(run_dir) + "\n", encoding="utf-8")
        return run_dir

    def build(self, **kwargs):
        return build_report(
            self.root,
            self.pointer_dir,
            self.registry,
            bootstrap_draws=kwargs.pop("bootstrap_draws", 200),
            seed=kwargs.pop("seed", 20260712),
            fixture_mode=kwargs.pop("fixture_mode", True),
        )


# Planted plan: (n_both, n_lenient_only) per role, per cell.
# Base is deliberately low on the readout role and high on the anchor role so the
# planted contrast is a clean branch (a): readout moves, anchor does not.
BASE_PLAN = {ANCHOR_ROLE: (3, 0), CANARY_ROLE: (3, 0), READOUT_ROLE: (0, 0)}
A1_PLAN = {ANCHOR_ROLE: (3, 0), CANARY_ROLE: (3, 0), READOUT_ROLE: (3, 0)}
A2_PLAN = {ANCHOR_ROLE: (3, 0), CANARY_ROLE: (0, 0), READOUT_ROLE: (3, 0)}


def _standard_bench(tmp_path: Path) -> Bench:
    bench = Bench(tmp_path)
    plans = {"base7b": BASE_PLAN, "a1real": A1_PLAN, "a2gray": A2_PLAN}
    for label, instrument, slot in CELLS:
        bench.write_cell(label, instrument, slot, plans[slot])
    return bench


# ---------------------------------------------------------------------------
# 1. planted per-role values recovered exactly, under both contracts
# ---------------------------------------------------------------------------
def test_planted_per_role_values_recovered_under_both_contracts(tmp_path):
    bench = _standard_bench(tmp_path)
    report = bench.build()

    assert report["schema_version"] == SCHEMA_VERSION
    assert report["seed_tag"] == SEED_TAG
    assert report["fixture_mode"] is True

    contrast = report["contrasts"]["c6_1_a1real_minus_base_r19"]
    anchor = contrast["roles"][ANCHOR_ROLE]
    readout = contrast["roles"][READOUT_ROLE]

    # anchor: 3/6 correct in both cells -> exactly zero movement, both contracts
    assert anchor["lenient"]["base_pair_accuracy"] == pytest.approx(0.5)
    assert anchor["lenient"]["arm_pair_accuracy"] == pytest.approx(0.5)
    assert anchor["lenient"]["arm_minus_base"] == pytest.approx(0.0)
    assert anchor["strict"]["arm_minus_base"] == pytest.approx(0.0)
    assert anchor["lenient"]["decision"] == "NOT MOVED"
    assert anchor["strict"]["decision"] == "NOT MOVED"

    # readout: 0/3 -> 3/3, a full +1.0 move on every item, both contracts
    assert readout["lenient"]["base_pair_accuracy"] == pytest.approx(0.0)
    assert readout["lenient"]["arm_pair_accuracy"] == pytest.approx(1.0)
    assert readout["lenient"]["arm_minus_base"] == pytest.approx(1.0)
    assert readout["strict"]["arm_minus_base"] == pytest.approx(1.0)
    assert readout["lenient"]["decision"] == "MOVED"
    assert readout["strict"]["decision"] == "MOVED"

    # the planted configuration is branch (a) under both contracts
    for contract in ("lenient", "strict"):
        assert contrast["pre_committed_reading"][contract]["branch"] == "a"
        assert contrast["pre_committed_reading"][contract]["canary_damage"] is False

    # and it replicates on the twin
    assert report["replication_across_the_twin"]["A1-real"]["lenient"]["replicates"] is True


def test_canary_damage_is_reported_as_damage(tmp_path):
    bench = _standard_bench(tmp_path)
    report = bench.build()
    # A2-gray was planted with the canary dropping 3/3 -> 0/3
    contrast = report["contrasts"]["c6_2_a2gray_minus_base_r19"]
    canary = contrast["roles"][CANARY_ROLE]
    assert canary["lenient"]["decision"] == "MOVED_NEGATIVE_DIRECTION"
    reading = contrast["pre_committed_reading"]["lenient"]
    assert reading["canary_damage"] is True
    assert "with canary damage" in reading["statement"]


def test_lenient_and_strict_are_not_merged(tmp_path):
    bench = Bench(tmp_path)
    # arm gains on the readout role only in the lenient channel (LENIENT_ONLY rows),
    # so the two contracts must disagree and both must be reported.
    plans = {
        "base7b": {ANCHOR_ROLE: (3, 0), CANARY_ROLE: (3, 0), READOUT_ROLE: (0, 0)},
        "a1real": {ANCHOR_ROLE: (3, 0), CANARY_ROLE: (3, 0), READOUT_ROLE: (0, 3)},
        "a2gray": {ANCHOR_ROLE: (3, 0), CANARY_ROLE: (3, 0), READOUT_ROLE: (0, 0)},
    }
    for label, instrument, slot in CELLS:
        bench.write_cell(label, instrument, slot, plans[slot])
    report = bench.build()
    contrast = report["contrasts"]["c6_1_a1real_minus_base_r19"]
    readout = contrast["roles"][READOUT_ROLE]
    assert readout["lenient"]["arm_minus_base"] == pytest.approx(1.0)
    assert readout["strict"]["arm_minus_base"] == pytest.approx(0.0)
    assert readout["lenient"]["decision"] == "MOVED"
    assert readout["strict"]["decision"] == "NOT MOVED"
    reading = contrast["pre_committed_reading"]
    assert reading["lenient"]["branch"] == "a"
    assert reading["strict"]["branch"] == "c"
    assert "contract_disagreement" in reading


# ---------------------------------------------------------------------------
# 2. structural refusals
# ---------------------------------------------------------------------------
def test_item_set_mismatch_between_models_refused(tmp_path):
    bench = Bench(tmp_path)
    plans = {"base7b": BASE_PLAN, "a1real": A1_PLAN, "a2gray": A2_PLAN}
    for label, instrument, slot in CELLS:
        kwargs = {}
        if label == "r19_a1real":
            kwargs["pair_id_prefix"] = "shifted"
        bench.write_cell(label, instrument, slot, plans[slot], **kwargs)
    with pytest.raises(ReadoutRefusal, match="check 8"):
        bench.build()


def test_pair_present_in_two_models_but_not_the_third_refused(tmp_path):
    bench = Bench(tmp_path)
    plans = {"base7b": BASE_PLAN, "a1real": A1_PLAN, "a2gray": A2_PLAN}
    victim = f"r19_{READOUT_ROLE}_0000"
    for label, instrument, slot in CELLS:
        kwargs = {}
        if label == "r19_a2gray":
            kwargs["drop_pair_ids"] = {victim}
        bench.write_cell(label, instrument, slot, plans[slot], **kwargs)
    with pytest.raises(ReadoutRefusal, match="check 8"):
        bench.build()


def test_duplicate_pair_id_within_a_cell_refused(tmp_path):
    bench = Bench(tmp_path)
    plans = {"base7b": BASE_PLAN, "a1real": A1_PLAN, "a2gray": A2_PLAN}
    for label, instrument, slot in CELLS:
        kwargs = {}
        if label == "r19_a1real":
            kwargs["extra_rows"] = [_row("r19", READOUT_ROLE, 0, "BOTH")]
        bench.write_cell(label, instrument, slot, plans[slot], **kwargs)
    with pytest.raises(ReadoutRefusal, match="check 8"):
        bench.build()


def test_manifest_hash_mismatch_refused(tmp_path):
    bench = Bench(tmp_path)
    plans = {"base7b": BASE_PLAN, "a1real": A1_PLAN, "a2gray": A2_PLAN}
    for label, instrument, slot in CELLS:
        kwargs = {}
        if label == "r20_a1real":
            kwargs["manifest_hash"] = "0" * 64
        bench.write_cell(label, instrument, slot, plans[slot], **kwargs)
    with pytest.raises(ReadoutRefusal, match="check 3"):
        bench.build()


def test_on_disk_manifest_rehash_mismatch_refused(tmp_path):
    bench = _standard_bench(tmp_path)
    # mutate the instrument manifest after the cells recorded its hash
    (bench.root / bench.manifests["r19"]["data_manifest"]).write_bytes(b"tampered\n")
    with pytest.raises(ReadoutRefusal, match="check 3"):
        bench.build()


def test_missing_run_manifest_refused(tmp_path):
    bench = Bench(tmp_path)
    plans = {"base7b": BASE_PLAN, "a1real": A1_PLAN, "a2gray": A2_PLAN}
    for label, instrument, slot in CELLS:
        kwargs = {}
        if label == "r19_base7b":
            kwargs["write_manifest"] = False
        bench.write_cell(label, instrument, slot, plans[slot], **kwargs)
    with pytest.raises(ReadoutRefusal, match="check 4"):
        bench.build()


def test_incomplete_run_manifest_refused(tmp_path):
    bench = Bench(tmp_path)
    plans = {"base7b": BASE_PLAN, "a1real": A1_PLAN, "a2gray": A2_PLAN}
    for label, instrument, slot in CELLS:
        kwargs = {}
        if label == "r20_a2gray":
            kwargs["status"] = "running"
        bench.write_cell(label, instrument, slot, plans[slot], **kwargs)
    with pytest.raises(ReadoutRefusal, match="check 4"):
        bench.build()


def test_wrong_model_revision_for_slot_refused(tmp_path):
    bench = Bench(tmp_path)
    plans = {"base7b": BASE_PLAN, "a1real": A1_PLAN, "a2gray": A2_PLAN}
    for label, instrument, slot in CELLS:
        kwargs = {}
        if label == "r19_a1real":
            # the A2-gray checkpoint standing in the A1-real slot
            kwargs["model_revision"] = f"/abs/prefix/{FIXTURE_MODELS['a2gray']}"
        bench.write_cell(label, instrument, slot, plans[slot], **kwargs)
    with pytest.raises(ReadoutRefusal, match="check 2"):
        bench.build()


def test_precanonical_rows_without_contract_fields_refused(tmp_path):
    """The 2026-07-10/11 7B base cells are excluded by construction (section 6)."""
    bench = Bench(tmp_path)
    plans = {"base7b": BASE_PLAN, "a1real": A1_PLAN, "a2gray": A2_PLAN}
    for label, instrument, slot in CELLS:
        kwargs = {}
        if label == "r19_base7b":
            kwargs["strip_contract_fields"] = True
        bench.write_cell(label, instrument, slot, plans[slot], **kwargs)
    with pytest.raises(ReadoutRefusal, match="check 6"):
        bench.build()


def test_per_role_composition_off_registered_refused(tmp_path):
    bench = Bench(tmp_path)
    plans = {"base7b": BASE_PLAN, "a1real": A1_PLAN, "a2gray": A2_PLAN}
    wrong = {ANCHOR_ROLE: 5, CANARY_ROLE: 3, READOUT_ROLE: 3}
    for label, instrument, slot in CELLS:
        kwargs = {}
        if instrument == "r20":
            kwargs["role_n"] = wrong
        bench.write_cell(label, instrument, slot, plans[slot], **kwargs)
    with pytest.raises(ReadoutRefusal, match="check 10"):
        bench.build()


def test_r19_r20_rows_combined_refused(tmp_path):
    """Instrument separation: shared pair_id between the twin sets is a refusal."""
    bench = Bench(tmp_path)
    plans = {"base7b": BASE_PLAN, "a1real": A1_PLAN, "a2gray": A2_PLAN}
    for label, instrument, slot in CELLS:
        kwargs = {}
        if instrument == "r20":
            kwargs["pair_id_prefix"] = "r19"  # collide with the R19 id space
        bench.write_cell(label, instrument, slot, plans[slot], **kwargs)
    with pytest.raises(ReadoutRefusal, match="check 9"):
        bench.build()


def test_reversed_orientation_refused(tmp_path):
    """A contrast whose left cell is not the 7B base must be refused (check 12)."""
    import scripts.build_c6_mechanism_at_scale_readout as mod

    bench = _standard_bench(tmp_path)
    original = mod.CONTRASTS
    reversed_contrasts = tuple(
        {
            **spec,
            "left_cell": spec["right_cell"],
            "right_cell": spec["left_cell"],
        }
        for spec in original
    )
    mod.CONTRASTS = reversed_contrasts
    try:
        with pytest.raises(ReadoutRefusal, match="check 12"):
            bench.build()
    finally:
        mod.CONTRASTS = original


def test_pooled_endpoint_without_label_refused(tmp_path):
    """A pooled-across-roles key that is not labelled NOT_AN_ENDPOINT is refused (check 13)."""
    import scripts.build_c6_mechanism_at_scale_readout as mod

    bench = _standard_bench(tmp_path)
    report = bench.build()
    contrast = report["contrasts"]["c6_1_a1real_minus_base_r19"]
    contrast["pooled_arm_minus_base"] = contrast["POOLED_ACROSS_ROLES_NOT_AN_ENDPOINT"][
        "lenient_arm_minus_base"
    ]
    with pytest.raises(ReadoutRefusal, match="check 13"):
        mod._audit_report(report)


def test_shard_level_quantity_refused(tmp_path):
    import scripts.build_c6_mechanism_at_scale_readout as mod

    bench = _standard_bench(tmp_path)
    report = bench.build()
    report["contrasts"]["c6_1_a1real_minus_base_r19"]["shard_0_pair_accuracy"] = 0.81
    with pytest.raises(ReadoutRefusal, match="check 13"):
        mod._audit_report(report)


def test_missing_seed_tag_on_an_endpoint_refused(tmp_path):
    import scripts.build_c6_mechanism_at_scale_readout as mod

    bench = _standard_bench(tmp_path)
    report = bench.build()
    del report["contrasts"]["c6_1_a1real_minus_base_r19"]["roles"][READOUT_ROLE]["strict"][
        "seed_tag"
    ]
    with pytest.raises(ReadoutRefusal, match="check 14"):
        mod._audit_report(report)


def test_non_registered_bootstrap_parameters_refused_outside_fixture_mode(tmp_path):
    bench = _standard_bench(tmp_path)
    with pytest.raises(ReadoutRefusal, match="check 11"):
        bench.build(bootstrap_draws=200, seed=1, fixture_mode=False)


def test_two_cells_bound_to_one_run_directory_refused(tmp_path):
    bench = _standard_bench(tmp_path)
    target = (bench.pointer_dir / "r19_base7b").read_text(encoding="utf-8")
    (bench.pointer_dir / "r19_a1real").write_text(target, encoding="utf-8")
    with pytest.raises(ReadoutRefusal, match="check 1"):
        bench.build()


def test_missing_pointer_refused(tmp_path):
    bench = _standard_bench(tmp_path)
    (bench.pointer_dir / "r20_a2gray").unlink()
    with pytest.raises(ReadoutRefusal, match="check 1"):
        bench.build()


# ---------------------------------------------------------------------------
# 3. determinism and write discipline
# ---------------------------------------------------------------------------
def test_two_invocations_are_byte_identical(tmp_path):
    bench = _standard_bench(tmp_path)
    first = json.dumps(bench.build(), indent=2, sort_keys=True)
    second = json.dumps(bench.build(), indent=2, sort_keys=True)
    assert first == second
    assert "timestamp" not in first.lower()


def test_markdown_renders_both_contracts_and_all_three_roles(tmp_path):
    bench = _standard_bench(tmp_path)
    markdown = render_markdown(bench.build())
    for role in (ANCHOR_ROLE, CANARY_ROLE, READOUT_ROLE):
        assert role in markdown
    assert "lenient" in markdown and "strict" in markdown
    assert "one seed" in markdown


def test_refuses_to_overwrite_an_existing_report(tmp_path, monkeypatch):
    import scripts.build_c6_mechanism_at_scale_readout as mod

    bench = _standard_bench(tmp_path)
    output = tmp_path / "reports" / "c6_fixture.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("{}\n", encoding="utf-8")
    registry_path = tmp_path / "fixture_registry.json"
    registry_path.write_text(json.dumps(bench.registry), encoding="utf-8")
    argv = [
        "build_c6_mechanism_at_scale_readout.py",
        "--root",
        str(bench.root),
        "--pointer-dir",
        str(bench.pointer_dir),
        "--output",
        str(output),
        "--bootstrap-draws",
        "200",
        "--fixture-registry",
        str(registry_path),
    ]
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(FileExistsError):
        mod.main()
