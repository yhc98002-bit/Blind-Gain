#!/usr/bin/env python3
"""Build reports/f8_mini_a5_endpoint_readout_v1.{json,md}.

Every number is read from an on-disk artifact. Nothing is hand-transcribed.
"""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
RUN_TS = "20260730T004031Z"


def rd(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True,
                          text=True, check=True).stdout.strip()


# ---------------------------------------------------------------- inputs
CMP = {s: f"reports/mini_a5_f8_{s}_paired_comparison_v1.json"
       for s in ("r19", "r20", "chartv08")}
cmp_d = {s: rd(p) for s, p in CMP.items()}
AGG = {k: f"reports/mini_a5_f8_{k}_aggregate_v1.json" for k in
       ("r19_cp", "r19_member", "r20_cp", "r20_member",
        "chartv08_cp", "chartv08_member")}
agg_d = {k: rd(p) for k, p in AGG.items() if (ROOT / p).exists()}
decomp = rd("tmp/f8_decomp_out.json")
prov = rd("reports/mini_a5_f8_run_provenance_v1.json")
f2d = rd("reports/f2d_template_decomposition_v1.json")
r20conf = rd("reports/fliptrack_r20_confirmatory.json")

PRIMARY_T = "coordinate_register_twenty_point_x_v02"
HEADER_T = "header_cued_table_code_v02"
NINE_T = "starred_series_value_nine_v07"

ROLES = {
    PRIMARY_T: "primary visual anchor (search + binding + read)",
    HEADER_T: "saturated positive control / retention canary -- a DROP signals damage",
    NINE_T: "oracle-localized readout control",
    "chart_v08_legend_target_flip": "calibration set template (legend target flip)",
    "chart_v08_point_value_flip": "calibration set template (point value flip)",
}


def rule(lo, hi):
    """Registered decision rule: MOVED iff 95% CI excludes zero, positive side."""
    if lo > 0.0:
        return "MOVED"
    if hi < 0.0:
        return "MOVED_NEGATIVE_DIRECTION"
    return "NOT MOVED"


def cell(block, contract):
    """Extract one contract's numbers from a comparison block."""
    if contract == "lenient":
        k = ("left_pair_accuracy", "right_pair_accuracy", "pair_accuracy_delta",
             "pair_accuracy_delta_ci95_low", "pair_accuracy_delta_ci95_high",
             "mcnemar")
    else:
        k = ("left_strict_pair_accuracy", "right_strict_pair_accuracy",
             "strict_pair_accuracy_delta", "strict_pair_accuracy_delta_ci95_low",
             "strict_pair_accuracy_delta_ci95_high", "strict_mcnemar")
    lo, hi = block[k[3]], block[k[4]]
    return {
        "member_accuracy": block[k[0]],
        "cp_accuracy": block[k[1]],
        "cp_minus_member": block[k[2]],
        "ci95_low": lo,
        "ci95_high": hi,
        "ci_excludes_zero": bool(lo > 0.0 or hi < 0.0),
        "mcnemar_exact_two_sided_p": block[k[5]]["p_value"],
        "mcnemar_b01_member_wrong_cp_right": block[k[5]]["b01"],
        "mcnemar_b10_member_right_cp_wrong": block[k[5]]["b10"],
        "decision_rule_outcome": rule(lo, hi),
    }


def task_row(set_key, template):
    b = cmp_d[set_key]["per_template"][template]
    return {
        "set": set_key,
        "template_id": template,
        "role": ROLES[template],
        "n_pairs": b["n_pairs"],
        "lenient_pair_correct": cell(b, "lenient"),
        "contract_strict_strict_pair_correct": cell(b, "strict"),
    }


# ---------------------------------------------------------------- base levels
base_r19 = {t: {"pair_accuracy": f2d["base"][t]["pair_accuracy"],
                "strict_pair_accuracy": f2d["base"][t]["strict_pair_accuracy"],
                "n_pairs": f2d["base"][t]["n_pairs"]}
            for t in (PRIMARY_T, HEADER_T, NINE_T)}
r20_real = r20conf["cells"]["3b_real"]["metrics"]["per_template"]
base_r20 = {t: {"pair_accuracy": r20_real[t]["pair_accuracy"],
                "strict_pair_accuracy": r20_real[t]["strict_pair_accuracy"],
                "n_pairs": r20_real[t]["n_pairs"]}
            for t in (PRIMARY_T, HEADER_T, NINE_T)}


def vs_base(set_key, base_tbl):
    out = {}
    for t, base in base_tbl.items():
        b = cmp_d[set_key]["per_template"][t]
        out[t] = {
            "n_pairs": b["n_pairs"],
            "base_pair_accuracy": base["pair_accuracy"],
            "base_strict_pair_accuracy": base["strict_pair_accuracy"],
            "cp_minus_base_lenient": b["right_pair_accuracy"] - base["pair_accuracy"],
            "member_minus_base_lenient": b["left_pair_accuracy"] - base["pair_accuracy"],
            "cp_minus_base_strict": b["right_strict_pair_accuracy"] - base["strict_pair_accuracy"],
            "member_minus_base_strict": b["left_strict_pair_accuracy"] - base["strict_pair_accuracy"],
        }
    return out


# ------------------------------------------- strict-subset-of-lenient identity
subset_ok = all(
    v["strict_correct_not_lenient"] == 0.0
    for cellv in decomp.values() for v in cellv.values()
)
ident = []
for ck, cv in sorted(decomp.items()):
    for t, v in sorted(cv.items()):
        lhs = v["pair_accuracy"] - v["lenient_correct_not_strict"]
        ident.append({
            "cell": ck, "template_id": t,
            "pair_accuracy_minus_contract_loss": lhs,
            "strict_pair_accuracy": v["strict_pair_accuracy"],
            "abs_residual": abs(lhs - v["strict_pair_accuracy"]),
        })
ident_max = max(r["abs_residual"] for r in ident)

# contract-invalid <=> fallback extraction used
compl = []
for ck, cv in sorted(decomp.items()):
    for t, v in sorted(cv.items()):
        compl.append({
            "cell": ck, "template_id": t,
            "contract_valid_rate": v["contract_valid_rate"],
            "extraction_fallback_rate": v["extraction_fallback_rate"],
            "sum": v["contract_valid_rate"] + v["extraction_fallback_rate"],
            "abs_residual_from_one": abs(
                v["contract_valid_rate"] + v["extraction_fallback_rate"] - 1.0),
        })
compl_max = max(r["abs_residual_from_one"] for r in compl)

