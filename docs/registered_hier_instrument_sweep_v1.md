# Registered: HB diagnostic D1 — the hierarchy as an instrument on already-trained checkpoints (v1)

**Filed 2026-08-17, before any measurement.** Diagnostic addendum to
`registered_hier_benchmark_v1.md`; development bucket only; no confirmatory
item is touched and no training is authorized by this document.

## 1. Question

Does **any** existing RLVR recipe — real-image or blind, 3B or 7B — buy
hierarchy capability, and at which layer? Paper 1 established that blind arms
gain on benchmarks without the image; Paper 2 claims the hierarchy separates
readout from discovery. This measures both claims on one instrument.

## 2. Arms measured (all already trained; eval-only)

- **M7 ViRL 3B**, `global_step_100`, both seeds: `a1_real`, `a2_gray`,
  `a2b_noimage`, `a3_caption` (8 checkpoints).
- **C5 7B**, `global_step_100`, seed 1: `c5_a1_real`, `c5_a2_gray` (2).
- Frozen bases `Qwen2.5-VL-3B/7B-Instruct` are the reference; their numbers
  already exist (`reports/hier_r2_gate_readout_v1.*`) and are reused, not
  re-measured.

## 3. Instrument and estimands

`data/hier_v1_dev_r2` (coord r2 render, 12 manifests: n8/n12/n20 × L1/L2/L3/
probe), registered FlipTrack open-form eval, locked decoding (I7: greedy,
answer-tags contract, max_new_tokens 32), scored with **matcher v3**
(sign-aware; `MATCHER_VERSION` recorded per run). Chart-v2 cells are appended
to the same sweep once they pass acceptance.

Per arm × cell × layer: member accuracy over the stable+invariance
composition (A2), target-switch reported separately, probe accuracy reported
separately. Two-seed arms are summarised with the registered per-item seed
mean before any aggregate (`registered_m7_amendment_v1.md`:52).

## 4. Pre-registered prediction (recorded before the runs)

Blind arms (`a2_gray`, `a2b_noimage`, `a3_caption`) move **L1/L2 at most** and
leave **L3 and probe within noise of the frozen base**; the real arm may move
L1/L2 and may show a small L3 movement at 7B. The interesting outcome is any
arm moving L3/probe beyond the base — that would be the first evidence a
recipe buys discovery, and it would reframe ST3's contrast.

## 5. Branches

- **No arm moves L3/probe** → corroborates Paper 1's no-content claim on a new
  instrument and sets the baseline ST3's IGPO arm must beat.
- **The real arm alone moves L3/probe** → the dissociation reproduces on the
  hierarchy; Paper 2 gains its instrument-validity result.
- **A blind arm moves L3/probe** → the instrument is leaking; the leak is
  investigated before any ST3 readout is claimed.

Numbers only, reported per layer, never averaged across layers (I13).
