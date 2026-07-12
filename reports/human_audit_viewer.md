# Offline Human Audit Viewer

Status:
- Complete. `tools/human_audit_viewer.html` is a single-file, offline viewer for packaged FlipTrack human audits.
- It supports both R19 and R20 because it joins the shared release-manifest and private-key schemas by `pair_id` and `member_id`.
- It does not load, accept, display, or export evaluation results.
- The unloaded state now gives explicit R19 paths and selection status. The package-folder picker automatically finds the packaged `manifest.jsonl`, reducing setup from three local selections to two.
- After validation, the setup panel collapses so the first pair occupies the viewport; **Change package** restores it.

Evidence:
- Viewer: `tools/human_audit_viewer.html`, SHA256 `1d5de22b4612218bd80085a0e08504b85a89973e23222ca1699a8b1d8e07fce3`.
- Tests: `tests/test_human_audit_viewer.py`, SHA256 `e7117b86f93dcb1f60a88529e20ff4d6ec3a2b04f4423bb8cac04213c953349e`; six focused tests pass.
- The tests verify single-file/local-only operation, all six registered checks, failure-only export fields, member-ID answer joining under randomized member order, path-traversal rejection, absence of result-related vocabulary, and JavaScript syntax.
- The HTML pins a Content Security Policy with `connect-src 'none'`, contains no external scripts or styles, and calls no network API.
- Selected image bytes are SHA256-checked against the release manifest before each pair is marked verified in the UI.
- Review progress is stored only in browser `localStorage`, keyed by the manifest and answer-key SHA256 hashes.

## Usage

1. Open `tools/human_audit_viewer.html` directly in a current Chromium or Firefox browser. No server is required.
2. Under **Choose the R19 package folder**, select `data/fliptrack_v02r19_artifact_expanded/`. Select that package root, which contains both `manifest.jsonl` and `images/`; do not select `images/` or the project root. The page reports the package name, detected manifest, and image count when accepted.
3. Under **Choose the R19 private answer key**, select `.private/fliptrack_v02r19_key.jsonl`. If the `.private` directory is hidden in the chooser, press `Ctrl+H` to reveal hidden files.
4. Select **Open human audit** after the status reads **Ready to open**. Loading fails closed on duplicate IDs, missing key rows, member mismatches, unsafe paths, missing images, or ambiguous image resolution. The setup panel then collapses and the first pair appears; use **Change package** in the header to reopen it.
5. Keep **First 20 per template** for the representative contact-sheet audit. This deterministically selects the same first 20 rows per template as the generator, for 60 pairs across the current three templates. Select **All pairs** for the full 1,200-pair package.
6. Inspect both full-resolution members, the question, and the member-aligned answers. Use **Fit**, the zoom slider, or the open-original icon on either member.
7. Record an explicit **Pass** or **Fail** for each of the six checks. A pair is complete only after all six have a value.
8. Record a concrete failure note when useful. Navigation, template filtering, and pair-ID search preserve decisions locally.
9. Select **Export failures**. Before sign-off, require `unreviewed_pair_ids` to be empty in the exported JSON for the chosen audit scope.

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
- The initial unloaded state was visually checked from the user-provided screenshot. The login node still has no runnable automated graphical/headless browser, so loaded-state verification covers HTML structure, JavaScript syntax, local-only policy, schema logic, and adversarial core behavior rather than an automated screenshot.
- Browser-local progress is specific to the browser profile and exact manifest/key hashes. Export the JSON before changing browser profiles or clearing site data.
- `.private/` keys are intentionally git-ignored and must remain private.

Decision:
- Use the packaged release manifest and private key, never source manifests containing unblinded side metadata.
- Keep the representative 20-per-template scope for the registered R19 and R20 contact-sheet audits; use all-pairs mode only when a full audit is explicitly intended.
- Treat any image SHA256 mismatch or nonempty `unreviewed_pair_ids` list as an incomplete audit, not an accepted instrument.

Next actions:
- A PI/team reviewer opens the viewer, completes the R19 representative scope, and attaches the exported failure JSON to the human-audit decision.
- Repeat with the R20 package for the independent confirmatory human sample.