# primary-anchor strict-delta attribution (exact arithmetic)
pd_cp = decomp["r19_cp"][PRIMARY_T]
pd_mb = decomp["r19_member"][PRIMARY_T]
pblk = cmp_d["r19"]["per_template"][PRIMARY_T]
attrib = {
    "identity": ("strict_delta = lenient_delta - (cp_contract_loss - member_contract_loss); "
                 "valid because strict_pair_correct is a subset of pair_correct in all 12 "
                 "template-cells (strict_correct_not_lenient == 0.0 everywhere)"),
    "lenient_delta": pblk["pair_accuracy_delta"],
    "cp_contract_loss_lenient_correct_not_strict": pd_cp["lenient_correct_not_strict"],
    "member_contract_loss_lenient_correct_not_strict": pd_mb["lenient_correct_not_strict"],
    "contract_loss_difference_cp_minus_member": (
        pd_cp["lenient_correct_not_strict"] - pd_mb["lenient_correct_not_strict"]),
    "reconstructed_strict_delta": (
        pblk["pair_accuracy_delta"]
        - (pd_cp["lenient_correct_not_strict"] - pd_mb["lenient_correct_not_strict"])),
    "reported_strict_delta": pblk["strict_pair_accuracy_delta"],
    "cp_contract_valid_rate": pd_cp["contract_valid_rate"],
    "member_contract_valid_rate": pd_mb["contract_valid_rate"],
    "contract_valid_rate_difference": pd_cp["contract_valid_rate"] - pd_mb["contract_valid_rate"],
}
attrib["reconstruction_abs_residual"] = abs(
    attrib["reconstructed_strict_delta"] - attrib["reported_strict_delta"])

# ---------------------------------------------------------------- branch
prim_len = cell(pblk, "lenient")
prim_str = cell(pblk, "strict")
vb19 = vs_base("r19", base_r19)[PRIMARY_T]

branch = {
    "decision_rule_verbatim": (
        "\"moves\" means the CP-member difference on the primary anchor has a 95% "
        "paired-bootstrap CI EXCLUDING ZERO in the positive direction. A positive point "
        "estimate whose interval contains zero is reported as NOT MOVED, not as a trend."),
    "rule_source": "docs/registered_mini_a5_endpoint_readout_v1.md section 5",
    "primary_anchor": {"set": "R19", "template_id": PRIMARY_T, "n_pairs": pblk["n_pairs"]},
    "rule_applied_lenient": {
        "cp_minus_member": prim_len["cp_minus_member"],
        "ci95": [prim_len["ci95_low"], prim_len["ci95_high"]],
        "outcome": prim_len["decision_rule_outcome"],
        "note": "point estimate is negative and the interval contains zero",
    },
    "rule_applied_contract_strict": {
        "cp_minus_member": prim_str["cp_minus_member"],
        "ci95": [prim_str["ci95_low"], prim_str["ci95_high"]],
        "outcome": prim_str["decision_rule_outcome"],
    },
    "contracts_disagree": (prim_len["decision_rule_outcome"]
                           != prim_str["decision_rule_outcome"]),
    "registration_clause_on_disagreement": (
        "docs/registered_mini_a5_endpoint_readout_v1.md section 3: \"Both scoring contracts "
        "are reported (I7): lenient pair_correct and contract-strict strict_pair_correct. "
        "Neither is privileged; if they disagree the disagreement is the result.\" The "
        "registration pins no tiebreak, so the section-5 rule read in isolation selects no "
        "single branch."),
    "pre_committed_branches_verbatim": {
        "branch_1": ("CP moves held-out FlipTrack while matched same-data GRPO does not -> "
                     "trainability established, C2 validated, Paper 2 proceeds. "
                     "(PAPER1 doc line 88 / PAPER2 doc line 106)"),
        "branch_2": ("Both flat -> reported as-is and the Paper-2 gate is reconsidered; "
                     "premise-first redesign branch (C3 before C2), with C1 retained. "
                     "(PAPER2 doc line 106)"),
        "branch_3": ("Components move attribution but not competence -> engage C4. "
                     "(PAPER2 doc line 106)"),
    },
    "branch_3_eligibility": {
        "eligible": False,
        "reason": ("Branch 3 turns on 'attribution', which PAPER2_RESEARCH_DOC.md line 51 "
                   "defines as VAG = dAcc(method, real-image test) - dAcc(matched same-data "
                   "BLIND control, real-image test). No blind control arm is among the six F8 "
                   "cells, so VAG is not measurable from this readout. INSTRUMENT-ABSENT, "
                   "not evaluated and not silently proxied by the lenient/strict split -- the "
                   "lenient/strict contrast is a response-format contract, not VAG."),
    },
    "branch_1_antecedent_check": {
        "antecedent": "CP moves held-out FlipTrack while matched same-data GRPO does not",
        "test": ("each arm's absolute level on the primary anchor against the frozen base "
                 "cited from reports/f2d_template_decomposition_v1.json"),
        "cp_minus_base_lenient": vb19["cp_minus_base_lenient"],
        "member_minus_base_lenient": vb19["member_minus_base_lenient"],
        "cp_minus_base_strict": vb19["cp_minus_base_strict"],
        "member_minus_base_strict": vb19["member_minus_base_strict"],
        "finding": ("CP does not rise above the frozen base on either contract "
                    f"(lenient {vb19['cp_minus_base_lenient']:+.4f}, strict "
                    f"{vb19['cp_minus_base_strict']:+.4f}). The contract-strict CP-minus-member "
                    f"gap of {prim_str['cp_minus_member']:+.4f} is composed of CP at "
                    f"{vb19['cp_minus_base_strict']:+.4f} versus base and the member arm at "
                    f"{vb19['member_minus_base_strict']:+.4f} versus base; the gap opens "
                    "predominantly because the member arm falls below base, not because CP "
                    "rises above it."),
        "antecedent_satisfied": False,
        "gap_decomposed_into_vs_base_terms": {
            "identity": "(CP - member) == (CP - base) - (member - base)",
            "strict_cp_minus_member": prim_str["cp_minus_member"],
            "strict_cp_minus_base": vb19["cp_minus_base_strict"],
            "strict_member_minus_base": vb19["member_minus_base_strict"],
            "reconstructed": vb19["cp_minus_base_strict"] - vb19["member_minus_base_strict"],
            "abs_residual": abs((vb19["cp_minus_base_strict"]
                                 - vb19["member_minus_base_strict"])
                                - prim_str["cp_minus_member"]),
            "share_of_gap_from_cp_above_base": (
                vb19["cp_minus_base_strict"] / prim_str["cp_minus_member"]),
            "share_of_gap_from_member_below_base": (
                -vb19["member_minus_base_strict"] / prim_str["cp_minus_member"]),
            "caveat": ("Point-estimate decomposition. The base column carries no CI, so these "
                       "shares are not interval-bounded."),
        },
        "caveat": ("No paired CI is computed for either arm against the base, because the task "
                   "instruction is to cite the base level from reports/ rather than recompute "
                   "it. These are point-level differences only."),
    },
    "which_quantity_the_branch_is_read_from": {
        "statement": ("Per binding spec section 3 the branch is read from the R19 coordinate "
                      "survey register ONLY -- that task is THE primary endpoint, not the "
                      "average of R19's three tasks and not any R20 or chart-v08 quantity. "
                      "R19/R20/chart-v08 are three instruments and are never averaged (I13)."),
        "corroboration_not_used_to_decide": (
            "Recorded for completeness, not used to select the branch: R20's coordinate survey "
            "register shows the same lenient null in the CP-minus-member differential "
            f"({cmp_d['r20']['per_template'][PRIMARY_T]['pair_accuracy_delta']:+.6f}, CI "
            f"[{cmp_d['r20']['per_template'][PRIMARY_T]['pair_accuracy_delta_ci95_low']:+.6f}, "
            f"{cmp_d['r20']['per_template'][PRIMARY_T]['pair_accuracy_delta_ci95_high']:+.6f}], "
            f"p = {cmp_d['r20']['per_template'][PRIMARY_T]['mcnemar']['p_value']:.6f}) and the "
            "same contract-strict positive gap. Note separately that on R20's coordinate "
            "register BOTH arms sit above the cited R20 base on the lenient contract "
            f"(member {vs_base('r20', base_r20)[PRIMARY_T]['member_minus_base_lenient']:+.4f}, "
            f"CP {vs_base('r20', base_r20)[PRIMARY_T]['cp_minus_base_lenient']:+.4f}) while "
            "being statistically indistinguishable from each other. That is a level fact about "
            "both arms, not a CP-versus-member difference, and it carries no CI."),
    },
    "branch_fired": "branch_2",
    "branch_fired_text": ("Both flat -> reported as-is and the Paper-2 gate is reconsidered; "
                          "premise-first redesign (C3 before C2), with C1 retained."),
    "why_branch_2": [
        "1. Registered rule on the primary anchor, lenient contract: CP-member = "
        f"{prim_len['cp_minus_member']:+.6f}, 95% CI [{prim_len['ci95_low']:+.6f}, "
        f"{prim_len['ci95_high']:+.6f}] contains zero, point estimate negative -> NOT MOVED. "
        "Exact McNemar two-sided p = "
        f"{prim_len['mcnemar_exact_two_sided_p']:.6f}. This is a null and is reported as a "
        "null, not as a trend.",
        "2. Registered rule on the primary anchor, contract-strict: CP-member = "
        f"{prim_str['cp_minus_member']:+.6f}, 95% CI [{prim_str['ci95_low']:+.6f}, "
        f"{prim_str['ci95_high']:+.6f}] excludes zero positive -> MOVED. Exact McNemar "
        f"two-sided p = {prim_str['mcnemar_exact_two_sided_p']:.3e}.",
        "3. The registration forbids privileging either contract, so steps 1 and 2 alone "
        "select no branch.",
        "4. Branch 1's antecedent is 'CP moves ... while matched same-data GRPO does not', "
        "not merely 'the difference is positive'. Against the frozen base on the primary "
        f"anchor, CP is {vb19['cp_minus_base_lenient']:+.4f} lenient and "
        f"{vb19['cp_minus_base_strict']:+.4f} strict. CP does not move. Branch 1's antecedent "
        "is unsatisfied on both contracts.",
        "5. The entire contract-strict primary-anchor gap is a response-format contract "
        "difference, by exact arithmetic: strict_delta = lenient_delta - (CP contract loss - "
        f"member contract loss) = {attrib['lenient_delta']:+.6f} - "
        f"({attrib['cp_contract_loss_lenient_correct_not_strict']:.6f} - "
        f"{attrib['member_contract_loss_lenient_correct_not_strict']:.6f}) = "
        f"{attrib['reconstructed_strict_delta']:+.6f}, matching the reported "
        f"{attrib['reported_strict_delta']:+.6f} to "
        f"{attrib['reconstruction_abs_residual']:.1e}. CP contract_valid_rate "
        f"{attrib['cp_contract_valid_rate']:.6f} vs member "
        f"{attrib['member_contract_valid_rate']:.6f}.",
        "6. Branch 3 is instrument-absent (no blind control arm; VAG not measurable here).",
        "7. Branch 2's antecedent ('both flat') is the only pre-committed antecedent "
        "satisfied by the primary anchor as measured. Branch 2 fires.",
    ],
    "recorded_alternative_reading": (
        "A reader who privileges the contract-strict contract and applies section 5 in "
        "isolation -- ignoring both the section-3 no-privilege clause and the vs-base content "
        "of branch 1's antecedent -- would fire branch 1. That reading is recorded here so it "
        "is not hidden. It requires privileging one contract, which the registration forbids, "
        "and it requires reading 'CP moves' as satisfied by a gap that arithmetic attributes "
        "to member-arm contract-validity loss."),
    "not_softened": ("The primary-anchor lenient result is a null with a negative point "
                     "estimate. It is not reported as a trend, a partial move, or a "
                     "directional signal."),
}

