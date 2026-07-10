import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_vlmevalkit_smoke_locks_greedy_decoding_and_local_model() -> None:
    config = json.loads((ROOT / "configs/eval/vlmevalkit_p1_2_smoke.json").read_text(encoding="utf-8"))
    model = config["model"]["BG-Qwen2.5-VL-3B-Greedy"]
    assert model["temperature"] == 0.0
    assert model["top_p"] == 1.0
    assert model["top_k"] == 1
    assert model["do_sample"] is False
    assert model["use_vllm"] is True
    assert "<answer>...</answer>" in model["system_prompt"]
    assert Path(model["model_path"]).is_dir()
    assert config["data"] == {"MMStar_MINI": {"class": "ImageMCQDataset", "dataset": "MMStar_MINI"}}
