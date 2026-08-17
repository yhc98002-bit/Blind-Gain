#!/usr/bin/env python3
"""Allow the one corpus-required deviation from the geo3k recipe.

build_m7_configs.py asserts each generated arm matches the geo3k pilot template
in `algorithm` and `worker`, to stop silent recipe drift between arms. That guard
is worth keeping. But ViRL39K legitimately needs worker.rollout.limit_images = 8
(geo3k is single-image and uses 0), so the guard now fires on a change that is
required for the run to work at all.

Rather than weaken the guard, exempt exactly this key and nothing else, and keep
comparing every other field. All eight arms still receive the identical value, so
arm-to-arm parity -- the property the guard actually protects -- is untouched.
"""
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
p = ROOT / "scripts/build_m7_configs.py"
t = p.read_text()

if "SANCTIONED_DEVIATIONS" in t:
    print("already patched")
    raise SystemExit(0)

old = '''    hyper_keys = ("algorithm", "worker")
    baseline = yaml.safe_load((ROOT / "configs/train" / ARMS["a1_real"][0]).read_text(encoding="utf-8"))
    for record in written:
        config = yaml.safe_load((ROOT / record["config"]).read_text(encoding="utf-8"))
        for key in hyper_keys:
            if json.dumps(config[key], sort_keys=True) != json.dumps(baseline[key], sort_keys=True):
                raise AssertionError(f"arm {record['arm']} deviates from the matched recipe in {key}")'''

new = '''    hyper_keys = ("algorithm", "worker")
    # ViRL39K carries up to 8 images per prompt; geo3k is single-image and uses 0.
    # This is the ONLY sanctioned deviation from the matched geo3k recipe, and all
    # eight arms receive the identical value, so arm-to-arm parity is preserved.
    SANCTIONED_DEVIATIONS = (("worker", "rollout", "limit_images"),)

    def _strip_sanctioned(blob, top):
        import copy as _copy
        out = _copy.deepcopy(blob)
        for path in SANCTIONED_DEVIATIONS:
            if path[0] != top:
                continue
            node = out
            for part in path[1:-1]:
                node = node.get(part) if isinstance(node, dict) else None
                if node is None:
                    break
            if isinstance(node, dict):
                node.pop(path[-1], None)
        return out

    baseline = yaml.safe_load((ROOT / "configs/train" / ARMS["a1_real"][0]).read_text(encoding="utf-8"))
    for record in written:
        config = yaml.safe_load((ROOT / record["config"]).read_text(encoding="utf-8"))
        for key in hyper_keys:
            got = json.dumps(_strip_sanctioned(config[key], key), sort_keys=True)
            want = json.dumps(_strip_sanctioned(baseline[key], key), sort_keys=True)
            if got != want:
                raise AssertionError(f"arm {record['arm']} deviates from the matched recipe in {key}")
        # arm-to-arm parity on the sanctioned key itself
        if config["worker"]["rollout"]["limit_images"] != 8:
            raise AssertionError(f"arm {record['arm']} has limit_images "
                                 f"{config['worker']['rollout']['limit_images']}, expected 8")'''

assert t.count(old) == 1, f"guard anchor {t.count(old)}"
p.write_text(t.replace(old, new, 1))
print("patched: guard now exempts worker.rollout.limit_images and pins it to 8")
