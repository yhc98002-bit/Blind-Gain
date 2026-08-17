import json, pathlib
root = pathlib.Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
# dataset_type -> (config basename stem, pinned TSV = the exact data_manifest of the with-image run)
BENCH = {
    "blink":         ("blink",     "data/vlmevalkit/BLINK_LOCAL.tsv"),
    "hallusionbench":("hallusion", "data/vlmevalkit/HallusionBench_LOCAL_V2.tsv"),
    "mmvp":          ("mmvp",      "data/vlmevalkit/MMVP_LOCAL_V2.tsv"),
    "mathverse":     ("mathverse", "data/vlmevalkit/MathVerse_LOCAL.tsv"),
    "mmmu":          ("mmmu",      "data/vlmevalkit/MMMU_LOCAL_V2.tsv"),
}
MODELS = {
    "3b": "artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct",
    "7b": "artifacts/models/Qwen/Qwen2.5-VL-7B-Instruct",
}
written = []
for dtype, (stem, tsv) in BENCH.items():
    assert (root / tsv).is_file(), tsv
    for scale, model in MODELS.items():
        cfg = {
            "dataset_type": dtype,
            "input_tsv": tsv,
            "model_path": model,
            # locked decode contract, byte-identical to the MMStar/MathVista blind template
            "system_prompt": "Return only the final answer wrapped exactly in <answer>...</answer>.",
            "max_new_tokens": 256,
            "max_model_len": 32768,
            "gpu_memory_utilization": 0.85,
            "seed": 20260710,
        }
        out = root / f"configs/eval/layer1_blind_{stem}_{scale}.json"
        out.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        written.append(str(out.relative_to(root)))
for w in written: print(w)
