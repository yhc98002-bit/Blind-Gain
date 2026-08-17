#!/usr/bin/env python3
"""Corrections to reports/RESULTS.md found by the adversarial verification sweep.

336 numbers were checked; 1 fatal, 13 material, 12 cosmetic findings. Every fix
below moves the file toward the artifact, and several restore qualifiers that the
consolidation dropped.
"""
from pathlib import Path

p = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/reports/RESULTS.md")
t = p.read_text()
n = 0


def sub(old, new, label):
    global t, n
    if old not in t:
        raise SystemExit(f"ANCHOR MISSING: {label}\n  {old[:120]}")
    t = t.replace(old, new, 1)
    n += 1
    print(f"  fixed: {label}")


# ---- FATAL: the strict control FAILED and the file dropped the disclosure ----
sub(
"""Registered branch (a) obtains: ratio > 2 for both blind arms in all three seeds.
Strict-scoring control reproduces direction and rough magnitude (ratios
1.95–2.69), qualifying rather than overturning the claim.""",
"""**Registered branch (a): partially verified, and the format control did NOT
confirm.** Two things must be said plainly here.

*The strict control failed its own bar.* `d3_condition_matrix_v1.json` records
`"strict_control_confirms": false`. Recomputed on Acc_strict the ratios are
1.95–2.69, and **two of six seed-arm cells fall below the registered 2× bar**
(A2b seed 2 = 1.945, seed 3 = 1.958). The D3 registration pre-commits that "if
the Acc_strict recomputation does not reproduce the Acc_final pattern, the
finding is reported as format/emission and the canonical claim is not rescoped."
On a strict reading of that clause the protocol-effect framing below is **not**
licensed to rescope the canonical claim, and the crossed/matched gap should carry
a format/emission caveat. This disclosure was present in the predecessor results
file and was lost in consolidation; it is restored here.

*Only half of branch (a) is verifiable.* The branch requires ratio > 2 **and**
non-overlapping crossed-vs-matched recovery CIs. The ratio half holds in all
three seeds for both blind arms. The CI half cannot be checked: the artifact
contains point values only, and the registered audit artifact carrying the
per-cell bootstrap CIs does not exist in `reports/`.""",
"FATAL strict control disclosure")

sub(
"""**The protocol effect.** The same gray checkpoint reports **6.6% recovery under
matched evaluation and 48.7% under crossed evaluation** — a seven-fold difference
in the scientific conclusion, produced by the evaluation protocol alone.""",
"""**The protocol effect.** The same gray checkpoint reports **6.6% recovery under
matched evaluation and ~48.6% under crossed evaluation** — a seven-fold
difference produced by the evaluation protocol. (6.6% and 48.6% are both
mean-of-ratios across seeds; the ratio-of-pooled-means is 48.7%. The two
estimators are mixed in some earlier text.) **Read this together with the failed
strict control above**: the magnitude of the gap is not in question, but the
registration's format/emission clause means it does not by itself license
rescoping the canonical claim.""",
"protocol effect estimator + strict caveat")

sub(
"""Branch: **headline at full strength** — every interval lies entirely above the
0.35 threshold, nearest lower bound 0.383, and all nine seed-arm values fall in
the same branch.""",
"""Branch: **headline at full strength on the pooled statistic** — every *pooled*
interval lies entirely above the 0.35 threshold, nearest lower bound 0.383, and
all nine seed-arm point values fall in the same branch. Per-seed intervals are
much wider and do **not** all clear it: A2 gray seed 3 is [0.272, 0.575].""",
"TrainShare pooled qualifier")

sub(
"""**Matched-condition gains, for contrast:** A1 +0.2435, A3 +0.1048, A2b +0.0460,
A2 gray +0.0161.""",
"""**Matched-condition gains, for contrast:** A1 +0.2435, A3 +0.1048, A2b +0.0460,
A2 gray +0.0161. *Convention warning:* these difference each arm against the base
**in its own condition**. §10 uses the other convention — everything against base
*real* — under which the same A2b figure is −0.0605. Both are correct; they
answer different questions and must never be mixed in one table.""",
"matched-condition convention collision")