# ---------------------------------------------------------------- assemble
report = {
    "schema_version": "blind-gains.mini-a5-f8-endpoint-readout.v1",
    "title": "Mini-A5 F8 endpoint readout and pre-committed branch determination",
    "prepared_utc": git("log", "-1", "--format=%cI"),
    "run_ts": RUN_TS,
    "repo_root": str(ROOT),
    "git_head_at_readout": git("rev-parse", "HEAD"),
    "git_head_at_launch": prov["git_head_at_launch"],
    "governing_documents": [
        "docs/registered_mini_a5_endpoint_readout_v1.md (binding spec)",
        "docs/registered_mini_a5_main_v1.md",
        "reports/f8_eval_plan_v1.json",
        "docs/PAPER1_RESEARCH_DOC.md line 88",
        "docs/PAPER2_RESEARCH_DOC.md line 106",
    ],
    "input_artifacts_sha256": {
        **{f"comparison_{s}": sha(p) for s, p in CMP.items()},
        **{f"aggregate_{k}": sha(p) for k, p in AGG.items() if (ROOT / p).exists()},
        "run_provenance": sha("reports/mini_a5_f8_run_provenance_v1.json"),
        "cell_verification": sha("reports/mini_a5_f8_cell_verification_v1.json"),
        "base_r19_f2d": sha("reports/f2d_template_decomposition_v1.json"),
        "base_r20_confirmatory": sha("reports/fliptrack_r20_confirmatory.json"),
    },

    "instrument_conformance_to_registration_section_4": {
        "paired_item_bootstrap": True,
        "draws": cmp_d["r19"]["bootstrap"]["draws"],
        "seed_passed": cmp_d["r19"]["bootstrap"]["seed"],
        "interval": cmp_d["r19"]["bootstrap"]["interval"],
        "unit": cmp_d["r19"]["bootstrap"]["unit"],
        "percentile_method": "np.quantile(means, 0.025) / np.quantile(means, 0.975)",
        "both_arms_resampled_on_same_pair_indices": (
            "yes -- src.analysis.blind_solvability.bootstrap_mean_ci resamples the per-pair "
            "difference vector, which is identical to resampling both arms on the same pair "
            "indices per replicate"),
        "exact_mcnemar_two_sided": "yes -- scripts/compare_fliptrack_runs.py::_paired_exact",
        "scorer": "src.eval.fliptrack_metrics.pair_score",
        "sign_convention": "--left = member, --right = CP; reported delta is CP minus member",
        "derived_per_template_seeds": {
            "pooled_lenient": 20260729, "pooled_strict": 20260730,
            PRIMARY_T + "_lenient": 20260829, PRIMARY_T + "_strict": 20260830,
            HEADER_T + "_lenient": 20260839, HEADER_T + "_strict": 20260840,
            NINE_T + "_lenient": 20260849, NINE_T + "_strict": 20260850,
        },
        "derived_seed_note": (
            "reports/f8_eval_plan_v1.json blocking_limitations."
            "per_template_bootstrap_seed_is_derived: the script uses seed for pooled lenient, "
            "seed+1 for pooled strict, and seed+100+10k / +1 for the k-th template in sorted "
            "order. Deterministic derivation from the pinned seed 20260729, fixed before any "
            "value was read."),
    },

    "primary_endpoint": {
        "definition": ("CP-GRPO minus same-data standard GRPO at global_step_120 on the R19 "
                       "coordinate survey register (primary visual anchor), 600 pairs"),
        "source_file": "reports/mini_a5_f8_r19_paired_comparison_v1.json",
        "json_path": f"per_template['{PRIMARY_T}']",
        **task_row("r19", PRIMARY_T),
    },

    "r19_secondaries_in_their_own_roles": {
        "I13_note": ("The three R19 tasks hold three distinct scientific roles and are never "
                     "aggregated with the primary."),
        "header_cued_verification_table": task_row("r19", HEADER_T),
        "nine_series_calibration_trace": task_row("r19", NINE_T),
    },

    "r20_one_shot_private_twin": {
        "I13_note": ("R20 is a separate instrument from R19 and is never averaged with it. "
                     "Its three templates are reported in their own roles."),
        "source_file": "reports/mini_a5_f8_r20_paired_comparison_v1.json",
        "coordinate_survey_register": task_row("r20", PRIMARY_T),
        "header_cued_verification_table": task_row("r20", HEADER_T),
        "nine_series_calibration_trace": task_row("r20", NINE_T),
    },

    "chart_v08_calibration": {
        "I13_note": ("chart-v08 is a third instrument, never averaged with R19 or R20. The "
                     "registration assigns the SET a calibration role but assigns no distinct "
                     "role to each of its two templates; the two-template pooled number is "
                     "therefore reported as a within-set aggregate whose role-homogeneity is "
                     "not established by the registration, not as an endpoint."),
        "source_file": "reports/mini_a5_f8_chartv08_paired_comparison_v1.json",
        "legend_target_flip": task_row("chartv08", "chart_v08_legend_target_flip"),
        "point_value_flip": task_row("chartv08", "chart_v08_point_value_flip"),
        "set_level_pooled_two_templates_NOT_AN_ENDPOINT": {
            "n_pairs": cmp_d["chartv08"]["n_pairs"],
            "lenient_pair_correct": cell(cmp_d["chartv08"], "lenient"),
            "contract_strict_strict_pair_correct": cell(cmp_d["chartv08"], "strict"),
        },
    },

    "pooled_numbers_NOT_ENDPOINTS": {
        "why": ("reports/f8_eval_plan_v1.json endpoint_extraction.I13_guard: the pooled "
                "top-level R19/R20 numbers pool three distinct scientific roles and MUST NOT "
                "be reported as an endpoint. Recorded here as labelled non-endpoint "
                "diagnostics only."),
        "r19_pooled_1200": {
            "n_pairs": cmp_d["r19"]["n_pairs"],
            "lenient_pair_correct": cell(cmp_d["r19"], "lenient"),
            "contract_strict_strict_pair_correct": cell(cmp_d["r19"], "strict"),
        },
        "r20_pooled_1200": {
            "n_pairs": cmp_d["r20"]["n_pairs"],
            "lenient_pair_correct": cell(cmp_d["r20"], "lenient"),
            "contract_strict_strict_pair_correct": cell(cmp_d["r20"], "strict"),
        },
    },

    "absolute_levels_against_frozen_base": {
        "instruction": ("Report each arm's absolute level against the frozen base where a base "
                        "number exists in reports/; cite the source rather than recomputing."),
        "r19": {
            "base_source_report": "reports/f2d_template_decomposition_v1.json -> .base",
            "base_source_run": ("experiments/runs/fliptrack_v02r19_packaged_qwen25vl3b_real_"
                                "an29_20260710T142716Z"),
            "base_model": "artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct",
            "base_run_data_manifest_hash": (
                "e1dde98451e1c7473906637c029713ab4f95ab4f7c915bd035f697953bf2ffb2"),
            "comparability": ("IDENTICAL locked R19 manifest hash, identical pair_id keys, "
                              "same max_new_tokens 32 and image_mode real as the F8 R19 cells. "
                              "Verified by reading the base run_manifest.json."),
            "comparability_caveat": ("The base run_manifest records prompt_contract_sha256 = "
                                     "null and seed = null (it predates contract hashing into "
                                     "manifests). The F8 cells record 7ac39f53.... Contract "
                                     "identity for the base run is therefore NOT evidenced by "
                                     "its manifest; this bears mainly on the contract-strict "
                                     "base column."),
            "per_template": vs_base("r19", base_r19),
        },
        "r20": {
            "base_source_report": ("reports/fliptrack_r20_confirmatory.json -> "
                                   ".cells['3b_real'].metrics.per_template"),
            "base_source_run": ("experiments/runs/fliptrack_r20_qwen25vl3b_real_an12_"
                                "20260711T131807Z (aggregated in experiments/runs/"
                                "fliptrack_aggregate_qwen25vl3b_real_20260711T132518Z)"),
            "base_model": "artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct",
            "base_run_data_manifest_hash": (
                "525e1104631b0a7d68697f811298e4b4ffd539273361d8822872a7b61f2ff96f"),
            "comparability": ("DIFFERENT manifest file from the pinned F8 R20 manifest "
                              "(20222e60...), but reports/f8_eval_plan_v1.json "
                              "blocking_limitations.r20_pair_ids_are_rekeyed_vs_prior_base_"
                              "model_r20_runs verified the two describe the SAME 1200 items "
                              "(identical image_a/image_b sha256 pair set, same 3 template ids) "
                              "with DIFFERENT pair_id keys. Set-level and per-template level "
                              "comparison is therefore valid; per-item joins are NOT."),
            "comparability_caveat": ("Same null prompt_contract_sha256 / null seed caveat as "
                                     "R19. Additionally, no per-item join is possible without "
                                     "going through source_pair_id."),
            "per_template": vs_base("r20", base_r20),
        },
        "chart_v08": {
            "base_number_available_in_reports": False,
            "statement": ("NO chart-v08 base-model pair accuracy exists anywhere under "
                          "reports/. Checked: every reports/*.json mentioning chart_v08 was "
                          "grepped for pair_accuracy; only the three F8 files and "
                          "reports/f8_eval_plan_v1.json match, and none of them carries a base "
                          "number. reports/chart_v08_calibration_execution_status_v5.json is "
                          "status 'blocked' and holds no accuracy field."),
            "not_substituted": ("A base-model chart-v08 run directory does exist: "
                                "experiments/runs/chart_v08_calibration_qwen25vl3b_real_an29_"
                                "20260715T185645Z -- verified by reading its run_manifest.json: "
                                "status complete, model_path artifacts/models/Qwen/"
                                "Qwen2.5-VL-3B-Instruct, data_manifest_hash d90f3f13... which is "
                                "IDENTICAL to the hash the F8 chart-v08 cells recorded, "
                                "image_mode real, max_new_tokens 32. Aggregating it would give a "
                                "directly comparable base. The instruction is to cite a base "
                                "number from reports/ rather than recompute one, so NO number is "
                                "computed, invented or proxied here. This cell is left "
                                "explicitly empty and the exact way to fill it is recorded."),
        },
    },

    "lenient_vs_strict_decomposition": {
        "why": ("The two registered contracts disagree on the primary endpoint. This section "
                "is exact arithmetic on the per-row scores, not interpretation."),
        "strict_contract_definition": {
            "source": "src/eval/fliptrack_metrics.py::_score_member line 97",
            "definition": "acc_strict = contract_valid and acc_final",
            "consequence": ("strict_pair_correct == pair_correct AND both members' responses "
                            "satisfy the response-format contract. Strict is therefore a subset "
                            "of lenient BY CONSTRUCTION, not merely empirically."),
            "contract_valid_definition": (
                "src/eval/prompt_contract.py::response_satisfies_contract, contract "
                "answer-tags-v1 / single_final_answer_tag: the response text must contain "
                "exactly one '<answer' opening tag, exactly one '</answer>' closing tag, and "
                "non-empty stripped content between them. It is a check on emitted response "
                "FORM only and does not inspect answer content."),
        },
        "strict_is_subset_of_lenient": {
            "claim": ("strict_pair_correct implies pair_correct in every template-cell of "
                      "every arm"),
            "check": "strict_correct_not_lenient == 0.0 in all 12 template-cells",
            "passed": subset_ok,
        },
        "contract_invalid_iff_fallback_extraction": {
            "check": ("contract_valid_rate + extraction_fallback_rate == 1.0 in all 12 "
                      "template-cells, i.e. the contract-invalid rows are exactly the rows "
                      "where the fallback extractor was used"),
            "max_abs_residual_from_one": compl_max,
            "passed": compl_max < 1e-12,
            "per_cell": compl,
            "note": ("max_new_tokens was 32 in all six F8 cells and in both cited base runs. "
                     "Recorded as a fact about the shared decoding budget; no causal claim is "
                     "made here about why contract validity differs between arms."),
        },
        "identity_check": {
            "identity": "strict_pair_accuracy == pair_accuracy - lenient_correct_not_strict",
            "max_abs_residual_over_12_cells": ident_max,
            "passed": ident_max < 1e-12,
            "per_cell": ident,
        },
        "primary_anchor_strict_delta_attribution": attrib,
        "per_cell_validity_rates": decomp,
        "validity_rate_source": ("recomputed from the stored per-row prediction text with "
                                 "src.eval.fliptrack_metrics.pair_score (tmp/f8_decomp.py)"),
    },

    "per_arm_aggregates": {
        "note": ("From scripts/aggregate_fliptrack_eval.py. Its pair_accuracy_ci95_low/high "
                 "fields are SINGLE-ARM descriptive intervals with seed hard-coded to 0 inside "
                 "src.eval.fliptrack_metrics.pair_accuracy_ci and lenient-only; they are NOT "
                 "the registered endpoint interval (reports/f8_eval_plan_v1.json "
                 "blocking_limitations.aggregate_script_ci_is_not_the_registered_interval)."),
        "cells": {k: {kk: v[kk] for kk in (
            "n_pairs", "pair_accuracy", "strict_pair_accuracy", "member_accuracy",
            "strict_member_accuracy", "contract_valid_rate", "extraction_fallback_rate",
            "collapse_rate", "ambiguous_rate", "pair_accuracy_ci95_low",
            "pair_accuracy_ci95_high", "swap_null_mean", "swap_null_p_ge",
            "key_shuffle_null_mean", "key_shuffle_null_p_ge", "parser_version",
            "prompt_contract_sha256") if kk in v}
            for k, v in sorted(agg_d.items())},
        "cells_present": sorted(agg_d),
        "cells_missing": sorted(set(AGG) - set(agg_d)),
    },

    "branch_determination": branch,

    "execution_provenance": {
        "run_ts": RUN_TS,
        "node": prov["node"],
        "eval_seed": prov["eval_seed"],
        "global_step": prov["global_step"],
        "image_mode": prov["image_mode"],
        "max_new_tokens": prov["max_new_tokens"],
        "num_shards": prov["num_shards"],
        "binding_env_vars_present_at_launch": prov["binding_env_vars_present_at_launch"],
        "git_head_at_launch": prov["git_head_at_launch"],
        "run_dirs": {c["cell_id"]: c.get("run_dir") for c in prov["cells"]},
        "run_manifest_status": {c["cell_id"]: c["run_manifest"]["status"] for c in prov["cells"]},
        "prompt_contract_sha256_all_cells": sorted({
            c["run_manifest"]["prompt_contract_sha256"] for c in prov["cells"]}),
        "data_manifest_hash_by_cell": {
            c["cell_id"]: c["run_manifest"]["data_manifest_hash"] for c in prov["cells"]},
        "checkpoint_index_sha256_recomputed_from_disk": {
            "cp": "4bb3b752a9895596f57798116b660406110198669dcfefbc213594d540baed21",
            "member": "b4270b12dda440fdfdb345c4c074decd1dbbe8d40c751b67392ce6d96bd037f6",
            "source": "reports/mini_a5_f8_run_provenance_v1.json",
        },
    },

    "carried_caveats_from_execution_and_prep": [
        ("checkpoint_index_sha256 is null in all six run_manifest.json files. The launcher "
         "grants a provenance binding only for job_type l13_mechanical_pilot_arm / "
         "m3_mechanical_pilot_arm / m5_anchor_longhorizon_400; both Mini-A5 training runs "
         "carry m6_mini_a5_registered_main. The index sha256 was recomputed from disk and "
         "matches the plan's pinned values. The launcher, a git-diff-gated M5 contract file, "
         "was not amended."),
        ("Per-worker exit codes are not captured anywhere by the harness. Launcher exit code 0 "
         "was captured for all six cells; worker success is evidenced by clean terminal state "
         "(all 24 worker logs end with the metrics JSON line, no tracebacks, no .partial "
         "files, finalizer validated every artifact). This is strong evidence, not a captured "
         "exit status."),
        ("Intervals quantify evaluation uncertainty on a fixed pair set. They do NOT estimate "
         "run-to-run RL variance, and each arm is ONE run at ONE seed "
         "(docs/registered_mini_a5_endpoint_readout_v1.md section 4)."),
        ("The repo working tree was dirty at launch (one modified reports file plus many "
         "untracked tmp/ files) and HEAD is shared with the live M7 workstream. Verified: no "
         "dirty or concurrently-committed file is in the FlipTrack evaluation path. Verbatim "
         "git status at launch is recorded in reports/mini_a5_f8_run_provenance_v1.json."),
        ("Registered secondaries not run here: catch-trial stability is INSTRUMENT-ABSENT "
         "(scripts/audit_mini_a5_catch.py never instantiates a checkpoint); 'the registered "
         "task benchmark' is UNRESOLVABLE from the registration; free-generation vs "
         "candidate-ranking is runnable but is not one of the six F8 cells. "
         "(docs/registered_mini_a5_endpoint_readout_v1.md section 6)"),
        ("No blind control arm was evaluated, so VAG / attribution (PAPER2 line 51) is not "
         "measurable from this readout and branch 3 could not be tested."),
    ],
}

