import json, sys, pathlib, collections
root = pathlib.Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
sys.path.insert(0, str(root))
from src.eval.layer1_blind import build_text_prompt, load_rows, score_predictions
from transformers import AutoProcessor

WITH_IMAGE = {
  "blink":          "experiments/runs/vlmevalkit_postprocess_l10_blink3b_canonicalv2_final_20260711T132325Z/rows.jsonl",
  "hallusionbench": "experiments/runs/vlmevalkit_postprocess_l10_hallusion3b_canonicalv2_final_20260711T132325Z/rows.jsonl",
  "mmvp":           "experiments/runs/vlmevalkit_postprocess_l10_mmvp3b_canonicalv2_final_20260711T132326Z/rows.jsonl",
  "mathverse":      "experiments/runs/vlmevalkit_postprocess_l10_mathverse3b_canonicalv2_v2_20260711T143923Z/rows.jsonl",
  "mmmu":           "experiments/runs/vlmevalkit_postprocess_l10_mmmu3b_v2_canonicalv2_20260711T145554Z/rows.jsonl",
}
model = str(root / "artifacts/models/Qwen/Qwen2.5-VL-7B-Instruct")
proc = AutoProcessor.from_pretrained(model, trust_remote_code=True, local_files_only=True)
tok = proc.tokenizer
SYS = "Return only the final answer wrapped exactly in <answer>...</answer>."
fail = 0
for dtype in ["blink","hallusionbench","mmvp","mathverse","mmmu"]:
    cfg = json.loads((root / f"configs/eval/layer1_blind_{ {'hallusionbench':'hallusion'}.get(dtype,dtype) }_7b.json").read_text())
    rows = load_rows(str(root / cfg["input_tsv"]), dtype)
    maxtok = 0; residual = 0
    for row in rows:
        p = build_text_prompt(row, dtype)
        if "<image" in p or "<|vision_" in p: residual += 1
        msgs = [{"role":"system","content":SYS},
                {"role":"user","content":[{"type":"text","text":p}]}]
        full = proc.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        if "<|vision_start|>" in full or "<|image_pad|>" in full:
            print("!! VISION TOKEN", dtype, row["index"]); fail += 1; break
        maxtok = max(maxtok, len(tok(full).input_ids))
    # gold / option_labels parity vs the with-image column
    wi = {}
    with open(root / WITH_IMAGE[dtype]) as fh:
        for line in fh:
            r = json.loads(line); wi[str(r["index"])] = r
    scored, metrics = score_predictions(rows, ["<answer>ZZZ</answer>"]*len(rows), dtype)
    mismatch_gold = mismatch_lab = missing = 0
    for r in scored:
        w = wi.get(r["index"])
        if w is None: missing += 1; continue
        if json.dumps(w["gold"], sort_keys=True) != json.dumps(r["gold"], sort_keys=True): mismatch_gold += 1
        if w["option_labels"] != r["option_labels"]: mismatch_lab += 1
    kd = collections.Counter(len(r["option_labels"]) for r in scored)
    contracts = collections.Counter(r["scoring_contract"] for r in scored)
    print(f"{dtype:15s} n={len(rows):5d} withimg_n={len(wi):5d} max_prompt_tok={maxtok:6d} "
          f"residual_image_str={residual} missing_idx={missing} gold_mismatch={mismatch_gold} labels_mismatch={mismatch_lab}")
    print(f"{'':15s} k_dist={dict(sorted(kd.items()))} contracts={dict(contracts)} cats={len(metrics['per_category'])}")
    fail += residual + missing + mismatch_gold + mismatch_lab
    if maxtok > 32768: print("!! prompt exceeds max_model_len"); fail += 1
print("PREFLIGHT", "FAIL" if fail else "OK")
