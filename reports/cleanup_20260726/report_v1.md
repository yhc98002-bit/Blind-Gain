# Storage cleanup 2026-07-26 — execution and incident report (v1)

## 1. Authorized cleanup — executed as planned

Six gated candidates, 291.7 GiB, deleted at 09:30:27Z after every fail-closed
gate passed (checksum sample-verification against relocation-time manifests;
merged step-60/100 presence per affected lineage; seed-2 eval markers; M5
fallback supersession; scientific-reference grep with provenance-record
exclusions). Records: `cleanup_inventory_dry-run_20260726T092933Z.json`,
`cleanup_execution_20260726T093027Z.json`,
`checksums_merged_mech_a2_gray_resume60_retry2_global_step_80.json`.
Deleted: three overflow entries (anchor_a0 73G; superseded pre-resume20
seed-2 A2 45G; superseded pre-resume150 M5 43G), both seed-2 resume20 raw
archives (60G each), one intermediate merged checkpoint (7G).

## 2. Incident — scratch archive disappearance (unattributed)

Between 09:30:27Z and 09:32:38Z the entire `/tmp/blindgain_checkpoint_archive`
tree on ln207 vanished — far beyond the two candidate entries inside it.
Evidence: the execution record lists exactly the six candidate paths; a
second execution pass at 09:32:38Z found zero candidates and the tree absent;
`ls /tmp` shows other users' files (Jul 3–12) untouched, ruling out a
system-wide purge; /tmp usage fell from ~599G to ~61G. The leading hypothesis
is an administrative removal of the node's single ~500 GB consumer
(/tmp is node-local scratch with no durability guarantee); an unknown
interaction cannot be fully excluded and the timeline is preserved here for
review. This event independently validates treating node-local /tmp as
volatile.

## 3. Loss inventory (unintended, beyond the authorized deletions)

- Seed-3 A1/A2/A2b raw archives (steps 20–100, incl. the eval-pinned step-60
  raws) and A3's already-relocated raws — optimizer-resume insurance only.
- M5 resume150 archived raws (steps 200/250) and the archived merged
  checkpoints for steps 250 and 300.
- Small seed-2 A1/A3 archive remnants (~1G each).

## 4. Impact assessment — published-result reproducibility intact

- All registered evaluation artifacts live on shared quota: verification
  sweep confirmed merged step-60 and step-100 indices for every seed-3 arm
  (A3 step-100 pending its training completion), seed-2 resume20 step-100,
  and the seed-1 lineages referenced by the frozen configs (9/10 sweep; the
  one miss was M5 merged-300, addressed below). Every registered readout's
  inputs and outputs (scores, predictions, manifests, reports) are on quota
  and in git.
- M5 merged step-300: regenerated from the on-quota raw shards
  (`easyr1_checkpoint_merge_m5_step300_regen_login_20260726T093656Z`) before
  the 350-boundary retention could remove them. The step-300 registered
  evaluation had already completed with results recorded in the segment run.
- M5 step-250 model state is unrecoverable (raw and merged existed only in
  the archive). Its registered role — segment-boundary integrity — was
  validated and recorded at boundary time; no registered analysis consumes
  the step-250 weights. This is the single genuine artifact loss.
- Running work unaffected throughout: A3 training advanced continuously
  (step 73 → 79+ across the window), M5's segment 300→350 launched and
  trains, A3's watcher and the seed-3 queue remain running; forward
  relocations recreate the archive directory automatically.

## 5. Broken retention promises and forward policy

- The pilot watchers' step-60 raw retention (hold until eval markers) is now
  vacuously unfulfillable for the seed-3 arms; at marker time the watchers'
  retirement step must tolerate the already-absent raws (deviation to be
  recorded at their finalization, alongside the code-bundle relaunch those
  watchers need anyway).
- Policy: archived raws are henceforth explicitly best-effort/expendable
  (consistent with their resume-only role); any artifact a registered
  analysis may consume — in particular M5 boundary merged checkpoints at
  steps 350 and 400 — must be kept or copied on shared quota at boundary
  time (action item on the M5 watcher configuration before the 350
  boundary).

## 6. Space state after all of the above

- ln207 /tmp: 61G used / 713G free (was 92% at the crisis peak).
- Shared quota: ~168 GiB returned (overflow entries + merged-80); overflow
  directory reduced to the move log.
- Plan tranche 3 (event-gated archive expiries) is moot — the event removed
  those entries; this report supersedes those plan lines.
