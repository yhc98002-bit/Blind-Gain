# External Evaluation Harness Version

Status:
- VLMEvalKit is pinned and isolated; the Gate-2 subset is complete for Qwen2.5-VL-3B and 7B on MMStar, MathVista-testmini, BLINK, HallusionBench, and MMVP.
- Registered image-removed MMStar and MathVista-testmini cells are complete for both model sizes.
- MathVerse and MMMU are explicitly owed by prelaunch task L10 and are not represented as Gate-2 results.

Evidence:
- Repository: `https://github.com/open-compass/VLMEvalKit.git`.
- Commit: `6a02ab92471a8c544ff0769da5968a29fd75971f`.
- Checkout: `artifacts/repos/VLMEvalKit`; environment: `artifacts/envs/vlmevalkit`.
- Environment recipe: `scripts/setup_vlmevalkit_env.sh`; resolved freeze: `artifacts/envs/vlmevalkit/requirements.freeze.txt`.
- Runner: `scripts/launch_vlmevalkit_eval.sh`; output validator: `scripts/validate_vlmeval_run.py`.
- Unified scorer: `scripts/postprocess_vlmeval_predictions.py`; six focused tests pass.
- Greedy lock in every model config: temperature 0, top-p 1, top-k 1, sampling off, one output, max 256 tokens.
- Shared system contract: `Return only the final answer wrapped exactly in <answer>...</answer>.`
- Local judge model: `Qwen/Qwen2.5-7B-Instruct`, ModelScope tree SHA256 `1e8d53b21b997eb18436573d3f5cc961fbaf00cd583131f6a89a05617e24c72c`.
- Judge launcher: `scripts/launch_local_judge.sh`; served name `qwen25-7b-judge`, OpenAI-compatible port 18080. It was stopped after smoke validation to return the GPU to scientific jobs and is restartable from the launcher.

Dataset adapters:
| Dataset | Rows | Local file | SHA256 / deviation |
| --- | ---: | --- | --- |
| MMStar | 1,500 | `data/vlmevalkit/MMStar_VLMEVAL.tsv` | `07fb57d8c07051623264df625534bf00ed8f5cab747efb136658ba4f52b36768` at adapter creation; source embedded options normalized to A-D columns |
| MathVista-testmini | 999 | `data/vlmevalkit/MathVista_LOCAL.tsv` | `0ba7ec2edf5cb674fd0f7136470b716e47c29ded86fcaee72c84d91c3a0c6d9a`; item 781 dropped because C and D are both `18` and no source answer label exists |
| BLINK validation | 1,901 | `data/vlmevalkit/BLINK_LOCAL.tsv` | `489094f32a1768c93a8cef50ef4afe1fa74a7c5a74c2ea02a7684f38abde6522`; 3,664 unique ordered images |

Problems:
- VLMEvalKit's OpenCompass host was unreachable from the cluster, so authoritative ModelScope/HF parquet sources are converted locally with immutable hashes.
- The first MMStar run used the unadapted source TSV and produced a false harness score of zero; it is preserved and excluded.
- The 7B MMStar run was launched before `exact_matching` became the runner default. Its configured OpenAI judge was unavailable and VLMEvalKit explicitly fell back to exact matching with zero judge failures; this deviation is reported, not hidden.
- HallusionBench and MMVP HF snapshots stopped at unauthenticated rate-limit HTTP 429. Partial files and failed run manifests are preserved.

Decision:
- Use VLMEvalKit's benchmark metric as the benchmark-authoritative score and publish the unified parser decomposition alongside it.
- Keep every failed smoke and adapter attempt immutable.
- Use the local judge only for benchmark rows that typed or exact extraction cannot resolve.

Next actions:
- Execute the L10 MathVerse and MMMU base rows under the pinned harness with canonical-v2 validity columns.
- Preserve Gate-2 rows and publish the L10 expansion as a versioned table.
