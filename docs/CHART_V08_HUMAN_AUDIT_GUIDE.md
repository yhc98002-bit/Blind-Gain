# Chart V08 Human Audit Guide

## Scope

This is a dataset audit, not a model evaluation. The package contains 100 frozen
calibration pairs: 50 legend-target flips and 50 point-value flips. Review every
loaded pair. Do not use or request model-performance results while auditing.

The chart-v08 construct is intended to require two visual hops:

1. Find the black star beside one legend entry and identify that series using its
   color, line style, and marker.
2. Follow that series to the x-coordinate named in the question and read its value.

No circle, highlight, or arrow should point to the queried plot point.

## Procedure

1. Use the v08 viewer mode. It fixes each image at 700 x 450 pixels and mechanically
   disables its zoom and full-resolution controls.
2. Read the question and independently solve member 1 and member 2.
3. Compare your readings with the displayed member-aligned answers.
4. Record Pass or Fail for all six standard checks and both v08 ratings.
5. Add a concrete note for every failure.
6. Export only after all 100 pairs have eight explicit decisions.

## Six Checks

### 1. Visual Necessity

Pass only if the answer cannot be inferred from the question alone and the image
must be inspected.

### 2. Single Answer-Changing Difference

For a legend-target flip, the curves must remain identical and only the star's
legend association may change. For a point-value flip, the starred legend entry
must stay fixed and only one value on that series, with its incident line segments,
may change.

### 3. Legibility Without Pop-Out

Pass only if the star, legend identity, requested x-coordinate, series path, and
y-value are readable in the fixed 700 x 450 rendering. Fail any circle, highlight, or arrow
on the queried plot point.

### 4. Unambiguous Labels and Wording

Pass only if exactly one legend entry is starred, the series remains identifiable
through crossings, and the requested x and y readings have one interpretation.

### 5. Artifact Parity

Pass only if both members have comparable sharpness, crop, spacing, line rendering,
and marker visibility. Fail member-specific clipping, corruption, or a unique
rendering artifact.

### 6. Answer-Key Exactness

Pass only if each displayed answer exactly equals the independently read value for
that member.

## Additional Construct Checks

- Distinguish every series by line style and marker, not color alone.
- Fail if a crossing makes the starred series impossible to trace at normal size.
- Fail if the black star could refer to more than one legend entry.
- Fail if any text inaccurately describes what the star marks.
- Do not treat ordinary antialiasing around the intended changed element as an
  artifact by itself.

## Two V08 Ratings

### 7. No-Zoom Correct

Pass only if both member answers can be obtained from the fixed 700 x 450 rendering.
Do not use browser zoom, operating-system magnification, screenshots, or image export.

### 8. Series Unambiguous

Pass only if the starred legend entry maps to exactly one series and that series can
be followed through every crossing needed to answer the question. Color alone is not
sufficient; line style and marker must preserve the identity.

The exported JSON is evidence for PI review. It does not itself accept the template.
