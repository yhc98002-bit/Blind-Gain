import json, sys
need = ["q_i", "p_i_jeffreys", "sample_correct_count", "greedy_canonical_correct"]
for d in [l.strip() for l in open("tmp/m7_step0_run_dirs.txt") if l.strip()]:
    p = f"{d}/per_item.jsonl"
    try:
        rows = [json.loads(l) for l in open(p)]
    except FileNotFoundError:
        print(d, "NO OUTPUT"); continue
    if not rows:
        print(d, "EMPTY"); continue
    r = rows[0]
    missing = [k for k in need if k not in r]
    print(f"{d.split('/')[-1]}  rows={len(rows)}  missing={missing or 'none'}  "
          f"cond={r.get('condition')}  src_sha={str(r.get('source_manifest_sha256'))[:12]}  "
          f"split={r.get('split')}  q_i={r.get('q_i')}  p_i={r.get('p_i_jeffreys')}  "
          f"c={r.get('sample_correct_count')}  greedy={r.get('greedy_canonical_correct')}  "
          f"n_img_sha={len(r.get('image_sha256') or [])}")
