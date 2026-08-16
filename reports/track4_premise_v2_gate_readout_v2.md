# Track-4 premise-v2 acceptance gates E1 + E2 - registered readout

Governing registration: `docs/registered_track4_premise_v2_design_v1.md` (sha256 `9ba7c96970d0150e733d1421b6f0712f2bf7558370694143336fa4a8d4c7df19`).

Machine artifact: `reports/track4_premise_v2_gate_readout_v2.json` (`blind-gains.track4-premise-v2-gate-readout.v1`).

This report states the registered verdicts and the section-5 branch the registered rule fires. It contains no interpretation; every choice the registration leaves open is left open here.

Discipline: both scoring contracts are reported separately and never merged (I7); every endpoint is per intervention type and nothing is pooled across types (I13). Each cell's own `metrics.json` is pooled across types and is NOT the registered endpoint; it is carried by sha256 only.

## E1 - difficulty band

Registered readout and pass criterion:

> Readout: per-intervention-type premise member accuracy (probe run) and final
> member/pair accuracy (causal run), lenient + strict (I7), no aggregation
> across types (I13). Pass: `chained_premise_easy` premise member accuracy in
> [0.40, 0.60] (else §5 branches fire).

### Per-intervention-type accuracy, real images

| type | premise n | premise member acc (lenient) | premise member acc (strict) | premise pair acc (lenient) | final n | final member acc (lenient) | final member acc (strict) | final pair acc (lenient) | final pair acc (strict) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `chained_premise` | 20 | 0.325000 | 0.325000 | 0.200000 | 20 | 0.125000 | 0.125000 | 0.050000 | 0.050000 |
| `chained_premise_easy` | 40 | 0.512500 | 0.512500 | 0.425000 | 40 | 0.237500 | 0.237500 | 0.025000 | 0.025000 |
| `fact_read` | n/a | n/a | n/a | n/a | 20 | 0.475000 | 0.475000 | 0.250000 | 0.250000 |
| `premise_transition` | 40 | 0.275000 | 0.275000 | 0.025000 | 40 | 0.250000 | 0.250000 | 0.050000 | 0.050000 |
| `premise_transition_easy` | 40 | 0.475000 | 0.475000 | 0.225000 | 40 | 0.287500 | 0.287500 | 0.075000 | 0.075000 |

Premise pair accuracy semantics per type (section 4; stability and transition are never aggregated with each other):

- `chained_premise`: premise_stability (section 4: equal premise golds, invariance reading)
- `chained_premise_easy`: premise_stability (section 4: equal premise golds, invariance reading)
- `fact_read`: no premise rows - no premise-probe rows for this intervention type; the registration (section 3) states: `fact_read` items carry no premise fields at all. Half-specified premise metadata fails closed in the loader.
- `premise_transition`: premise_transition_accuracy (section 4: differing premise golds, discriminative two-gold branch)
- `premise_transition_easy`: premise_transition_accuracy (section 4: differing premise golds, discriminative two-gold branch)

### Registered pass criterion on `chained_premise_easy`

| contract | premise member accuracy | registered band | in band | verdict | section-5 branch fired |
|---|---:|---|---|---|---|
| lenient | 0.512500 | [0.40, 0.60] (inclusive both ends) | yes | **PASS** | a (a) band hit |
| strict | 0.512500 | [0.40, 0.60] (inclusive both ends) | yes | **PASS** | a (a) band hit |

Contracts agree: yes.

Section 7 E1 states the pass criterion as 'premise member accuracy in [0.40, 0.60]' and requires 'lenient + strict (I7)' without naming which contract carries the band (contrast section 7 E2, which says 'on lenient scoring'). This instrument therefore reports the verdict separately under each contract and does not choose between them; if they disagree, the disagreement is the result and the choice is the PI's.

Section-5 branch (a) band hit - registered text:

> - **(a) band hit** (0.40 ≤ acc ≤ 0.60): `n=8` is frozen as the Phase-2
>   curriculum entry difficulty. No further lever moves.

Section-5 branch (d) is defined on 'the single re-measure' and cannot be fired by a first measurement; it is quoted for completeness only.

## E2 - blind floor

Registered pass criterion and consequence:

> **E2 — blind floor** (1 GPU): repeat both E1 commands with
> `--image-mode no_image` and `--image-mode gray` (four runs). Pass, per type:
> blind (no_image and gray) **final** member accuracy ≤ 0.133 (2× the 1/15
> uniform-x chance) and blind **premise** member accuracy ≤ 2×`1/(n_points−1)`
> (n=20: ≤ 0.105; n=8: ≤ 0.286), on lenient scoring. Fail ⇒ the failing type is
> excluded from any training use; the blind-solvable `pair_id`s are reported; no
> silent regeneration.

