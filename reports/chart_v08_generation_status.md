# Chart V08 Generation Status

Status:
- The first declared calibration batch is generated but not yet scored.
- M12 remains incomplete; no template is frozen and no confirmatory split has
  been minted.

Generation:
- Run: `chart_v08_calibration_generation_login_20260713T031256Z`.
- Git: `3322bf39b9ed1296c7611b44701e93ae3d259dc7`.
- Seed: 2026071208.
- Manifest:
  `data/fliptrack_chart_v08_calibration_v1_manifest.jsonl`.
- Manifest SHA256:
  `d90f3f13c1f3304669c8ca6c717ae58eaa7cfe4e785fab3bae8520e15065c292`.

Counts:
| Subfamily | Pairs |
| --- | ---: |
| legend-target flip | 50 |
| point-value flip | 50 |
| total | 100 |

Mechanical checks:
- Legend-target curves are identical across pair members; only the starred
  legend entry changes.
- Point-value target legend entry is fixed; exactly one target-series value
  changes.
- Every pair has an exact changed-pixel mask.
- Every pair has no-star and randomized-star diagnostic images.
- All 100 rows record no circle, highlight, or arrow on the queried plot point.
- Every series is dual-coded by color, linestyle, and marker.
- The six-color palette has an enforced minimum CIE76 distance above 25.
- Difficulty metadata lists only crossing density and value-grid granularity.

Next actions:
- Run human legibility sampling without zoom.
- Score 3B/7B real and caption conditions, the stronger-caption gate, artifact
  attackers, and the two-hop necessity diagnostics.
- Publish `reports/chart_v08_calibration.md` only after those cells exist.