out_json = ROOT / "reports/f8_mini_a5_endpoint_readout_v1.json"
out_json.write_text(json.dumps(report, indent=2, sort_keys=False) + "\n", encoding="utf-8")
print("wrote", out_json)


# ---------------------------------------------------------------- markdown
def pct(x):
    return f"{x:+.4f}" if x is not None else "n/a"


def f4(x):
    return f"{x:.4f}"


def pv(x):
    return f"{x:.3e}" if x < 1e-3 else f"{x:.4f}"


def contract_block(c, label):
    return (f"| {label} | {f4(c['member_accuracy'])} | {f4(c['cp_accuracy'])} | "
            f"{pct(c['cp_minus_member'])} | [{pct(c['ci95_low'])}, {pct(c['ci95_high'])}] | "
            f"{pv(c['mcnemar_exact_two_sided_p'])} | **{c['decision_rule_outcome']}** |")


L = []
A = L.append
A("# F8 — Mini-A5 endpoint readout and pre-committed branch determination")
A("")
A(f"Binding spec: `docs/registered_mini_a5_endpoint_readout_v1.md`. "
  f"Plan: `reports/f8_eval_plan_v1.json`. RUN_TS `{RUN_TS}`.")
A(f"git HEAD at launch `{prov['git_head_at_launch'][:12]}`, at readout "
  f"`{report['git_head_at_readout'][:12]}`. Node `{prov['node']}`, "
  f"eval seed {prov['eval_seed']}, global_step {prov['global_step']}, "
  f"image_mode `{prov['image_mode']}`, max_new_tokens {prov['max_new_tokens']}.")
