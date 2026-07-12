# Offline Human Audit Viewer

Status:
- Complete. `tools/human_audit_viewer.html` is a single-file, offline viewer for packaged FlipTrack human audits.
- It supports both R19 and R20 because it joins the shared release-manifest and private-key schemas by `pair_id` and `member_id`.
- It does not load, accept, display, or export evaluation results.

Evidence:
- Viewer: `tools/human_audit_viewer.html`, SHA256 `cb72acd1db7fbe727be5f60e0255890cd5add682d9787af3b27144b90622e861`.
- Tests: `tests/test_human_audit_viewer.py`, SHA256 `ade9d9f69a2b898bdad8f90e2206bb7fadf0a64e24a8d168b0e31c7c9a86fdb1`; six focused tests pass.
- The tests verify single-file/local-only operation, all six registered checks, failure-only export fields, member-ID answer joining under randomized member order, path-traversal rejection, absence of result-related vocabulary, and JavaScript syntax.
- The HTML pins a Content Security Policy with `connect-src 'none'`, contains no external scripts or styles, and calls no network API.
- Selected image bytes are SHA256-checked against the release manifest before each pair is marked verified in the UI.
- Review progress is stored only in browser `localStorage`, keyed by the manifest and answer-key SHA256 hashes.

## Usage

1. Open `tools/human_audit_viewer.html` directly in a current Chromium or Firefox browser. No server is required.
2. Choose the packaged release `manifest.jsonl` under **Release manifest**.
3. Choose its private JSONL key under **Private answer key**.
4. Choose the release package directory under **Release package directory**. Select the package root containing `images/`, not the project root.
5. Select **Load audit**. Loading fails closed on duplicate IDs, missing key rows, member mismatches, unsafe paths, missing images, or ambiguous image resolution.
6. Keep **First 20 per template** for the representative contact-sheet audit. This deterministically selects the same first 20 rows per template as the generator, for 60 pairs across the current three templates. Select **All pairs** for the full 1,200-pair package.
7. Inspect both full-resolution members, the question, and the member-aligned answers. Use **Fit**, the zoom slider, or the open-original icon on either member.
8. Record an explicit **Pass** or **Fail** for each of the six checks. A pair is complete only after all six have a value.
9. Record a concrete failure note when useful. Navigation, template filtering, and pair-ID search preserve decisions locally.
10. Select **Export failures**. Before sign-off, require `unreviewed_pair_ids` to be empty in the exported JSON for the chosen audit scope.

## Package Paths

R19:

| Input | Path | SHA256 |
| --- | --- | --- |
| Manifest | `data/fliptrack_v02r19_artifact_expanded/manifest.jsonl` | `62553d701eb3e949910110057b65ab4e1146c602d21936268818fd1725b1b427` |
| Answer key | `.private/fliptrack_v02r19_key.jsonl` | `c7da389436d705218aaa494de649beb1ce973e227e5db3b3b5facd3eb3d42cfe` |
| Package directory | `data/fliptrack_v02r19_artifact_expanded/` | selected locally |

R20:

| Input | Path | SHA256 |
| --- | --- | --- |
| Manifest | `data/fliptrack_r20/manifest.jsonl` | `be033f67bd78d6207fb6dd1a3156810f3515416203b48fc65ae59334308255b4` |
| Answer key | `.private/fliptrack_r20_key.jsonl` | `136055580e05164ded27aac476a75ead3eb2de37b59ed0e90150f7b96291f0ec` |
| Package directory | `data/fliptrack_r20/` | selected locally |

## Check Semantics

| Check ID | Pass means |
| --- | --- |
| `visual_necessity` | The question cannot be answered without seeing the image. |
| `single_answer_changing_difference` | Only the required visual fact changes the answer. |
| `legible_without_popout` | The changed fact is legible without an artificial pop-out cue. |
| `unambiguous_labels_and_wording` | Labels, legends, axes, headers, and wording are unambiguous. |
| `artifact_parity` | Neither member is uniquely compressed, clipped, crowded, or otherwise artifact-prone. |
| `answer_key_exact` | Both displayed answers match their corresponding image member exactly. |

## Export Contract

The downloaded JSON uses schema `blind-gains.human-audit-failures.v1` and includes:

- manifest/key names and SHA256 hashes;
- selected audit scope and pair counts;
- registered check definitions;
- only failed pair records, with `pair_id`, `template_id`, failed check IDs, all six audit decisions, and the reviewer note;
- all incomplete pair IDs under `unreviewed_pair_ids`.

Answers and image paths are intentionally omitted from the export. The viewer never reads arbitrary fields from evaluation JSONL and has no input for such files.

Problems:
- The login node has no runnable graphical/headless browser: `/usr/bin/firefox` is an uninstalled snap shim. Verification here therefore covers HTML structure, JavaScript syntax, local-only policy, schema logic, and adversarial core behavior, but not a screenshot of the interactive loaded state.
- Browser-local progress is specific to the browser profile and exact manifest/key hashes. Export the JSON before changing browser profiles or clearing site data.
- `.private/` keys are intentionally git-ignored and must remain private.

Decision:
- Use the packaged release manifest and private key, never source manifests containing unblinded side metadata.
- Keep the representative 20-per-template scope for the registered R19 and R20 contact-sheet audits; use all-pairs mode only when a full audit is explicitly intended.
- Treat any image SHA256 mismatch or nonempty `unreviewed_pair_ids` list as an incomplete audit, not an accepted instrument.

Next actions:
- A PI/team reviewer opens the viewer, completes the R19 representative scope, and attaches the exported failure JSON to the human-audit decision.
- Repeat with the R20 package for the independent confirmatory human sample.
