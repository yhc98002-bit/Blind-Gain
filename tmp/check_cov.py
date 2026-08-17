import json
from src.eval.conditioned_inputs import load_caption_map

need = set()
for line in open("data/virl39k_m7_heldout_v3.jsonl"):
    d = json.loads(line)
    need.update(d["metadata"]["image_sha256"])
cm = load_caption_map(["data/virl39k_caption_store_3b_main_v2.jsonl"])
print("unique heldout image sha256:", len(need))
print("caption map size:", len(cm))
print("covered:", len(need & set(cm)), "missing:", len(need - set(cm)))
