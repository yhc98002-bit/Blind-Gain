# Dataset And License Triage V2

Status:
- Gate-critical license identification is complete for both Qwen2.5-VL sizes, Geometry3K, ViRL39K, and MMK12; no `VERIFY` placeholder remains for those artifacts.
- ViRL39K and MMK12 acquisition and loader acceptance both pass with `0.0%` missing-image rates.
- COCO, VisMin, and VQAv2 remain pending with named provenance/redistribution review tasks; they are not used by current claims.

Evidence:
- Machine-readable table: `reports/license_log_v2.csv`.
- Verbatim source terms/cards: `reports/license_terms/`.
- Retrieval date: `2026-07-10`.
- Qwen2.5-VL-3B local `LICENSE`, Sections 2(a), 3, and 4(b): research/evaluation and derivatives are noncommercial-only; redistribution has notice/attribution conditions.
- Qwen2.5-VL-7B official model-card frontmatter declares `apache-2.0`.
- Geometry3K card at revision `fd21e533e1e50d0662a2bf7b223e60511bd5f8b7` declares `mit` and identifies the InterGPS conversion source.
- ViRL39K card at revision `812ec617dea4bc8a4e751663b88e4ebb7de4d00e` declares `mit` and lists contributing datasets.
- Authoritative MM-Eureka source is `FanqingM/MMK12@372a609268ea79b5e78d90ab173e02c37b486163`; its repository `LICENSE` is Apache-2.0.
- MMK12 acquisition: `experiments/runs/hf_dataset_mmk12_20260710T003410Z/run_manifest.json`; full scan: `experiments/runs/prepare_mmk12_20260710T003926Z/run_manifest.json`.

| Artifact | Declared license | Training | Evaluation | Redistribution decision |
|---|---|---|---|---|
| Qwen2.5-VL-3B-Instruct | Qwen Research License | Noncommercial only | Noncommercial only | Conditional; include agreement, modification notices, attribution, and required Qwen wording |
| Qwen2.5-VL-7B-Instruct | Apache-2.0 | Allowed | Allowed | Allowed with Apache notice/license obligations |
| Geometry3K | MIT | Allowed by repository declaration | Allowed | Dataset derivatives allowed under MIT declaration; review InterGPS image provenance before mirroring images |
| ViRL39K | MIT | Allowed by repository declaration, but prohibited in this phase by `prompt2.md` | Allowed | Do not mirror bundled images until component-source terms are audited |
| MMK12 | Apache-2.0 | Allowed | Allowed | Allowed under Apache terms; real-world image provenance still warrants release review |

Problems:
- License labels do not automatically clear third-party image rights. ViRL39K and MMK12 aggregate or collect real-world visual material, so public redistribution has a separate provenance risk from local research use.
- ModelScope search found no authoritative MMK12 mirror. The logged Hugging Face fallback completed through proxy `7890`.
- COCO has per-image rights considerations; VisMin inherits source-image terms; VQAv2 depends on COCO images. Their final release policy is not yet resolved.

Decision:
- Permit local noncommercial research use of the five resolved artifacts under the recorded terms.
- Treat Qwen2.5-VL-3B checkpoints as noncommercial and retain the required attribution language in any checkpoint card.
- Do not redistribute ViRL39K/MMK12 image payloads in the project release until the component provenance audit is complete.

Next actions:
- Feed the completed MMK12 loader into P1.10 decontamination and later blind-solvability sampling.
- Retrieve and preserve the official COCO, VisMin, and VQAv2 terms before those assets enter an experiment.
- Add release-card attribution templates for the Qwen Research License and Apache-2.0 artifacts.
