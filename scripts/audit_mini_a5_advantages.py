#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import torch
import yaml

from src.train.cp_grouping import (
    compute_pair_level_grpo_advantage,
    source_grpo_uids,
)


ALLOWED_ARM_DIFFS = {
    "algorithm.pair_group_mode",
    "trainer.experiment_name",
    "trainer.save_checkpoint_path",
    "worker.reward.reward_function",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, dict):
        flattened: dict[str, Any] = {}
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            flattened.update(flatten(child, path))
        return flattened
    if isinstance(value, list):
        return {prefix: value}
    return {prefix: value}


def config_differences(left: dict[str, Any], right: dict[str, Any]) -> dict[str, list[Any]]:
    flat_left = flatten(left)
    flat_right = flatten(right)
    paths = sorted(set(flat_left) | set(flat_right))
    return {
        path: [flat_left.get(path), flat_right.get(path)]
        for path in paths
        if flat_left.get(path) != flat_right.get(path)
    }


def independent_grpo(scores: torch.Tensor, group_uids: list[str]) -> torch.Tensor:
    if scores.ndim != 1 or len(scores) != len(group_uids):
        raise ValueError("reference GRPO inputs must be aligned one-dimensional arrays")
    grouped: dict[str, list[int]] = defaultdict(list)
    for index, uid in enumerate(group_uids):
        grouped[str(uid)].append(index)
    output = torch.empty_like(scores)
    for uid, indices in grouped.items():
        if len(indices) < 2:
            raise ValueError(f"reference GRPO group {uid!r} has fewer than two rollouts")
        group_scores = scores[indices]
        normalized = (group_scores - group_scores.mean()) / (group_scores.std() + 1e-6)
        output[indices] = normalized
    return output


def _pair_case(joint_scores: list[float]) -> tuple[torch.Tensor, torch.Tensor]:
    rollout_n = len(joint_scores)
    duplicated = torch.tensor(joint_scores + joint_scores, dtype=torch.float32)
    token_rewards = torch.zeros((rollout_n * 2, 3), dtype=torch.float32)
    token_rewards[:, -1] = duplicated
    mask = torch.ones_like(token_rewards)
    advantages, _ = compute_pair_level_grpo_advantage(
        token_rewards,
        mask,
        ["pair-1"] * (rollout_n * 2),
        ["a"] * rollout_n + ["b"] * rollout_n,
        list(range(rollout_n)) * 2,
    )
    reference_unique = independent_grpo(
        torch.tensor(joint_scores, dtype=torch.float32), ["pair-1"] * rollout_n
    )
    reference_broadcast = torch.cat([reference_unique, reference_unique])
    return advantages[:, 0], reference_broadcast


