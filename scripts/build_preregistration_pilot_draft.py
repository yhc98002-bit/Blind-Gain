#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from src.rewards.pilot_reward import (
    DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
    SYMBOLIC_GRADER_GUARD_VERSION,
)


ARM_CONFIGS = {
    "A1 real": Path("configs/train/mech_a1_real_3b_geo3k.yaml"),
    "A2 gray": Path("configs/train/mech_a2_gray_3b_geo3k.yaml"),
    "A2b no-image": Path("configs/train/mech_a2b_noimage_3b_geo3k.yaml"),
    "A3 caption": Path("configs/train/mech_a3_caption_3b_geo3k.yaml"),
}
ARM_CONDITIONS = {
    "A1 real": "real",
    "A2 gray": "gray",
    "A2b no-image": "none",
    "A3 caption": "caption",
}
BLIND_CONDITIONS = ("gray", "none", "caption")
PILOT_Q_CONDITIONS = ("real", "gray", "none", "caption")
ONE_SEED_SCOPE = (
    "These are pilot estimands and directional predictions, not definitive hypothesis tests "
    "of the training procedure; item-level paired intervals quantify evaluation uncertainty, "
    "not run-to-run RL variance."
)
FALSIFICATION = (
    "If A1 improves geo3k strongly and produces a material geometry-FlipTrack gain while "
    "blind arms do not, the shortcut-only account is disfavored."
)
PRIOR_OBSERVATION_DISCLOSURE = (
    "The existence and approximate magnitude of the A1 benchmark/FlipTrack dissociation "
    "were observed before registration. Therefore, hypotheses concerning A1's qualitative "
    "direction are partially informed. Blind-arm recovery, A3 behavior, q_i–gain "
    "associations, and cross-arm contrasts remain prospective."
)
R20_CAVEAT = (
    "The primary FlipTrack endpoint was selected during R19 calibration. R20 independently "
    "satisfies all registered validity and anti-shortcut criteria but narrowly misses the "
    "preregistered 3B-real sensitivity floor for geometry and chart; it is therefore reported "
    "as robustness evidence, not a confirmatory pass."
)
CHART_CONSTRUCT = (
    "In the R19 chart template, a circle indicates the queried plot point in both pair members. "
    "The task therefore certifies fine-grained value reading at a visually cued location; it "
    "does not certify the intended legend-to-series localization hop. An accompanying in-image "
    "sentence inaccurately describes the star as marking the queried point, although the star "
    "appears in the legend and the circle marks the plot point. Human audit found no resulting "
    "answer ambiguity, but the wording and cue narrow the construct. Chart results are secondary "
    "and are reported separately from the geometry-primary endpoint."
)
EXECUTION_ACCESS_DISCLOSURE = (
    "the executing agent had continuous log access; PIs reviewed the anchor and audit artifacts "
    "before registration."
)
ANCHOR_GEO3K = Path("reports/grpo_anchor_step100_prepost_v1.json")
ANCHOR_FLIPTRACK = Path("reports/anchor_step100_fliptrack_r19_v2.json")
ANCHOR_BLIND = Path("reports/anchor_step100_fliptrack_r19_blind_ablation_v2.json")
ANCHOR_RESOLVED_CONFIG = Path(
    "checkpoints/anchor_a0_recipe_3b_geo3k/"
    "anchor_a0_recipe_3b_geo3k_20260709T224852Z/experiment_config.json"
)
R20_CONFIRMATORY = Path("reports/fliptrack_r20_confirmatory.json")
R19_HUMAN_AUDIT = Path("reports/fliptrack_v02r19_human_audit.md")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalized_config(config: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(config)
    normalized["data"].pop("image_condition")
    normalized["trainer"].pop("experiment_name")
    normalized["trainer"].pop("save_checkpoint_path")
    return normalized


def audit_arm_configs(root: Path) -> dict[str, Any]:
    loaded: dict[str, dict[str, Any]] = {}
    hashes: dict[str, str] = {}
    for arm, relative in ARM_CONFIGS.items():
        path = root / relative
        loaded[arm] = yaml.safe_load(path.read_text(encoding="utf-8"))
        hashes[arm] = _sha256(path)
    reference = _normalized_config(loaded["A1 real"])
    if any(_normalized_config(config) != reference for config in loaded.values()):
        raise ValueError("pilot configs differ outside registered arm identity fields")
    for arm, config in loaded.items():
        if config["data"]["image_condition"] != ARM_CONDITIONS[arm]:
            raise ValueError(f"pilot config image condition mismatch for {arm}")
        if config["worker"]["rollout"]["tensor_parallel_size"] != 1:
            raise ValueError(f"pilot config violates TP1 placement for {arm}")
        if config["trainer"]["n_gpus_per_node"] != 4:
            raise ValueError(f"pilot config must use four colocated GPUs for {arm}")
        if config["trainer"]["max_steps"] != 100:
            raise ValueError(f"pilot config max steps drifted for {arm}")
        if config["trainer"]["save_freq"] != 20 or config["trainer"]["val_freq"] != 10:
            raise ValueError(f"pilot checkpoint/evaluation cadence drifted for {arm}")
    return {"hashes": hashes, "normalized_config": reference}


def _load_json(path: Path, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload


def _q_group_rows(
    root: Path, summary: dict[str, Any], audit: dict[str, Any]
) -> list[str]:
    rows: list[str] = []
    for condition in PILOT_Q_CONDITIONS:
        run = audit.get("runs", {}).get(condition)
        if not isinstance(run, str):
            raise ValueError(f"L7 audit does not identify the {condition} per-item run")
        per_item = root / run / "per_item.jsonl"
        expected_hash = audit["per_item_output_sha256"][condition]
        if _sha256(per_item) != expected_hash:
            raise ValueError(f"L7 {condition} per-item hash differs from the audited hash")

        n_train = 0
        floor_count = 0
        above_count = 0
        floor_q: set[float] = set()
        with per_item.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                item = json.loads(line)
                if item.get("split") != "train":
                    continue
                if item.get("condition") != condition:
                    raise ValueError(f"L7 per-item condition mismatch for {condition}")
                count = item.get("sample_correct_count")
                sample_count = item.get("sample_count")
                q_i = item.get("q_i")
                if (
                    not isinstance(count, int)
                    or sample_count != 16
                    or not isinstance(q_i, (int, float))
                ):
                    raise ValueError(f"invalid q_i row for {condition}")
                n_train += 1
                if count == 0:
                    floor_count += 1
                    floor_q.add(round(float(q_i), 12))
                else:
                    above_count += 1

        expected_n = summary["aggregates"][condition]["train"]["n"]
        if n_train != expected_n or floor_count + above_count != n_train:
            raise ValueError(f"L7 q_i group count mismatch for {condition}")
        if floor_q != {round(0.13865898995462222, 12)}:
            raise ValueError(f"L7 {condition} 0/16 floor q_i drifted: {sorted(floor_q)}")
        mean_q = summary["aggregates"][condition]["train"]["metrics"]["q_i"]["mean"]
        rows.append(
            f"| {condition} | {n_train} | {floor_count} | {floor_count / n_train:.4f} | "
            f"{above_count} | {above_count / n_train:.4f} | {mean_q:.6f} |"
        )
    return rows


def _load_prior_observations(root: Path) -> dict[str, Any]:
    geo3k_path = root / ANCHOR_GEO3K
    fliptrack_path = root / ANCHOR_FLIPTRACK
    blind_path = root / ANCHOR_BLIND
    anchor_config_path = root / ANCHOR_RESOLVED_CONFIG
    r20_path = root / R20_CONFIRMATORY
    human_path = root / R19_HUMAN_AUDIT
    geo3k = _load_json(geo3k_path, "anchor Geometry3K report")
    fliptrack = _load_json(fliptrack_path, "anchor FlipTrack report")
    blind = _load_json(blind_path, "anchor blind ablation")
    anchor_config = _load_json(anchor_config_path, "resolved anchor config")
    r20 = _load_json(r20_path, "R20 confirmatory report")
    if (
        geo3k.get("status") != "pass"
        or fliptrack.get("status") != "pass"
        or blind.get("status") != "pass"
        or r20.get("status") != "pass"
    ):
        raise ValueError("prior-observation input has non-pass machine status")
    human_text = human_path.read_text(encoding="utf-8")
    if "verdict=accepted" not in human_text or "60/60" not in human_text:
        raise ValueError("R19 human audit acceptance is not recorded")

    a1 = yaml.safe_load((root / ARM_CONFIGS["A1 real"]).read_text(encoding="utf-8"))
    anchor_freeze = anchor_config["worker"]["actor"]["model"]["freeze_vision_tower"]
    a1_freeze = a1["worker"]["actor"]["model"]["freeze_vision_tower"]
    if anchor_freeze is not False or a1_freeze is not True:
        raise ValueError("anchor/A1 vision-tower difference no longer matches the disclosed prior")
    if anchor_config["worker"]["reward"].get("reward_function_kwargs") != {}:
        raise ValueError("resolved anchor unexpectedly overrides native reward kwargs")

    geometry = r20["template_results"]["coordinate_register_twenty_point_x_v02"]
    chart = r20["template_results"]["starred_series_value_nine_v07"]
    if (
        geometry["automated_outcome"] != "downgrade-to-R19-selected"
        or chart["automated_outcome"] != "downgrade-to-R19-selected"
        or geometry["checks"]["3b_real_at_least_0_40"] is not False
        or chart["checks"]["3b_real_at_least_0_40"] is not False
        or any(
            not value
            for key, value in geometry["checks"].items()
            if key != "3b_real_at_least_0_40"
        )
        or any(
            not value
            for key, value in chart["checks"].items()
            if key != "3b_real_at_least_0_40"
        )
    ):
        raise ValueError("R20 geometry/chart status differs from the registered caveat")

    return {
        "geo3k": geo3k["splits"]["test"]["metrics"]["pilot_accuracy"],
        "fliptrack_overall": fliptrack["comparison"]["all"],
        "fliptrack_geometry": fliptrack["comparison"]
        ["geometry_coordinate_register_twenty_point_x_v02"],
        "anchor_gray": blind["endpoints"]["anchor_gray"],
        "anchor_noise": blind["endpoints"]["anchor_noise"],
        "anchor_config": anchor_config,
        "a1_config": a1,
        "r20_geometry": geometry,
        "r20_chart": chart,
        "hashes": {
            "geo3k": _sha256(geo3k_path),
            "fliptrack": _sha256(fliptrack_path),
            "blind": _sha256(blind_path),
            "anchor_config": _sha256(anchor_config_path),
            "r20": _sha256(r20_path),
            "human": _sha256(human_path),
        },
    }


def build_draft(
    *,
    root: Path,
    l7_summary_path: Path,
    l7_audit_path: Path,
    filtered_ids_path: Path,
) -> str:
    summary = json.loads(l7_summary_path.read_text(encoding="utf-8"))
    audit = json.loads(l7_audit_path.read_text(encoding="utf-8"))
    if summary.get("status") != "complete" or audit.get("status") != "pass":
        raise ValueError("preregistration draft requires complete L7 summary and pass audit")
    if summary.get("audit", {}).get("status") != "pass":
        raise ValueError("L7 summary does not embed a passing audit")
    if summary.get("audit", {}).get("per_item_output_sha256") != audit.get(
        "per_item_output_sha256"
    ):
        raise ValueError("L7 summary/audit per-item output hashes differ")
    contract = summary.get("evaluation_contract", {})
    if (
        contract.get("symbolic_grader_guard_version")
        != SYMBOLIC_GRADER_GUARD_VERSION
        or contract.get("symbolic_grader_timeout_seconds")
        != DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS
        or contract.get("max_tokens") != 2048
        or contract.get("sample_count") != 16
        or contract.get("group_size") != 5
    ):
        raise ValueError("L7 summary does not use the registered pilot contract")
    for condition in PILOT_Q_CONDITIONS:
        if condition not in summary.get("aggregates", {}):
            raise ValueError(f"L7 summary lacks preregistration condition: {condition}")

    config_audit = audit_arm_configs(root)
    prior = _load_prior_observations(root)
    filtered_hash = _sha256(filtered_ids_path)
    summary_hash = _sha256(l7_summary_path)
    audit_hash = _sha256(l7_audit_path)
    output_hashes = audit["per_item_output_sha256"]
    if set(output_hashes) != {"real", "gray", "noise", "none", "caption"} or any(
        not isinstance(digest, str) or len(digest) != 64
        for digest in output_hashes.values()
    ):
        raise ValueError("L7 audit does not pin one SHA256 per registered condition")
    q_rows = _q_group_rows(root, summary, audit)
    config_rows = [
        f"| {arm} | `{ARM_CONDITIONS[arm]}` | `{ARM_CONFIGS[arm]}` | `{digest}` |"
        for arm, digest in config_audit["hashes"].items()
    ]
    source_rows = [
        f"| {condition} | `{output_hashes[condition]}` |"
        for condition in PILOT_Q_CONDITIONS
    ]

    lines = [
        "# Four-Arm Mechanical Pilot Preregistration V1 Draft — Main-Phase Revision",
        "",
        "Status:",
        "- `draft only`; not merged as M0 and not authorization for a pilot optimizer step.",
        "- Richard accepted the frozen R19 human audit at 60/60 pairs. Under the main-phase rule, merge is sign-off; there are no signature or sealing rounds.",
        "- M2/M3 remain fail-closed. No pilot optimizer step is authorized by this draft.",
        "",
        "Frozen inputs:",
        f"- Filtered Geometry3K IDs: `{filtered_ids_path}`, SHA256 `{filtered_hash}`.",
        f"- L7 summary: `{l7_summary_path}`, SHA256 `{summary_hash}`.",
        f"- L7 independent audit: `{l7_audit_path}`, SHA256 `{audit_hash}`, machine status `pass`.",
        f"- Pilot reward guard: `{SYMBOLIC_GRADER_GUARD_VERSION}` at `{DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS}` seconds.",
        "",
        "| Arm | Image condition | Config | SHA256 |",
        "| --- | --- | --- | --- |",
        *config_rows,
        "",
        "The configs are structurally identical after removing only `data.image_condition`, `trainer.experiment_name`, and `trainer.save_checkpoint_path`.",
        "",
        "Design:",
        "- Four arms: A1 real, A2 gray, A2b no-image, and A3 fixed 3B question-blind captions.",
        "- Qwen2.5-VL-3B, frozen vision tower, seed 1, G=5, 100 optimizer steps, and identical configs except registered arm identity.",
        "- Synchronous EasyR1/GRPO stays on one node with four colocated GPUs; 3B rollout serving is TP1.",
        "- Checkpoints: steps 0, 20, 40, 60, 80, and 100. Step 0 is the base model already on disk and is not duplicated.",
        "- Greedy full Geometry3K-test validation every 10 steps under one locked prompt contract.",
        "- Pilot checkpoints save to shared arm directories and are swept under the latest-raw-only retention rule; only step-100 merged remains on shared storage.",
        "",
        "One-seed scope:",
        f"> {ONE_SEED_SCOPE}",
        "",
        "Prior observations (disclosed before launch):",
        f"- Engineering anchor Geometry3K test `Acc_final`: `{prior['geo3k']['before']:.4f} -> {prior['geo3k']['after']:.4f}`, paired delta `{prior['geo3k']['delta']:+.4f}`, 95% item-bootstrap CI `[{prior['geo3k']['delta_ci_low']:+.4f}, {prior['geo3k']['delta_ci_high']:+.4f}]`.",
        f"- Engineering anchor R19 overall pair accuracy: `{prior['fliptrack_overall']['base_pair_accuracy']:.4f} -> {prior['fliptrack_overall']['step100_pair_accuracy']:.4f}`, paired delta `{prior['fliptrack_overall']['pair_delta']:+.4f}`, 95% CI `[{prior['fliptrack_overall']['pair_delta_ci95'][0]:+.4f}, {prior['fliptrack_overall']['pair_delta_ci95'][1]:+.4f}]`.",
        f"- Engineering anchor R19 geometry pair accuracy: `{prior['fliptrack_geometry']['base_pair_accuracy']:.4f} -> {prior['fliptrack_geometry']['step100_pair_accuracy']:.4f}`, paired delta `{prior['fliptrack_geometry']['pair_delta']:+.4f}`, 95% CI `[{prior['fliptrack_geometry']['pair_delta_ci95'][0]:+.4f}, {prior['fliptrack_geometry']['pair_delta_ci95'][1]:+.4f}]`.",
        f"- At step 100, R19 gray and noise pair accuracy were `{prior['anchor_gray']['pair_accuracy']:.4f}` and `{prior['anchor_noise']['pair_accuracy']:.4f}`; both Collapse Rates were `{prior['anchor_gray']['collapse_rate']:.1f}`. These are evaluation-time ablations of the real-trained anchor, not matched blind-training arms.",
        f"> {PRIOR_OBSERVATION_DISCLOSURE}",
        "- The anchor is an observed engineering calibration and is never presented as a preregistered confirmation.",
        "- Prior-observation source SHA256 values: "
        f"Geometry3K `{prior['hashes']['geo3k']}`, R19 real `{prior['hashes']['fliptrack']}`, "
        f"R19 blind `{prior['hashes']['blind']}`, resolved anchor config `{prior['hashes']['anchor_config']}`.",
        "",
        "Anchor-to-pilot-A1 comparison:",
        "| Field | Engineering anchor as launched | Pilot A1 |",
        "| --- | --- | --- |",
        "| Corpus filtering | all 2,101 Geometry3K train rows | frozen 1,288-row subset after conservative-candidate removal |",
        "| Reward implementation | native EasyR1 `r1v.py` extraction/grading | `pilot-reward-v1`: canonical-v2 extraction, MathRuler precedence, contract-valid format component, native shadow |",
        f"| Tower setting | `freeze_vision_tower={str(prior['anchor_config']['worker']['actor']['model']['freeze_vision_tower']).lower()}` as resolved at launch | `freeze_vision_tower={str(prior['a1_config']['worker']['actor']['model']['freeze_vision_tower']).lower()}` |",
        "| Prompt/parser | `r1v.jinja`; native non-DOTALL training extractor | same `r1v.jinja`; immutable canonical-v2 extraction for pilot reward/evaluation |",
        f"| Data | `{prior['anchor_config']['data']['train_files']}` + `{prior['anchor_config']['data']['val_files']}` | `{prior['a1_config']['data']['train_files']}` + `{prior['a1_config']['data']['val_files']}` |",
        "| Checkpoint schedule | steps 20/40/60/80/100; validation every 10 steps | steps 20/40/60/80/100; validation every 10 steps |",
        "| Eval set | 601-row Geometry3K test; post-hoc R19 at base/step 100 | same 601-row test; R19 at steps 0/60/100 |",
        "| Decontamination | none applied before anchor training | Layer-1 plus train-vs-test conservative candidates removed under frozen V4 rule |",
        f"| Rollout placement | TP`{prior['anchor_config']['worker']['rollout']['tensor_parallel_size']}` | TP`{prior['a1_config']['worker']['rollout']['tensor_parallel_size']}` |",
        "| Shared optimization fields | Qwen2.5-VL-3B, real images, seed 1, G=5, 100 steps, batch/LR/KL settings | same |",
        "",
        "Outcome tiers:",
        "- Primary RQ1: cross-arm final-accuracy contrasts and recovery fractions on the Geometry3K test.",
        "- Primary RQ2: change in R19 geometry pair accuracy.",
        "- Key secondary: R19 overall pair-accuracy change; the q_i hurdle contrast; `D_caption^final = Acc_A3,100 - Acc_A1,100` with directional prediction `>= 0` on filtered Geometry3K; and `D_caption^gain = Delta_A3 - Delta_A1` reported separately.",
        "- Secondary: all per-category FlipTrack endpoints, including the cued chart point-value reading category.",
        "- Robustness: R20, chart v08, long horizon, and alternative parser fields.",
        "- Overall R19 is always shown with every per-template result. No post-hoc R19-minus-chart composite is computed.",
        "",
        "Primary RQ1 estimands:",
        "- `D_gray = Delta_A1 - Delta_A2gray`.",
        "- `D_none = Delta_A1 - Delta_A2b`.",
        "- `D_caption = Delta_A1 - Delta_A3`.",
        "- `Delta` is final minus step-0 greedy `Acc_final` on Geometry3K test; each estimand uses a paired item-bootstrap confidence interval.",
        "- Recovery fractions are `Delta_arm / Delta_A1`, reported with paired item-bootstrap intervals and the registered denominator-stability condition.",
        "",
        "Mechanism analysis:",
        "- `q_i` is a Jeffreys-smoothed estimate of baseline reward-opportunity; it is never described as a directly observed latent.",
        "- PRIMARY mechanism analysis: within each arm under its own baseline condition, the hurdle contrast `mean_gain(c_i > 0) - mean_gain(c_i = 0)` is greater than zero, with a paired-item bootstrap CI. Here `c_i` is the number correct among the 16 frozen baseline samples.",
        "- Secondary: tie-corrected Spearman rank association between q_i and per-item gain over all items. Spearman rho is the Pearson correlation of average ranks, with midranks for ties in q_i and gain.",
        "- Secondary: the same tie-corrected rank association restricted to `c_i > 0` items.",
        "- The floor is exactly `c_i=0` (0/16 sampled successes, `q_i=0.138659`), not every item numerically sharing that symmetric q_i.",
        "- Descriptive gain table: report the at-floor group plus ten equal-count deciles of the above-floor tail. Sort above-floor items by `(q_i, row_index)`; `row_index` is the deterministic tie-breaker from the frozen per-item artifact. Report n and q_i range for every decile.",
        "- The per-item q_i values are frozen by these guarded L7 output hashes:",
        "",
        "| Condition | Per-item output SHA256 |",
        "| --- | --- |",
        *source_rows,
        "",
        "Computed filtered-train floor/above-floor anchors:",
        "| Condition | n | At floor (0/16) | Floor fraction | Above floor | Above fraction | Mean q_i |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        *q_rows,
        "",
        "Directional predictions:",
        "- `Delta_A3 >= Delta_A2gray` and `Delta_A3 >= Delta_A2b`.",
        "- `Delta_A1` and `Delta_A3` are closer to each other than either is to the zero-visual-bit arms.",
        "- `D_caption^final = Acc_A3,100 - Acc_A1,100 >= 0` is secondary and prospective; `D_caption^gain = Delta_A3 - Delta_A1` is reported separately.",
        "",
        "Secondary analyses:",
        "- Recovery fractions are interpreted only if `Delta_A1 >= 2 x paired SE`; otherwise the registered primary values are shown with an unstable-denominator warning.",
        "- Equivalence of `Delta_A2gray - Delta_A2b` uses margin +/-0.05 and is supported only if the paired CI lies entirely inside the margin.",
        "- Format prediction: `DeltaFormat_blind >= DeltaFormat_A1 - 0.05` using `contract_valid`, conditional on a nontrivial A1 format gain.",
        "",
        "RQ2 FlipTrack R19 endpoints:",
        "- Checkpoints: 0, 60, and 100. Step 60 is scored from the scratch-resident merged checkpoint before cleanup.",
        "- PRIMARY: geometry-category pair accuracy.",
        "- SECONDARY: overall R19 pair accuracy.",
        "- Document category is calibration only because the 7B instrument is saturated.",
        "- Label: `cued chart point-value reading`.",
        f"> {CHART_CONSTRUCT}",
        "- SESOI is +/-0.05; no material change is supported only if the paired CI is entirely within [-0.05, +0.05].",
        f"> {R20_CAVEAT}",
        "- R19 and R20 are never pooled.",
        "",
        "Falsification statement:",
        f"> {FALSIFICATION}",
        "- Because the engineering anchor already informed the A1 branch, falsification is evaluated against the preregistered matched blind-arm contrasts; the blind-arm directions above remain forecasts.",
        "",
        "Parser acceptance conditions:",
        "- The 0.9156 canonical-v2/native agreement rate is context, not an acceptance criterion; the retired 0.95 threshold is not used.",
        "- All disagreements remain preserved row-by-row under a fixed residual taxonomy.",
        "- Blinded adjudication contains no native-correct/canonical-wrong residual.",
        "- Canonical-v2 passes the adversarial negative set, including unit-conflict and malformed-answer cases.",
        "- Parser and reward versions become immutable before launch; native r1v reward is logged as a shadow for every rollout.",
        "",
        "ViRL39K interpretation fork:",
        "| Observed M1 pattern | Registered ruling |",
        "| --- | --- |",
        "| caption q≈real AND zero-bit q substantial | Geo3K mechanism likely generalizes. |",
        "| caption well below real AND zero-bit near floor | Shortcut susceptibility is corpus-dependent; Geo3K cannot support a broad claim. |",
        "| strong source/category heterogeneity | H-mixed becomes the headline; stratify. |",
        "| captions exceed real | Caption-mediated accessibility; A3 indispensable. |",
        "| gray materially differs from no-image | Image-token presence is itself causal; retain both. |",
        "- M1 records the obtaining row after this registration merges; PIs confirm through Richard.",
        "",
        "Registration provenance and no-peeking:",
        "- Registration commit hash: `PENDING_RICHARD_MERGE`; the final file must replace this token with the merged commit recorded by the launcher before M0 can pass.",
        "- Exact planned launch commands:",
        "  - `scripts/launch_mech_pilot_arm.sh a1_real an12 0,1,2,3`",
        "  - `scripts/launch_mech_pilot_arm.sh a2_gray an12 4,5,6,7`",
        "  - `scripts/launch_mech_pilot_arm.sh a2b_noimage an29 0,1,2,3`",
        "  - `scripts/launch_mech_pilot_arm.sh a3_caption an29 4,5,6,7`",
        "- no pilot optimizer step has run",
        f"- {EXECUTION_ACCESS_DISCLOSURE}",
        "- No one, including the implementing agent, may inspect pilot training or validation metrics before this preregistration is merged as `reports/preregistration_pilot_v1.md` and present unchanged at Git `HEAD`.",
        "- `scripts/launch_mech_pilot_arm.sh` invokes fail-closed authorization before creating a run directory or touching GPUs, then requires the final preregistration to be tracked and byte-clean against `HEAD`; it also requires critical pilot code and the selected config to be clean against `HEAD`.",
        "- Any failed prerequisite exits before the first optimizer step. The draft filename is never sufficient.",
        "",
        "Deviations log:",
        "| Time | Deviation | Reason | Effect on estimands | PI disposition |",
        "| --- | --- | --- | --- | --- |",
        "",
        "Registration state:",
        "- R19 human contact-sheet audit: approved. Richard accepted all three templates, 60/60 pairs across all six checks.",
        "- Merge state: pending Richard merge; merge is sign-off and no separate signature round exists.",
        "- Final M0 path `reports/preregistration_pilot_v1.md`: intentionally absent.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--l7-summary", type=Path, required=True)
    parser.add_argument("--l7-audit", type=Path, required=True)
    parser.add_argument(
        "--filtered-ids",
        type=Path,
        default=Path("data/geo3k_pilot_filtered_ids.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    if args.output.name == "preregistration_pilot_v1.md":
        raise ValueError("draft generator refuses the final L12 preregistration filename")
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite preregistration draft: {args.output}")
    text = build_draft(
        root=args.root,
        l7_summary_path=args.l7_summary,
        l7_audit_path=args.l7_audit,
        filtered_ids_path=args.filtered_ids,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