# ---- F2: the 84/42 gradient belongs to A2b, not to the 49% gray rung ---------
sub(
"""**The 49% is an average over a gradient, not a constant.** G0.2 (§10) finds A2b's
image-present gain concentrates on blind-*answerable* items: 84% of A1's gain
where blind reward opportunity exists, 42% where none was observed. The
image-free share falls as an item's dependence on the image rises.""",
"""**Each rung is an average over a gradient, not a constant.** G0.2 (§10) finds the
blind arms' image-present gain concentrates on blind-*answerable* items. For
**A2b** (the 53% rung): 84% of A1's gain where blind reward opportunity exists,
42% where none was observed — item-weighted average 52.9%, which is that rung.
For **A2 gray** (the 49% rung) the corresponding split is 83% and 36%, averaging
48.8%. The image-free share falls as an item's dependence on the image rises, in
both arms.""",
"F2 gradient attribution")

sub("gray **+0.119 (49%)** → no-image\n**+0.129 (53%)** → caption **+0.175 (72%)** → real **+0.244 (100%)**.",
    "gray **+0.119 (49%)** → no-image\n**+0.129 (53%)** → caption **+0.175 (72%)** → real **+0.2435 (100%)**.",
    "ladder real value rounding")

sub("""So 49% of the gain requires no visual information during training at all; a
further 23% is transmissible through frozen textual descriptions; 28% requires
actual pixels during optimisation.""",
"""So 49% of the gain requires no visual information during training at all; 28%
requires actual pixels during optimisation. The middle band is 23% measured from
the gray rung, or 19 points measured from the adjacent no-image rung (71.8 −
52.9) — the latter is the like-for-like comparison against the nearest image-free
condition.""",
"ladder middle band")

# ---- F4 ----------------------------------------------------------------------
sub("""Margin inflation vs base under the **correct** image: A1 +0.150, caption +0.090,
no-image +0.035, gray +0.036 — the same information ordering as F2.""",
"""Margin inflation vs base under the **correct** image (seed 1, primary template):
A1 +0.150, caption +0.090, gray +0.036, no-image +0.035. The two blind arms are a
**tie, not an ordering** — their CIs overlap ([+0.0337, +0.0375] vs [+0.0327,
+0.0369]) and gray is nominally above no-image, the reverse of F2. The honest
statement is `gray ≈ no-image < caption < real`, which is F2's ordering only at
the coarse level. Seed 2 differs materially (A1 +0.129, caption +0.076, no-image
+0.058, gray +0.037), so these values are seed- and template-specific.""",
"F4 ordering is a tie + seed qualifier")

sub("""Under the **twin's** image every model including the frozen base prefers the
twin's gold (0.948–0.955). Blind-condition entropy stays at 0.998, so this is not
a global temperature change.""",
"""Under the **twin's** image every model including the frozen base prefers the
twin's gold — 0.948–0.955 on the primary template (0.920–0.938 on the nine-series
template, 1.000 on the header template; the direction holds in all 30 cells).
Blind-condition normalized entropy stays at 0.998
(`reports/blindarm_margin_calibration_results_v1.json`, not the X1/X5
artifacts), so this is not a global temperature change.""",
"F4 twin range + entropy artifact")

