# M11 Runtime Recovery V1

Status:
- M11 remains `blocked`; four smoke cells failed and no full-matrix cell ran.
- The two root causes have tracked fixes and 32 focused tests pass.
- An isolated M11 environment must finish its machine audit before a new capacity
  queue is launched. The pilot `.venv` is unchanged.

Observed smoke failures:
| Backend | Cells attempted | Root cause | Full-cell effect |
| --- | ---: | --- | --- |
| InternVL3-9B | real, no-image, caption | nested `language_model.generation_config` was `None` after the Transformers 4.56 generation shim | full matrix stayed closed |
| Gemma-3-12B-IT | real | Transformers visual-token mask composition requires Torch >=2.6; shared environment is 2.5.1+cu121 | full matrix stayed closed |

InternVL repair:
- `ensure_internvl_generation_compatibility()` now initializes
  `GenerationConfig.from_model_config(language_model.config)` whether `generate`
  was inherited or added by the shim.
- Runtime metadata includes `generation_config_ready=true`; row, resume, and final
  matrix validators reject its absence.
- The adversarial fixture presents a callable `generate` with a null generation
  config. The previous helper returned early; the fixed helper initializes it.

Gemma runtime isolation:
- The shared `.venv` remains Torch 2.5.1+cu121 because active EasyR1 pilot arms
  depend on it.
- M11 uses `.venv-m11` with exact top-level pins: Torch 2.6.0+cu118,
  Torchvision 0.21.0+cu118, Transformers 4.56.2, Accelerate 1.14.0, and
  timm 0.9.12.
- CUDA 11.8 wheels are compatible with the installed A800 driver while avoiding a
  cluster-wide CUDA or pilot-environment mutation.
- Gemma loading now fails early with an explicit runtime error below Torch 2.6.
  Every Gemma result records `torch_version`, and final validators reject an older
  runtime.

Launch plumbing:
- Both non-Qwen launchers accept only registered project virtual-environment
  paths and stamp `runtime_python`, runtime-audit SHA256, and exact-freeze SHA256
  in each child manifest.
- `configs/eval/m11_generalization_v1.json` pins both backends to
  `.venv-m11/bin/python` and names the A2b retry as the current pilot neighbor.
- The capacity scheduler passes the runtime path explicitly to each child.
- Queue launch fails closed unless the machine audit is pass, every audit check is
  true, the freeze hash matches, and all critical queue/adapter files equal HEAD.
- Six one-pair smoke cells remain a hard barrier before 18 full cells.

Verification:
- Focused adapter, runtime, queue, blind-resume, aggregate, and final-builder suite:
  `32 passed`.
- Shell syntax and Python compilation pass.
- The setup job writes an exact `pip freeze` and a machine audit checking versions,
  CUDA runtime, Torch mask combinators, and Gemma class importability.

Decision:
- Build the isolated environment as a login-node CPU/network job through the
  explicit international proxy.
- Relaunch the M11 queue only after the runtime machine audit passes. Because all
  an29 GPUs are pilot-owned, the queue will remain capacity-waiting afterward.

Next actions:
- Commit setup inputs and start `scripts/launch_m11_runtime_setup.sh`.
- Publish a versioned queue update with the environment audit hash.
- Leave M11 queued until the blind arms release an29.
