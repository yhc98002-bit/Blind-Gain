# Blind Gains Paper 1 Workspace

This directory is the live Paper-1 artifact pipeline. Result slots remain empty
until the corresponding registered machine artifact exists.

Contents:
- `outline.md`: section skeleton and claim discipline.
- `master_result_table.md`: registered result slots.
- `figure_registry.md`: figure inputs and scripts.
- `methods_appendix.md`: shared methods and reproducibility details.
- `data_card.md`: FlipTrack and corpus documentation.
- `contribution_nonoverlap.md`: Paper-1/Paper-2 scope boundary.

Required terminology:
- Use **caption-mediated accessibility**.
- Do not make information-superiority, anti-vision, or blind-training
  equivalence claims.

Maintenance contract:
- Populate a result only from its registered, hash-pinned machine artifact.
- Preserve pending slots until every required input exists.
- Version pipeline audits and generated figures; never overwrite an earlier
  report or rendering.
- Keep R19 and R20 separate and show overall R19 with every template result.
