# Generated Artifact Manifests

Generated datasets, predictions, captions, checkpoints, and run outputs remain outside Git. Their checksums are tracked here so a local artifact can be identified without committing it.

The historical files named `*_scored.jsonl` contain artifact-gate metadata but no `prediction_a` or `prediction_b` fields. They must never be passed to the QA metric aggregator. They are retained locally only for provenance and are no longer tracked by Git.

Verify locally available historical files with:

```bash
sha256sum -c experiments/manifests/generated_data.sha256
```