def build_advantage_checks() -> tuple[dict[str, bool], dict[str, Any]]:
    mixed = [0.0, 1.0, 1.0, 0.0, 1.0]
    cp_mixed, cp_reference = _pair_case(mixed)
    cp_zero, zero_reference = _pair_case([0.0] * 5)
    cp_one, one_reference = _pair_case([1.0] * 5)

    members = ["a"] * 5 + ["b"] * 5
    source_pair_uids = ["pair-1", "pair-1"]
    source_members = ["a", "b"]
    member_source_uids = source_grpo_uids(source_pair_uids, source_members, "member")
    member_group_uids = [str(member_source_uids[0])] * 5 + [str(member_source_uids[1])] * 5

    identical_member_rewards = torch.tensor(mixed + mixed, dtype=torch.float32)
    member_identical = independent_grpo(identical_member_rewards, member_group_uids)

    member_scores = torch.tensor(
        [0.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 1.0],
        dtype=torch.float32,
    )
    member_reference = independent_grpo(member_scores, member_group_uids)
    shared_uid_bug = independent_grpo(member_scores, ["pair-1"] * 10)

    malformed_rejected = False
    try:
        token_rewards = torch.tensor([[0.0], [1.0]], dtype=torch.float32)
        compute_pair_level_grpo_advantage(
            token_rewards,
            torch.ones_like(token_rewards),
            ["pair-1", "pair-1"],
            ["a", "a"],
            [0, 0],
        )
    except ValueError:
        malformed_rejected = True

    max_cp_reference_diff = float(torch.max(torch.abs(cp_mixed - cp_reference)).item())
    max_path_diff_when_rewards_equal = float(
        torch.max(torch.abs(cp_mixed - member_identical)).item()
    )
    old_shared_uid_diff = float(
        torch.max(torch.abs(member_reference - shared_uid_bug)).item()
    )
    checks = {
        "g_is_exactly_five": len(mixed) == 5,
        "cp_matches_independent_unique_pair_grpo": max_cp_reference_diff <= 1e-7,
        "constant_zero_vector_is_finite_zero": torch.equal(cp_zero, zero_reference)
        and torch.isfinite(cp_zero).all().item()
        and float(torch.max(torch.abs(cp_zero)).item()) == 0.0,
        "constant_one_vector_is_finite_zero": torch.equal(cp_one, one_reference)
        and torch.isfinite(cp_one).all().item()
        and float(torch.max(torch.abs(cp_one)).item()) == 0.0,
        "paths_equal_when_reward_assignment_is_equal": max_path_diff_when_rewards_equal
        <= 1e-7,
        "member_control_has_distinct_prompt_groups": member_source_uids[0]
        != member_source_uids[1],
        "old_shared_2g_control_fixture_is_detected": old_shared_uid_diff > 1e-3,
        "malformed_pair_metadata_is_rejected": malformed_rejected,
        "member_fixture_has_ten_rollout_rows": len(members) == 10,
    }
    evidence = {
        "g": 5,
        "mixed_joint_scores": mixed,
        "max_abs_cp_vs_independent_reference": max_cp_reference_diff,
        "max_abs_cp_vs_member_when_rewards_equal": max_path_diff_when_rewards_equal,
        "max_abs_standard_member_vs_old_shared_2g_bug": old_shared_uid_diff,
        "member_group_uids": member_source_uids.tolist(),
    }
    return checks, evidence


def _nested(config: dict[str, Any], path: str) -> Any:
    value: Any = config
    for part in path.split("."):
        value = value[part]
    return value


def machine_audit_passed(payload: dict[str, Any]) -> bool:
    return payload.get("status") == "pass"


