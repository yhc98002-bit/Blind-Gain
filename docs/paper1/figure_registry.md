# Figure Registry

| Figure | Inputs | Script | State |
| --- | --- | --- | --- |
| decomposition bars by corpus/scale | M3, M7, M9 machine outputs | `scripts/paper1/build_figures.py decomposition` | pending |
| hurdle mechanism plot | M2/M3 per-item outputs | `scripts/paper1/build_figures.py hurdle` | pending |
| benchmark versus FlipTrack dissociation | anchor, M3, M7, M9; any chart-category input additionally requires the registered R19 key-shuffle and answer-prior diagnostics | `scripts/paper1/build_figures.py dissociation` | pending; chart deltas fail closed until diagnostics land |
| audit table | hash-pinned parser, R19 human/attacker, R20, strong-caption inputs landed; M11/M12 pending | `scripts/paper1/build_figures.py audits` | pending |

Scripts fail closed when an input is absent or still contains a pending slot.
