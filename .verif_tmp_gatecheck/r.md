# Track-4 premise-v2 acceptance gates E1 + E2 - registered readout

Governing registration: `docs/registered_track4_premise_v2_design_v1.md` (sha256 `9ba7c96970d0150e733d1421b6f0712f2bf7558370694143336fa4a8d4c7df19`).

Machine artifact: `.verif_tmp_gatecheck/r.json` (`blind-gains.track4-premise-v2-gate-readout.v1`).

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
| `chained_premise` | 20 | 0.375000 | 0.375000 | 0.250000 | 20 | 0.225000 | 0.225000 | 0.000000 | 0.000000 |
| `chained_premise_easy` | 40 | 0.287500 | 0.287500 | 0.175000 | 40 | 0.212500 | 0.212500 | 0.025000 | 0.025000 |
| `fact_read` | n/a | n/a | n/a | n/a | 20 | 0.675000 | 0.675000 | 0.550000 | 0.550000 |
| `premise_transition` | 40 | 0.325000 | 0.325000 | 0.175000 | 40 | 0.162500 | 0.162500 | 0.025000 | 0.025000 |
| `premise_transition_easy` | 40 | 0.462500 | 0.462500 | 0.200000 | 40 | 0.275000 | 0.275000 | 0.025000 | 0.025000 |

Premise pair accuracy semantics per type (section 4; stability and transition are never aggregated with each other):

- `chained_premise`: premise_stability (section 4: equal premise golds, invariance reading)
- `chained_premise_easy`: premise_stability (section 4: equal premise golds, invariance reading)
- `fact_read`: no premise rows - no premise-probe rows for this intervention type; the registration (section 3) states: `fact_read` items carry no premise fields at all. Half-specified premise metadata fails closed in the loader.
- `premise_transition`: premise_transition_accuracy (section 4: differing premise golds, discriminative two-gold branch)
- `premise_transition_easy`: premise_transition_accuracy (section 4: differing premise golds, discriminative two-gold branch)

### Registered pass criterion on `chained_premise_easy`

| contract | premise member accuracy | registered band | in band | verdict | section-5 branch fired |
|---|---:|---|---|---|---|
| lenient | 0.287500 | [0.40, 0.60] (inclusive both ends) | no | **FAIL** | c (c) still too hard |
| strict | 0.287500 | [0.40, 0.60] (inclusive both ends) | no | **FAIL** | c (c) still too hard |

Contracts agree: yes.

Section 7 E1 states the pass criterion as 'premise member accuracy in [0.40, 0.60]' and requires 'lenient + strict (I7)' without naming which contract carries the band (contrast section 7 E2, which says 'on lenient scoring'). This instrument therefore reports the verdict separately under each contract and does not choose between them; if they disagree, the disagreement is the result and the choice is the PI's.

Section-5 branch (c) still too hard - registered text:

> - **(c) still too hard** (acc < 0.40): one pre-committed step to `n=5` (the
>   minimum at which the premise remains a genuine 4-distractor search); same
>   single re-measure discipline.

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
| `chained_premise` | 20 | 0.105263 | gray | 0.250000 | **OVER** | 0.000000 | ok | **FAIL** |
| `chained_premise` | 20 | 0.105263 | no_image | 0.250000 | **OVER** | 0.000000 | ok | **FAIL** |
| `chained_premise_easy` | 8 | 0.285714 | gray | 0.225000 | **OVER** | 0.000000 | ok | **FAIL** |
| `chained_premise_easy` | 8 | 0.285714 | no_image | 0.225000 | **OVER** | 0.000000 | ok | **FAIL** |
| `fact_read` | 20 | n/a | gray | 0.200000 | **OVER** | n/a | n/a | **FAIL** |
| `fact_read` | 20 | n/a | no_image | 0.200000 | **OVER** | n/a | n/a | **FAIL** |
| `premise_transition` | 20 | 0.105263 | gray | 0.137500 | **OVER** | 0.000000 | ok | **FAIL** |
| `premise_transition` | 20 | 0.105263 | no_image | 0.137500 | **OVER** | 0.000000 | ok | **FAIL** |
| `premise_transition_easy` | 8 | 0.285714 | gray | 0.225000 | **OVER** | 0.000000 | ok | **FAIL** |
| `premise_transition_easy` | 8 | 0.285714 | no_image | 0.225000 | **OVER** | 0.000000 | ok | **FAIL** |

