# Registered: E1b — trained-arm external columns under the access matrix (v1)

**Filed:** 2026-07-28, before any E1b prediction file is opened.
**Status at filing:** 48 configs generated and preflight-passed; zero cells run;
zero predictions read. `reports/e1b_config_inventory_v1.json`,
`scripts/preflight_e1b.py`.

## 1. Question

F1's access matrix was established on geo3k and R19. E1b asks whether it holds on
an external suite the arms never trained on: does the blind-column gain from RLVR
survive out of domain, and does it depend on what the model could see during
training?

## 2. Design

4 arms (A1 real, A2 gray, A2b no-image, A3 caption) x 3 seeds x 2 benchmarks
(MMStar, MathVista) x 2 conditions (image, blind) = **48 cells**. The base row for
every cell already exists from E1a and is not re-run.

**Item sets are pinned to the E1a base items**, verified by index intersection
before filing: MMStar 1500/1500 and MathVista 999/999 base indices are present in
the current TSVs. (The current TSVs contain embedded newlines, so a line count
reads 2106/4421; the parsed record counts are 1500/999. An earlier preflight that
counted lines reported a spurious mismatch and has been fixed to parse records.)

**Two harnesses, deliberately.** With-image uses vlmevalkit; blind uses
`eval_layer1_blind.py`, which raises if a vision token reaches the prompt. Both are
used exactly as the base rows used them, with only `model_path` swapped, so
decoding, prompt template and scoring are inherited rather than re-specified.

**Resource isolation.** E1b runs on **an12 GPUs 4-7 only**. M7 holds GPUs 0-3 at
its registered 4-GPU width and is not touched, widened, or paused. Every generated
config carries the isolation block declaring [4,5,6,7] allowed and [0,1,2,3]
forbidden. If the 48 cells do not fit comfortably on four GPUs they run
sequentially; M7's width is not a variable here.

## 3. Preregistered expectations

**P1 (primary) — the blind gain transfers.** Trained arms exceed base in the blind
column on both benchmarks, pooled across seeds. Rationale: RLVR installs answer-format
and answer-prior competence that is image-independent, so it should transfer as a
blind gain even out of domain.
- (a) confirmed: all four arms > base blind on both benchmarks
- (b) partial: transfer on one benchmark only, or some arms only
- (c) refuted: arms <= base blind

**P2 (primary) — the blind gain does not require training-time image access.** This
is the external test of the access matrix: A2b, which never saw an image in training,
gains at least as much blind accuracy as A1.
- (a) access-independent: |A2b − A1| in the blind column is smaller than A1's own
  blind gain over base
- (b) access-dependent: A1 exceeds A2b by more than that gain
- (c) inverted: A2b exceeds A1 by more than that gain

**S1 (secondary) — corrosion transfers.** A2-gray's with-image accuracy falls below
A1's on the external suite, the signature F6 predicts beyond R19/geo3k. A miss here
does not overturn F6, which is registered on R19; it bounds F6's external reach, and
a miss is reported as such.

**S2 (secondary) — with-image transfer.** Trained arms >= base with images.

Any outcome not enumerated above is reported as unanticipated, not folded into the
nearest branch.

## 4. Reporting contract

Bound to the CHANCE contract, not naive retention. Every retention figure is reported
as `(blind − null)/(with-image − null)` with item-level bootstrap CIs on the ratio of
differences, alongside its null and the raw numbers.

**Null by answer format.** MMStar is multiple choice: null = 1/k. **MathVista is
mixed and is split into MC and free-form subsets and reported separately** — no single
global null is applied to it, and no MathVista corrected figure is asserted until the
CHANCE split lands.

Lenient and contract-strict are both reported (I7). No aggregate crosses task roles
(I13). Schema versioned (I15).

## 5. Sealed

No E1b prediction, metrics or accuracy file is opened before this registration is
merged. The preflight that has already run is non-evaluative by construction: it
instantiates no model and opens no prediction file.
