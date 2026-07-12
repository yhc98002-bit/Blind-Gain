# Blind Gains Human Audit Guide

## What This Task Is

You are **not evaluating a person**. You are also not deciding whether an answer-producing system is good or bad.

You are auditing a dataset. Each item contains two images, one shared question, and one answer for each image. The images are intended to differ in exactly the visual fact needed to answer the question. Your job is to decide whether that intended measurement is valid.

For every pair, make six independent Pass/Fail decisions. Do not decide whether the whole dataset is accepted; the PI will make that decision from the exported audit record.

## What You Receive

The portable R19 audit contains:

- 60 pairs total;
- 20 geometry pairs;
- 20 document/table pairs;
- 20 chart pairs;
- two full-resolution images per pair;
- the question and member-aligned answer for each image;
- six registered checks.

The two displayed answers should normally differ. Member order is randomized, so never assume the left image is source A or that the right image is source B.

## Review Procedure

For each pair:

1. Read the question.
2. Inspect both images at Fit view.
3. Use modest zoom or open the original image when needed.
4. Independently solve the question for the left image and then the right image.
5. Compare your readings with the displayed answers.
6. Compare the two images and decide all six checks below.
7. Add a concrete note for every Fail decision.
8. Move to the next pair only after all six checks have a value.

Use **Pass** only when the requirement is satisfied. Use **Fail** when it is violated or when reasonable inspection cannot resolve a material ambiguity. For uncertainty, explain what could not be verified in the note.

## The Six Decisions

### 1. Visual Necessity

Question: **Could the answer be known without seeing the image?**

Pass when:

- the question alone does not reveal either member's answer;
- the requested coordinate, cell content, or plotted value must be read visually;
- generic knowledge or wording is insufficient.

Fail when:

- the question text contains or strongly implies the answer;
- an identifier encodes the answer directly;
- the answer follows from a nonvisual template rule rather than the displayed content.

Ignore the answers shown by the audit viewer when making this decision. Imagine receiving only the question, without either image or the audit answer labels.

### 2. Single Answer-Changing Difference

Question: **Is the queried visual fact the only semantic difference that could change the answer?**

Pass when:

- the same question applies cleanly to both members;
- unrelated labels, values, legends, and layout stay fixed;
- only the target fact changes.

Fail when:

- another cell, point, label, legend mapping, axis, or unrelated value also changes;
- the pair differs in multiple independent facts;
- a layout change creates a second plausible reason for the answer to differ.

Pixel-perfect identity is not required. Natural rendering consequences count as one change: moving a chart point also moves its adjacent line segments; replacing a table code changes its glyph pixels; moving a labeled geometry point may move its label slightly.

### 3. Legibility Without Pop-Out

Question: **Can the relevant fact be read at normal full-resolution viewing without a cue that gives away the changed content?**

Pass when:

- the target label, code, coordinate, marker, or value is readable at normal size or modest zoom;
- the target is not hidden by overlap, clipping, or severe crowding;
- any navigation cue is symmetric across both members and identifies where to look without revealing the answer.

Fail when:

- the target requires extreme zoom, enhancement, or guessing;
- labels overlap or confusable characters cannot be resolved;
- the changed content alone has a unique glow, border, size, color, or edit seam;
- one member makes the target conspicuously easier to locate than the other.

For document pairs, matching row/column header outlines are acceptable navigation cues when they appear in both members and do not reveal the target cell's value.

### 4. Unambiguous Labels and Wording

Question: **Does the question identify one clear visual target with one clear reading?**

Pass when:

- the requested point label, row/column intersection, or starred series is unique;
- axes, ticks, legends, and headers support one interpretation;
- the question uses the same names shown in the image.

Fail when:

- a label is duplicated, missing, or attached to the wrong object;
- more than one series could be the “starred series”;
- row or column headers do not identify a unique cell;
- axis ticks or wording permit multiple reasonable answers.

### 5. Artifact Parity

Question: **Are both members equally clean and comparable?**

Pass when:

- resolution, sharpness, margins, rendering, and crop are comparable;
- neither member has a unique visual defect;
- the changed region looks naturally rendered in both members.

Fail when:

- only one member is blurred, compressed, clipped, shifted, or corrupted;
- one member has a visible edit boundary or inconsistent font rendering;
- metadata-like text, a filename, or another cue distinguishes member identity;
- one image is materially easier to read for reasons unrelated to the intended change.

Do not fail ordinary antialiasing differences confined to the legitimately changed glyph, point, or line segment.

### 6. Answer-Key Exactness

Question: **Does each displayed answer exactly match its corresponding image?**

Pass when:

- you independently read both images and both displayed answers are exact;
- signs, digits, letters, and character order all match.

Fail when:

- either answer belongs to the other member;
- a negative sign is missing;
- a two-character code has any wrong or transposed character;
- a plotted value or coordinate does not match the visual target.

Check confusable characters carefully, including `0/O`, `1/I`, `5/S`, and `8/B`.

## Template-Specific Reading

### Geometry

Find the exact point label named in the question and read its horizontal coordinate. Values left of the vertical axis are negative and values right of it are positive. The target point's x-position should change between members while unrelated points and labels remain fixed.

Fail the relevant check if the label cannot be uniquely attached to a point, the point is between ticks without a clear intended integer, or unrelated points also move.

### Document/Table

Find the named row and column headers, then read the two-character code at their intersection. Inspect every character exactly. The queried cell should change between members while other cells, headers, and layout stay fixed.

Fail the relevant check if the intersection is unclear, a character is unreadable, another cell changes, or the displayed key does not match the cell.

### Chart

Identify the series marked by the star, follow that series to the requested x-value, and read the y-value from the axis. The target point should change between members. Adjacent line segments moving with that point are a consequence of the same semantic change and are not an additional failure.

Fail the relevant check if the star could refer to multiple series, the x-position or y-tick is ambiguous, another series changes, or the displayed answer does not match the target value.

## Writing Failure Notes

Write one short, observable statement. Include the failed check, affected member, and concrete evidence.

Good notes:

- `answer_key_exact; member 2; displayed H7, target cell reads H1.`
- `legible_without_popout; both; point G7 label overlaps the y-axis at full resolution.`
- `single_answer_changing_difference; member comparison; an unrelated table cell also changes.`
- `artifact_parity; member 1; right edge is clipped while member 2 has a full margin.`

Avoid vague notes such as `looks bad`, `hard`, or `not sure`. State what you observed and why it affects a registered check.

## What Not to Judge

Do not judge:

- visual attractiveness;
- whether the task is interesting;
- whether you personally like the template;
- any aggregate score or external result;
- whether a failed pair should be repaired or regenerated.

Record the evidence only. Content changes, acceptance, and study interpretation are separate PI decisions.

## Completion and Export

The R19 audit is complete only when:

- progress shows `60/60 reviewed`;
- every pair has six explicit decisions;
- every failure has a useful note;
- the exported JSON has an empty `unreviewed_pair_ids` list.

Select **Export failures** and return the downloaded JSON unchanged. A zero-failure audit still needs an export proving that all 60 pairs were reviewed.

## Quick Reference

For each pair, ask:

1. Must I see the image?
2. Did only the queried fact change?
3. Is it readable without a giveaway cue?
4. Is there exactly one interpretation?
5. Are both members equally clean?
6. Are both displayed answers exact?

Then record Pass/Fail for all six, note any failure, and continue.
