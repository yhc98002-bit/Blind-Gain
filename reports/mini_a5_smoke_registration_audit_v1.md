# Mini-A5 Smoke Registration Audit V1

Status:
- Registration marker status: `registered`.
- This marker authorizes at most one CP and one member smoke step; it authorizes zero main M6 steps.
- No scientific gate decision is made.

Evidence:
- Machine marker: `reports/mini_a5_smoke_registration_marker_v1.json`.
- Registration commit: `5e429b335dc4bf10e885bc1907d731d9e0a503f3`.
- Registration document SHA256: `c93bcb3e41e9a2ec4ac1df738e6b7fa025991f9038dfdab45ed073f430fec155`.
- EasyR1 worktree diff SHA256: `c12ca1eaddf11d13b5206834490d71179596af89c58d37741cc2f8624602766a`.
- Smoke config hashes: `{"cp": "3dfcd9d8f2a9f654d51a0441166820d7b06ca4cf083bff97f781a065c00e4014", "member": "f94f8b4426d11f9eb8f183640bfeeca8c6258801125477f759b46e488ef2e118"}`.

Checks:
| Check | Result |
| --- | --- |
| `registration_commit_is_head` | `pass` |
| `registration_commit_exists` | `pass` |
| `all_registered_artifacts_present` | `pass` |
| `document_contains_every_registered_hash` | `pass` |
| `document_registers_exact_commands` | `pass` |
| `document_authorizes_smoke_only` | `pass` |
| `registered_files_identical_to_commit` | `pass` |
| `advantage_audit_passed_31_checks` | `pass` |
| `step0_and_catch_audits_passed` | `pass` |
| `isolated_easyr1_revision_exact` | `pass` |
| `isolated_easyr1_diff_nonempty` | `pass` |

Decision:
- The launcher remains fail-closed unless this marker is committed and its registration commit is an ancestor of launch `HEAD`.
- Main M6 launch remains separately blocked after smoke completion.
