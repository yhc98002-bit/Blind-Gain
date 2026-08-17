#!/bin/bash
R=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd $R
python3 - <<'PY'
import json,os,datetime as dt,statistics
now=dt.datetime.now(dt.timezone.utc)
arms=[("arm1 a1_real   (DONE, ref)","m7_virl_a1_real_seed1","2026-07-28T10:20:36Z","an12 0-3"),
      ("arm2 a2_gray   (live)","m7_virl_a2_gray_seed1","2026-07-30T12:18:03Z","an12 4-7"),
      ("arm3 a2b_noimg (live)","m7_virl_a2b_noimage_seed1","2026-07-30T12:18:34Z","an29 0-3"),
      ("arm4 a3_caption(live)","m7_virl_a3_caption_seed1","2026-07-30T13:13:11Z","an12 0-3")]
print("now =",now.strftime("%Y-%m-%dT%H:%M:%SZ"))
for label,name,start,place in arms:
    p="checkpoints/m7/%s/experiment_log.jsonl"%name
    st=dt.datetime.strptime(start,"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    el=(now-st).total_seconds()/60
    if not os.path.exists(p):
        print("%-26s %-9s elapsed=%6.1f min  NO experiment_log.jsonl"%(label,place,el)); continue
    rows=[json.loads(l) for l in open(p) if l.strip()]
    real=[r for r in rows if r.get("timing_s",{}).get("step")]
    print("%-26s %-9s elapsed=%6.1f min  rows=%d  completed_real_steps=%d  last_step=%s"%(
        label,place,el,len(rows),len(real),rows[-1].get("step") if rows else None))
    if real:
        vals=[r["timing_s"]["step"] for r in real]
        print("      step_min: n=%d mean=%.2f median=%.2f min=%.2f max=%.2f  last3=%s"%(
            len(vals),statistics.mean(vals)/60,statistics.median(vals)/60,min(vals)/60,max(vals)/60,
            [round(v/60,2) for v in vals[-3:]]))
PY
