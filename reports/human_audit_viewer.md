# Offline Human Audit Viewer

Status:
- Complete. `tools/human_audit_viewer.html` is a single-file, offline viewer for packaged FlipTrack human audits.
- It supports both R19 and R20 because it joins the shared release-manifest and private-key schemas by `pair_id` and `member_id`.
- It does not load, accept, display, or export evaluation results.
- The unloaded state now gives explicit R19 paths and selection status. The package-folder picker automatically finds the packaged `manifest.jsonl`, reducing setup from three local selections to two.
- After validation, the setup panel collapses so the first pair occupies the viewport; **Change package** restores it.

Evidence:
- Viewer: `tools/human_audit_viewer.html`, SHA256 `0ffc01c17a59e54732e13a269b2428f7f3ffc38513d40eb2c5728e37a5dcc595`.
- Tests: `tests/test_human_audit_viewer.py`, SHA256 `1f02388470b335f82836f5dd47d3a1280bc3e8eb916240be64a932c426494d21`; six focused tests pass.
- Portable-bundle builder: `scripts/build_human_audit_bundle.py`, SHA256 `19a4b1e90fc1719ab4cf9325606fa6450e09544451b4d3b9607429d72c37e731`.
- Builder tests: `tests/test_human_audit_bundle.py`, SHA256 `ffcc82a18a32afa6eb4ac8164122f61bfe2aa48c4df3523ebbc209b920c8c55b`; four focused tests pass.
- The tests verify single-file/local-only operation, all six registered checks, failure-only export fields, member-ID answer joining under randomized member order, path-traversal rejection, absence of result-related vocabulary, and JavaScript syntax.
- The HTML pins a Content Security Policy with `connect-src 'none'`, contains no external scripts or styles, and calls no network API.
- Selected image bytes are SHA256-checked against the release manifest before each pair is marked verified in the UI.
- Review progress is stored only in browser `localStorage`, keyed by the manifest and answer-key SHA256 hashes.

## Usage

For a reviewer whose browser runs on another computer, use the portable bundle in `reports/review_packages/`; a browser file picker can only access files on the browser's computer.

1. Download and extract `blind_gains_r19_human_audit_20260712_v2.zip` on the reviewing computer.
2. Open the extracted `human_audit_viewer.html` directly in a current Chromium or Firefox browser. No server is required.
3. Under **Choose the R19 package folder**, select the extracted `package/` directory.
4. Under **Choose the R19 private answer key**, select the extracted `private/answer_key.jsonl`.
5. Select **Open human audit** after the status reads **Ready to open**. The exact 60-pair bundle defaults to **All loaded pairs**. Loading fails closed on duplicate IDs, missing key rows, member mismatches, unsafe paths, missing images, or ambiguous image resolution.
6. Inspect both full-resolution members, the question, and the member-aligned answers. Use **Fit**, the zoom slider, or the open-original icon on either member.
7. Record an explicit **Pass** or **Fail** for each of the six checks. A pair is complete only after all six have a value.
8. Record a concrete failure note when useful. Navigation, template filtering, and pair-ID search preserve decisions locally.
9. Select **Export failures**. Before sign-off, require `unreviewed_pair_ids` to be empty.

On a browser running on the cluster itself, the equivalent inputs are `data/fliptrack_v02r19_artifact_expanded/` and `.private/fliptrack_v02r19_key.jsonl`. That full package is not the preferred registered-audit input because its release order is randomized.

## Package Paths

R19:

| Input | Path | SHA256 |
| --- | --- | --- |
| Manifest | `data/fliptrack_v02r19_artifact_expanded/manifest.jsonl` | `62553d701eb3e949910110057b65ab4e1146c602d21936268818fd1725b1b427` |
| Answer key | `.private/fliptrack_v02r19_key.jsonl` | `c7da389436d705218aaa494de649beb1ce973e227e5db3b3b5facd3eb3d42cfe` |
| Package directory | `data/fliptrack_v02r19_artifact_expanded/` | selected locally |
| Portable registered sample | `reports/review_packages/blind_gains_r19_human_audit_20260712_v2.zip` | `0d2df5810120789a4bb6f74ad9325ea268f4c30e63e0dff99505f4a359a30236` |

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
- The full release manifest has randomized opaque-pair order. Therefore, selecting its first 20 loaded rows per template does not reproduce the frozen generator contact-sheet sample. The portable bundle resolves this by selecting the first 20 source-order rows per template and mapping them through private `source_pair_id` values.

Decision:
- Use the packaged release manifest and private key, never source manifests containing unblinded side metadata.
- Use the exact portable 60-pair bundle and **All loaded pairs** for the registered R19 contact-sheet audit. Do not substitute the first 20 rows of the randomized full release manifest.
- Treat any image SHA256 mismatch or nonempty `unreviewed_pair_ids` list as an incomplete audit, not an accepted instrument.

Next actions:
- A PI/team reviewer opens the portable viewer, completes all 60 loaded R19 pairs, and attaches the exported failure JSON to the human-audit decision.
- Repeat with the R20 package for the independent confirmatory human sample.
