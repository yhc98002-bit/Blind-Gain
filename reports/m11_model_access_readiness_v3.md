# M11 Model Access Readiness V3

Status:
- Both requested non-Qwen models are downloaded ModelScope-first, checksum
  manifested, and independently verified after staging to an29 `/dev/shm`.
- M11 remains `blocked`: model-specific adapters, smoke inference, and the
  registered R19/R20 and blind-solvability evaluations are not complete.

Access and download evidence:

| Model | ModelScope run | Login artifact bytes | Artifact-manifest SHA256 | Result |
| --- | --- | ---: | --- | --- |
| InternVL3-9B | `m11_modelscope_InternVL3-9B_login_20260713T031825Z` | 18,282,482,992 | `136ec9506f90dbae9d92408a00995288d2635a31c3184c2dee875099a305ebee` | complete |
| Gemma-3-12B-IT | `m11_modelscope_gemma-3-12b-it_login_20260713T031825Z` | 24,414,167,778 | `1e0cd8b91727def612f98310ba8f967593a64a4b7a6d376ce8fd59232faf4c9a` | complete |

The preserved direct-an29 attempts transferred zero bytes because an29 could not
resolve `modelscope.cn`. The fallback used direct ModelScope traffic on the login
node; no Hugging Face substitution was made.

Verified staging evidence:

| Model | Stage run | Destination | Relative-manifest SHA256 | Verified bytes | Result |
| --- | --- | --- | --- | ---: | --- |
| InternVL3-9B | `m11_stage_InternVL3-9B_an29_20260713T035801Z` | `/dev/shm/blind-gains/models/InternVL3-9B` | `8344c367d2c6cec273d212baf6cce902fac78fbc513871e67588c51511923cd8` | 18,282,475,400 | complete |
| Gemma-3-12B-IT | `m11_stage_gemma-3-12b-it_an29_20260713T040041Z` | `/dev/shm/blind-gains/models/gemma-3-12b-it` | `d608a920658a110caf1cb340cd0b3b147fb86ebdf657c8d3e38db95ea5f10eb8` | 24,414,164,102 | complete |

Staging method:
- `scripts/launch_ephemeral_model_stage.sh` refuses non-complete source runs,
  existing final/partial destinations, unsafe paths, and a transfer that would
  leave less than 40 GiB on target `/dev/shm`.
- Each transfer used resumable `rsync`, then ran `sha256sum -c` over every remote
  file before atomically renaming the partial directory.
- Both stage manifests record node, no GPU allocation, null TP width, zero
  replicas, command, git/config/data hashes, timestamps, and artifact paths.
- an29 `/dev/shm` free space after both stages: 329,536,684,032 bytes.

Decision:
- Keep the staged copies ephemeral and do not copy model weights to shared
  persistent storage.
- Do not start model serving on GPUs occupied by M2. Prepare and test the
  model-specific prompt/image adapters on CPU, then use a free single-node TP1
  slot for each smoke and registered inference run.

Next actions:
- Implement deterministic InternVL3 and Gemma-3 adapters with the fixed prompt
  contract and explicit real/no-image/question-blind-caption conditions.
- Run one-image and no-image smoke fixtures before batch evaluation.
- Execute R19+R20 and the registered blind-solvability sample; publish
  `reports/generalization_audits_v1.md` only after row/hash audits pass.
