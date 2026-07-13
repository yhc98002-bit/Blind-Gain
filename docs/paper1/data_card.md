# Data Card

## FlipTrack R19

Frozen 1,200-pair instrument with document, geometry, and cued chart
point-value reading templates. Provenance, masks, answer keys, attacker results,
and human-audit evidence are referenced from immutable manifests. Release
manifest: `data/fliptrack_v02r19_artifact_expanded/manifest.jsonl`, SHA256
`62553d701eb3e949910110057b65ab4e1146c602d21936268818fd1725b1b427`.

R19 geometry is the primary FlipTrack endpoint. Overall R19 is key secondary
and is always shown with all template results. The chart template is a cued
point-value-reading construct, not a legend-to-series localization test.

## FlipTrack R20

One-shot generator confirmation on fresh seeds. R19 and R20 are never pooled.
Release manifest: `data/fliptrack_r20/manifest.jsonl`, SHA256
`be033f67bd78d6207fb6dd1a3156810f3515416203b48fc65ae59334308255b4`.
Template failures are preserved and downgrade certification to R19-selected;
no R21 is minted in this protocol.

## Chart V08 Development

Chart v08 is a separate development family with legend-target and point-value
flips, no answer-pointing cue, dual color/linestyle/marker coding, and explicit
no-star/randomized-star necessity interventions. It is not an edit to R19.
Calibration and one-shot confirmatory artifacts remain `{result-pending}`.

## Training Corpora

Geometry3K pilot IDs: `data/geo3k_pilot_filtered_ids.json`, SHA256
`8631d015ee8593669b46cc707b9fe1fb3690391520bccf416b64bbb2306ff7d1`.
The ViRL39K training subset and decontamination manifest remain
`{result-pending}` until M7 data preparation freezes them.

## Intended Use and Limitations

FlipTrack measures dependence on paired visual changes within its renderable
families; it does not establish general natural-scene perception. Human audits
sample semantic validity and legibility but do not exhaustively certify every
possible viewing condition. Caption gates measure caption-mediated
accessibility under fixed captioners, not an ordering of image and text
information. Dataset access, training/evaluation permissions, and
redistribution constraints are tracked in `reports/license_log.csv`.
