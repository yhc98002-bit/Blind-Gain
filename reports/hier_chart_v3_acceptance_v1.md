# chart-v3 acceptance — FAILED (attempt 2 of 2); registered coord-only split fires

One-shot acceptance of `hier_chart_v3` (Amendment A6). **Verdict: FAIL** on the
artifact-attacker gate. This is the **second** failure, so the PI's
pre-committed fallback — *"coord-only split if chart-v2 fails its re-run gates
twice"* — is now in force. **No third attempt is made.** ST3-7B trains on the
coordinate family alone.

## 1. What the construction achieved

Three of the four attack channels were eliminated by construction. Pooled
folded statistics, v1 → v2 → v3:

| attacker | v1 | v2 | **v3** | v3 worst cell |
|---|---|---|---|---|
| file_size | — | 0.5603 | **0.5028** | s9_high 0.5579 |
| frequency_stat | 0.6957 | 0.7262 | **0.5258** | s9_high 0.5366 |
| metadata | 0.5910 | 0.6003 | **0.5050** | s9_high 0.5545 |
| dinov2 | 0.6711 | 0.6758 | **0.5525** | **s9_low 0.7469** (CI up 0.7897) |

file_size, frequency_stat and metadata now sit at chance pooled (0.503–0.526),
against 0.60–0.73 in v2 and worst-cell values up to 1.0000. The pixel-statistics
leak is gone: matched-magnitude excursions from a common ancestor do exactly
what A6 claimed.

Informativeness held up too (`reports/hier_chart_v3_gate_readout_v1.md`,
base 3B): **s9_low passes every gate** — L1 0.7250 / L2 0.7000 / L3 0.1200,
monotone, all bands, switch 0.2600 — and s9_high fails only its L1 band
(0.4500). Blind floors 0.0000 throughout.

## 2. Why it still failed, and why this is a real limit rather than a bug

`dinov2` separates `s9_low` at **0.7469**. The other three attackers read
pixel *statistics* — total ink, compression, byte size — and those are matched
by construction. dinov2 reads a learned *representation*, and the one thing
that cannot be matched is **where the causal edit lands**.

A causal edit must act on the target series at the anchor x — that is what
makes it causal. The compensating edit cannot land there without either
changing the answer or changing the argmax, so it lands on some other series.
The two members therefore differ systematically in the *structural position* of
their excursion — "the topmost line at the anchor dips" versus "some other line
dips" — and a learned visual representation picks that up even when ink,
magnitude, byte size and frequency content are identical.

**The general lesson, which belongs in Paper 2's methods:** for counterfactual
pair benchmarks, matching pixel statistics is achievable and matching
*structural position* is not, because position-of-intervention is intrinsic to
causality. Artifact gates built on learned features are therefore strictly
harder to satisfy than gates built on pixel statistics, and a family can look
clean under three statistical attackers while remaining separable under the
fourth.

## 3. Consequence, executed

Per the pre-commitment, the **coord-only ST3 split** is now the registered
training configuration. `hier_chart_v3` is retained as a development-tier
instrument (its s9_low cell passes every informativeness gate and every
non-learned attacker) and may be reported as a secondary readout, but it is
**not** confirmatory and is **not** trained on.

The frozen coordinate family (`data/hier_v1_dev_r2`, cells n8/n12) carries the
ST3 training split; the coordinate confirmatory bucket becomes the held-out
endpoint. Paper 2's confirmatory instrument question is now an open item for
the PI, with three measured options recorded: accept coord n12 with its
caption caveat, accept chart-v3 s9_low with its dinov2 caveat, or commission a
renderer-level change (the density knob is exhausted — see
`hier_chart_v2_acceptance_v1.md` §3).
