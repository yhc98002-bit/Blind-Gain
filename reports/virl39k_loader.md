# ViRL39K Loader

Status:
- Loader acceptance is `pass` for the pinned ViRL39K snapshot.
- `38,870` rows and `42,908` image references load from the full release with `0` missing or unreadable images (`0.0%`, below the `0.5%` limit).
- This establishes an evaluation/audit data path only. `prompt2.md` explicitly prohibits training on ViRL39K in this phase.

Evidence:
- Source: `TIGER-Lab/ViRL39K@812ec617dea4bc8a4e751663b88e4ebb7de4d00e`.
- Completed run: `experiments/runs/prepare_virl39k_20260710T001032Z/run_manifest.json` (`exit_code=0`).
- Loader: `src/data/virl39k_loader.py`; regression tests: `tests/test_virl39k_loader.py`.
- Parquet SHA256: `ea1655368fd3774d37baf54c65aef345b0766f4c80d6aeac91a311fa7e4fba92`.
- Image ZIP SHA256: `49e6485a02815430fe4a468a25c03c3514adf8c2b68135068fc36c7656d8ad27`.
- Machine statistics: `reports/virl39k_stats.json` (SHA256 `1bf85326b012d4285268cce0016c634428e07c6fe39f7288cb181ae0aa16cce5`).
- Human spot-check sheet: `reports/contact_sheets/virl39k_16.png` (SHA256 `cc80dd66311b5466bbf5c19f2da84c5f134a86f3cd405166ed2f3b946d4596e2`).
- Extracted image tree: `data/virl39k/images`; total extracted footprint: `1.8G`.

| Field | Count |
|---|---:|
| Rows | 38,870 |
| Image references | 42,908 |
| Readable image references | 42,908 |
| Missing/unreadable | 0 |
| Numeric answers | 18,800 |
| Multiple-choice answers | 12,361 |
| Text/expression answers | 7,709 |

Problems:
- The generic `load_dataset()` route misclassified `images.zip` as parquet. The supported path is direct parquet reading plus explicit ZIP extraction.
- The release combines transformed material from multiple upstream datasets. Its card declares MIT, but redistribution of bundled source images still requires source-specific review before a public data mirror is created.

Decision:
- Use `load_rows()` as the canonical ViRL39K interface. It checks required columns and duplicate QIDs and resolves every image path against the extracted root.
- Queue a stratified `4k-8k` blind-solvability sample and decontamination pass; do not launch ViRL39K training.

Next actions:
- Build the stratified sampler from category, source, answer type, and pass-rate fields.
- Run P2.2 real/gray/noise/no-image/caption inference after the caption store is available.
- Compare ViRL39K against Layer-1 benchmarks with the P1.10 decontamination harness.