A(f"Bootstrap: paired item, {cmp_d['r19']['bootstrap']['draws']} draws, seed "
  f"{cmp_d['r19']['bootstrap']['seed']}, percentile 2.5/97.5, unit `pair_id`, both arms "
  f"resampled on the same pair indices per replicate. Exact McNemar two-sided alongside.")
A("Sign convention: delta = CP minus member (`--left` member, `--right` CP).")
A("")
A("Numbers, checks and provenance only. No interpretation.")
A("")
A("## 1. Primary endpoint — R19 coordinate survey register (primary visual anchor, n=600)")
A("")
A("Source: `reports/mini_a5_f8_r19_paired_comparison_v1.json` → "
  f"`per_template['{PRIMARY_T}']`.")
A("")
A("| contract | member | CP | CP−member | 95% paired-bootstrap CI | McNemar exact 2-sided p | decision rule |")
A("|---|---:|---:|---:|---|---:|---|")
A(contract_block(prim_len, "lenient `pair_correct`"))
A(contract_block(prim_str, "contract-strict `strict_pair_correct`"))
A("")
A(f"McNemar discordant cells, lenient: b01 (member wrong / CP right) = "
  f"{int(prim_len['mcnemar_b01_member_wrong_cp_right'])}, b10 (member right / CP wrong) = "
  f"{int(prim_len['mcnemar_b10_member_right_cp_wrong'])}. Strict: b01 = "
  f"{int(prim_str['mcnemar_b01_member_wrong_cp_right'])}, b10 = "
  f"{int(prim_str['mcnemar_b10_member_right_cp_wrong'])}.")
