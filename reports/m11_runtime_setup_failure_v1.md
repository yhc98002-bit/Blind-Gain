# M11 Runtime Setup Failure V1

Status:
- Setup run `experiments/runs/m11_runtime_setup_login_20260713T102155Z`
  failed before any package download.
- No GPU was allocated and the active pilot environment was untouched.

Root cause:
- `python3 -m venv .venv-m11` returned exit code 1 because the login-node system
  Python installation has no `ensurepip` module.
- The repository user's executable
  `/HOME/paratera_xy/pxy1289/.local/bin/virtualenv` is available and is the
  established fallback used by other project setup scripts.

Failed artifact:
- Incomplete path: `.venv-m11`.
- Allocated size before deletion: 24,812 bytes (`du -sb`).
- Contents are incomplete virtual-environment scaffolding only; no wheel or model
  payload was downloaded.
- Classification: failed and superseded by a `virtualenv`-based retry. This file
  records the artifact before deletion.
- Deletion completed at `2026-07-13T10:23:09Z`; `.venv-m11` no longer existed
  immediately afterward.

Decision:
- Remove the 24,812-byte incomplete directory.
- Replace `python3 -m venv` with an explicit `virtualenv --python python3` command,
  add a launcher fixture, commit, and retry in a new immutable setup run.
