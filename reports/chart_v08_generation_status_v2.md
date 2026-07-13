# Chart V08 Generation Status V2

Status:
- The declared 100-pair calibration batch remains immutable and unscored.
- CPU-side renderer construction and necessity-diagnostic plumbing pass all 12 mechanical checks.
- M12 remains `blocked`: human legibility, 3B/7B visual sensitivity, caption gates, artifact attackers, two-hop performance degradation, template freeze, and one-shot confirmation are not complete.
- V1 is retained as the original generation record; this V2 adds the post-generation mechanical audit and explicit intervention sidecar.

Evidence:
- Pair manifest: `data/fliptrack_chart_v08_calibration_v1_manifest.jsonl`, SHA256 `d90f3f13c1f3304669c8ca6c717ae58eaa7cfe4e785fab3bae8520e15065c292`.
- Mechanical audit: `reports/chart_v08_mechanical_audit_v2.md` and `.json`, machine status `pass`.
- Necessity sidecar: `data/fliptrack_chart_v08_calibration_v1_diagnostics_v2.jsonl`, 100 rows, SHA256 `18ccefd2be6efc0d10ff6c710e25e56c67fd2b65818872aa398f68941f12f800`.
- Diagnostic images: `data/fliptrack_chart_v08_calibration_v1_diagnostics_v2/`, 400 PNG files, 20 MiB.
- Successful run: `experiments/runs/chart_v08_mechanical_audit_v2_login_20260713T093740Z`; git `fb73368a46100696f8446dbb4e3ba21839457cb2`, config hash `1663f6f2dc8f324291ff607b8c2557fb9170983eeb685ac8ec8ef99ebef9fb49`.
- Focused renderer/auditor tests: 7 passed.

Mechanical results:
| Check | Result |
| --- | --- |
| 100 unique rows, 50 per subfamily | pass |
| source image hashes and metadata reconstruction | pass |
| answer keys and subfamily mechanics | pass |
| exact changed-pixel masks | pass |
| no circle/highlight/arrow answer cue | pass |
| only crossing density and value-grid granularity tune difficulty | pass |
| six distinct colors, line styles, and markers | pass |
| normal-vision minimum CIE76 >= 25 | pass, 26.4339 |
| severity-100 CVD minimum CIE76 >= 15 | pass, minimum 16.1750 |
| no-star and randomized-star image for both members | pass |
| randomized star implies an answer different from the original key | pass |
| rerun refuses to overwrite generated files | pass |

Diagnostic contract:
- Every pair has `no_star_a`, `no_star_b`, `random_star_a`, and `random_star_b` images.
- Every intervention is scored against that member's original answer.
- Randomized-star targets are selected deterministically and must imply a different answer, preventing a false no-effect case caused by equal values.
- Consumers join the sidecar to the immutable pair manifest by `pair_id`.

Run deviation:
- `experiments/runs/chart_v08_mechanical_audit_v2_login_20260713T092331Z` failed before writing an artifact because the shared guard rejected a 22,242-second-old usage snapshot.
- The failure was retained. A quota-aware refresh completed in 746.797 seconds and wrote `reports/storage_usage_snapshot_20260713T092416Z.json`, SHA256 `7508d5f14364b1f85a947a9ba3f4a09162d4902e41983562f32446f1e2d38925`.
- The refreshed snapshot measured 517,918,819,328 bytes used and 1,092,693,916,672 bytes available under the conservative 1,500-GiB guard capacity. The retry then passed the 20-GiB floor check.

Decision:
- Preserve the original calibration images and answer keys.
- Use the V2 sidecar for the registered no-star/randomized-star necessity cells.
- Do not freeze or mint a confirmatory split until the remaining calibration gates are reported.

Next actions:
- Complete the preregistered human legibility review without zoom.
- When GPUs release, score 3B/7B real and caption conditions, the strong-caption gate, attackers, and both necessity interventions.
- Freeze the renderer only after the declared calibration decision, then generate one one-shot confirmatory split with no replacement or post-score edits.