# ---- F5 ----------------------------------------------------------------------
sub("""Structured hard-negative discrimination: base 0.517, A1 0.513–0.527. Chained
premise-to-reasoning at floor for every model (0.000 pair). Binding swap flat.
Fact-read unimproved. The 28% that requires training-time pixels is more readout
policy tuned against real evidence — not new visual distinctions.""",
"""Structured hard-negative discrimination: base 0.517, A1 0.513–0.527. Binding
swap flat. Fact-read unimproved. Chained premise-to-reasoning sits at 0.000 pair
for every model — but per P0.1's registered branch (b) that floor is
**uninformative about chaining** rather than evidence against it (§11), so it
cannot be counted as a competence layer that failed to move.

**One intervention type does move, and it is reported here rather than omitted.**
`prior_conflict` rises in every trained cell: +0.214 and +0.143 (A1 seeds 1–2),
+0.286 (A2b), +0.286 (A3) on pair accuracy, with member-level gains of +0.107 to
+0.143. It is the only one of B1's six types to move in all cells, and it moves
*most* in the blind arms. n=14 pairs, so it is a small cell and no claim rests on
it — but a section arguing that competence layers stay flat must disclose the one
that did not.

With that qualification, the 28% requiring training-time pixels still looks like
readout policy tuned against real evidence rather than new visual distinctions.""",
"F5 chained caveat + prior_conflict disclosure")

# ---- F6: 19/20 is two per-seed counts, not a 95% rate ------------------------
sub("""resolves to **42 shared pairs** (Jaccard 0.724 vs permutation null 0.098,
p = 1e-4), the same extracted wrong answer in 41/42, nearest-gridline off-by-one
in 19/20.""",
"""resolves to **42 shared pairs** (Jaccard 0.724 vs permutation null 0.098,
p = 1e-4), with the same extracted wrong answer in 41 of those 42. The
nearest-gridline transition accounts for **19 wrong member slots in seed 1 and 20
in seed 2** — i.e. roughly 37% of wrong slots in each seed (19/52 and 20/53), not
a 95% rate. An earlier phrasing of "19/20" invited exactly that misreading and is
corrected here.""",
"F6 nearest-gridline 19/20 misreading")

# ---- G0.2 and G0.3 -----------------------------------------------------------
sub("""The title claim survives with a scope qualifier: the image-free gain is real on
image-requiring items (+0.197) but is disproportionately the blind-attainable
component.""",
"""The title claim survives with a scope qualifier: the image-free gain is real on
image-requiring items — **+0.197 restricted to base-wrong items** (n=406, where
headroom is identical), or **+0.093 across all** items in that stratum (n=484) —
but is disproportionately the blind-attainable component.""",
"G0.2 +0.197 base-wrong restriction")

sub("a permutation null of 0.157–0.177, p ≤ 0.004 in all three seeds.",
    "a permutation null of 0.157–0.177, p = 1e-4 in all three seeds (the weaker "
    "bound p ≤ 0.004 appears in some earlier text and understates it 40-fold).",
    "G0.3 p-value")

# ---- P0.1 pair-level figures are void per its own registration ---------------
sub("""| cell | premise member | premise pair | transition | final member | final pair | reasoning \\| premise |
|---|---|---|---|---|---|---|
| base | 0.275 | 0.200 | 0.200 | 0.150 | 0.000 | 0.273 (n=11) |
| A1 s1 | 0.225 | 0.200 | 0.200 | 0.100 | 0.000 | 0.222 (n=9) |
| A1 s2 | 0.175 | 0.150 | 0.150 | 0.075 | 0.000 | 0.000 (n=7) |
| A2b s1 | 0.300 | 0.200 | 0.200 | 0.125 | 0.000 | 0.250 (n=12) |
| A3 s1 | 0.250 | 0.200 | 0.200 | 0.075 | 0.000 | 0.200 (n=10) |""",
"""| cell | premise member | final member | reasoning \\| correct premise |
|---|---|---|---|
| base | 0.275 | 0.150 | 0.273 (n=11) |
| A1 s1 | 0.225 | 0.100 | 0.222 (n=9) |
| A1 s2 | 0.175 | 0.075 | 0.000 (n=7) |
| A2b s1 | **0.300** | 0.125 | 0.250 (n=12) |
| A3 s1 | 0.250 | 0.075 | 0.200 (n=10) |

*Pair-level and transition columns are omitted deliberately.* The probe's own
registration states that because both golds are equal by design, the harness's
pair logic is degenerate and **"any pair-level figure from this run is void and
will not be reported."* An earlier version of this file tabled them anyway.""",
"P0.1 void pair-level columns")