Contract of record for E2: **lenient** (Section 7 E2 names its contract: 'on lenient scoring'. The strict contract is computed and reported for every cell (I7) but is never merged into the E2 criterion; see strict_contract_reported_separately_NOT_A_CRITERION.)

| type | n_points | premise ceiling 2/(n_points-1) | mode | blind final member acc | <= 0.133 | blind premise member acc | <= ceiling | type verdict |
|---|---:|---:|---|---:|---|---:|---|---|
| `chained_premise` | 20 | 0.105263 | gray | 0.200000 | **OVER** | 0.000000 | ok | **FAIL** |
| `chained_premise` | 20 | 0.105263 | no_image | 0.200000 | **OVER** | 0.000000 | ok | **FAIL** |
| `chained_premise_easy` | 5 | 0.500000 | gray | 0.200000 | **OVER** | 0.000000 | ok | **FAIL** |
| `chained_premise_easy` | 5 | 0.500000 | no_image | 0.200000 | **OVER** | 0.000000 | ok | **FAIL** |
| `fact_read` | 20 | n/a | gray | 0.200000 | **OVER** | n/a | n/a | **FAIL** |
| `fact_read` | 20 | n/a | no_image | 0.200000 | **OVER** | n/a | n/a | **FAIL** |
| `premise_transition` | 20 | 0.105263 | gray | 0.150000 | **OVER** | 0.000000 | ok | **FAIL** |
| `premise_transition` | 20 | 0.105263 | no_image | 0.150000 | **OVER** | 0.000000 | ok | **FAIL** |
| `premise_transition_easy` | 5 | 0.500000 | gray | 0.200000 | **OVER** | 0.000000 | ok | **FAIL** |
| `premise_transition_easy` | 5 | 0.500000 | no_image | 0.200000 | **OVER** | 0.000000 | ok | **FAIL** |

- `fact_read`: this type carries no premise clause and is absent from the premise-probe manifest by registered design; section 3: `fact_read` items carry no premise fields at all. Half-specified premise metadata fails closed in the loader.

E2 passing types: none.
E2 failing types: `chained_premise`, `chained_premise_easy`, `fact_read`, `premise_transition`, `premise_transition_easy`.

### Failing types - registered consequence and blind-solvable `pair_id`s

#### `chained_premise` - FAIL

Failing criteria: gray:final_member_accuracy, no_image:final_member_accuracy.

Training use: **EXCLUDED** - Registered consequence, applied mechanically: 'Fail => the failing type is excluded from any training use; the blind-solvable `pair_id`s are reported; no silent regeneration.'

Blind-solvable `pair_id`s, gray / final (lenient scoring):

- any member correct (n=8): `t4v2c_chained_premise_0de86341d2edcfe1`, `t4v2c_chained_premise_7b59ec16a32ed583`, `t4v2c_chained_premise_a50c28b83235703f`, `t4v2c_chained_premise_c4540d08710dc1f3`, `t4v2c_chained_premise_c4ead46789c3d83e`, `t4v2c_chained_premise_d23db24dbb07b1a3`, `t4v2c_chained_premise_f2285bbb548ee8e3`, `t4v2c_chained_premise_f649766095665b49`
- both members correct (n=0): none

Blind-solvable `pair_id`s, gray / premise (lenient scoring):

- any member correct (n=0): none
- both members correct (n=0): none

Blind-solvable `pair_id`s, no_image / final (lenient scoring):

- any member correct (n=8): `t4v2c_chained_premise_0de86341d2edcfe1`, `t4v2c_chained_premise_7b59ec16a32ed583`, `t4v2c_chained_premise_a50c28b83235703f`, `t4v2c_chained_premise_c4540d08710dc1f3`, `t4v2c_chained_premise_c4ead46789c3d83e`, `t4v2c_chained_premise_d23db24dbb07b1a3`, `t4v2c_chained_premise_f2285bbb548ee8e3`, `t4v2c_chained_premise_f649766095665b49`
- both members correct (n=0): none

Blind-solvable `pair_id`s, no_image / premise (lenient scoring):

- any member correct (n=0): none
- both members correct (n=0): none

#### `chained_premise_easy` - FAIL

Failing criteria: gray:final_member_accuracy, no_image:final_member_accuracy.

Training use: **EXCLUDED** - Registered consequence, applied mechanically: 'Fail => the failing type is excluded from any training use; the blind-solvable `pair_id`s are reported; no silent regeneration.'

