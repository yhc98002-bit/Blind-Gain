# MMK12 Loader

Status:
- Acquisition and loader acceptance are `pass` for `FanqingM/MMK12@372a609268ea79b5e78d90ab173e02c37b486163`.
- All `17,616` unique rows have readable embedded images; missing/unreadable rate is `0.0%`.
- The corpus contains `15,616` train rows and `2,000` test rows.

Evidence:
- Acquisition run: `experiments/runs/hf_dataset_mmk12_20260710T003410Z/run_manifest.json`.
- Full scan: `experiments/runs/prepare_mmk12_20260710T003926Z/run_manifest.json` (`exit_code=0`).
- Loader: `src/data/mmk12_loader.py`; regression tests: `tests/test_mmk12_loader.py`.
- Aggregate parquet manifest hash: `cac62c4e3e3e059a8d5ef7bed33d5877b7307a45836c0ada2aaa7b299092a0b9`.
- Stats: `reports/mmk12_stats.json`, SHA256 `814f325570870e59330d3e7ae585ad642097acd626223a5d0b8eb6317a270cf9`.
- Contact sheet: `reports/contact_sheets/mmk12_16.png`, SHA256 `55418acab369e6615a6c93912df5186de338c8227e17baf5ae355d6485ebb80e`.
- Local source size: `1.4G` under `data/mmk12`.

| Field | Count |
|---|---:|
| Rows / unique IDs | 17,616 / 17,616 |
| Train / test | 15,616 / 2,000 |
| Readable / missing images | 17,616 / 0 |
| Math / physics / chemistry / biology | 16,116 / 500 / 500 / 500 |
| Multiple-choice / numeric / expression answers | 2,000 / 4,552 / 11,064 |

Source file SHA256 values:
- Test: `93959742f479497bbddba2c85421e641d0c3275f87a94c0e1297b13c174a2ea8`.
- Train shard 0: `913a78a22df4532571c8955bf7fb46a397ed7854ca47f04cc60ea9b1e7dd2ed3`.
- Train shard 1: `6767548adbd337a97fdfaf932079e66d28750e9c5de1b7f0ca21f8f4cef3ecf1`.
- Train shard 2: `53980c9fffd9826b2dab26818586e53c9b2e4b35940b721adb9dbc473cbddcd8`.

Problems:
- ModelScope search did not expose an authoritative MMK12 mirror, so acquisition used the policy-approved Hugging Face fallback through proxy `7890`.
- The repository carries Apache-2.0, but its real-world image provenance is not itemized enough to justify public image mirroring without a separate review.

Decision:
- Use the streaming parquet iterator as the canonical loader. It bounds memory by batch size, checks required columns and duplicate IDs, and validates every image decode.
- Permit local training/evaluation under the recorded Apache-2.0 terms; do not redistribute the image corpus in the initial release.

Next actions:
- Feed MMK12 metadata into P1.10 decontamination.
- Add MMK12 to the blind-solvability audit only after the registered ViRL39K sample path is stable.
