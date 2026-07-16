from __future__ import annotations

import random

from PIL import ImageChops

from src.fliptrack.build_mini_a5_catch import CATCH_BUILDERS, CATCH_TEMPLATE_IDS


def test_catch_builders_preserve_answer_change_only_nuisance_and_use_heldout_ids() -> None:
    rng = random.Random(7)
    for index, builder in enumerate(CATCH_BUILDERS):
        row = builder(rng, index)
        assert row["template_id"] in CATCH_TEMPLATE_IDS
        assert row["answer"] == row["verifier_results"]["target_fact_a"]
        assert row["answer"] == row["verifier_results"]["target_fact_b"]
        difference = ImageChops.difference(row["image_a"], row["image_b"])
        assert difference.getbbox() is not None
        target_box = tuple(row["verifier_results"]["target_region_xyxy"])
        assert difference.crop(target_box).getbbox() is None
        assert "unused_base_question" not in row


def test_catch_template_ids_do_not_alias_training_template_ids() -> None:
    assert all("_catch_" in template for template in CATCH_TEMPLATE_IDS)
    assert len(CATCH_TEMPLATE_IDS) == len(set(CATCH_TEMPLATE_IDS)) == 3
