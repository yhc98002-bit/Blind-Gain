# Pilot Launch Blocked Probe V1

Status:
- `pass` for fail-closed behavior; this is not launch authorization and no optimizer step ran.

Evidence:
- Command: `bash scripts/launch_mech_pilot_arm.sh a1_real an12 0,1,2,3`.
- Exit code: `1`, produced by the authorization checker before any SSH or GPU probe.
- Machine artifact: `reports/pilot_launch_authorization_a1_real_20260712T084911Z.json`, SHA256 `0a9c10131cace686707226601c74dbf8155c06d517defa913be1f2a0f8c8fff9`.
- A1 training-run directories before/after: `0 / 0`.
- A1 checkpoint namespace before/after: `absent / absent`.
- The machine artifact reports `status=blocked`; its positive checks include exact ledger parsing, L13 not predeclared, matched arm configs, and an absent selected checkpoint namespace.

Problems:
- Expected blockers are L3 evidence, final L12 preregistration, human/two-PI approvals, reward spec v3, and preregistered config/data hashes.

Decision:
- Preserve the blocked artifact as the production launcher’s first end-to-end fail-closed probe.
- Do not test the authorized branch by fabricating approval files in the working repository; unit fixtures cover that branch without crossing the real gate.

Next actions:
- Re-run the same production launcher only after the genuine L3 and L12 artifacts exist.
