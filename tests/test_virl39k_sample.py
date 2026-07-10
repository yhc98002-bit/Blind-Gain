from __future__ import annotations

from collections import Counter
from pathlib import Path

from PIL import Image

from src.data.virl39k_sample import build_manifest_rows, stratified_sample


def _row(index: int, source: str, image_path: Path, answer: str = "1") -> dict:
    return {
        "qid": f"q{index:03d}",
        "question": "Read the diagram.",
        "answer": answer,
        "category": "geometry",
        "source": source,
        "pass_rate_32b_trained": 0.8,
        "pass_rate_7b_base": 0.3,
        "image_paths": [str(image_path)],
        "relative_image_paths": [image_path.name],
    }


def test_stratified_sample_is_exact_deterministic_and_proportional(tmp_path: Path) -> None:
    image = tmp_path / "image.png"
    Image.new("RGB", (8, 8), "white").save(image)
    rows = [_row(index, "large" if index < 15 else "small", image) for index in range(20)]
    first = stratified_sample(rows, sample_size=8, seed=17)
    second = stratified_sample(rows, sample_size=8, seed=17)
    assert [row["qid"] for row in first] == [row["qid"] for row in second]
    assert Counter(row["source"] for row in first) == {"large": 6, "small": 2}


def test_manifest_repairs_missing_markers_and_unboxes_answer(tmp_path: Path) -> None:
    image = tmp_path / "source.png"
    Image.new("RGB", (8, 8), "white").save(image)
    rows, stats = build_manifest_rows(
        [_row(0, "source", image, answer=r"\boxed{\frac{1}{2}}")],
        tmp_path / "image-index",
    )
    assert rows[0]["problem"].startswith("<image>\n")
    assert rows[0]["problem"].count("<image>") == 1
    assert rows[0]["answer"] == r"\frac{1}{2}"
    assert rows[0]["metadata"]["answer_raw"] == r"\boxed{\frac{1}{2}}"
    assert stats["marker_repaired_rows"] == 1
    links = list((tmp_path / "image-index").iterdir())
    assert len(links) == 1 and links[0].is_symlink()
