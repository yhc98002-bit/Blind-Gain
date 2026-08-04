# Blind Gains Support-Expansion Candidate Review Guide

## What This Task Is

You are **not evaluating a person**, and you are not deciding whether a training method is good or bad.

You are reviewing 24 individual test items. Each one is a geo3k geometry question where the frozen base model produced **0 correct answers in 16 samples** under the arm's input condition, and **0 correct answers in 64 additional registered draws** (0/80 total), while the RL-trained arm's step-100 greedy answer is recorded correct. The machine pipeline can only call these *high-confidence support-expansion candidates*; it cannot tell whether the trained answer is a real solve. Your judgment is that missing step.

The registered language lock applies: nothing in this review permits a causal capability claim. You record per-item evidence; the PI folds it into the readout.

## What You Receive

- 24 items: A1 real 16, A2 gray 1, A2b no-image 5, A3 caption 2.
- A2b's five items matter most: that arm trained with **no image input at all**, so its candidates are the qualitative window into what image-free training installed.
- For each item: the question, the full-resolution image, the gold answer, the trained arm's step-100 answer (with its full response text), the base's step-0 greedy answer, and all 16 base sampled responses.
- `support_expansion_viewer.html` — a static page with every item; no setup needed.
- `response_sheet.csv` — one row per item, identity columns pre-filled.

Expected time: about 30 minutes (roughly 70 seconds per item).

## The Two Decisions

For each item, record exactly two values in `response_sheet.csv`, plus a note when required.

### 1. `trained_answer_verdict`

Question: **Is the trained arm's correct answer a genuine solve, a guess, or an artifact?**

Read the full step-100 response, then choose one:

- `genuine_solve` — the response contains a derivation that actually reaches the gold answer from facts stated in the question or read from the image. The reasoning need not be elegant, but the answer must follow from it.
- `guess` — the final answer is correct but not supported: the derivation is wrong or absent and the correct number appears anyway, or the response pattern-matches to a common default that happens to be right.
- `artifact` — the recorded correctness is an accident of measurement: the extracted answer matches gold only through parsing or normalization quirks, the gold answer is itself wrong for the image, or the question admits the answer without any visual or stated fact.
- `unclear` — reasonable inspection cannot distinguish the above. Say what could not be resolved in the note.

Use the 16 base sampled responses as context, not as a verdict input: they establish that the base's sampled support did not contain this answer. Noticing that several base samples attempt the same (wrong) route can help you judge whether the trained response is a real derivation or a sharpened guess.

### 2. `item_legible`

Question: **Is the item itself well-posed?**

- `pass` — the image is readable at normal size or modest zoom, the question identifies one clear target, and the gold answer is correct for the image.
- `fail` — the image is unreadable or ambiguous, the question is unanswerable or admits multiple reasonable answers, or the gold answer does not match the image.

Judge legibility independently of the verdict: an item can be `fail` legible and still have a `genuine_solve` response, and vice versa.

## Notes

Write one short, observable sentence in the `note` column whenever:

- `trained_answer_verdict` is anything other than `genuine_solve`, or
- `item_legible` is `fail`.

Good notes:

- `guess; final answer 48 appears after an incorrect similar-triangles setup that yields 24.`
- `artifact; gold is 13 but the marked segment in the image reads 12.`
- `item_legible fail; the angle labels overlap and cannot be attached to vertices.`

Avoid vague notes such as `looks wrong` or `not sure`. Notes for `genuine_solve` + `pass` items are welcome but optional.

## Review Procedure

1. Open `support_expansion_viewer.html`; work through the items in the order shown.
2. Read the question and inspect the image (click it for full resolution).
3. Solve or estimate the answer yourself when feasible.
4. Read the trained step-100 response in full and decide `trained_answer_verdict`.
5. Decide `item_legible`.
6. Fill the item's row in `response_sheet.csv` and add a note if required.
7. Move on only when both columns have a value.

## What Not to Judge

- Whether support expansion "really" happened mechanistically — that is a PI interpretation of the pooled record.
- Whether the arms rank correctly or any aggregate score.
- Whether the item should be repaired, reweighted, or excluded.
- Visual attractiveness of images or elegance of model prose.

## Completion

The review is complete only when all 24 rows of `response_sheet.csv` have both `trained_answer_verdict` and `item_legible` filled, and every non-`genuine_solve` / `fail` row carries a note. Return the completed CSV unchanged in structure — do not add, remove, or reorder rows.
