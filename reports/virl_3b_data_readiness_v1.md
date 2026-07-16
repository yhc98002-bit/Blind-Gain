# ViRL39K 3B Data Readiness V1

Status:
- `blocked`. M4 authorization and the M1 heterogeneity fork ruling are both
  satisfied, but the frozen ViRL39K training subset and full 3B question-blind
  caption store do not yet exist.
- No M7 optimizer step is authorized by this report.

Evidence:
- Full pinned release: `TIGER-Lab/ViRL39K@812ec617dea4bc8a4e751663b88e4ebb7de4d00e`;
  38,870 items, 42,908 readable image references, zero missing images.
- Registered fork: `reports/virl_fork_ruling.md`; the headline analysis must be
  source/category stratified and a pooled-only readout is prohibited.
- Seven-suite Layer-1 record path: commit `04b17865e973d2bf4824026ccdc6f46599dfb9bb`.
  It includes MMStar, MathVista, BLINK, MMVP, HallusionBench, MathVerse, and
  MMMU; multi-image MMMU items expand to one linked record per image.
- Fail-closed whole-item freezer: commit
  `23844402b54576d79461f45215c64608f4612152`. If any image record is an
  automatic-remove conservative contamination candidate, the entire ViRL item
  is removed; inspect-only candidates remain.
- Active CPU hash/text pass:
  `experiments/runs/decon_virl39k_layer1_hash_text_login_20260716T193506Z`.
  The immutable manifest pins git `e7aa7415737e1adbbb3a88300ed9a4a6d09e12d2`,
  config hash `a349ade4dcec533cb3433f149b83e4bc4f73137cbaf9cecf6d7c88cab6d15245`,
  and data hash `5303f5a032bee71f55b8106217d35b48da4027368561908255309024e71dfde0`.
- The storage guard passed with 644,411,318,272 bytes of measured shared
  headroom before the 536,870,912-byte reservation.
- Focused verification: 22 freezer/filter/decontamination tests and 21
  launcher/decontamination tests passed. Fixtures reject image-free ViRL rows,
  unknown filter IDs, incomplete filters, dropped MMMU images, and missing run
  placement fields.
- A first detached-launch attempt is preserved as `fail` at
  `experiments/runs/decon_virl39k_layer1_hash_text_login_20260716T193315Z`.
  It produced no artifacts; the replacement launcher uses a named `tmux`
  session and has a regression fixture.

Problems:
- The active hash/text pass is not the complete decontamination decision.
  DINOv2, BGE, and RapidOCR coverage plus the final calibrated merge remain
  pending.
- The final filter manifest, frozen item-ID list, and immutable EasyR1 training
  JSONL remain pending until every decontamination layer is complete.
- The existing 3B caption store covers only the frozen 4,096-item audit sample.
  It cannot be substituted for the future training-subset store.
- M7 arm configs, two exact seeds, step/token budget, and checkpoint cadence
  remain unregistered computed fields.

Decision:
- Use all seven registered Layer-1 suites for the M7 decontamination pass.
- Preserve calibrated thresholds and the phrase “conservative contamination
  candidates”; do not treat inspect-band candidates as confirmed duplicates.
- Keep M7 GPU work queued behind seed 2, M5, M11, Mini-A5 smoke/main readiness,
  and seed 3 according to the PI priority ruling.

Next actions:
- Finish and audit the active CPU pass.
- Run DINOv2, BGE, and RapidOCR extraction/merge when higher-priority GPU work
  releases capacity; summarize only after `pending_layers=[]`.
- Freeze the whole-item filtered subset, generate a full-coverage 3B caption
  store, then hash matched A1/A2/A2b/A3 configs before requesting M7 launch.
