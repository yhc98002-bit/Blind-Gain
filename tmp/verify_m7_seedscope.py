#!/usr/bin/env python3
"""Independent verification of the regenerated M7 arm configs (does not reuse
build_m7_configs.py's own assertions)."""
import hashlib, json, subprocess
from pathlib import Path

R = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
BK = R / "tmp/m7_config_backup_pre_seedscope"
import yaml

ARMS = ["a1_real", "a2_gray", "a2b_noimage", "a3_caption"]
S1 = {a: R / f"configs/train/m7_virl_{a}_seed1_3b.yaml" for a in ARMS}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


print("=== CHECK 0: arm 1 configs byte-identical to pre-change backup ===")
for name in ["m7_virl_a1_real_seed1_3b.yaml", "m7_virl_a1_real_seed2_3b.yaml"]:
    new, old = R / "configs/train" / name, BK / name
    print(f"  {name}: {'IDENTICAL' if sha(new)==sha(old) else 'CHANGED'}  sha={sha(new)[:16]}")

print("\n=== CHECK 1: algorithm + worker blocks byte-identical across all four seed-1 arms ===")
raw = {}
for a in ARMS:
    txt = S1[a].read_text()
    doc = yaml.safe_load(txt)
    for block in ("algorithm", "worker"):
        raw[(a, block)] = hashlib.sha256(
            yaml.safe_dump(doc[block], sort_keys=True).encode()
        ).hexdigest()
for block in ("algorithm", "worker"):
    hs = {a: raw[(a, block)] for a in ARMS}
    uniq = set(hs.values())
    print(f"  {block}: {len(uniq)} distinct hash across 4 arms -> "
          f"{'PASS (identical)' if len(uniq)==1 else 'FAIL'}  {list(uniq)[0][:16]}")

print("\n=== CHECK 1b: same, across all EIGHT configs ===")
allc = sorted((R / "configs/train").glob("m7_virl_*_3b.yaml"))
for block in ("algorithm", "worker"):
    hs = {p.name: hashlib.sha256(yaml.safe_dump(yaml.safe_load(p.read_text())[block], sort_keys=True).encode()).hexdigest() for p in allc}
    uniq = set(hs.values())
    print(f"  {block}: n={len(hs)} distinct={len(uniq)} -> {'PASS' if len(uniq)==1 else 'FAIL'}")

print("\n=== CHECK 2: full leaf-level diff of each seed-1 arm vs arm 1 seed 1 ===")


def flat(d, pre=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flat(v, f"{pre}.{k}" if pre else str(k)))
    else:
        out[pre] = d
    return out


base = flat(yaml.safe_load(S1["a1_real"].read_text()))
ALLOWED_TRAINER = {"trainer.experiment_name", "trainer.save_checkpoint_path",
                   "trainer.project_name", "trainer.load_checkpoint_path",
                   "trainer.save_model_only"}
for a in ARMS[1:]:
    cur = flat(yaml.safe_load(S1[a].read_text()))
    keys = sorted(set(base) | set(cur))
    diffs = [k for k in keys if base.get(k, "<absent>") != cur.get(k, "<absent>")]
    tr = [k for k in diffs if k.startswith("trainer.")]
    nontr = [k for k in diffs if not k.startswith("trainer.")]
    print(f"  -- {a} vs a1_real (seed 1): {len(diffs)} differing leaves")
    print(f"     trainer diffs   : {tr}")
    print(f"     trainer subset of registered allow-list? "
          f"{'YES' if set(tr) <= ALLOWED_TRAINER else 'NO -> ' + str(set(tr)-ALLOWED_TRAINER)}")
    print(f"     non-trainer diffs: {nontr}")
    for k in nontr:
        print(f"        {k}: a1={base.get(k,'<absent>')!r} -> {a}={cur.get(k,'<absent>')!r}")

print("\n=== CHECK 2b: registered allow-list fields that in fact do NOT differ ===")
for a in ARMS[1:]:
    cur = flat(yaml.safe_load(S1[a].read_text()))
    same = [k for k in sorted(ALLOWED_TRAINER) if base.get(k) == cur.get(k)]
    print(f"  {a}: identical to arm1 despite being on the allow-list -> {same}")

print("\n=== CHECK 3: save_freq / max_steps / n_gpus_per_node / save_model_only / seed ===")
print(f"  {'arm':14} {'save_freq':>9} {'max_steps':>9} {'gpus':>5} {'save_model_only':>16} {'seed':>5} {'save_limit':>10}")
for a in ARMS:
    t = yaml.safe_load(S1[a].read_text())
    tr, da = t["trainer"], t["data"]
    print(f"  {a:14} {tr['save_freq']:>9} {tr['max_steps']:>9} {tr['n_gpus_per_node']:>5} "
          f"{str(tr['save_model_only']):>16} {da['seed']:>5} {tr['save_limit']:>10}")

print("\n=== CHECK 4: manifest agrees with on-disk config hashes ===")
man = json.loads((R / "reports/m7_arm_configs_v1.json").read_text())
ok = True
for rec in man["configs"]:
    p = R / rec["config"]
    disk = hashlib.sha256(p.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    match = disk == rec["config_sha256"]
    ok &= match
    if rec["seed"] == 1:
        print(f"  {rec['config'].split('/')[-1]:36} {rec['config_sha256'][:16]} "
              f"{'MATCH' if match else 'MISMATCH'}  exec_scope={rec['in_execution_scope']}")
print(f"  all 8 entries match on-disk sha256: {ok}")
print(f"  manifest.sanctioned_deviations = {man['sanctioned_deviations']}")
print(f"  manifest.execution_scope.seeds  = {man['execution_scope']['seeds']}")
print(f"  manifest.checkpoint_policy      = save_freq={man['checkpoint_policy']['save_freq']}, "
      f"arms={man['checkpoint_policy']['save_model_only_arms']}")

print("\n=== CHECK 5: running arm 1 effective_config untouched ===")
eff = R / "experiments/runs/m7_virl_a1_real_seed1_an12_20260728T102036Z/effective_config.yaml"
print(f"  {eff.name} sha={sha(eff)[:16]}  == configs/train arm1 seed1? {sha(eff)==sha(S1['a1_real'])}")
print(f"  mtime/perm: {subprocess.run(['ls','-l',str(eff)],capture_output=True,text=True).stdout.strip()}")