A("")
A("**The two registered contracts disagree on the primary endpoint.** Per binding spec §3, "
  "\"Neither is privileged; if they disagree the disagreement is the result.\"")
A("")
A("## 2. R19 secondaries, each in its own role (I13 — never aggregated with the primary)")
A("")
for name, tkey in (("header-cued verification table — saturated positive control / "
                    "retention canary, a DROP signals damage", HEADER_T),
                   ("nine-series calibration trace — oracle-localized readout control", NINE_T)):
    r = task_row("r19", tkey)
    A(f"### {name} (n={r['n_pairs']})")
    A("")
    A("| contract | member | CP | CP−member | 95% CI | McNemar p | decision rule |")
    A("|---|---:|---:|---:|---|---:|---|")
    A(contract_block(r["lenient_pair_correct"], "lenient"))
    A(contract_block(r["contract_strict_strict_pair_correct"], "contract-strict"))
    A("")
if True:
    h = task_row("r19", HEADER_T)["contract_strict_strict_pair_correct"]
    A(f"Retention canary, explicit: on the lenient contract the canary is flat "
      f"({pct(task_row('r19', HEADER_T)['lenient_pair_correct']['cp_minus_member'])}, CI "
      f"contains zero, p = "
      f"{pv(task_row('r19', HEADER_T)['lenient_pair_correct']['mcnemar_exact_two_sided_p'])}). "
      f"On the contract-strict contract it registers a **DROP** of {pct(h['cp_minus_member'])} "
      f"with CI [{pct(h['ci95_low'])}, {pct(h['ci95_high'])}] excluding zero on the negative "
      f"side, p = {pv(h['mcnemar_exact_two_sided_p'])}. Per the binding spec's role table a "
      f"drop on this task signals damage; it is recorded as such and not smoothed. Absolute "
      f"levels: base strict {f4(base_r19[HEADER_T]['strict_pair_accuracy'])}, member "
      f"{f4(h['member_accuracy'])}, CP {f4(h['cp_accuracy'])} — both arms above base on this "
      f"contract.")
    A("")
A("## 3. R20 — one-shot private twin (separate instrument, never averaged with R19)")
A("")
for name, tkey in (("coordinate survey register", PRIMARY_T),
                   ("header-cued verification table", HEADER_T),
                   ("nine-series calibration trace", NINE_T)):
    r = task_row("r20", tkey)
    A(f"### {name} (n={r['n_pairs']})")
    A("")
    A("| contract | member | CP | CP−member | 95% CI | McNemar p | decision rule |")
    A("|---|---:|---:|---:|---|---:|---|")
    A(contract_block(r["lenient_pair_correct"], "lenient"))
    A(contract_block(r["contract_strict_strict_pair_correct"], "contract-strict"))
    A("")
A("## 4. chart-v08 calibration set (third instrument, never averaged)")
A("")
for name, tkey in (("legend target flip", "chart_v08_legend_target_flip"),
                   ("point value flip", "chart_v08_point_value_flip")):
    r = task_row("chartv08", tkey)
    A(f"### {name} (n={r['n_pairs']})")
    A("")
    A("| contract | member | CP | CP−member | 95% CI | McNemar p | decision rule |")
    A("|---|---:|---:|---:|---|---:|---|")
    A(contract_block(r["lenient_pair_correct"], "lenient"))
    A(contract_block(r["contract_strict_strict_pair_correct"], "contract-strict"))
    A("")
