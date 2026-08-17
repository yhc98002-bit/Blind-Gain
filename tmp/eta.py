#!/usr/bin/env python3
import datetime as dt, json
now = dt.datetime(2026,7,30,13,28,22, tzinfo=dt.timezone.utc)

PLAIN_A1   = 28.40   # measured: arm1 mean of 95 non-checkpoint steps (min)
CK_A1      = 59.71   # measured: arm1 mean of 5 checkpoint steps (min)
CK_OVH_A1  = CK_A1 - PLAIN_A1               # 31.31 min to write 38.16 GiB
FULL_GIB, MODEL_GIB = 38.16, 7.59           # measured / measured-analogue
CK_OVH_MO  = CK_OVH_A1 * MODEL_GIB/FULL_GIB # ASSUMES write time ~ linear in bytes

print("arm1 measured: plain %.2f min, ckpt %.2f min, ckpt overhead %.2f min for %.2f GiB"
      % (PLAIN_A1, CK_A1, CK_OVH_A1, FULL_GIB))
print("model-only ckpt overhead ASSUMED %.2f min for %.2f GiB (linear-in-bytes)\n" % (CK_OVH_MO, MODEL_GIB))

arms = [
  # label, steps_done, per-step basis (min), basis note
  ("arm2 a2_gray    an12 4-7", 1, 26.26, "its OWN 1 measured step"),
  ("arm3 a2b_noimage an29 0-3", 1, 18.59, "its OWN 1 measured step"),
  ("arm4 a3_caption  an12 0-3", 0, PLAIN_A1, "arm1 plain-step mean (arm4 has NO measured step)"),
]
latest = None
for label, done, per, note in arms:
    rem = 100 - done
    ck_rem = len([s for s in (20,40,60,80,100) if s > done])
    total = (rem - ck_rem)*per + ck_rem*(per + CK_OVH_MO)
    eta = now + dt.timedelta(minutes=total)
    latest = eta if latest is None or eta > latest else latest
    print("%s  done=%3d rem=%3d (incl %d ckpt steps)  basis=%.2f min/step [%s]"
          % (label, done, rem, ck_rem, per, note))
    print("      remaining %.1f min = %.2f h  ->  step100 ETA %s\n"
          % (total, total/60, eta.strftime("%Y-%m-%dT%H:%MZ")))
print("arm1 a1_real     an12 0-3  ALREADY AT STEP 100 (2026-07-30T12:57:50Z, measured)")
print("=> ALL FOUR at step 100 when the slowest lands: %s (~%.1f h from now)"
      % (latest.strftime("%Y-%m-%dT%H:%MZ"), (latest-now).total_seconds()/3600))
print("\nDISK (measured where stated):")
print("  arm1 full-FSDP ckpt   : 40,970,253,322 B = 38.16 GiB each x5 = %.1f GiB  [MEASURED]" % (38.16*5))
print("  model-only analogue   : 8,147,620,485 B = 7.59 GiB           [MEASURED on a comparable HF export, NOT on an arm 2-4 ckpt]")
print("  arms 2-4 projected    : 3 arms x 5 x 7.59 GiB = %.1f GiB     [PROJECTION]" % (3*5*7.59))
