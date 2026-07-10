# FlipTrack R19 Exact-Package Evaluation

Status:
- Automated package evaluation passes the registered numerical gates on all 1,200 pairs; final human acceptance is still pending.
- Qwen2.5-VL-3B real-image pair accuracy is 0.5617 and Qwen2.5-VL-7B reaches 0.8092.
- Caption-only pair accuracy is 0.0125 at 3B and 0.0208 at 7B. Gray and pair-shared-noise pair accuracy are 0 for both model sizes, with collapse rate 1.0.
- Do not call caption signal zero: the document template rises significantly from 0.0100 to 0.0600 under caption-only QA.

Evidence:
- Machine summary: `reports/fliptrack_v02r19_exact_package.json`, SHA256 `5056eb2be0c97793dedb4c9f87ad75b817ed727dd85239beec5c2b1be9cc860a`.
- Release manifest: `data/fliptrack_v02r19_artifact_expanded/manifest.jsonl`, SHA256 `62553d701eb3e949910110057b65ab4e1146c602d21936268818fd1725b1b427`.
- Leakage linter: `reports/fliptrack_v02r19_lint.json`, `status=true`.
- Grouped attackers: `reports/artifact_gate_v02_r19.json`, `status=true`.
- Every cell uses the same opaque packaged members and private member-ID answer mapping; independent mapping audit found zero side/key errors.
- Full repository regression suite: 166 tests passed in 297.45 seconds after the final adapters, aggregators, and comparison tooling were added.

Exact-package metrics:

| Model | Mode | Pair acc | Strict pair | Member acc | Collapse | Format valid | Pair 95% CI |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 3B | real | 0.5617 | 0.3717 | 0.7129 | 0.0958 | 0.8475 | [0.5333, 0.5892] |
| 7B | real | 0.8092 | 0.8067 | 0.8900 | 0.0167 | 0.9988 | [0.7867, 0.8317] |
| 3B | caption | 0.0125 | 0.0125 | 0.0954 | 0.4392 | 1.0000 | [0.0067, 0.0192] |
| 7B | caption | 0.0208 | 0.0208 | 0.0954 | 0.3817 | 0.9992 | [0.0133, 0.0292] |
| 3B | gray | 0.0000 | 0.0000 | 0.0854 | 1.0000 | 1.0000 | [0, 0] |
| 7B | gray | 0.0000 | 0.0000 | 0.0158 | 1.0000 | 1.0000 | [0, 0] |
| 3B | noise | 0.0000 | 0.0000 | 0.0900 | 1.0000 | 1.0000 | [0, 0] |
| 7B | noise | 0.0000 | 0.0000 | 0.0604 | 1.0000 | 1.0000 | [0, 0] |

Per-template scale control:

| Template | 3B real | 7B real | Real delta | 3B caption | 7B caption | Caption delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Document | 0.8667 | 0.9933 | +0.1267 | 0.0100 | 0.0600 | +0.0500 |
| Geometry | 0.4717 | 0.7850 | +0.3133 | 0.0200 | 0.0083 | -0.0117 |
| Chart | 0.4367 | 0.6733 | +0.2367 | 0.0000 | 0.0067 | +0.0067 |

Paired tests:
- Overall real-image scale gain is +0.2475: 354 pairs improve and 57 regress; McNemar `p=1.84e-53`.
- Overall caption-only change is +0.0083: 24 pairs improve and 14 regress; McNemar `p=0.1433`.
- Document caption-only change is significant: 17 improve and 2 regress; McNemar `p=0.000729`. It remains far below the 0.15 ceiling and the 0.9933 real-image score, but this is partial caption compressibility.
- Geometry caption performance decreases with scale; chart increases by only two pairs and is not significant (`p=0.5`).

Problems:
- The 3B document format-valid rate is 0.4483, making strict document pair accuracy 0.1800 despite final-answer pair accuracy 0.8667. Final and strict metrics must remain separate.
- The qualitative Control-B phrase "caption does not rise in parallel" has no preregistered ratio threshold. The package passes the explicit 0.15 ceiling, but the document trend prevents a clean claim that caption scale is flat for every template.
- Automated gates cannot establish wording naturalness, visual legibility, or semantic uniqueness; `reports/fliptrack_v02r19_human_audit.md` remains incomplete.

Decision:
- Retain R19 as the sole automated freeze candidate. The exact package strongly separates real pixels from gray/noise/caption conditions and scales visually from 3B to 7B.
- Treat the document caption rise as a disclosed caveat, not as zero leakage and not as a post-hoc reason to alter the frozen package.
- Do not declare final scientific freeze or begin a human-informed repair batch until the representative audit is recorded.

Next actions:
- PI/team completes the three-template table in `reports/fliptrack_v02r19_human_audit.md` and identifies any failed pair IDs.
- If accepted, record approval and freeze hashes. If rejected, preserve R19 and create a separately versioned repair batch tied to the stated human failure mode.
