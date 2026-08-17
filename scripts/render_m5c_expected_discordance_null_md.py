#!/usr/bin/env python3
"""Render reports/m5c_expected_discordance_null_v1.md from the v1 JSON."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
SRC = ROOT / "reports/m5c_expected_discordance_null_v1.json"
DST = ROOT / "reports/m5c_expected_discordance_null_v1.md"


def f(x: float, n: int = 4) -> str:
    return f"{x:.{n}f}"


def ci(pair, n: int = 4) -> str:
    return f"[{pair[0]:.{n}f}, {pair[1]:.{n}f}]"


VERDICT_TAGS = {
    "observed_exceeds_expected": "OBSERVED EXCEEDS the sampled-variability expectation",
    "observed_below_expected": "OBSERVED IS BELOW the sampled-variability expectation",
    "not_distinguishable": (
        "OBSERVED IS NOT DISTINGUISHABLE from the sampled-variability expectation"
    ),
    "mixed_bootstrap_and_monte_carlo_disagree": (
        "MIXED: the bootstrap CI on the difference and the Monte-Carlo count test do not agree"
    ),
}


def verdict(block: dict) -> tuple[str, str]:
    d = block["plugin_mle"]
    diff = d["observed_minus_expected_fraction"]
    lo, hi = d["observed_minus_expected_bootstrap_ci95"]
    p_mc = d["mc_null_plugin"]["p_one_sided_observed_ge_null"]
    p_pp = d["mc_null_posterior_propagated"]["p_one_sided_observed_ge_null"]
    tag = VERDICT_TAGS[block["direction_of_result"]["verdict"]]
    detail = (
        f"observed {f(block['observed_greedy_discordance_fraction'])} "
        f"vs expected {f(d['expected_discordance_fraction'])}; "
        f"difference {f(diff)} (bootstrap 95% CI {ci([lo, hi])}); "
        f"one-sided Monte-Carlo p(null count >= observed) = {p_mc:.4f} plug-in, "
        f"{p_pp:.4f} posterior-propagated"
    )
    return tag, detail


def metric_section(name: str, block: dict) -> list[str]:
    L: list[str] = [f"### {name} — `{block['metric']}`", ""]
    n = block["n_items"]
    L.append(
        f"Observed greedy discordance: **{block['observed_greedy_discordance_count']}/{n} = "
        f"{f(block['observed_greedy_discordance_fraction'])}**"
    )
    L.append("")
    L.append("| quantity | plug-in `p=c/16` | Jeffreys `p=(c+0.5)/17` |")
    L.append("| --- | --- | --- |")
    a, b = block["plugin_mle"], block["jeffreys"]
    rows = [
        ("mean p_i step 100", "mean_p_i_step100", 4),
        ("mean p_i step 400", "mean_p_i_step400", 4),
        ("mean p_i (400 - 100)", "mean_p_i_step400_minus_step100", 4),
        ("Pearson r(p100, p400)", "pearson_r_p100_p400", 4),
        ("mean |p400 - p100|", "mean_abs_p400_minus_p100", 4),
        ("**E[disc] fraction**", "expected_discordance_fraction", 4),
        ("E[disc] count", "expected_discordance_count", 2),
        ("observed - expected", "observed_minus_expected_fraction", 4),
        ("observed - expected (count)", "observed_minus_expected_count", 2),
    ]
    for label, key, dp in rows:
        L.append(f"| {label} | {a[key]:.{dp}f} | {b[key]:.{dp}f} |")
    L.append(
        f"| E[disc] bootstrap 95% CI | {ci(a['expected_discordance_bootstrap_ci95'])} | "
        f"{ci(b['expected_discordance_bootstrap_ci95'])} |"
    )
    L.append(
        f"| observed bootstrap 95% CI | {ci(a['observed_bootstrap_ci95'])} | "
        f"{ci(b['observed_bootstrap_ci95'])} |"
    )
    L.append(
        f"| (obs - exp) bootstrap 95% CI | {ci(a['observed_minus_expected_bootstrap_ci95'])} | "
        f"{ci(b['observed_minus_expected_bootstrap_ci95'])} |"
    )
    L.append(
        f"| bootstrap one-sided p (obs > exp) | "
        f"{a['bootstrap_one_sided_p_observed_gt_expected']:.4f} | "
        f"{b['bootstrap_one_sided_p_observed_gt_expected']:.4f} |"
    )
    for key, tag in (
        ("mc_null_plugin", "MC null (plug-in p_i)"),
        ("mc_null_posterior_propagated", "MC null (Jeffreys-posterior p_i)"),
    ):
        L.append(
            f"| {tag}: null count mean +- sd | "
            f"{a[key]['null_mean_count']:.2f} +- {a[key]['null_sd_count']:.2f} | "
            f"{b[key]['null_mean_count']:.2f} +- {b[key]['null_sd_count']:.2f} |"
        )
        L.append(
            f"| {tag}: 95% range | {ci(a[key]['null_ci95_count'], 1)} | "
            f"{ci(b[key]['null_ci95_count'], 1)} |"
        )
        L.append(
            f"| {tag}: one-sided p(null >= obs) | "
            f"{a[key]['p_one_sided_observed_ge_null']:.4f} | "
            f"{b[key]['p_one_sided_observed_ge_null']:.4f} |"
        )
    L.append("")
    L.append("Per-item rate extremes (plug-in):")
    L.append("")
    L.append(
        f"- step 100: {a['n_items_p100_eq_0']} items at p=0, {a['n_items_p100_eq_1']} at p=1"
    )
    L.append(
        f"- step 400: {a['n_items_p400_eq_0']} items at p=0, {a['n_items_p400_eq_1']} at p=1"
    )
    L.append("")
    ref = block["single_endpoint_reference_variants"]
    L.append("Single-endpoint reference variants (both-ends-same-p_i, for contrast only):")
    L.append("")
    L.append(f"- p_i(100) at both ends: {f(ref['p100_at_both_ends_fraction'])}")
    L.append(f"- p_i(400) at both ends: {f(ref['p400_at_both_ends_fraction'])}")
    L.append("")
    tag, detail = verdict(block)
    dr = block["direction_of_result"]
    L.append(f"**Direction: {tag}.** {detail}.")
    L.append("")
    L.append(f"- Licensed by this measurement: {dr['licensed_statement']}")
    L.append(f"- NOT licensed by this measurement: {dr['not_licensed']}")
    L.append("")
    return L


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, default=SRC)
    ap.add_argument("--dst", type=Path, default=DST)
    args = ap.parse_args()
    src, dst = args.src, args.dst
    d = json.loads(src.read_text(encoding="utf-8"))
    r = d["results"]
    L: list[str] = []
    L.append("# M5C Task B — expected-discordance null from sampled per-item rates at BOTH endpoints")
    L.append("")
    L.append(f"- schema: `{d['schema_version']}`")
    L.append(f"- generated: {d['generated_utc']}")
    L.append(f"- git: `{d['git_hash']}`")
    L.append(f"- source JSON: `reports/{src.name}`")
    L.append("")
    L.append("## 0. What this closes and what it does not")
    L.append("")
    L.append(d["question"])
    L.append("")
    L.append(f"Null: `{d['null_definition']}`")
    L.append("")
    L.append(
        "The prior figure recorded in `reports/m5c_turnover_v1.json` "
        "(`noise_reference_not_a_test`) estimated p_i from 16-sample temperature decoding at "
        "step 100 ONLY and then assumed the same per-item rates at step 400. That assumption "
        "is the thing under question, so p_i is estimated separately at each endpoint here."
    )
    L.append("")
    pr = d["prior_reference_figure_reproduced"]
    L.append(
        f"Prior reference figure reproduced exactly before replacing it: recorded "
        f"{pr['value_in_m5c_turnover_v1']}, recomputed "
        f"{pr['recomputed_here_from_step100_p_i_at_both_ends']}."
    )
    L.append("")
    L.append("## 1. Sampled protocol, verbatim")
    L.append("")
    for tag, key in (("step 100", "sampled_protocol_step100_verbatim"),
                     ("step 400", "sampled_protocol_step400_verbatim")):
        b = d[key]
        L.append(f"### {tag} — `{b['run_id']}`")
        L.append("")
        L.append("```json")
        L.append(json.dumps(b["decoding"], indent=2, sort_keys=True))
        L.append("```")
        L.append("")
        L.append(f"- `sample_count` = {b['sample_count']}")
        L.append(f"- `sample_temperature` = {b['sample_temperature']}")
        L.append(f"- `seed` = {b['seed']}")
        L.append(f"- `max_tokens` = {b['max_tokens']}")
        L.append(f"- `group_size` = {b['group_size']}, `format_weight` = {b['format_weight']}")
        L.append(f"- `model_revision` = `{b['model_revision']}`")
        L.append(f"- `prompt_contract_sha256` = `{b['prompt_contract_sha256']}`")
        L.append(f"- `source_manifest_sha256` = `{b['source_manifest_sha256']}`")
        L.append(f"- `parser_version` = `{b['parser_version']}`, "
                 f"`scoring_mode` = `{b['scoring_mode']}`")
        L.append(f"- `per_item.jsonl` sha256 = `{b['per_item_sha256']}`")
        if b.get("deviations"):
            L.append("- deviations:")
            for dev in b["deviations"]:
                L.append(f"  - {dev}")
        L.append("")
        L.append("Command:")
        L.append("")
        L.append("```")
        L.append(b["command"])
        L.append("```")
        L.append("")
    L.append("Greedy labels: " + d["greedy_source"]["greedy_decoding"] + ", from "
             f"`{d['greedy_source']['substrate']}` "
             f"(sha256 `{d['greedy_source']['substrate_sha256']}`).")
    L.append("")
    L.append("## 2. Results")
    L.append("")
    L.extend(metric_section("2.1 Lenient", r["acc_final_lenient"]))
    L.extend(metric_section("2.2 Strict contract", r["acc_strict_contract"]))
    gx = d.get("greedy_replicate_floor_cross_reference") or {}
    if gx.get("source") and gx.get("present") is not False:
        L.append("### 2.3 Relation to the greedy replicate floor (Task A)")
        L.append("")
        L.append(f"- source: `{gx['source']}` (sha256 `{gx['source_sha256']}`)")
        L.append(f"- `measured_floor_is_zero` = {gx['measured_floor_is_zero']}")
        L.append(
            f"- max replicate discordance across cells = "
            f"{gx['max_replicate_discordance_count_across_cells']}"
        )
        L.append(
            f"- greedy responses byte-identical across all replicate pairs = "
            f"{gx['response_text_byte_identical_across_all_pairs']}"
        )
        L.append("")
        L.append(gx["relation_to_this_null"])
        L.append("")
    L.append("## 3. Checks")
    L.append("")
    L.append("| check | value |")
    L.append("| --- | --- |")
    for k, v in d["checks"].items():
        L.append(f"| `{k}` | {v} |")
    L.append("")
    rb = d["step100_reproduction_cell"]
    L.append("### 3.1 Step-100 reproduction cell")
    L.append("")
    if rb.get("present") and rb.get("run_id"):
        L.append(f"- run: `{rb['run_id']}` (status `{rb['status']}`, exit {rb['exit_code']})")
        L.append(
            f"- items whose full 16-sample success vector is identical to the registered "
            f"step-100 run: {rb['items_with_identical_sample_correct_vector_vs_registered_step100']}"
            f"/{rb['items_total']}"
        )
        L.append(
            f"- items with byte-identical greedy response: "
            f"{rb['items_with_byte_identical_greedy_response']}/{rb['items_total']}"
        )
        L.append(
            f"- items with all 16 sampled responses byte-identical: "
            f"{rb['items_with_byte_identical_all_16_sampled_responses']}/{rb['items_total']}"
        )
        L.append(f"- sum |success-count difference| across items: {rb['sum_abs_count_difference']}")
        L.append(
            f"- mean p_i: repro {rb['mean_p_i_repro']:.6f} vs registered "
            f"{rb['mean_p_i_registered']:.6f}"
        )
        L.append(
            f"- greedy label agreement with substrate `acc_final_step100`: "
            f"{rb['greedy_matches_substrate_acc_final']}/{rb['items_total']}"
        )
        L.append(
            f"- E[disc] recomputed with the repro p_i(100) against p_i(400): "
            f"{rb['expected_discordance_using_repro_p100_and_step400']:.6f}"
        )
    else:
        L.append(f"- not available: {rb.get('reason')}")
    L.append("")
    L.append("## 4. Caveats")
    L.append("")
    for c in d["caveats"]:
        L.append(f"- {c}")
    L.append("")
    dst.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("wrote", dst)


if __name__ == "__main__":
    main()
