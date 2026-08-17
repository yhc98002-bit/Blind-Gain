import json, os, collections, struct
HF = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/checkpoints/m7/m7_virl_a1_real_seed1/global_step_100/actor/huggingface"

idx = json.load(open(os.path.join(HF, "model.safetensors.index.json")))
wm = idx["weight_map"]
print("INDEX_PARSES_OK True")
print("total_size", idx["metadata"]["total_size"])
print("weight_entries", len(wm))
print("MINI_A5_REF entries=825 total_size=8131575808")
print("MATCH_entries", len(wm) == 825)
print("MATCH_total_size", idx["metadata"]["total_size"] == 8131575808)
print("shard_files", sorted(set(wm.values())))
c = collections.Counter(wm.values())
for k in sorted(c): print("  entries_in", k, c[k])

cfg = json.load(open(os.path.join(HF, "config.json")))
print("architectures", cfg.get("architectures"))
print("ARCH_OK", cfg.get("architectures") == ["Qwen2_5_VLForConditionalGeneration"])
print("model_type", cfg.get("model_type"), "torch_dtype", cfg.get("torch_dtype") or cfg.get("dtype"))

tot = 0
for f in sorted(set(wm.values())):
    p = os.path.join(HF, f)
    ex = os.path.exists(p); sz = os.path.getsize(p) if ex else -1
    tot += sz
    # parse safetensors header
    with open(p, "rb") as fh:
        n = struct.unpack("<Q", fh.read(8))[0]
        hdr = json.loads(fh.read(n))
    keys = [k for k in hdr if k != "__metadata__"]
    maxend = max(hdr[k]["data_offsets"][1] for k in keys)
    print(f"shard {f} exists={ex} bytes={sz} header_tensors={len(keys)} payload_end={maxend} expected_file_len={8+n+maxend} len_ok={8+n+maxend==sz}")
print("sum_shard_bytes", tot)

# cross-check: does every index entry exist in the shard it claims?
present = {}
for f in sorted(set(wm.values())):
    with open(os.path.join(HF, f), "rb") as fh:
        n = struct.unpack("<Q", fh.read(8))[0]
        hdr = json.loads(fh.read(n))
    present[f] = {k for k in hdr if k != "__metadata__"}
bad = [k for k, f in wm.items() if k not in present[f]]
print("index_entries_missing_from_shards", len(bad), bad[:5])
extra = sum(len(v) for v in present.values()) - len(wm)
print("shard_tensors_not_in_index", extra)

# sum of tensor nbytes
DT = {"F32":4,"F16":2,"BF16":2,"I64":8,"I32":4,"I8":1,"U8":1,"BOOL":1,"F64":8,"F8_E4M3":1,"F8_E5M2":1}
nb = 0
for f in sorted(set(wm.values())):
    with open(os.path.join(HF, f), "rb") as fh:
        n = struct.unpack("<Q", fh.read(8))[0]
        hdr = json.loads(fh.read(n))
    for k, v in hdr.items():
        if k == "__metadata__": continue
        nb += v["data_offsets"][1] - v["data_offsets"][0]
print("sum_tensor_payload_bytes", nb, "equals_total_size", nb == idx["metadata"]["total_size"])