Blind-solvable `pair_id`s, gray / final (lenient scoring):

- any member correct (n=16): `t4v2c_chained_premise_easy_151452abc3241834`, `t4v2c_chained_premise_easy_2a833856ded0d494`, `t4v2c_chained_premise_easy_480f20864549c9ea`, `t4v2c_chained_premise_easy_4c8770710207ee11`, `t4v2c_chained_premise_easy_5ac2b81189baa711`, `t4v2c_chained_premise_easy_5b577b10060bba23`, `t4v2c_chained_premise_easy_7ad4d9e140a64c4f`, `t4v2c_chained_premise_easy_b1fcad275aa5ceaa`, `t4v2c_chained_premise_easy_b48ad74b875d2048`, `t4v2c_chained_premise_easy_bf840c9a3b74df89`, `t4v2c_chained_premise_easy_d10fae2dd0bab050`, `t4v2c_chained_premise_easy_d4b9b93cf20324d6`, `t4v2c_chained_premise_easy_e3814663dc1a7b0f`, `t4v2c_chained_premise_easy_e5a8ccf745a24477`, `t4v2c_chained_premise_easy_e5b2f56d2d7f1a81`, `t4v2c_chained_premise_easy_f0370ed354cba1e9`
- both members correct (n=0): none

Blind-solvable `pair_id`s, gray / premise (lenient scoring):

- any member correct (n=0): none
- both members correct (n=0): none

Blind-solvable `pair_id`s, no_image / final (lenient scoring):

- any member correct (n=16): `t4v2c_chained_premise_easy_151452abc3241834`, `t4v2c_chained_premise_easy_2a833856ded0d494`, `t4v2c_chained_premise_easy_480f20864549c9ea`, `t4v2c_chained_premise_easy_4c8770710207ee11`, `t4v2c_chained_premise_easy_5ac2b81189baa711`, `t4v2c_chained_premise_easy_5b577b10060bba23`, `t4v2c_chained_premise_easy_7ad4d9e140a64c4f`, `t4v2c_chained_premise_easy_b1fcad275aa5ceaa`, `t4v2c_chained_premise_easy_b48ad74b875d2048`, `t4v2c_chained_premise_easy_bf840c9a3b74df89`, `t4v2c_chained_premise_easy_d10fae2dd0bab050`, `t4v2c_chained_premise_easy_d4b9b93cf20324d6`, `t4v2c_chained_premise_easy_e3814663dc1a7b0f`, `t4v2c_chained_premise_easy_e5a8ccf745a24477`, `t4v2c_chained_premise_easy_e5b2f56d2d7f1a81`, `t4v2c_chained_premise_easy_f0370ed354cba1e9`
- both members correct (n=0): none

Blind-solvable `pair_id`s, no_image / premise (lenient scoring):

- any member correct (n=0): none
- both members correct (n=0): none

#### `fact_read` - FAIL

Failing criteria: gray:final_member_accuracy, no_image:final_member_accuracy.

Training use: **EXCLUDED** - Registered consequence, applied mechanically: 'Fail => the failing type is excluded from any training use; the blind-solvable `pair_id`s are reported; no silent regeneration.'

Blind-solvable `pair_id`s, gray / final (lenient scoring):

- any member correct (n=8): `t4v2c_fact_read_2cc58752b50cdffe`, `t4v2c_fact_read_5275ca8436939dc7`, `t4v2c_fact_read_7e6605ded75f3615`, `t4v2c_fact_read_81dc8ad282d877b4`, `t4v2c_fact_read_9dcd760f0705c9a9`, `t4v2c_fact_read_baf3418b1600e358`, `t4v2c_fact_read_cb5da097dd8a9c1b`, `t4v2c_fact_read_e8a0afe7997b6bc1`
- both members correct (n=0): none

Blind-solvable `pair_id`s, no_image / final (lenient scoring):

- any member correct (n=8): `t4v2c_fact_read_2cc58752b50cdffe`, `t4v2c_fact_read_5275ca8436939dc7`, `t4v2c_fact_read_7e6605ded75f3615`, `t4v2c_fact_read_81dc8ad282d877b4`, `t4v2c_fact_read_9dcd760f0705c9a9`, `t4v2c_fact_read_baf3418b1600e358`, `t4v2c_fact_read_cb5da097dd8a9c1b`, `t4v2c_fact_read_e8a0afe7997b6bc1`
- both members correct (n=0): none

#### `premise_transition` - FAIL

Failing criteria: gray:final_member_accuracy, no_image:final_member_accuracy.

