# M11 Model Access Readiness V2

Status:
- Supersedes the routing section of
  `reports/m11_model_access_readiness.md`.
- Model access is unblocked; login-node ModelScope downloads are active.
- M11 inference remains incomplete.

Failed node-local attempts:
| Run | Bytes transferred | Root cause |
| --- | ---: | --- |
| `m11_modelscope_InternVL3-9B_an29_20260713T030638Z` | 0 | an29 DNS could not resolve modelscope.cn |
| `m11_modelscope_gemma-3-12b-it_an29_20260713T030642Z` | 0 | an29 DNS could not resolve modelscope.cn |

The failed immutable manifests are retained. Their zero-byte partial
directories are retention-expired and may be removed after this report.

Active fallback:
| Model | Active run | Download tier |
| --- | --- | --- |
| InternVL3-9B | `m11_modelscope_InternVL3-9B_login_20260713T031825Z` | login `/tmp` |
| Gemma-3-12B-IT | `m11_modelscope_gemma-3-12b-it_login_20260713T031825Z` | login `/tmp` |

Decision:
- Use direct ModelScope traffic on the login node.
- After per-file SHA256 manifests complete, stage models to
  `an29:/dev/shm/blind-gains/models/`.
- Preserve the ModelScope revision/license metadata and run the registered
  one-node minimal-TP smoke before inference.
