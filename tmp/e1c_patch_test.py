import pathlib
p = pathlib.Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/tests/test_layer1_blind.py")
s = p.read_text(encoding="utf-8")
assert "assert len(configs) == 4" in s
s = s.replace("assert len(configs) == 4", "assert len(configs) == 14", 1)

extra = '''

def test_blink_and_mmvp_reuse_the_image_mcq_option_block_builder() -> None:
    row = {
        "index": 7,
        "question": "Which image matches?",
        "answer": "A",
        "A": "first",
        "B": "second",
    }
    expected = (
        "Question: Which image matches?\\n"
        "Options:\\n"
        "A. first\\n"
        "B. second\\n"
        "Please select the correct answer from the options above. \\n"
    )
    for dataset_type in ("blink", "mmvp"):
        prompt = build_text_prompt(row, dataset_type)
        assert prompt == expected
        assert "<image>" not in prompt and "<|vision_" not in prompt


def test_hallusionbench_and_mathverse_keep_the_question_verbatim() -> None:
    row = {"question": "Is the left circle larger than the right circle?"}
    for dataset_type in ("hallusionbench", "mathverse"):
        assert build_text_prompt(row, dataset_type) == row["question"]


def test_mmmu_blind_prompt_consumes_image_markers_like_split_mmmu() -> None:
    # MMMUDataset.build_prompt runs split_MMMU, which removes "<image N>" from the
    # text as it interleaves real images; the blind mirror must delete them too.
    row = {
        "index": 9,
        "question": "Refer to <image 1> and <image 2>. What is the missing amount?",
        "answer": "B",
        "A": "ten",
        "B": "see <image 3>",
    }
    prompt = build_text_prompt(row, "mmmu")
    assert "<image" not in prompt
    assert prompt == (
        "Question: Refer to  and . What is the missing amount?\\n"
        "Options:\\n"
        "A. ten\\n"
        "B. see \\n"
        "Please select the correct answer from the options above. \\n"
    )


def test_mmstar_keeps_image_markers_because_image_mcq_does_not_split_them() -> None:
    row = {"index": 3, "question": "Look at <image 1>.", "answer": "A", "A": "yes"}
    assert "<image 1>" in build_text_prompt(row, "mmstar")


def test_mixed_format_blind_scoring_routes_per_item_not_per_benchmark() -> None:
    rows = [
        {"index": 1, "question": "Q1", "answer": "B", "A": "x", "B": "y", "category": "geometry"},
        {"index": 2, "question": "Q2", "answer": "11.8", "category": "geometry"},
    ]
    scored, _ = score_predictions(rows, ["<answer>B</answer>", "<answer>11.8</answer>"], "mathverse")
    assert scored[0]["scoring_contract"] == "multiple_choice_final_span"
    assert scored[0]["option_labels"] == ["A", "B"]
    assert scored[1]["scoring_contract"] == "open_final_span"
    assert scored[1]["option_labels"] == []
    assert all(record["category"] == "geometry" for record in scored)


def test_unsupported_blind_dataset_type_still_raises() -> None:
    import pytest

    with pytest.raises(ValueError):
        build_text_prompt({"question": "Q"}, "not_a_benchmark")
'''
s = s.rstrip("\n") + "\n" + extra
p.write_text(s, encoding="utf-8")
print("patched tests")