- `fact_read`: this type carries no premise clause and is absent from the premise-probe manifest by registered design; section 3: `fact_read` items carry no premise fields at all. Half-specified premise metadata fails closed in the loader.

E2 passing types: none.
E2 failing types: `chained_premise`, `chained_premise_easy`, `fact_read`, `premise_transition`, `premise_transition_easy`.

### Failing types - registered consequence and blind-solvable `pair_id`s

#### `chained_premise` - FAIL

Failing criteria: gray:final_member_accuracy, no_image:final_member_accuracy.

Training use: **EXCLUDED** - Registered consequence, applied mechanically: 'Fail => the failing type is excluded from any training use; the blind-solvable `pair_id`s are reported; no silent regeneration.'

Blind-solvable `pair_id`s, gray / final (lenient scoring):

- any member correct (n=10): `t4v2c_chained_premise_3c76f68fdb222eb2`, `t4v2c_chained_premise_41bbf3b3c8703284`, `t4v2c_chained_premise_4ffe6d4cc79a95c0`, `t4v2c_chained_premise_525bdb1e2b6e4c24`, `t4v2c_chained_premise_5a71652c3a6e58c1`, `t4v2c_chained_premise_7fa51b280faf254c`, `t4v2c_chained_premise_baee38f89b94cca8`, `t4v2c_chained_premise_c8f3f61c673dcad5`, `t4v2c_chained_premise_fb20724a7d3cf532`, `t4v2c_chained_premise_fd45eafd654d3712`
- both members correct (n=0): none

Blind-solvable `pair_id`s, gray / premise (lenient scoring):

- any member correct (n=0): none
- both members correct (n=0): none

Blind-solvable `pair_id`s, no_image / final (lenient scoring):

- any member correct (n=10): `t4v2c_chained_premise_3c76f68fdb222eb2`, `t4v2c_chained_premise_41bbf3b3c8703284`, `t4v2c_chained_premise_4ffe6d4cc79a95c0`, `t4v2c_chained_premise_525bdb1e2b6e4c24`, `t4v2c_chained_premise_5a71652c3a6e58c1`, `t4v2c_chained_premise_7fa51b280faf254c`, `t4v2c_chained_premise_baee38f89b94cca8`, `t4v2c_chained_premise_c8f3f61c673dcad5`, `t4v2c_chained_premise_fb20724a7d3cf532`, `t4v2c_chained_premise_fd45eafd654d3712`
- both members correct (n=0): none

Blind-solvable `pair_id`s, no_image / premise (lenient scoring):

- any member correct (n=0): none
- both members correct (n=0): none

#### `chained_premise_easy` - FAIL

Failing criteria: gray:final_member_accuracy, no_image:final_member_accuracy.

Training use: **EXCLUDED** - Registered consequence, applied mechanically: 'Fail => the failing type is excluded from any training use; the blind-solvable `pair_id`s are reported; no silent regeneration.'

Blind-solvable `pair_id`s, gray / final (lenient scoring):

- any member correct (n=18): `t4v2c_chained_premise_easy_02eb19b3fecf5eb5`, `t4v2c_chained_premise_easy_0a27bd760a84983f`, `t4v2c_chained_premise_easy_3b298e109d8f4e32`, `t4v2c_chained_premise_easy_43fc51bbb30c23d6`, `t4v2c_chained_premise_easy_6a8e2a7bbb38e02a`, `t4v2c_chained_premise_easy_6fc010b6ca4c589e`, `t4v2c_chained_premise_easy_7a4e85593241b6d1`, `t4v2c_chained_premise_easy_8093426042fd7b1e`, `t4v2c_chained_premise_easy_a07032170750d183`, `t4v2c_chained_premise_easy_a09eb5d40669273f`, `t4v2c_chained_premise_easy_a1397793ba8d3de1`, `t4v2c_chained_premise_easy_a464d71e7cb1fffe`, `t4v2c_chained_premise_easy_a89dd70dea6f6530`, `t4v2c_chained_premise_easy_ad447251ce648fa5`, `t4v2c_chained_premise_easy_c7d19767eeb8056b`, `t4v2c_chained_premise_easy_d65e19102ab221ce`, `t4v2c_chained_premise_easy_da710a70dd928b6e`, `t4v2c_chained_premise_easy_f8cab27f239b232f`
- both members correct (n=0): none

