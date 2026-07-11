from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIGS = sorted((ROOT / "configs/eval").glob("vlmevalkit_l10_*_local_?b.json"))


def test_l10_configs_exist_and_share_one_decoding_contract() -> None:
    assert len(CONFIGS) == 4
    contracts = set()
    for path in CONFIGS:
        config = json.loads(path.read_text(encoding="utf-8"))
        assert len(config["model"]) == 1 and len(config["data"]) == 1
        model = next(iter(config["model"].values()))
        contracts.add(
            (
                model["min_pixels"],
                model["max_pixels"],
                model["max_new_tokens"],
                model["temperature"],
                model["top_p"],
                model["top_k"],
                model["do_sample"],
                model["system_prompt"],
            )
        )
        dataset_name = next(iter(config["data"]))
        assert (ROOT / "data/vlmevalkit" / f"{dataset_name}.tsv").is_file()
    assert len(contracts) == 1


def test_l10_configs_bind_dataset_specific_prompt_classes() -> None:
    for path in CONFIGS:
        config = json.loads(path.read_text(encoding="utf-8"))
        dataset = next(iter(config["data"].values()))
        expected = "MathVerse" if "mathverse" in path.name else "MMMUDataset"
        assert dataset["class"] == expected
