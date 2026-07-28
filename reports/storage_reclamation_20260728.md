# Storage reclamation — 2026-07-28

PI authorization: full access to the quota root; AudioDiffusion is shelved
with unsatisfactory results, its runtime environments may be deleted, and
large files may go provided some experimental results are retained.

Quota 1500 GiB. Used at start: 1133 GiB 
(free: 366 GiB).

| target | why | freed (GiB) |
|---|---|---|
| `blindgain_archive` | raw optimizer-state checkpoints for mech_a1_real_seed2 and mech_a3_caption_seed2; both arms complete with sealed readouts, and their merged step-100 checkpoints were verified present in the project tree before deletion | 136 |
| `HaocunYe/Research/AudioDiffusion_envs` | AudioDiffusion runtime environments, model caches and pip temp trees; project shelved, environments rebuildable | 44 |
| `.uv_cache` | uv package cache; regenerates on next install | 35 |

Used at end: 915 GiB (free: 584 GiB).

**Total reclaimed this pass: 217 GiB**

Not touched in this pass: the AudioDiffusion *research* trees. Those are
pruned by file in pass 2 — large binaries removed, results (JSON, CSV,
markdown, logs, configs) retained per the PI's instruction.
| `HaocunYe/Research/benchmark_v2_runtime` | downloaded stable-audio-open-1.0 weights (plus a .partial duplicate) and two Python environments; all re-downloadable, project shelved | 126 |

## Pass 2

Reclaimed a further 126 GiB. Free after both passes:
**711 GiB** of 1500 GiB.

### Deliberately retained

The AudioDiffusion research trees were pruned of nothing. Their large
files are rater bundles and listening-review packets
(`t2_aprime_core.zip`, `t6_calibration.zip`,
`pi_listening_review_packet_20260529.zip`, and similar) — human-annotation
artifacts that cannot be regenerated. At ~12.5 GiB they are not what
constrains the quota, and they are the experimental results most worth
keeping if the project is ever revived.
