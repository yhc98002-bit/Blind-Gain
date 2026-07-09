# Dataset And License Triage

Status:
- Triage is `partial`.
- Geometry3K is available and is being used only as an engineering GRPO fallback.
- ViRL39K was actually attempted, not left as pending, and is currently blocked by a dataset-loader failure.
- MMK12/COCO/VisMin/VQAv2 require controlled acquisition and license review before use in claims or release.

Evidence:
- Geometry3K cache: `artifacts/hf_home/datasets`
- ViRL39K attempted path: `TIGER-Lab/ViRL39K`
- ViRL39K observed snapshot: `artifacts/hf_home/hub/datasets--TIGER-Lab--ViRL39K/snapshots/812ec617dea4bc8a4e751663b88e4ebb7de4d00e`
- HF dataset search found MMK12 candidates: `FanqingM/MMK12`, `MMEureka123/MMK12-Dataset`, `MM-PRM/MM-K12`.
- HF dataset search found VisMin candidates: `mair-lab/vismin`, `mair-lab/vismin-bench`.

Problems:
- `load_dataset("TIGER-Lab/ViRL39K")` generated `38870` train rows but then failed on `images.zip` with `Parquet magic bytes not found`.
- `load_dataset("mair-lab/vismin")` triggered a 75-file bulk download; it was interrupted intentionally because this triage step should not silently start a large download job.
- Dataset licenses are still not sufficiently audited for release.

Decision:
- Continue Geometry3K for the GRPO engineering anchor.
- Do not use ViRL39K in a named reproduction until its loader path is fixed and license status is recorded.
- Do not treat MMK12/COCO/VisMin/VQAv2 as acquired.

Next actions:
- Inspect the ViRL39K repo script/data card and build a manual manifest if the HF loader expects custom image extraction.
- Select authoritative MMK12 source and license before download.
- Run COCO/VQAv2 downloads only as controlled jobs with local manifests/checksums.
