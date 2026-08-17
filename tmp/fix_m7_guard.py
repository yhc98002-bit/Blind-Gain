#!/usr/bin/env python3
"""Fix the M7 launcher's one-trainer-per-node guard, which never passes.

The guard runs, on the target node:

    pgrep -f 'verl.trainer.main' >/dev/null

The remote argv itself contains the literal string `verl.trainer.main`, so
pgrep -f matches its own wrapper and the guard reports a trainer on every node,
always. an12 was verified idle (0 compute apps, GUARD_CLEAR under a bracketed
pattern) while the guard still refused.

Bracketing the last character keeps the regex matching a real trainer's argv
while no longer matching the command line that carries the pattern.
"""
from pathlib import Path

p = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/"
         "scripts/launch_m7_virl_arm.sh")
t = p.read_text()

old = """if ssh "${NODE}" "pgrep -f 'verl.trainer.main' >/dev/null"; then"""
new = ("# Bracketing the final character stops pgrep matching the very command line\n"
       "# that carries the pattern: the remote argv holds \"verl.trainer.mai[n]\",\n"
       "# which the regex does not match, while a real trainer argv does.\n"
       """if ssh "${NODE}" "pgrep -f 'verl.trainer.mai[n]' >/dev/null"; then""")

if new.splitlines()[-1] in t:
    print("already patched")
    raise SystemExit(0)
if t.count(old) != 1:
    raise SystemExit(f"anchor count {t.count(old)}")
p.write_text(t.replace(old, new, 1))
print("patched: M7 colocation guard no longer self-matches")