Blind-solvable `pair_id`s, gray / premise (lenient scoring):

- any member correct (n=0): none
- both members correct (n=0): none

Blind-solvable `pair_id`s, no_image / final (lenient scoring):

- any member correct (n=18): `t4v2c_chained_premise_easy_02eb19b3fecf5eb5`, `t4v2c_chained_premise_easy_0a27bd760a84983f`, `t4v2c_chained_premise_easy_3b298e109d8f4e32`, `t4v2c_chained_premise_easy_43fc51bbb30c23d6`, `t4v2c_chained_premise_easy_6a8e2a7bbb38e02a`, `t4v2c_chained_premise_easy_6fc010b6ca4c589e`, `t4v2c_chained_premise_easy_7a4e85593241b6d1`, `t4v2c_chained_premise_easy_8093426042fd7b1e`, `t4v2c_chained_premise_easy_a07032170750d183`, `t4v2c_chained_premise_easy_a09eb5d40669273f`, `t4v2c_chained_premise_easy_a1397793ba8d3de1`, `t4v2c_chained_premise_easy_a464d71e7cb1fffe`, `t4v2c_chained_premise_easy_a89dd70dea6f6530`, `t4v2c_chained_premise_easy_ad447251ce648fa5`, `t4v2c_chained_premise_easy_c7d19767eeb8056b`, `t4v2c_chained_premise_easy_d65e19102ab221ce`, `t4v2c_chained_premise_easy_da710a70dd928b6e`, `t4v2c_chained_premise_easy_f8cab27f239b232f`
- both members correct (n=0): none

Blind-solvable `pair_id`s, no_image / premise (lenient scoring):

- any member correct (n=0): none
- both members correct (n=0): none

#### `fact_read` - FAIL

Failing criteria: gray:final_member_accuracy, no_image:final_member_accuracy.

Training use: **EXCLUDED** - Registered consequence, applied mechanically: 'Fail => the failing type is excluded from any training use; the blind-solvable `pair_id`s are reported; no silent regeneration.'

Blind-solvable `pair_id`s, gray / final (lenient scoring):

- any member correct (n=8): `t4v2c_fact_read_174471d24bf8f6f5`, `t4v2c_fact_read_6e2b4ae0c0b0e32c`, `t4v2c_fact_read_7ce53b902d1c1b01`, `t4v2c_fact_read_9a24012d393ab1fd`, `t4v2c_fact_read_a30fbfd81217f3ef`, `t4v2c_fact_read_a73e56f92df117d1`, `t4v2c_fact_read_c4b7e2d1cc35d9ea`, `t4v2c_fact_read_e8290182cb6b08af`
- both members correct (n=0): none

Blind-solvable `pair_id`s, no_image / final (lenient scoring):

- any member correct (n=8): `t4v2c_fact_read_174471d24bf8f6f5`, `t4v2c_fact_read_695157d92ab82297`, `t4v2c_fact_read_6e2b4ae0c0b0e32c`, `t4v2c_fact_read_7ce53b902d1c1b01`, `t4v2c_fact_read_9a24012d393ab1fd`, `t4v2c_fact_read_a73e56f92df117d1`, `t4v2c_fact_read_c4b7e2d1cc35d9ea`, `t4v2c_fact_read_e8290182cb6b08af`
- both members correct (n=0): none

#### `premise_transition` - FAIL

Failing criteria: gray:final_member_accuracy, no_image:final_member_accuracy.

Training use: **EXCLUDED** - Registered consequence, applied mechanically: 'Fail => the failing type is excluded from any training use; the blind-solvable `pair_id`s are reported; no silent regeneration.'

Blind-solvable `pair_id`s, gray / final (lenient scoring):

- any member correct (n=11): `t4v2c_premise_transition_07cea3de05268e7d`, `t4v2c_premise_transition_0bb30ed12b2cc272`, `t4v2c_premise_transition_21f992441bdb5b9f`, `t4v2c_premise_transition_35dba92d552473e8`, `t4v2c_premise_transition_51ff2dc942ebad9d`, `t4v2c_premise_transition_6a2e6e0a936b4e90`, `t4v2c_premise_transition_6d9365f5bf26b8b5`, `t4v2c_premise_transition_a184d0654a727681`, `t4v2c_premise_transition_b04694074d729010`, `t4v2c_premise_transition_c4c060f7e80497ea`, `t4v2c_premise_transition_fd03f21c6075fa37`
- both members correct (n=0): none

