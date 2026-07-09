from pathlib import Path


def test_sdpa_patch_diff_documents_env_switch():
    patch = Path("docs/easyr1_sdpa_patch.diff").read_text(encoding="utf-8")
    assert "EASYR1_ATTN_IMPLEMENTATION" in patch
    assert 'os.getenv("EASYR1_ATTN_IMPLEMENTATION", "flash_attention_2")' in patch
