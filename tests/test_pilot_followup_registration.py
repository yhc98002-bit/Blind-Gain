from __future__ import annotations

import copy
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.prepare_pilot_followup_configs import ALLOWED_DIFFS, build, config_diff


ROOT = Path(__file__).resolve().parents[1]


def test_followup_generator_changes_only_registered_fields(tmp_path: Path) -> None:
    outputs = build(2, tmp_path)
    assert len(outputs) == 4
    for output in outputs:
        base_name = output.name.replace("_seed2", "")
        base = yaml.safe_load((ROOT / "configs/train" / base_name).read_text(encoding="utf-8"))
        derived = yaml.safe_load(output.read_text(encoding="utf-8"))
        assert config_diff(base, derived) == ALLOWED_DIFFS
        assert derived["data"]["seed"] == 2
        assert derived["data"]["image_condition_seed"] == 20260710


def test_diff_audit_rejects_hidden_reward_change() -> None:
    base = {"data": {"seed": 1}, "worker": {"reward": {"reward_function": "native"}}, "trainer": {"experiment_name": "x", "save_checkpoint_path": "/x"}}
    derived = copy.deepcopy(base)
    derived["data"]["seed"] = 2
    derived["trainer"]["experiment_name"] = "x_seed2"
    derived["trainer"]["save_checkpoint_path"] = "/x_seed2"
    derived["worker"]["reward"]["reward_function"] = "shaped"

    assert config_diff(base, derived) != ALLOWED_DIFFS


def test_generator_refuses_unregistered_seed(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="seed must be 2 or 3"):
        build(4, tmp_path)


def test_followup_launchers_are_valid_shell_and_fail_closed() -> None:
    launcher = ROOT / "scripts/launch_mech_pilot_followup_arm.sh"
    queue = ROOT / "scripts/launch_pilot_seed2_queue.sh"
    subprocess.run(["bash", "-n", str(launcher)], check=True)
    subprocess.run(["bash", "-n", str(queue)], check=True)
    source = launcher.read_text(encoding="utf-8")

    authorization = source.index("scripts/check_pilot_followup_launch_authorization.py")
    run_dir = source.index('mkdir -p "${RUN_DIR}/logs"')
    remote = source.index('ssh "${NODE}" "cd')
    assert authorization < run_dir < remote
    assert "refusing a second project EasyR1 trainer" in source
    assert 'job_type: "m3_mechanical_pilot_arm"' in source
    assert "--require-tp 1" in source


def test_seed2_queue_does_not_open_metrics_or_preempt() -> None:
    source = (ROOT / "scripts/run_pilot_followup_queue.py").read_text(encoding="utf-8")

    assert "experiment_log.jsonl" not in source
    assert "reward_shadow.jsonl" not in source
    assert "os.kill" not in source
    assert "kill -9" not in source
    assert 'get("status") in {"integrity_running", "complete"}' in source
    assert "node == reserved_node and not longhorizon_launched" in source
    assert "streaks[node][gpu] >= 2" in source


def test_checkpoint_watcher_accepts_registered_m3_parent_and_propagates_seed() -> None:
    source = (ROOT / "scripts/launch_pilot_checkpoint_watch.sh").read_text(encoding="utf-8")

    assert '"m3_mechanical_pilot_arm"' in source
    assert '--argjson seed "$(jq -er \'.seed\' "${TRAINING_MANIFEST}")"' in source
    assert "seed: $seed" in source
