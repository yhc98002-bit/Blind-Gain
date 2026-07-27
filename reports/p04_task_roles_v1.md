# P0.4 — task roles fixed, cross-role aggregates audited

Required by `docs/EXPERIMENT_TODO.md` Part 2B and invariant **I13**: causal
sensitivity and invariance specificity are always reported separately, and no
aggregate may combine tasks that hold different scientific roles.

## The three roles

| task (template) | category | role | measured base pair acc |
|---|---|---|---|
| `coordinate_register_twenty_point_x_v02` | `geometry_coordinate_indexing` | primary visual anchor — the only R19 task requiring search, binding and read | 0.4717 |
| `header_cued_table_code_v02` | `document_header_indexing` | saturated positive control / retention canary | 0.8667 |
| `starred_series_value_nine_v07` | `chart_two_hop_read` | oracle-localized readout control | 0.4367 |

Canonicalised in `src/eval/task_roles.py`; enforced by
`tests/test_task_roles.py` (8 cases). `assert_no_cross_role_aggregate()` raises
on any set of tasks spanning more than one role, and unknown task ids **fail
closed** so a new task cannot be reported on before it is given a role.

## Audit result

**The registered primary endpoint is already role-pure.** All three seed readouts
record `primary_endpoint = category:geometry_coordinate_indexing`, i.e. the
primary visual anchor alone, and already carry role annotations
(`document_role: "calibration only"`, `chart_label: "cued chart point-value
reading"`). No registered claim rests on a cross-role average.

**One exposure remains: the `overall` key.** `fliptrack_r19.arms.<arm>["100"].overall`
exists in all three sealed readouts, and the overall R19 deltas
(+0.0283 / +0.0208 / +0.0267) are quoted in the prose as the numerator of the
exchange rate. That number averages all three roles.

**Disposition.** The sealed readouts are registered artifacts and are **not**
edited. The overall figure may continue to be reported, but only as an
**accounting identity** — the item-weighted sum of three separately-meaningful
deltas — never as a capability score, and never as a primary endpoint.
`reports/f2d_template_decomposition_v1.md` now supplies that decomposition, and
it is what should be cited wherever the overall number appears.

F2d also shows why the distinction is not pedantic: for A2 gray the overall delta
is −0.0014, which reads as "nothing happened", while the underlying tasks moved
−0.0422 (anchor, CI excludes zero) and +0.0556 (oracle-localized, CI excludes
zero). The aggregate destroyed a real result of each sign.

## Correction carried into the registry

The role name *saturated positive control* is inherited from the prose, which
states the task is "saturated at 1.000 for every model including base" and
"cannot show improvement". R19 does not measure that: base pair accuracy is
**0.8667** (strict 0.1800), and the task moves +0.019 to +0.023 in every trained
arm. The retention-canary function is intact — nothing drops — but the saturation
claim is false.

`src/eval/task_roles.py` keeps the documented name, because the documents specify
it, and records `SATURATION_CLAIM_IS_ACCURATE = False` with the measured value
next to it. A test asserts the flag stays false, so the prose claim cannot be
re-adopted as fact by later code. **PAPER1 §5 and §3 F2 need the PI to correct
the wording**; that is prose, not an executor section.

## Not in scope here

Causal-sensitivity versus invariance-specificity reporting (the other half of
I13) applies to Paper 2's Layer-B tracks, which do not exist yet. The guard in
`task_roles.py` covers R19 today; Track-3 groups must register their own roles
before they are scored.
