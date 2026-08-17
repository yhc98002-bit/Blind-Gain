#!/usr/bin/env python3
"""Fold the independent-verification results into reports/m5c_turnover_v1.json."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys

ROOT = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
os.chdir(ROOT)

verify = json.loads(subprocess.run(
    [os.path.join(ROOT, ".venv/bin/python"), "tmp/m5c_verify.py"],
    capture_output=True, text=True, cwd=ROOT, check=True).stdout)

path = "reports/m5c_turnover_v1.json"
art = json.load(open(path, encoding="utf-8"))

art["verification"] = {
    "substrate_reread_rows": verify["substrate_rows"],
    "substrate_unique_item_keys": verify["substrate_unique_keys"],
    "substrate_vs_source_value_mismatches": verify["substrate_vs_source_mismatches"],
    "source_keys_absent_from_substrate": verify["source_keys_absent_from_substrate"],
    "transition_counts_rederived_from_written_file_match": verify["matches_turnover_json"],
    "transition_labels_in_file_match_rederived": all(
        "LABEL_MISMATCH" not in v for v in verify["rederived"].values()
    ),
    "acc_final_equals_acc_strict_per_item_all_steps": verify["lenient_equals_strict_per_item_all_steps"],
    "note": "acc_final and acc_strict are identical on every item at every trained step "
            "(100-400), so the lenient and contract-strict transition tables coincide "
            "exactly. Both are reported per I7; they are not collapsed.",
}
art["gained_share_of_discordant"] = verify["gained_share_of_discordant"]
art["mcnemar_scope_note"] = (
    "McNemar's exact test asks only whether the discordant pairs split away from 50/50 "
    "(i.e. whether the NET delta is larger than the observed turnover would produce by "
    "chance). It does NOT test whether the TOTAL turnover (b01+b10) exceeds per-item "
    "noise. Testing that would require replicate evaluations of the SAME checkpoint, "
    "which do not exist: every geo3k eval here is single-pass greedy decoding "
    "(temperature 0.0, seed 20260710), deterministic by construction. No such "
    "replicate-noise test is computed."
)
art["noise_reference_not_a_test"] = verify["sampling_dispersion_reference"]

json.dump(art, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
open(path, "a", encoding="utf-8").write("\n")

h = hashlib.sha256(open(path, "rb").read()).hexdigest()
print(json.dumps({"patched": path, "sha256": h,
                  "substrate_sha256": art["substrate_sha256"],
                  "verification": art["verification"]}, indent=2))