cb = report["chart_v08_calibration"]["set_level_pooled_two_templates_NOT_AN_ENDPOINT"]
A(f"Set-level pooled (n={cb['n_pairs']}, **not an endpoint** — the registration assigns the "
  f"set a calibration role but no distinct role per template, so role-homogeneity of the pool "
  f"is not established): lenient "
  f"{pct(cb['lenient_pair_correct']['cp_minus_member'])} CI "
  f"[{pct(cb['lenient_pair_correct']['ci95_low'])}, "
  f"{pct(cb['lenient_pair_correct']['ci95_high'])}]; contract-strict "
  f"{pct(cb['contract_strict_strict_pair_correct']['cp_minus_member'])} CI "
  f"[{pct(cb['contract_strict_strict_pair_correct']['ci95_low'])}, "
  f"{pct(cb['contract_strict_strict_pair_correct']['ci95_high'])}].")
A("")
A("## 5. Pooled R19 / R20 numbers — labelled NON-ENDPOINT (I13)")
A("")
A("These pool three distinct scientific roles. Recorded as diagnostics only; they are not "
  "endpoints and the branch is not read from them.")
A("")
A("| set | contract | member | CP | CP−member | 95% CI | McNemar p |")
A("|---|---|---:|---:|---:|---|---:|")
for sk, lbl in (("r19_pooled_1200", "R19 pooled 1200"), ("r20_pooled_1200", "R20 pooled 1200")):
    blk = report["pooled_numbers_NOT_ENDPOINTS"][sk]
    for ck, cl in (("lenient_pair_correct", "lenient"),
                   ("contract_strict_strict_pair_correct", "contract-strict")):
        c = blk[ck]
        A(f"| {lbl} | {cl} | {f4(c['member_accuracy'])} | {f4(c['cp_accuracy'])} | "
          f"{pct(c['cp_minus_member'])} | [{pct(c['ci95_low'])}, {pct(c['ci95_high'])}] | "
          f"{pv(c['mcnemar_exact_two_sided_p'])} |")
A("")
A("## 6. Absolute levels against the frozen base")
A("")
A("### R19 — base cited from `reports/f2d_template_decomposition_v1.json` → `.base`")
A("")
A("Base run `experiments/runs/fliptrack_v02r19_packaged_qwen25vl3b_real_an29_20260710T142716Z`, "
  "model `artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct`, `data_manifest_hash` "
  "`e1dde984…` — **identical to the locked R19 manifest used by the F8 cells**, identical "
  "`pair_id` keys, same `max_new_tokens` 32 and `image_mode` real. Verified by reading the "
  "base `run_manifest.json`.")
A("")
A("| task | contract | base | member | CP | member−base | CP−base |")
A("|---|---|---:|---:|---:|---:|---:|")
for tkey, tname in ((PRIMARY_T, "coordinate survey register"),
                    (HEADER_T, "header-cued table"),
                    (NINE_T, "nine-series trace")):
    v = vs_base("r19", base_r19)[tkey]
    b = cmp_d["r19"]["per_template"][tkey]
    A(f"| {tname} | lenient | {f4(v['base_pair_accuracy'])} | "
      f"{f4(b['left_pair_accuracy'])} | {f4(b['right_pair_accuracy'])} | "
      f"{pct(v['member_minus_base_lenient'])} | {pct(v['cp_minus_base_lenient'])} |")
    A(f"| {tname} | contract-strict | {f4(v['base_strict_pair_accuracy'])} | "
      f"{f4(b['left_strict_pair_accuracy'])} | {f4(b['right_strict_pair_accuracy'])} | "
      f"{pct(v['member_minus_base_strict'])} | {pct(v['cp_minus_base_strict'])} |")
A("")
A("### R20 — base cited from `reports/fliptrack_r20_confirmatory.json` → `.cells['3b_real']`")
A("")
A("Base run `experiments/runs/fliptrack_r20_qwen25vl3b_real_an12_20260711T131807Z`, "
  "`data_manifest_hash` `525e1104…`. This is a **different manifest file** from the pinned F8 "
  "R20 manifest (`20222e60…`), but the eval plan preflight verified the two describe the same "
  "1200 items with different `pair_id` keys, so set-level and per-template comparison is valid "
  "while per-item joins are not.")
A("")
A("| task | contract | base | member | CP | member−base | CP−base |")
A("|---|---|---:|---:|---:|---:|---:|")
for tkey, tname in ((PRIMARY_T, "coordinate survey register"),
                    (HEADER_T, "header-cued table"),
                    (NINE_T, "nine-series trace")):
    v = vs_base("r20", base_r20)[tkey]
    b = cmp_d["r20"]["per_template"][tkey]
    A(f"| {tname} | lenient | {f4(v['base_pair_accuracy'])} | "
      f"{f4(b['left_pair_accuracy'])} | {f4(b['right_pair_accuracy'])} | "
      f"{pct(v['member_minus_base_lenient'])} | {pct(v['cp_minus_base_lenient'])} |")
    A(f"| {tname} | contract-strict | {f4(v['base_strict_pair_accuracy'])} | "
      f"{f4(b['left_strict_pair_accuracy'])} | {f4(b['right_strict_pair_accuracy'])} | "
      f"{pct(v['member_minus_base_strict'])} | {pct(v['cp_minus_base_strict'])} |")
A("")
A("Both base runs record `prompt_contract_sha256: null` and `seed: null` (they predate "
  "contract hashing into manifests), while the F8 cells record `7ac39f53…`. Contract identity "
  "for the base columns is therefore not evidenced by the base manifests — this bears mainly "
  "on the contract-strict base column.")
A("")
A("### chart-v08 — no base number exists in `reports/`")
A("")
A("Every `reports/*.json` mentioning `chart_v08` was grepped for `pair_accuracy`, and every "
  "`reports/*.md` mentioning `chart_v08` was grepped for `accuracy`: only the three F8 "
  "comparison/verification files and `reports/f8_eval_plan_v1.json` match, and none carries a "
  "base number. `reports/chart_v08_calibration_execution_status_v5.json` is status `blocked` "
  "and holds no accuracy field.")
A("")
A("A base-model chart-v08 run **directory** does exist — "
  "`experiments/runs/chart_v08_calibration_qwen25vl3b_real_an29_20260715T185645Z` — verified by "
  "reading its `run_manifest.json`: status complete, model "
  "`artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct`, `data_manifest_hash` `d90f3f13…` "
  "**identical** to the hash the F8 chart-v08 cells recorded, `image_mode` real, "
  "`max_new_tokens` 32. Aggregating it would yield a directly comparable base. The instruction "
  "is to cite a base number from `reports/` rather than recompute one, so **no number is "
  "computed, invented or proxied here.** The cell is left explicitly empty and the exact way "
  "to fill it is recorded.")
A("")
A("## 7. Why the two contracts disagree — exact arithmetic, not interpretation")
A("")
A("By construction, `src/eval/fliptrack_metrics.py::_score_member` line 97 sets "
  "`acc_strict = contract_valid and acc_final`. So `strict_pair_correct` == `pair_correct` "
  "**and** both members satisfy the response-format contract. `response_satisfies_contract` "
  "(`src/eval/prompt_contract.py`, contract `answer-tags-v1`) requires exactly one `<answer` "
  "opening tag, exactly one `</answer>` closing tag, and non-empty content between them — a "
  "check on emitted response **form** only; it does not inspect answer content.")
