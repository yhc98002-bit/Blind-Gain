from __future__ import annotations

from src.eval.image_grid_consistency import image_grid_contract


def test_double_resize_fixture_reproduces_fourteen_feature_drift() -> None:
    result = image_grid_contract(20, 36)

    assert result["first_resize"] == [381, 686]
    assert result["second_resize"] == [381, 687]
    assert result["old_prompt_tokens"] == 336
    assert result["old_worker_features"] == 350
    assert result["old_feature_delta"] == 14
    assert result["old_grid_mismatch"] is True
    assert result["fixed_grid_mismatch"] is False
