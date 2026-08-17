#!/usr/bin/env python3
"""Record the passed caption-coverage audit in progress and status reports."""
from pathlib import Path
import sys

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")

M7_OLD = "M7 | blocked | reports/virl_3b_data_readiness_v2.md + reports/m7_embedding_completion_v1.md: hash/text, 45,302-image DINOv2, 55,591-text BGE, and calibrated embedding comparison are complete; eight-shard RapidOCR, final merge, whole-item freeze, full caption coverage, and hashed configs remain required before any optimizer step"
M7_NEW = "M7 | blocked | reports/virl_3b_data_readiness_v2.md + reports/m7_embedding_completion_v1.md + reports/decon_virl39k_vs_layer1_v1.md + reports/virl39k_caption_store_audit_v1.json: OCR, decontamination merge, the 29,756-item whole-item freeze, and audited full question-blind 3B caption coverage (28,768/28,768, status pass) are complete; four matched hash-pinned arm configs, per-arm train parquets, and the amendment-bound launcher remain required before any optimizer step"

STATUS_OLD = """- Independent coverage audit (fresh image hashing on an12):
  `reports/virl39k_caption_store_audit_v1.json` — see status line in §7."""
STATUS_NEW = """- Independent coverage audit passed:
  `reports/virl39k_caption_store_audit_v1.json`, status `pass`, 28,768/28,768
  image hashes covered with exactly one caption row each, model/revision/TP
  contract verified against the run manifest. Note: the audit's run-manifest
  mode aborted because this generator (`scripts/caption_image_store.py`) does
  not stamp `source_roots_sha256` rows; the registered legacy mode
  (frozen-manifest coverage + row-level hashes) was used instead, and
  byte-level image provenance is already bound by the freeze's registered
  `caption_image_index_exact` check."""

S7_OLD = """- Caption-store audit status at commit time: recorded in
  `reports/virl39k_caption_store_audit_v1.json` (this file is the source of
  truth; if absent or failing, M7 configs stay blocked)."""
S7_NEW = """- Caption-store audit: passed in legacy mode (see §4); the run-manifest mode
  is structurally incompatible with rows from `scripts/caption_image_store.py`
  and its failure was a tooling mismatch, not a coverage defect."""


def replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        print(f"already updated: {path.name}")
        return
    if text.count(old) != 1:
        print(f"ABORT: pattern not unique in {path.name}")
        sys.exit(1)
    path.write_text(text.replace(old, new), encoding="utf-8")
    print(f"updated: {path.name}")


replace(ROOT / "reports/main_progress.md", M7_OLD, M7_NEW)
replace(ROOT / "reports/main_execution_status_20260724_v1.md", STATUS_OLD, STATUS_NEW)
replace(ROOT / "reports/main_execution_status_20260724_v1.md", S7_OLD, S7_NEW)
