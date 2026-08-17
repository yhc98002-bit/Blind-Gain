import json, struct, os, collections
HF="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/checkpoints/m7/m7_virl_a1_real_seed1/global_step_100/actor/huggingface"
c=collections.Counter()
for f in ["model-00001-of-00002.safetensors","model-00002-of-00002.safetensors"]:
    with open(os.path.join(HF,f),"rb") as fh:
        n=struct.unpack("<Q",fh.read(8))[0]; hdr=json.loads(fh.read(n))
    for k,v in hdr.items():
        if k=="__metadata__": continue
        c[v["dtype"]]+=1
print("tensor_dtypes", dict(c))
cfg=json.load(open(os.path.join(HF,"config.json")))
print("config_torch_dtype", cfg.get("torch_dtype"))
print("config_keys_sample", sorted(cfg.keys()))
print("gen_cfg", json.load(open(os.path.join(HF,"generation_config.json"))))