def build_audit(
    cp_config_path: Path,
    member_config_path: Path,
    corpus_audit_path: Path,
    subset_manifest_path: Path,
    step0_audit_path: Path,
    catch_audit_path: Path,
) -> dict[str, Any]:
    cp_config = yaml.safe_load(cp_config_path.read_text(encoding="utf-8"))
    member_config = yaml.safe_load(member_config_path.read_text(encoding="utf-8"))
    corpus_audit = json.loads(corpus_audit_path.read_text(encoding="utf-8"))
    subset_manifest = json.loads(subset_manifest_path.read_text(encoding="utf-8"))
    step0_audit = json.loads(step0_audit_path.read_text(encoding="utf-8"))
    catch_audit = json.loads(catch_audit_path.read_text(encoding="utf-8"))
    differences = config_differences(cp_config, member_config)
    advantage_checks, advantage_evidence = build_advantage_checks()

    train_path = Path(str(_nested(cp_config, "data.train_files")))
    val_path = Path(str(_nested(cp_config, "data.val_files")))
    train_rows = pq.read_metadata(train_path).num_rows
    rollout_batch = int(_nested(cp_config, "data.rollout_batch_size"))
    rollout_n = int(_nested(cp_config, "worker.rollout.n"))
    max_response = int(_nested(cp_config, "data.max_response_length"))
    max_steps = int(_nested(cp_config, "trainer.max_steps"))
    maximum_generated_token_budget = rollout_batch * rollout_n * max_response * max_steps
    overlay_path = Path("docs/easyr1_mini_a5_pair_grouping_patch.diff")
    overlay_text = overlay_path.read_text(encoding="utf-8")

    config_checks = {
        "only_registered_arm_fields_differ": set(differences) == ALLOWED_ARM_DIFFS,
        "cp_mode_is_joint": _nested(cp_config, "algorithm.pair_group_mode") == "joint",
        "control_mode_is_member": _nested(member_config, "algorithm.pair_group_mode")
        == "member",
        "cp_reward_callback_exact": str(
            _nested(cp_config, "worker.reward.reward_function")
        ).endswith("src/rewards/cp_grpo_reward.py:compute_score"),
        "control_reward_callback_exact": str(
            _nested(member_config, "worker.reward.reward_function")
        ).endswith("src/rewards/cp_grpo_reward.py:compute_member_score"),
        "pre_shuffled_order_preserved": _nested(cp_config, "data.shuffle") is False,
        "online_filtering_disabled": _nested(cp_config, "algorithm.online_filtering")
        is False,
        "kl_is_loss_not_reward_shaping": _nested(cp_config, "algorithm.use_kl_loss")
        is True,
        "vision_tower_frozen": _nested(
            cp_config, "worker.actor.model.freeze_vision_tower"
        )
        is True,
        "real_images_used": _nested(cp_config, "data.image_condition") == "real",
        "single_node_eight_gpu_tp1": _nested(cp_config, "trainer.nnodes") == 1
        and _nested(cp_config, "trainer.n_gpus_per_node") == 8
        and _nested(cp_config, "worker.rollout.tensor_parallel_size") == 1,
        "duration_fixed_at_120_steps": max_steps == 120,
        "rollout_group_size_is_five": rollout_n == 5,
        "all_corpus_rows_consumed_per_epoch": train_rows % rollout_batch == 0,
        "duration_is_eight_exact_corpus_passes": max_steps
        == 8 * (train_rows // rollout_batch),
        "plumbing_val_hash_exact": sha256_file(val_path)
        == subset_manifest["plumbing_validation"]["sha256"],
        "training_parquet_hash_exact": sha256_file(train_path)
        == corpus_audit["artifact_sha256"]["train_parquet"],
        "corpus_independent_audit_passed": corpus_audit.get("status") == "pass",
        "fixed_subset_manifest_passed": subset_manifest.get("status") == "pass"
        and subset_manifest.get("pair_id_overlap") == 0,
        "step0_reward_audit_passed": machine_audit_passed(step0_audit),
        "catch_set_independent_audit_passed": machine_audit_passed(catch_audit),
        "runtime_advantage_marker_present": "BLIND_GAINS_CP_ADVANTAGE_AUDIT"
        in overlay_text
        and 'os.getenv("BLIND_GAINS_CP_RUNTIME_AUDIT") == "1"' in overlay_text,
    }
    checks = {**advantage_checks, **config_checks}
    return {
        "schema_version": "blind-gains.mini-a5-advantage-config-audit.v2",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "config_differences": differences,
        "allowed_arm_differences": sorted(ALLOWED_ARM_DIFFS),
        "advantage_evidence": advantage_evidence,
        "fixed_budget": {
            "optimizer_steps": max_steps,
            "rollout_source_prompts_per_step": rollout_batch,
            "rollouts_per_prompt": rollout_n,
            "max_response_tokens": max_response,
            "maximum_generated_tokens_per_arm": maximum_generated_token_budget,
            "training_rows": train_rows,
            "batches_per_corpus_pass": train_rows // rollout_batch,
            "exact_corpus_passes": max_steps // (train_rows // rollout_batch),
        },
        "artifacts": {
            "cp_config": str(cp_config_path),
            "cp_config_sha256": sha256_file(cp_config_path),
            "member_config": str(member_config_path),
            "member_config_sha256": sha256_file(member_config_path),
            "corpus_audit": str(corpus_audit_path),
            "corpus_audit_sha256": sha256_file(corpus_audit_path),
            "fixed_subset_manifest": str(subset_manifest_path),
            "fixed_subset_manifest_sha256": sha256_file(subset_manifest_path),
            "step0_audit": str(step0_audit_path),
            "step0_audit_sha256": sha256_file(step0_audit_path),
            "catch_audit": str(catch_audit_path),
            "catch_audit_sha256": sha256_file(catch_audit_path),
            "cp_grouping_source_sha256": sha256_file(Path("src/train/cp_grouping.py")),
            "reward_source_sha256": sha256_file(Path("src/rewards/cp_grpo_reward.py")),
            "easyr1_overlay_sha256": sha256_file(overlay_path),
        },
        "scientific_gate_decision": None,
        "optimizer_steps_authorized_by_this_artifact": 0,
    }


def render_markdown(payload: dict[str, Any], machine_path: Path) -> str:
    rows = [
        f"| `{name}` | `{'pass' if passed else 'fail'}` |"
        for name, passed in payload["checks"].items()
    ]
    return "\n".join(
        [
            "# Mini-A5 Advantage and Config Audit V2",
            "",
            "Status:",
            f"- Audit status: `{payload['status']}`.",
            "- This is prerequisite evidence only. It authorizes zero optimizer steps and makes no PI gate decision.",
            "",
            "Evidence:",
            f"- Machine artifact: `{machine_path}`.",
            f"- Fixed budget: `{json.dumps(payload['fixed_budget'], sort_keys=True)}`.",
            f"- Allowed config differences: `{json.dumps(payload['allowed_arm_differences'])}`.",
            f"- Observed config differences: `{json.dumps(payload['config_differences'], sort_keys=True)}`.",
            f"- Advantage evidence: `{json.dumps(payload['advantage_evidence'], sort_keys=True)}`.",
            f"- Step-0 and catch audit inputs: `{payload['artifacts']['step0_audit']}`, `{payload['artifacts']['catch_audit']}`.",
            "",
            "Checks:",
            "| Check | Result |",
            "| --- | --- |",
            *rows,
            "",
            "Problems:",
            "- A real EasyR1 GPU plumbing smoke and its post-smoke main-arm registration marker remain pending.",
            "",
            "Decision:",
            "- Supersede the draft shared-UID control behavior. Standard member-level GRPO uses one UID per source prompt; CP alone uses the shared pair UID.",
            "- Keep M6 fail-closed until the remaining diagnostics and merged registration marker exist.",
            "",
        ]
    )


def atomic_write(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite audit output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cp-config", type=Path, default=Path("configs/train/mini_a5_cp_3b_v1.yaml")
    )
    parser.add_argument(
        "--member-config",
        type=Path,
        default=Path("configs/train/mini_a5_same_data_3b_v1.yaml"),
    )
    parser.add_argument(
        "--corpus-audit",
        type=Path,
        default=Path("reports/mini_a5_corpus_audit_v1.json"),
    )
    parser.add_argument(
        "--subset-manifest",
        type=Path,
        default=Path("data/mini_a5_fixed_subsets_v1_manifest.json"),
    )
    parser.add_argument(
        "--step0-audit",
        type=Path,
        default=Path("reports/mini_a5_step0_reward_audit_v1.json"),
    )
    parser.add_argument(
        "--catch-audit",
        type=Path,
        default=Path("reports/mini_a5_catch_audit_v1.json"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("reports/mini_a5_advantage_equivalence_v2.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("reports/mini_a5_advantage_equivalence_v2.md"),
    )
    args = parser.parse_args()
    payload = build_audit(
        args.cp_config,
        args.member_config,
        args.corpus_audit,
        args.subset_manifest,
        args.step0_audit,
        args.catch_audit,
    )
    atomic_write(args.json_output, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    atomic_write(args.markdown_output, render_markdown(payload, args.json_output))
    print(json.dumps({"status": payload["status"], "checks": payload["checks"]}, sort_keys=True))
    raise SystemExit(0 if payload["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
