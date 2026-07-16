from scripts.summarize_decon import build_filter_manifest


def test_filter_manifest_is_incomplete_and_ands_pending_layers() -> None:
    comparison = {
        "candidate_edges": [
            {
                "action": "remove",
                "train_record_id": "train-a",
                "eval_record_id": "eval-a",
                "eval_dataset": "mathvista",
            },
            {
                "action": "inspect",
                "train_record_id": "train-b",
                "eval_record_id": "eval-b",
                "eval_dataset": "mmstar",
            },
        ],
        "pending_layers": ["ocr_text_overlap"],
        "completed_layers": ["sha256"],
        "thresholds": {},
        "n_train_records": 2,
        "n_eval_records": 2,
        "template_disjointness_rule": "disjoint",
    }
    result = build_filter_manifest(comparison)
    assert result["complete"] is False
    assert result["remove_train_record_ids"] == ["train-a"]
    assert result["inspect_only_train_record_ids"] == ["train-b"]
    assert result["auto_remove_rule"] == (
        "drop a training record if any candidate edge has action=remove"
    )
