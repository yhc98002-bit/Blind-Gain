# ViRL39K Fork Ruling

Status:
- The registered row that obtains is **strong source/category heterogeneity**.
- Registered consequence: **H-mixed becomes the headline; stratify.**
- This records the preregistered rule after M0 merged. It does not pool
  Geometry3K and ViRL39K or declare a scientific gate passed.

Evidence:
- Frozen sample: 4,096 unique ViRL39K items.
- Audit status: all 15 machine checks pass with zero score mismatches.
- Mean reward-opportunity `q_i`: real 0.5115, caption 0.4355, gray 0.4188,
  noise 0.4251, and no-image 0.4151.
- Caption is below real, but every zero-visual-bit condition remains
  substantial rather than near the Jeffreys floor.
- Category ranges are wide: real spans 0.2204 to 0.5687, caption spans 0.1745
  to 0.5832, and no-image spans 0.1693 to 0.4796.
- Tables/Diagrams/Charts show a large condition spread
  (real 0.5411, caption 0.3860, no-image 0.2609), while several non-visual
  categories retain high blind opportunity.

Registered fork exclusions:
| Row | Obtains | Reason |
| --- | --- | --- |
| caption q approximately real and zero-bit substantial | no | caption is materially below real overall |
| caption well below real and zero-bit near floor | no | zero-bit q is approximately 0.42, not near floor |
| strong source/category heterogeneity | **yes** | category and condition spreads are both substantial |
| captions exceed real | no | caption q is below real |
| gray materially differs from no-image | no | gray/no-image q differs by 0.0037 |

Decision:
- Stratify subsequent ViRL analyses by registered source/category.
- Treat corpus-level shortcut susceptibility as heterogeneous; do not infer a
  universal Geometry3K mechanism from the aggregate alone.

Artifacts:
- `reports/blind_solvability_virl39k_sample_v1.md`
- `reports/blind_solvability_virl39k_sample_v1.json`
- `reports/blind_solvability_virl39k_sample_v1_audited.md`
- `reports/blind_solvability_virl39k_sample_v1_audited.json`