Training use: **EXCLUDED** - Registered consequence, applied mechanically: 'Fail => the failing type is excluded from any training use; the blind-solvable `pair_id`s are reported; no silent regeneration.'

Blind-solvable `pair_id`s, gray / final (lenient scoring):

- any member correct (n=12): `t4v2c_premise_transition_029b28a5018ff4ac`, `t4v2c_premise_transition_42c0a7c3b9016e84`, `t4v2c_premise_transition_592bf68516d33e86`, `t4v2c_premise_transition_6cfd87e64d453c7d`, `t4v2c_premise_transition_a09e9760638f7e4e`, `t4v2c_premise_transition_b3978fed5abb99cc`, `t4v2c_premise_transition_ba3ef19e42312fec`, `t4v2c_premise_transition_bb57ded5cd19879d`, `t4v2c_premise_transition_c6e93da05a9e61e8`, `t4v2c_premise_transition_ea3c5d3be4c12371`, `t4v2c_premise_transition_f2e3adf0e989bbb9`, `t4v2c_premise_transition_fe38bcdc91eefa24`
- both members correct (n=0): none

Blind-solvable `pair_id`s, gray / premise (lenient scoring):

- any member correct (n=0): none
- both members correct (n=0): none

Blind-solvable `pair_id`s, no_image / final (lenient scoring):

- any member correct (n=12): `t4v2c_premise_transition_029b28a5018ff4ac`, `t4v2c_premise_transition_42c0a7c3b9016e84`, `t4v2c_premise_transition_592bf68516d33e86`, `t4v2c_premise_transition_6cfd87e64d453c7d`, `t4v2c_premise_transition_a09e9760638f7e4e`, `t4v2c_premise_transition_b3978fed5abb99cc`, `t4v2c_premise_transition_ba3ef19e42312fec`, `t4v2c_premise_transition_bb57ded5cd19879d`, `t4v2c_premise_transition_c6e93da05a9e61e8`, `t4v2c_premise_transition_ea3c5d3be4c12371`, `t4v2c_premise_transition_f2e3adf0e989bbb9`, `t4v2c_premise_transition_fe38bcdc91eefa24`
- both members correct (n=0): none

Blind-solvable `pair_id`s, no_image / premise (lenient scoring):

- any member correct (n=0): none
- both members correct (n=0): none

#### `premise_transition_easy` - FAIL

Failing criteria: gray:final_member_accuracy, no_image:final_member_accuracy.

Training use: **EXCLUDED** - Registered consequence, applied mechanically: 'Fail => the failing type is excluded from any training use; the blind-solvable `pair_id`s are reported; no silent regeneration.'

Blind-solvable `pair_id`s, gray / final (lenient scoring):

- any member correct (n=16): `t4v2c_premise_transition_easy_0f73e73b0c2db47c`, `t4v2c_premise_transition_easy_11e5b92dd27f2f7c`, `t4v2c_premise_transition_easy_3570a0ce7fa1cf87`, `t4v2c_premise_transition_easy_531bed8259aaf109`, `t4v2c_premise_transition_easy_5891a9dc687ad424`, `t4v2c_premise_transition_easy_5b73347b5e0ca9eb`, `t4v2c_premise_transition_easy_7a32249e8ac0b3bf`, `t4v2c_premise_transition_easy_7cb45a78454b4c7a`, `t4v2c_premise_transition_easy_83b761dc1e01fef6`, `t4v2c_premise_transition_easy_a3aca725aeedc485`, `t4v2c_premise_transition_easy_af9aa288b973036d`, `t4v2c_premise_transition_easy_b4c5861e9941b7cb`, `t4v2c_premise_transition_easy_bca73333b9815b0c`, `t4v2c_premise_transition_easy_bcdb2c95bde1a901`, `t4v2c_premise_transition_easy_cf1e625ef0e1b770`, `t4v2c_premise_transition_easy_d8032df82a781d08`
- both members correct (n=0): none

Blind-solvable `pair_id`s, gray / premise (lenient scoring):

- any member correct (n=0): none
- both members correct (n=0): none

Blind-solvable `pair_id`s, no_image / final (lenient scoring):

