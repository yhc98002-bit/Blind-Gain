# F2d — template decomposition of the overall R19 movement

Serves PAPER1 §3 **F2**. Cached per-item predictions, no new inference. Each task
is reported in its own scientific role and **no aggregate is computed across
roles** (I13); the 'overall' column exists only because F2 quotes an overall
number, and it is reported as an accounting identity, not as a capability score.

Artifact: `reports/f2d_template_decomposition_v1.json`.

## Base rates by task

| task | role | n | pair acc | strict pair acc | member acc |
|---|---|---|---|---|---|
| coordinate survey register | primary visual anchor (search + binding + read) | 600 | 0.4717 | 0.4433 | 0.6450 |
| header-cued verification table | saturated positive control / retention canary | 300 | 0.8667 | 0.1800 | 0.9000 |
| nine-series calibration trace | oracle-localized readout control | 300 | 0.4367 | 0.4200 | 0.6617 |

## Correction to PAPER1 §5 and §3

**The header-cued verification table is not saturated.** PAPER1 §5 describes it as
"saturated at 1.000 for every model including base" and as a control that
"cannot show improvement", and §3 F2 builds the mechanism on it contributing
"nothing to any delta". Measured on R19 the base sits at **0.8667**
pair accuracy, not 1.000, and it moves in **every** arm:
A1 real +0.0189 [-0.0022, +0.0422],
A2 gray +0.0233 [+0.0022, +0.0467],
A2b no-image +0.0233 [+0.0000, +0.0489],
A3 caption +0.0211 [-0.0011, +0.0444].

A2 gray's interval excludes zero. It contributes **18.7%** of A1's overall
movement, not 0%. The retention-canary function still works — nothing here
*drops* — but the premise that it is pinned at ceiling and arithmetically inert
is false and must be corrected in both sections before the claim is written up.

Note also the lenient/strict split on this task: pair accuracy
0.8667 against strict 0.1800. The
header table is the R19 task most dependent on fallback extraction, which is
worth stating wherever it is used as a control.

## Where the movement actually lands

Mean per-item delta over three seeds, with the contribution each task makes to the
overall figure (delta x n/1200):

| arm | overall | anchor Δ (contrib) | header Δ (contrib) | nine-series Δ (contrib) |
|---|---|---|---|---|
| A1 real | +0.0253 | +0.0056 (+0.0028) | +0.0189 (+0.0047) | +0.0711 (+0.0178) |
| A2 gray | -0.0014 | -0.0422 (-0.0211) | +0.0233 (+0.0058) | +0.0556 (+0.0139) |
| A2b no-image | -0.0019 | -0.0272 (-0.0136) | +0.0233 (+0.0058) | +0.0233 (+0.0058) |
| A3 caption | +0.0092 | -0.0050 (-0.0025) | +0.0211 (+0.0053) | +0.0256 (+0.0064) |

**For A1 the F2 mechanism holds, with the header correction applied.** The
oracle-localized readout control moves +0.0711
(CI [+0.0256, +0.1167], excludes zero) and
supplies **70%** of the overall movement, while the
primary visual anchor — the only R19 task requiring search and binding — moves
+0.0056 with an interval
[-0.0183, +0.0294] that spans zero, supplying
11%. **The gain lands where localization has
already been supplied by the cue.**

## The blind arms separate the layers more sharply than A1 does

Percentage shares are omitted for A2 gray and A2b: their overall deltas are
≈0 (−0.0014 and −0.0019), so a share of that denominator is meaningless. The
per-task deltas are what carry the result, and they are opposite in sign:

| arm | primary visual anchor | oracle-localized readout control |
|---|---|---|
| A2 gray | -0.0422 [-0.0683, -0.0161] | +0.0556 [+0.0100, +0.1011] |
| A2b no-image | -0.0272 [-0.0522, -0.0017] | +0.0233 [-0.0200, +0.0678] |

Both blind-trained arms **decline on the search-and-binding anchor** with
intervals excluding zero, while **rising on the cued readout control**. Their
flat overall numbers are therefore not inertness: they are two real effects of
opposite sign cancelling inside an aggregate that should never have been read as
a single capability score.

This localizes F5. Blind-reward corrosion is not diffuse damage — it is specific
to the task that requires locating a label and binding it to a point, and it
coexists with genuine improvement on the task where the target is already marked.
A cue that supplies localization is enough to protect a blind-trained model from
its own corrosion, which is a sharper statement of the utilization thesis than
the overall numbers can express, and a concrete prediction for the cue ladder
(F4b): the damage should appear at the search rungs and vanish at the exact-cue rung.
