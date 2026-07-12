from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from scripts.audit_prelaunch_objective import EXPECTED_TASK_IDS
from scripts.check_pilot_launch_authorization import build_authorization


CONFIGS = {
    "mech_a1_real_3b_geo3k.yaml": ("real", "mech_a1_real"),
    "mech_a2_gray_3b_geo3k.yaml": ("gray", "mech_a2_gray"),
    "mech_a2b_noimage_3b_geo3k.yaml": ("none", "mech_a2b_noimage"),
    "mech_a3_caption_3b_geo3k.yaml": ("caption", "mech_a3_caption"),
}


def _fixture(tmp_path: Path) -> Path:
    (tmp_path / "reports").mkdir()
    (tmp_path / "data").mkdir()
    config_dir = tmp_path / "configs" / "train"
    config_dir.mkdir(parents=True)
    ledger = []
    for task in EXPECTED_TASK_IDS:
        status = "pass" if task in {"L3", "L4", "L5", "L12"} else "blocked"
        ledger.append(f"{task} | {status} | fixture {task}")
    (tmp_path / "reports" / "prelaunch_progress.md").write_text(
        "\n".join(ledger) + "\n", encoding="utf-8"
    )
    base = {
        "data": {"image_condition": "real"},
        "worker": {"rollout": {"tensor_parallel_size": 1}},
        "trainer": {
            "n_gpus_per_node": 4,
            "max_steps": 100,
            "save_freq": 20,
            "val_freq": 10,
            "experiment_name": "arm",
            "save_checkpoint_path": "checkpoint",
        },
    }
    config_hashes = []
    for name, (condition, identity) in CONFIGS.items():
        payload = json.loads(json.dumps(base))
        payload["data"]["image_condition"] = condition
        payload["trainer"]["experiment_name"] = identity
        payload["trainer"]["save_checkpoint_path"] = str(
            tmp_path / "checkpoints" / "pilot" / identity
        )
        path = config_dir / name
        path.write_text(yaml.safe_dump(payload), encoding="utf-8")
        config_hashes.append(hashlib.sha256(path.read_bytes()).hexdigest())
    ids = tmp_path / "data" / "geo3k_pilot_filtered_ids.json"
    ids.write_text("[1, 2]\n", encoding="utf-8")
    ids_hash = hashlib.sha256(ids.read_bytes()).hexdigest()
    prereg = (
        "# Approved preregistration\n"
        "- R19 human contact-sheet audit: approved.\n"
        "- PI 1 approval: approved.\n"
        "- PI 2 approval: approved.\n"
        + "\n".join(config_hashes)
        + f"\n{ids_hash}\n"
    )
    (tmp_path / "reports" / "preregistration_pilot_v1.md").write_text(
        prereg, encoding="utf-8"
    )
    (tmp_path / "reports" / "pilot_reward_spec_v3.md").write_text(
        "complete\n", encoding="utf-8"
    )
    (tmp_path / "reports" / "pilot_reward_smoke_audit_v4.json").write_text(
        json.dumps(
            {
                "schema_version": "blind-gains.pilot-reward-smoke-audit.v6",
                "status": "pass",
                "placement_audit": {"status": "pass", "checks": {"tp1": True}},
            }
        ),
        encoding="utf-8",
    )
    return tmp_path


def test_authorization_accepts_only_fully_approved_clean_arm(tmp_path: Path) -> None:
    root = _fixture(tmp_path)

    result = build_authorization(root, "a1_real")

    assert result["status"] == "authorized"
    assert all(result["checks"].values())
    assert result["preregistration_sha256"]


def test_authorization_rejects_blocked_l12_before_optimizer_launch(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    ledger = root / "reports" / "prelaunch_progress.md"
    ledger.write_text(
        ledger.read_text(encoding="utf-8").replace(
            "L12 | pass | fixture L12", "L12 | blocked | human audit pending"
        ),
        encoding="utf-8",
    )

    result = build_authorization(root, "a1_real")

    assert result["status"] == "blocked"
    assert result["checks"]["required_dependencies_pass"] is False


def test_authorization_rejects_nonempty_checkpoint_namespace(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    checkpoint = root / "checkpoints" / "pilot" / "mech_a1_real"
    checkpoint.mkdir(parents=True)
    (checkpoint / "stale.json").write_text("{}\n", encoding="utf-8")

    result = build_authorization(root, "a1_real")

    assert result["status"] == "blocked"
    assert result["checks"]["selected_checkpoint_namespace_absent"] is False


def test_current_repository_remains_blocked_before_l12() -> None:
    root = Path(__file__).resolve().parents[1]

    result = build_authorization(root, "a1_real")

    assert result["status"] == "blocked"
    assert result["checks"]["required_dependencies_pass"] is False
    assert result["checks"]["final_preregistration_exists"] is False
