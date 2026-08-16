# Track-4 premise-v2 — E3 caption stress, per-type readout

Registration: `docs/registered_track4_premise_v2_design_v1.md#7-E3`.

> Pass, per type: caption member accuracy <= blind-floor threshold + 0.10 absolute. Fail => the track is caption-leaky: eval-only until revised.

'blind-floor threshold' is not disambiguated in section 7 E3. Both readings are reported; where they disagree the disagreement is the result and the choice is the PI's.

| type | n pairs | caption member acc (lenient) | (strict) | ceiling (a) 0.133+0.10 | verdict (a) | ceiling (b) measured+0.10 | verdict (b) |
|---|---:|---:|---:|---:|---|---:|---|
| `chained_premise` | 20 | 0.1750 | 0.1750 | 0.2330 | **PASS** / **PASS** | 0.3000 | **PASS** / **PASS** |
| `chained_premise_easy` | 40 | 0.2000 | 0.2000 | 0.2330 | **PASS** / **PASS** | 0.3000 | **PASS** / **PASS** |
| `fact_read` | 20 | 0.1000 | 0.1000 | 0.2330 | **PASS** / **PASS** | 0.3000 | **PASS** / **PASS** |
| `premise_transition` | 40 | 0.1375 | 0.1375 | 0.2330 | **PASS** / **PASS** | 0.2500 | **PASS** / **PASS** |
| `premise_transition_easy` | 40 | 0.1625 | 0.1625 | 0.2330 | **PASS** / **PASS** | 0.3000 | **PASS** / **PASS** |

**No type fails under reading (a).** The track is not caption-leaky by the registered criterion.
