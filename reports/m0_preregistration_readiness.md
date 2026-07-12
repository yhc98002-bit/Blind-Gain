# M0 Preregistration Readiness

Status:
- `blocked` pending Richard's merge of the final registration path and the provenance follow-up described below.
- Candidate: `reports/preregistration_pilot_v1_DRAFT_v3_20260712.md`, SHA256 `143d2b48be52da66b0e33acf5b9fdec88fea0898af3ae05298ca4ee97900987b`.
- Candidate source commit: `2de840e748bfb9be86c7f36f1248ab074751154e`.
- `reports/preregistration_pilot_v1.md` is absent; no pilot optimizer step has run.

Applied main-phase requirements:

| M0 item | Evidence in v3 | Status |
| --- | --- | --- |
| 1. Prior observations and anchor/A1 comparison | Exact disclosure; benchmark, overall R19, and geometry deltas; 10-row comparison including resolved `freeze_vision_tower=false` | applied |
| 2. Mechanism hierarchy | Primary arm-specific `c_i>0` versus `c_i=0` hurdle; full and above-floor rank associations secondary; q_i language fixed | applied |
| 3. R20 caveat | Verbatim paragraph; explicit no-pooling rule | applied |
| 4. Provenance | Four exact launch commands, no-step statement, access disclosure, commit placeholder | blocked on merge hash |
| 5. ViRL39K fork | Five mandatory rows | applied |
| 6. Outcome tiers | RQ1/RQ2 primary, key secondary, secondary, and robustness tiers; caption final/gain separated | applied |
| 7. Chart construct | Verbatim paragraph and `cued chart point-value reading` label | applied |
| 8. Parser acceptance | 0.9156 is context; row preservation, taxonomy, blinded direction, negatives, version lock, shadow | applied |
| 9. Native weights | `reports/pilot_reward_spec_v3.md` quotes r1v lines 45/49; resolved weights are 0.5/0.5 | applied |
| 10. Human audit | `reports/fliptrack_v02r19_human_audit.md`: accepted, 60/60, all three chart notes | applied |

Commit-hash resolution:
- A commit cannot contain its own hash. Treat `registration commit hash` as the hash of the first commit that introduces `reports/preregistration_pilot_v1.md`.
- Commit 1: Richard copies the v3 candidate to the final path and merges it. Its merge is the sign-off; no signatures or sealing occur.
- Commit 2, before any training: replace `PENDING_RICHARD_MERGE` in the final file with Commit 1's full hash, add `- Registration state: merged-at-HEAD; merge is sign-off.`, and change M0 to `pass` in `reports/main_progress.md`.
- The launcher requires M0 pass, the exact merge marker, no placeholder, final config/data hashes, a tracked final path, and byte equality with `HEAD`. It exits before creating a run directory or touching GPUs if any check fails.

Verification:
- Full repository suite at source commit: `481 passed in 186.13s`.
- Live A1 authorization probe: `status=blocked`; failed checks include `M0_registration_pass` and `final_preregistration_exists`; `M2_not_predeclared=true`.
- No pilot arm checkpoint namespace exists under `checkpoints/pilot/mech_*`.

Decision:
- Do not create the final path on behalf of Richard and do not mark M0 pass.
- After the two commits above, rerun all four authorization probes before launching any arm.