Blind-solvable `pair_id`s, gray / premise (lenient scoring):

- any member correct (n=0): none
- both members correct (n=0): none

Blind-solvable `pair_id`s, no_image / final (lenient scoring):

- any member correct (n=11): `t4v2c_premise_transition_07cea3de05268e7d`, `t4v2c_premise_transition_0bb30ed12b2cc272`, `t4v2c_premise_transition_21f992441bdb5b9f`, `t4v2c_premise_transition_35dba92d552473e8`, `t4v2c_premise_transition_51ff2dc942ebad9d`, `t4v2c_premise_transition_6a2e6e0a936b4e90`, `t4v2c_premise_transition_6d9365f5bf26b8b5`, `t4v2c_premise_transition_a184d0654a727681`, `t4v2c_premise_transition_b04694074d729010`, `t4v2c_premise_transition_c4c060f7e80497ea`, `t4v2c_premise_transition_fd03f21c6075fa37`
- both members correct (n=0): none

Blind-solvable `pair_id`s, no_image / premise (lenient scoring):

- any member correct (n=0): none
- both members correct (n=0): none

#### `premise_transition_easy` - FAIL

Failing criteria: gray:final_member_accuracy, no_image:final_member_accuracy.

Training use: **EXCLUDED** - Registered consequence, applied mechanically: 'Fail => the failing type is excluded from any training use; the blind-solvable `pair_id`s are reported; no silent regeneration.'

Blind-solvable `pair_id`s, gray / final (lenient scoring):

- any member correct (n=18): `t4v2c_premise_transition_easy_2f43b4e9f532ad5e`, `t4v2c_premise_transition_easy_2f7db136893ea785`, `t4v2c_premise_transition_easy_33f5fe1c98234de1`, `t4v2c_premise_transition_easy_43681c784ac02b87`, `t4v2c_premise_transition_easy_4a9db79b618cfc2a`, `t4v2c_premise_transition_easy_55cc839ea54633d0`, `t4v2c_premise_transition_easy_5c3ab4173d2eec78`, `t4v2c_premise_transition_easy_6eeea720a2e5f3a0`, `t4v2c_premise_transition_easy_75cd86cb0c2a46bc`, `t4v2c_premise_transition_easy_792c326341347ca4`, `t4v2c_premise_transition_easy_a1a1d8f91988108a`, `t4v2c_premise_transition_easy_b167d4a96b50fd90`, `t4v2c_premise_transition_easy_b4a9a5b79a4ba117`, `t4v2c_premise_transition_easy_c3e0dbfc49be8bc8`, `t4v2c_premise_transition_easy_cf05532a66fce24b`, `t4v2c_premise_transition_easy_e15ed7801213012b`, `t4v2c_premise_transition_easy_f43b0ccc7b21202f`, `t4v2c_premise_transition_easy_f5c84246535a44c1`
- both members correct (n=0): none

Blind-solvable `pair_id`s, gray / premise (lenient scoring):

- any member correct (n=0): none
- both members correct (n=0): none

Blind-solvable `pair_id`s, no_image / final (lenient scoring):

- any member correct (n=18): `t4v2c_premise_transition_easy_2f43b4e9f532ad5e`, `t4v2c_premise_transition_easy_2f7db136893ea785`, `t4v2c_premise_transition_easy_33f5fe1c98234de1`, `t4v2c_premise_transition_easy_43681c784ac02b87`, `t4v2c_premise_transition_easy_4a9db79b618cfc2a`, `t4v2c_premise_transition_easy_55cc839ea54633d0`, `t4v2c_premise_transition_easy_5c3ab4173d2eec78`, `t4v2c_premise_transition_easy_6eeea720a2e5f3a0`, `t4v2c_premise_transition_easy_75cd86cb0c2a46bc`, `t4v2c_premise_transition_easy_792c326341347ca4`, `t4v2c_premise_transition_easy_a1a1d8f91988108a`, `t4v2c_premise_transition_easy_b167d4a96b50fd90`, `t4v2c_premise_transition_easy_b4a9a5b79a4ba117`, `t4v2c_premise_transition_easy_c3e0dbfc49be8bc8`, `t4v2c_premise_transition_easy_cf05532a66fce24b`, `t4v2c_premise_transition_easy_e15ed7801213012b`, `t4v2c_premise_transition_easy_f43b0ccc7b21202f`, `t4v2c_premise_transition_easy_f5c84246535a44c1`
- both members correct (n=0): none

