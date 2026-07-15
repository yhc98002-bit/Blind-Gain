# M2 Step-60 FlipTrack Lifecycle

Status:
- `complete` for the mechanical step-60 evaluation lifecycle of A1, A2b, and A3: each evaluation, aggregate, and fail-closed checkpoint marker completed.
- M2 remains `blocked`; this report makes no scientific gate decision and does not report or interpret model performance.

Evidence:

| Arm | Evaluation run | Node/GPUs | Evaluation manifest SHA256 | Marker SHA256 |
|---|---|---|---|---|
| A1 real | `pilot_fliptrack_mech_a1_real_seed1_step60_real_an12_20260715T172019Z` | `an12:4,5,6,7` | `788bf0830f4c8f55716978ca5b7fd1546cc2bc09e158c1c4534c1e84f79d21e8` | `2fe0a83cc0fbbcced39ea2cfa627b66baaae7d0e345748ace55e5ec3fa098012` |
| A2b no-image | `pilot_fliptrack_mech_a2b_noimage_seed1_step60_real_an29_20260715T170816Z` | `an29:0,1,2,3` | `6ff2a527a7ce595021ce51dc9075973d4dac3546b7bd67295a5799e04ce0b1ac` | `f086a14873357f60e5349a92ad63e702426ecb7645b327a914dd4a3cf5e7ff3e` |
| A3 caption | `pilot_fliptrack_mech_a3_caption_seed1_step60_real_an29_20260715T170816Z` | `an29:4,5,6,7` | `b10882a9795ea83dd90758d71869ff967e461ffb0d04c07f34171bf95a4cc2bb` | `fcca0c99d404a2839499162f8e1f763ffcdab8f1bf84c5d8f33632d45876185a` |

- Every evaluation used real R19 images, greedy decoding, `temperature=0`, `top_p=1`, `n=1`, and `max_new_tokens=32`.
- Frozen R19 manifest SHA256: `e1dde98451e1c7473906637c029713ab4f95ab4f7c915bd035f697953bf2ffb2`; exact coverage: 1,200 pairs.
- Prompt-contract SHA256: `7ac39f53a2a824490fc5ee22671a888d2d79d55e1d8351919006d7d71c7a8f3f`.
- Each evaluation used four independent TP1 replicas on one node. No job crossed nodes.
- A1 is bound through the completed resume run's audited `load_checkpoint_path`; A2b and A3 are bound directly through their run-local step-60 merged checkpoints.
- Finalization watchers completed with exit code 0 and verified both state and marker artifacts:
  - `pilot_step_eval_finalize_watch_a1_real_step60_login_20260715T172057Z`
  - `pilot_step_eval_finalize_watch_a2b_noimage_step60_login_20260715T171650Z`
  - `pilot_step_eval_finalize_watch_a3_caption_step60_login_20260715T171654Z`
- Each marker checks the exact checkpoint path/index hash, evaluation manifest, aggregate lineage, decoding lock, prompt contract, R19 hash, and 1,200-pair aggregate coverage.
- A2b/A3 step-60 merged checkpoints were subsequently copied to their login-node archives and committed with `MERGED_CHECKPOINT_RELOCATED.json`; their retention watchers are advancing toward steps 80/100.
- Finalization implementation commits: `9531c164c38a` (automatic aggregate/marker lifecycle) and `52dcd87` (resumed-source checkpoint binding). Verification after the latter: `31 passed`.

Problems:
- A2 gray has not reached final completion; its step-60 endpoint remains pending until the completed retry lineage can be bound.
- A1/A2b/A3 step-100 endpoints and geo3k-test evaluations remain pending.
- A2b/A3 retention currently performs quota snapshots before subsequent merge/relocation phases. A1 retention recovery is intentionally queued behind the active snapshots to avoid redundant concurrent full-quota scans.

Decision:
- Treat step-60 evaluation completion as a mechanical lifecycle fact only.
- Keep aggregate metrics unopened in this operational report; registered result computation remains in the final M2 readout.
- Continue checkpoint retention before scheduling the corresponding step-100 evaluations.

Next actions:
- Let A2b/A3 retention finish hash-verified steps 80/100.
- Start A1's audited failed-watcher recovery after the active quota scans complete.
- Launch step-100 R19 evaluations from final merged checkpoints, then complete geo3k-test and registered mechanism/accounting analyses.