sub("""Reasoning given a correct premise is only 0.273 at base — premise extraction is
the first bottleneck but not the only one, so an easier premise curriculum alone
will not make these items trainable.""",
"""Reasoning given a correct premise is only 0.273 at base — premise extraction is
the first bottleneck but not the only one, so an easier premise curriculum alone
will not make these items trainable. Note the Wald interval straddles the
0.30 (b)/(c) boundary, so the evidence does not cleanly separate "too hard" from
"intermediate"; the consequence is identical under either branch. Note also that
A2b seed 1 reaches 0.300, *above* base — the claim "no arm beats base on premise
extraction" appears in the P0.1 markdown and is contradicted by its own table.""",
"P0.1 honest interval + self-contradiction")

sub("""**0 of 30 cells move**, so the published B1 table stands.""",
    """**nothing moves** across all 30 equal-gold items (10 model×type cells), so the
published B1 table stands.""",
    "B1 rescore 30 items not cells")

# ---- R2 secondaries ----------------------------------------------------------
sub("""Strict and lenient move identically, so the decline is answer content, not
formatting. Descriptive trajectory (overall R19, cannot select the endpoint per
the ruling): 0.5600 → 0.5433 → 0.5383 → 0.5167 at steps 150/200/300/400 —
monotone.""",
"""Strict and lenient move identically, so the decline is answer content, not
formatting.

**Registered secondaries** (the ruling designates overall R19 a secondary *under
the same rule*, not merely descriptive): overall R19 falls 0.5633 → 0.5167 from
step 100 to step 400, Δ = −0.0467. Blind-floor persistence at step 400 **passes**:
gray pair accuracy 0.0 with collapse 1.0, noise 0.0 with collapse 1.0 — the model
has not learned to answer these blind.

Steps 150/200/300 are descriptive only and cannot select the endpoint; their
overall values are 0.5600 / 0.5433 / 0.5383, so the trajectory from step 100
onward is monotone.""",
"R2 secondaries + step-100 overall")

# ---- contract-validity ordering + A2b equivalence verdict --------------------
sub("""Every trained arm
falls **below** the frozen base, and the ordering tracks how degraded the arm's
endpoint is.""",
"""Every trained arm
falls **below** the frozen base. The ordering is *broadly* but not exactly aligned
with endpoint degradation: contract validity runs A1 > A2b > A3 > A2-gray while
the endpoint runs A1 > A3 > A2b > A2-gray, so A2b and A3 are inverted
(Spearman 0.8, not 1).""",
"contract validity ordering")

sub("| A2b no-image | −0.0272 | [−0.0483, −0.0061] | marginal |",
    "| A2b no-image | −0.0272 | [−0.0483, −0.0061] | yes (marginal — lower bound "
    "−0.0483 against a −0.05 bound) |",
    "A2b equivalence verdict")

# ---- cue ladder rung count ---------------------------------------------------
sub("""Four rungs replayed
from the frozen R19 nine-series `pair_seed`s (300/300 replay integrity), so the
ladder is item-paired with R19.""",
"""**Six** rung conditions were built and are reported — v1's exact / region / none
/ decoy plus v2's named_exact / named_region — all replayed from the frozen R19
nine-series `pair_seed`s (300/300 replay integrity), so the ladder is item-paired
with R19.""",
"cue ladder rung count")

# ---- §18: chained premise caveat must propagate ------------------------------
sub("""- **The competence layers it should move do not move.** Hard negatives, binding,
  chained premise all flat or at floor (F5).""",
"""- **The competence layers it should move do not move.** Hard negatives and
  binding are flat (F5). Chained premise is at floor but that floor is
  *uninformative* per P0.1 branch (b), so it is not counted as evidence here. The
  one exception is `prior_conflict`, which moves in every trained cell — a small
  cell (n=14) that the argument must acknowledge rather than omit.""",
"section 18 chained premise + prior_conflict")

p.write_text(t)
print(f"\napplied {n} corrections")