Blind-solvable `pair_id`s, no_image / premise (lenient scoring):

- any member correct (n=0): none
- both members correct (n=0): none

### Strict contract on the blind cells (reported separately, NOT an E2 criterion)

| type | mode | final member acc (strict) | premise member acc (strict) |
|---|---|---:|---:|
| `chained_premise` | gray | 0.250000 | 0.000000 |
| `chained_premise` | no_image | 0.250000 | 0.000000 |
| `chained_premise_easy` | gray | 0.225000 | 0.000000 |
| `chained_premise_easy` | no_image | 0.225000 | 0.000000 |
| `fact_read` | gray | 0.200000 | n/a |
| `fact_read` | no_image | 0.200000 | n/a |
| `premise_transition` | gray | 0.137500 | 0.000000 |
| `premise_transition` | no_image | 0.137500 | 0.000000 |
| `premise_transition_easy` | gray | 0.225000 | 0.000000 |
| `premise_transition_easy` | no_image | 0.225000 | 0.000000 |

## Gates not read here

- E3: caption stress - not read by this instrument
- E4: attacker check - not read by this instrument

> The track is unusable for training or release reporting until all four gates
> run and pass.

## Provenance

- root: `/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain`
- git HEAD: `2ebf8c0dbd9753c272498f0e999fdabba369b9f3`
- decoding lock: prompt contract `answer-tags-v1` (sha256 `7ac39f53a2a824490fc5ee22671a888d2d79d55e1d8351919006d7d71c7a8f3f`), parser `canonical-v2`
- premise-probe manifest: `data/track4_premise_v2_dev_v1/manifest_premise_probe.jsonl` sha256 `693ef38bea73fb81e5f3e4b7cc2d0712a634f98b4b06413e4939e8ddaf7e7290` (140 rows)
- causal-pairs manifest: `data/track4_premise_v2_dev_v1/manifest_causal_pairs.jsonl` sha256 `5963dd0f9899dc8b0ea38463edbaba546ae5c85c6630dd55c1fedbf8db4143a3` (160 rows)

| cell | image mode | rows | predictions sha256 | metrics sha256 (pooled, NOT the endpoint) |
|---|---|---:|---|---|
| `premise_probe_real` | real | 140 | `6813dbe50dc3fd030bce4b1162cec9304974a834aadbada3920188d06086701b` | `06f93e561c8e5e72224ff69c8ac7f87223168e355d0ceeb43c577b9e5e1087db` |
| `premise_probe_gray` | gray | 140 | `f92b174f9b8131c663d0629c5c7f0ff52f717de4bb873a61c315147850286ec0` | `8de1ff35e1e1066e1ff15acb3f4699a46545ee998bd1f79bde69d3e0f5b116c7` |
| `premise_probe_no_image` | no_image | 140 | `2e719f697f4d5ca1a607b934987e7e253cb399e4308cf0d17625e1c86bcde3ec` | `c4e957ba5c9035014952607b8f2c57a5b287ca931eba97effbe89768830cade0` |
| `final_real` | real | 160 | `59c9240a0594429384d95bf73047ca95499d5ad811c4cef11eb24b91226477f1` | `7c5b397adda9d7c976bd97356b78749e9ecf1db5b739405f6205f433d55e75c4` |
| `final_gray` | gray | 160 | `9d878d919fb2c8631fb5a86fd6ffe08e05fdf7fd6f9bbae9a6cd2768ae995135` | `b7002a69bc7cc7c0b24febd45b7ec7b4470d5b8751b819f4c745ccdd782703e7` |
| `final_no_image` | no_image | 160 | `3a95a3362e6175f3919bcee7811849c755b7488c88da6100d012c3b8d894104f` | `be1058a0a1f99381afb52aabb2c39db45365e33cc58c35efc48934381734d251` |

