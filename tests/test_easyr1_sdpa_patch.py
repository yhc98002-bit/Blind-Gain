from pathlib import Path

import yaml


def test_sdpa_patch_diff_documents_env_switch():
    patch = Path("docs/easyr1_sdpa_patch.diff").read_text(encoding="utf-8")
    assert "EASYR1_ATTN_IMPLEMENTATION" in patch
    assert 'os.getenv("EASYR1_ATTN_IMPLEMENTATION", "flash_attention_2")' in patch


def test_sdpa_anchor_disables_flash_attn_only_padding_free_path():
    config = yaml.safe_load(Path("configs/train/anchor_a0_recipe_3b_geo3k.yaml").read_text(encoding="utf-8"))
    actor_source = Path("artifacts/repos/EasyR1/verl/workers/actor/dp_actor.py").read_text(encoding="utf-8")

    assert config["worker"]["actor"]["padding_free"] is False
    assert config["worker"]["ref"]["padding_free"] is False
    assert "from flash_attn.bert_padding import" in actor_source
    assert "if self.config.padding_free:" in actor_source
    assert "unpad_input(" in actor_source
