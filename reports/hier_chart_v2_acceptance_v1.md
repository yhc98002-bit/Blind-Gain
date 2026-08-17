# chart-v2 acceptance readout — FAILED, with a structural diagnosis (2026-08-17)

One-shot acceptance of `hier_chart_v2` (Amendment A4). **Verdict: FAIL** on the
artifact-attacker gate. This is the **first** of the two failures the PI's
pre-commitment requires before the coord-only ST3 split fires; no knob was
iterated and no regeneration was attempted.

## 1. Attacker gate — fail, and worse than v1 in the low-crossing cells

`reports/hier_chart_v2_attacker_gate.json`, four attackers incl. the permanent
`file_size`. Criterion: folded ≤ 0.55 point and CI-upper ≤ 0.62.

| attacker | pooled (v2) | worst cell (v2) | pooled (v1) | worst cell (v1) |
|---|---|---|---|---|
| dinov2 | 0.6758 | s5_low **0.9999** | 0.6711 | s5_low 0.9190 |
| frequency_stat | 0.7262 | s5_low **1.0000** | 0.6957 | s5_low 0.9819 |
| metadata | 0.6003 | s5_low 0.9771 | 0.5910 | s5_low 0.9315 |
| file_size (new) | 0.5603 | s5_low 0.9813 | — | — |

Point failures are **confined to the low-crossing cells**: every failure is
`pooled`, `s5_low` or `s9_low`. **`s5_high` and `s9_high` pass every attacker
per template** — the first chart cells ever to do so.

## 2. Why the transposition construction failed (measured, not surmised)

A4 reasoned that a within-column transposition leaves each column's value
multiset identical on both sides, so ink, compression and file size would be
equal by construction. The multiset claim is true and verifier-enforced; the
inference from it was wrong. **Pixels follow line paths, not column
multisets.** Measured excursion and PNG separation:

| cell | role | mean max excursion | mean PNG delta | edited larger |
|---|---|---|---|---|
| s5_low | stable / switch | 18.9 / 18.2 | **+1931 / +1882 B** | **50/50 · 50/50** |
| s9_low | stable / switch | 24.2 / 8.6 | **+2208 / +968 B** | **50/50 · 50/50** |
| s5_high | stable / switch | 10.8 / 13.9 | +27 / −8 B | 28/50 · 25/50 |
| s9_high | stable / switch | 12.6 / 9.8 | −22 / +78 B | 25/50 · 28/50 |

In a banded (low-crossing) scene every series occupies its own narrow lane
~19–24 units from its neighbours, so **any** edit that changes which series
holds which level forces two large excursions out of the lanes: two new
spikes, ~+2 KB of ink, on the edited side every single time. v1 moved one
value 5–15 units; v2 swaps two values ~19–24 units, so v2 is *worse*. In the
high-crossing cells the lines already overlap, an edit of the same magnitude
adds no distinguishable ink, and the size channel is a coin flip (25–28/50) —
the construction is genuinely clean there.

## 3. Informativeness — the cells that are clean are the cells the model cannot read

`reports/hier_chart_v2_gate_readout_v1.md` (base 3B, stable+invariance):

| cell | L1 | L2 | L3 | gates | attacker |
|---|---:|---:|---:|---|---|
| s5_low | 0.9350 | 0.9100 | 0.3450 | L2 band FAIL (too easy) | **leaky** |
| s9_low | 0.7700 | 0.7100 | 0.1050 | **all PASS** | **leaky** |
| s5_high | 0.4300 | 0.4500 | 0.1300 | monotone + L1 FAIL | clean |
| s9_high | 0.2850 | 0.2900 | 0.0650 | monotone + L1 FAIL | clean |

Blind floors are 0.0000 everywhere (all cells, all layers, gray and no_image).

**The finding:** informativeness and attacker-resistance are anti-correlated
along the crossing-density knob, and for one mechanism — visual crowding. Low
crossing means cleanly separable lines: the model can read them (informative)
but an edit stands out (leaky). High crossing means tangled lines: the edit is
camouflaged (clean) but the data is unreadable (L1 0.29–0.43, i.e. the readout
layer itself fails). The property that hides the edit from an attacker also
hides the scene from the model. **No chart cell is simultaneously informative
and attacker-clean, under either edit rule tried.**

## 4. Where the whole benchmark stands (three criteria, no cell passes all)

| cell | informative | attacker-clean | caption-resistant |
|---|---|---|---|
| coord n8 / n12 (frozen) | ✅ | ✅ | ❌ (0.265 / 0.150 vs 0.167 / 0.140) |
| chart-v2 s9_low | ✅ | ❌ | ✅ (chart 0.0413 vs 0.0000 floor) |
| chart-v2 s5_high / s9_high | ❌ (L1 fails) | ✅ | ✅ |

`chart-v2 s9_low` is one criterion short of a full pass, and the missing one is
the attacker gate.

## 5. What a v3 would have to change (PI decision — not executed)

Both v1 and v2 edited **values**, which necessarily moves ink. The only edit
channel that leaves ink invariant is one that permutes *identity* rather than
position: **swap the two series' legend/style identities** (colour, dash,
marker, label) while leaving every polyline exactly where it is. The argmax at
the anchor x then belongs to a different named series, the read-x answer
changes, and both sides contain the identical set of paths and the identical
set of colours — only the pairing differs. File size, ink budget and frequency
content are equal by construction *and* by geometry, not merely by multiset.
Residual risk: dinov2 may still separate a colour-permuted pair, which is
exactly what the gate would measure.

Recommended target if the PI authorises attempt 2: **s9_low only** (the cell
that already passes every informativeness gate and caption stress), with the
identity-permutation edit. That is the second and final attempt under the
pre-commitment; a failure there fires the registered coord-only ST3 split.