- any member correct (n=16): `t4v2c_premise_transition_easy_0f73e73b0c2db47c`, `t4v2c_premise_transition_easy_11e5b92dd27f2f7c`, `t4v2c_premise_transition_easy_3570a0ce7fa1cf87`, `t4v2c_premise_transition_easy_531bed8259aaf109`, `t4v2c_premise_transition_easy_5891a9dc687ad424`, `t4v2c_premise_transition_easy_5b73347b5e0ca9eb`, `t4v2c_premise_transition_easy_7a32249e8ac0b3bf`, `t4v2c_premise_transition_easy_7cb45a78454b4c7a`, `t4v2c_premise_transition_easy_83b761dc1e01fef6`, `t4v2c_premise_transition_easy_a3aca725aeedc485`, `t4v2c_premise_transition_easy_af9aa288b973036d`, `t4v2c_premise_transition_easy_b4c5861e9941b7cb`, `t4v2c_premise_transition_easy_bca73333b9815b0c`, `t4v2c_premise_transition_easy_bcdb2c95bde1a901`, `t4v2c_premise_transition_easy_cf1e625ef0e1b770`, `t4v2c_premise_transition_easy_d8032df82a781d08`
- both members correct (n=0): none

Blind-solvable `pair_id`s, no_image / premise (lenient scoring):

- any member correct (n=0): none
- both members correct (n=0): none

### Strict contract on the blind cells (reported separately, NOT an E2 criterion)

| type | mode | final member acc (strict) | premise member acc (strict) |
|---|---|---:|---:|
| `chained_premise` | gray | 0.200000 | 0.000000 |
| `chained_premise` | no_image | 0.200000 | 0.000000 |
| `chained_premise_easy` | gray | 0.200000 | 0.000000 |
| `chained_premise_easy` | no_image | 0.200000 | 0.000000 |
| `fact_read` | gray | 0.200000 | n/a |
| `fact_read` | no_image | 0.200000 | n/a |
| `premise_transition` | gray | 0.150000 | 0.000000 |
| `premise_transition` | no_image | 0.150000 | 0.000000 |
| `premise_transition_easy` | gray | 0.200000 | 0.000000 |
| `premise_transition_easy` | no_image | 0.200000 | 0.000000 |

## Gates not read here

- E3: caption stress - not read by this instrument
- E4: attacker check - not read by this instrument

> The track is unusable for training or release reporting until all four gates
> run and pass.

## Provenance

- root: `/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain`
- git HEAD: `2248c7f4eda6c800237924cabce8f43f5ac03e82`
- decoding lock: prompt contract `answer-tags-v1` (sha256 `7ac39f53a2a824490fc5ee22671a888d2d79d55e1d8351919006d7d71c7a8f3f`), parser `canonical-v2`
- premise-probe manifest: `data/track4_premise_v2_dev_v2/manifest_premise_probe.jsonl` sha256 `a67344acb3e8bac38cd548bdfd3812c05035ca2921adc7b48a29fc82087013ae` (140 rows)
- causal-pairs manifest: `data/track4_premise_v2_dev_v2/manifest_causal_pairs.jsonl` sha256 `318f53011db428f6275eeb44deb34ebfe9d26482806571c7b7d60bd66884f9ca` (160 rows)

| cell | image mode | rows | predictions sha256 | metrics sha256 (pooled, NOT the endpoint) |
|---|---|---:|---|---|
| `premise_probe_real` | real | 140 | `1373dab07d00e2ed63191d8a96314718e5d76723249267177d04c16a346a3261` | `9325ee84fd6753000fcfffded64696087f5e024d96da68e3d70bbbe187515a27` |
| `premise_probe_gray` | gray | 140 | `13e6b0ea99c0a35e4d448a330e90712870dbec1c8b96291407997e2460c3b44d` | `8de1ff35e1e1066e1ff15acb3f4699a46545ee998bd1f79bde69d3e0f5b116c7` |
| `premise_probe_no_image` | no_image | 140 | `928e64a1c82c22ba53afd4c60ef846e3958e4985687e101cc4498cf2edb4f25d` | `c4e957ba5c9035014952607b8f2c57a5b287ca931eba97effbe89768830cade0` |
| `final_real` | real | 160 | `b8c584c5a91cbaca6e535e2b5fc37f60f6eac20b0d84edcbf4485f3875cc4031` | `e45e19777578627197b7586aa883d5c9326ce5f3a4436794bce1c7d3c04654a2` |
| `final_gray` | gray | 160 | `677c29e81f584bce36e92f9a37a61f47db2e86e7d407908ccab9d1c21942edc8` | `b0b57caafee711a71d7e81ea1c807c9a9579db671d65429f3224186f1e3b7db7` |
| `final_no_image` | no_image | 160 | `ea69795d2fc280b70add79c6299351e2a4e6a9d1191421d59d245b049b4f1a31` | `a6be043edea6052791092a20ea289207145684132c5b14f77f28524b6c8aebf0` |

