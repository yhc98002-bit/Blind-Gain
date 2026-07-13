# Figure Registry

| Figure | Inputs | Script | State |
| --- | --- | --- | --- |
| decomposition bars by corpus/scale | M3, M7, M9 machine outputs | `scripts/paper1/build_figures.py decomposition` | pending |
| hurdle mechanism plot | M2/M3 per-item outputs | `scripts/paper1/build_figures.py hurdle` | pending |
| benchmark versus FlipTrack dissociation | anchor, M3, M7, M9 | `scripts/paper1/build_figures.py dissociation` | pending |
| audit table | hash-pinned parser, R19 human/attacker, R20, strong-caption inputs landed; M11/M12 pending | `scripts/paper1/build_figures.py audits` | pending |

Scripts fail closed when an input is absent or still contains a pending slot.