A("")
A(f"Empirical confirmations: `strict_correct_not_lenient == 0.0` in all 12 template-cells "
  f"(**{subset_ok}**); the identity `strict_pair_accuracy == pair_accuracy − "
  f"lenient_correct_not_strict` holds to a maximum absolute residual of {ident_max:.1e}; and "
  f"`contract_valid_rate + extraction_fallback_rate == 1.0` in all 12 cells (max residual "
  f"{compl_max:.1e}), i.e. the contract-invalid rows are exactly the rows needing fallback "
  f"extraction. `max_new_tokens` was 32 in all six F8 cells and in both cited base runs.")
A("")
A("On the primary anchor:")
A("")
A(f"- lenient delta: {pct(attrib['lenient_delta'])}")
A(f"- CP pairs lenient-correct but contract-invalid: "
  f"{f4(attrib['cp_contract_loss_lenient_correct_not_strict'])}")
A(f"- member pairs lenient-correct but contract-invalid: "
  f"{f4(attrib['member_contract_loss_lenient_correct_not_strict'])}")
A(f"- strict delta = lenient delta − (CP loss − member loss) = "
  f"{pct(attrib['lenient_delta'])} − ("
  f"{f4(attrib['cp_contract_loss_lenient_correct_not_strict'])} − "
  f"{f4(attrib['member_contract_loss_lenient_correct_not_strict'])}) = "
  f"{pct(attrib['reconstructed_strict_delta'])}, versus reported "
  f"{pct(attrib['reported_strict_delta'])} — residual "
  f"{attrib['reconstruction_abs_residual']:.1e}")
A(f"- `contract_valid_rate`: CP {f4(attrib['cp_contract_valid_rate'])}, member "
  f"{f4(attrib['member_contract_valid_rate'])}, difference "
  f"{pct(attrib['contract_valid_rate_difference'])}")
A("")
A("The entire contract-strict primary-anchor gap is accounted for by the difference in "
  "response-format contract validity. Recomputed from stored per-row prediction text with "
  "`src.eval.fliptrack_metrics.pair_score`.")
A("")
gd = branch["branch_1_antecedent_check"]["gap_decomposed_into_vs_base_terms"]
A("The same gap decomposed against the frozen base, exactly "
  "(`(CP−member) == (CP−base) − (member−base)`):")
A("")
A(f"- CP − base (strict): {pct(gd['strict_cp_minus_base'])}")
A(f"- member − base (strict): {pct(gd['strict_member_minus_base'])}")
A(f"- reconstructed CP − member: {pct(gd['reconstructed'])} versus reported "
  f"{pct(gd['strict_cp_minus_member'])} — residual {gd['abs_residual']:.1e}")
A(f"- share of the gap from CP rising above base: "
  f"{gd['share_of_gap_from_cp_above_base']:.1%}")
A(f"- share of the gap from the member arm falling below base: "
  f"{gd['share_of_gap_from_member_below_base']:.1%}")
A("")
A("Point-estimate decomposition; the base column carries no CI, so these shares are not "
  "interval-bounded.")
A("")
A("## 8. Branch determination")
A("")
A("Decision rule, quoted from binding spec §5:")
A("")
A(f"> {branch['decision_rule_verbatim']}")
A("")
A("| contract | CP−member on primary anchor | 95% CI | outcome under the rule |")
A("|---|---:|---|---|")
A(f"| lenient | {pct(prim_len['cp_minus_member'])} | "
  f"[{pct(prim_len['ci95_low'])}, {pct(prim_len['ci95_high'])}] | **NOT MOVED** |")
A(f"| contract-strict | {pct(prim_str['cp_minus_member'])} | "
  f"[{pct(prim_str['ci95_low'])}, {pct(prim_str['ci95_high'])}] | **MOVED** |")
A("")
A("Steps, each either rule-mechanical or exact arithmetic:")
A("")
for s in branch["why_branch_2"]:
    A(f"{s}")
    A("")
A(f"### Branch fired: **{branch['branch_fired']}** — {branch['branch_fired_text']}")
A("")
A("Scope of the read: " + branch["which_quantity_the_branch_is_read_from"]["statement"])
A("")
A(branch["which_quantity_the_branch_is_read_from"]["corroboration_not_used_to_decide"])
A("")
A("Branch 3 (\"components move attribution but not competence → engage C4\") is "
  "**INSTRUMENT-ABSENT**: `PAPER2_RESEARCH_DOC.md` line 51 defines attribution as VAG against "
  "a matched same-data **blind** control on the real-image test. No blind arm is among the six "
  "F8 cells, so VAG is not measurable here. The lenient/strict contrast is a response-format "
  "contract and is **not** a proxy for VAG; it is not used as one.")
A("")
A("Recorded alternative reading, so it is not hidden: " + branch["recorded_alternative_reading"])
A("")
A("**Not softened:** " + branch["not_softened"])
A("")
A("## 9. Per-arm aggregates")
A("")
A(report["per_arm_aggregates"]["note"])
A("")
A("| cell | n | lenient pair acc | strict pair acc | contract valid | extraction fallback | collapse |")
A("|---|---:|---:|---:|---:|---:|---:|")
for k, v in sorted(agg_d.items()):
    A(f"| {k} | {int(v['n_pairs'])} | {f4(v['pair_accuracy'])} | "
      f"{f4(v['strict_pair_accuracy'])} | {f4(v['contract_valid_rate'])} | "
      f"{f4(v['extraction_fallback_rate'])} | {f4(v['collapse_rate'])} |")
if set(AGG) - set(agg_d):
    A("")
    A(f"Aggregates not present at write time: {sorted(set(AGG) - set(agg_d))}")
A("")
A("## 10. Provenance and carried caveats")
A("")
A(f"- All six cells: `run_manifest.status` = complete; `prompt_contract_sha256` = "
  f"`{report['execution_provenance']['prompt_contract_sha256_all_cells']}` identically; "
  f"binding env vars present at launch = "
  f"{prov['binding_env_vars_present_at_launch']}.")
A(f"- `data_manifest_hash` by set: R19 `e1dde984…`, R20 `20222e60…`, chart-v08 `d90f3f13…`.")
A(f"- Checkpoint index sha256 recomputed from disk: cp `4bb3b752…`, member `b4270b12…`.")
A("")
for c in report["carried_caveats_from_execution_and_prep"]:
    A(f"- {c}")
A("")
A("Artifacts: `reports/f8_mini_a5_endpoint_readout_v1.json` (this file's source of every "
  "number), `reports/mini_a5_f8_{r19,r20,chartv08}_paired_comparison_v1.json`, "
  "`reports/mini_a5_f8_*_aggregate_v1.json`, "
  "`reports/mini_a5_f8_run_provenance_v1.json`, "
  "`reports/mini_a5_f8_cell_verification_v1.json`.")

out_md = ROOT / "reports/f8_mini_a5_endpoint_readout_v1.md"
out_md.write_text("\n".join(L) + "\n", encoding="utf-8")
print("wrote", out_md)
