import json

mine = json.load(open("reports/c6_mechanism_at_scale_v1_independent_replicate.json"))
th = json.load(open("reports/c6_mechanism_at_scale_v1.json"))
ROLES = [
    "coordinate_register_twenty_point_x_v02",
    "header_cued_table_code_v02",
    "starred_series_value_nine_v07",
]
SHORT = {
    "coordinate_register_twenty_point_x_v02": "ANCHOR(600)",
    "header_cued_table_code_v02": "CANARY(300)",
    "starred_series_value_nine_v07": "READOUT(300)",
}
FIELDS = ["base_pair_accuracy", "arm_pair_accuracy", "arm_minus_base", "ci95_low", "ci95_high", "decision"]
ncmp = 0
ndiff = 0
hdr = "%-30s %-12s %-8s %8s %8s %9s %22s  %-22s %s" % (
    "contrast", "role", "contract", "base", "arm", "delta", "ci95", "decision", "agree")
print(hdr)
for ck in [
    "c6_1_a1real_minus_base_r19",
    "c6_2_a2gray_minus_base_r19",
    "c6_3_a1real_minus_base_r20",
    "c6_4_a2gray_minus_base_r20",
]:
    m = mine["contrasts"][ck]["roles"]
    t = th["registered_contrasts"][ck]["per_task_role"]
    for role in ROLES:
        for cn_m, cn_t in (("lenient", "lenient"), ("strict", "contract_strict")):
            a = m[role][cn_m]
            b = t[role][cn_t]
            agree = all(
                (a[f] == b[f]) if f == "decision" else abs(a[f] - b[f]) < 1e-12 for f in FIELDS
            )
            ncmp += 1
            ndiff += 0 if agree else 1
            ci = "[%+.4f,%+.4f]" % (a["ci95_low"], a["ci95_high"])
            print("%-30s %-12s %-8s %8.4f %8.4f %+9.4f %22s  %-22s %s" % (
                ck, SHORT[role], cn_m, a["base_pair_accuracy"], a["arm_pair_accuracy"],
                a["arm_minus_base"], ci, a["decision"], "OK" if agree else "DIFF"))
print()
print("cells compared=%d  disagreements=%d" % (ncmp, ndiff))
print()
print("BRANCH READING (mine):")
for ck in mine["contrasts"]:
    r = mine["contrasts"][ck]["pre_committed_reading"]
    print("  %-30s lenient=(%s) strict=(%s)  canary_damage L/S = %s/%s" % (
        ck, r["lenient"]["branch"], r["strict"]["branch"],
        r["lenient"]["canary_damage"], r["strict"]["canary_damage"]))
print()
print("REPLICATION ACROSS TWIN (mine):")
for arm, pc in mine["replication_across_the_twin"].items():
    for contract in ("lenient", "strict"):
        row = pc[contract]
        print("  %-8s %-8s R19=(%s) R20=(%s) replicates=%s" % (
            arm, contract, row["r19_branch"], row["r20_branch"], row["replicates"]))
