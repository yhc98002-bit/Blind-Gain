# ViRL Caption-Store Launcher Audit V1

Status:
- Engineering audit passed. This does not authorize M7 training and does not claim that the full ViRL39K training caption store exists.

Evidence:
- `scripts/launch_caption_store_shards.sh` maps shards by replica ordinal, so a TP1 allocation such as physical GPUs `4 5 6 7` produces shards `0 1 2 3` instead of incorrectly producing no workers.
- A single-node launch must cover every declared shard; partial mappings are rejected before SSH so the finalizer cannot wait forever for shards that were never assigned.
- The launcher serializes its final capacity check and refuses an occupied target GPU with exit code `75` before writing `run_manifest.json`.
- The run manifest records the active GPU IDs, TP width, replica count, model ID, model revision, input-tree hash, decoding contract, and resume provenance.
- `scripts/caption_image_store.py` stamps `caption_model_id`, `caption_model_revision`, and `tensor_parallel_width` into every newly generated row.
- Resume validation pins model revision and TP width in addition to model path, image order, and token budget.
- `PYTHONPATH=. pytest -q tests/test_caption_store_launcher.py tests/test_caption_store_resume.py tests/test_caption_launcher_contracts.py tests/test_caption_store_audit.py`: `41 passed`.
- `bash -n scripts/launch_caption_store_shards.sh` and Python bytecode compilation passed.

Problems:
- The seven-suite ViRL39K decontamination pass is still running. Therefore the final whole-item filtered manifest and retained-image index do not yet exist.
- No full-corpus 3B or 7B training caption generation has been launched. Existing 4,096-item audit caption stores are not valid substitutes.

Decision:
- Use only `data/virl39k_main_filtered_images` produced by the fail-closed whole-item freezer as the future caption input root.
- Set `BLIND_GAINS_CAPTION_MODEL_ID` and `BLIND_GAINS_CAPTION_MODEL_REVISION` to immutable identifiers at launch. Defaulting both to the local model path remains available for engineering tests only.
- Keep M7 and M8 training readiness blocked until exact manifest coverage and row-level hashes pass `scripts/audit_caption_store.py`.

Next actions:
- Complete all seven decontamination layers and freeze the retained whole-item subset.
- Generate the 3B caption store over the retained-image index on the next priority-compliant GPU window.
- Audit 100% hash coverage, model revision, TP1 placement, and question-blind prompt invariants before hashing training configs.
