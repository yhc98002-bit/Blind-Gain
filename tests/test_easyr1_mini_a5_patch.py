from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "docs" / "easyr1_mini_a5_pair_grouping_patch.diff"
PREPARE = ROOT / "scripts" / "prepare_easyr1_mini_a5_worktree.sh"
LIVE_EASYR1 = ROOT / "artifacts" / "repos" / "EasyR1"


def test_patch_carries_pair_identity_through_reward_and_advantage() -> None:
    source = PATCH.read_text(encoding="utf-8")
    assert 'pair_group_mode: str = "none"' in source
    assert "repeated_pair_metadata" in source
    assert "pair_group_uids=data.non_tensor_batch" in source
    assert 'pair_fields = ("pair_group_uid", "pair_member", "pair_rollout_index")' in source
    assert "compute_pair_level_grpo_advantage" in source


def test_patch_rejects_independent_row_shuffle_and_odd_batches() -> None:
    source = PATCH.read_text(encoding="utf-8")
    assert "data.shuffle=false" in source
    assert "pair-grouped rollout batch sizes must be even" in source


def test_prepare_script_never_targets_the_live_checkout() -> None:
    source = PREPARE.read_text(encoding="utf-8")
    assert 'TARGET="${1:-${ROOT}/artifacts/repos/EasyR1-mini-a5}"' in source
    assert 'SOURCE="${ROOT}/artifacts/repos/EasyR1"' in source
    assert "worktree add --detach" in source
    assert "refusing to replace existing mini-A5 worktree target" in source


def test_prepare_script_refuses_preexisting_target(tmp_path: Path) -> None:
    target = tmp_path / "occupied"
    target.mkdir()
    before = subprocess.run(
        ["git", "-C", str(LIVE_EASYR1), "diff", "--binary"],
        check=True,
        capture_output=True,
    ).stdout
    result = subprocess.run(
        ["bash", str(PREPARE), str(target)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    after = subprocess.run(
        ["git", "-C", str(LIVE_EASYR1), "diff", "--binary"],
        check=True,
        capture_output=True,
    ).stdout
    assert result.returncode != 0
    assert "refusing to replace" in result.stderr
    assert before == after
