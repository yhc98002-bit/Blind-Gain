from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any


def build_caption_qa_rows(
    release_rows: Iterable[dict[str, Any]],
    key_rows: Iterable[dict[str, Any]],
    caption_rows: Iterable[dict[str, Any]],
    release_dir: str | Path,
) -> list[dict[str, Any]]:
    release_dir = Path(release_dir)
    keys_by_pair: dict[str, dict[str, Any]] = {}
    for key in key_rows:
        pair_id = str(key["pair_id"])
        if pair_id in keys_by_pair:
            raise ValueError(f"duplicate key pair_id: {pair_id}")
        keys_by_pair[pair_id] = key

    captions_by_hash: dict[str, dict[str, Any]] = {}
    for caption in caption_rows:
        digest = str(caption["image_sha256"])
        if digest in captions_by_hash:
            raise ValueError(f"duplicate caption image hash: {digest}")
        if not str(caption["caption"]).strip():
            raise ValueError(f"empty caption for image hash: {digest}")
        captions_by_hash[digest] = caption

    output: list[dict[str, Any]] = []
    release_hashes: set[str] = set()
    seen_pairs: set[str] = set()
    for release in release_rows:
        pair_id = str(release["pair_id"])
        if pair_id in seen_pairs:
            raise ValueError(f"duplicate release pair_id: {pair_id}")
        seen_pairs.add(pair_id)
        if pair_id not in keys_by_pair:
            raise ValueError(f"missing private key row for pair: {pair_id}")
        key = keys_by_pair[pair_id]
        release_members = {str(member["member_id"]): member for member in release["members"]}
        if len(release_members) != 2:
            raise ValueError(f"release pair must have two unique members: {pair_id}")
        keyed_sides = {str(member["source_side"]): member for member in key["members"]}
        if set(keyed_sides) != {"a", "b"}:
            raise ValueError(f"key must define source sides a and b exactly: {pair_id}")
        if {str(member["member_id"]) for member in key["members"]} != set(release_members):
            raise ValueError(f"release/key member mismatch for pair: {pair_id}")

        row: dict[str, Any] = {
            "schema_version": "blind-gains.fliptrack-caption-qa-input.v1",
            "pair_id": pair_id,
            "source_pair_id": str(key["source_pair_id"]),
            "question": str(release["question"]),
            "category": key.get("category"),
            "template_id": key.get("template_id"),
            "catch_twin_id": key.get("catch_twin_id"),
        }
        for side in ("a", "b"):
            key_member = keyed_sides[side]
            member_id = str(key_member["member_id"])
            release_member = release_members[member_id]
            image_hash = str(release_member["image_sha256"])
            if image_hash in release_hashes:
                raise ValueError(f"release image hash reused across members: {image_hash}")
            release_hashes.add(image_hash)
            if image_hash not in captions_by_hash:
                raise ValueError(f"missing caption for release image hash: {image_hash}")
            caption = captions_by_hash[image_hash]
            row.update(
                {
                    f"member_id_{side}": member_id,
                    f"answer_{side}": str(key_member["answer"]),
                    f"image_{side}_path": str(release_dir / str(release_member["image_path"])),
                    f"image_{side}_sha256": image_hash,
                    f"caption_{side}": str(caption["caption"]).strip(),
                }
            )
        output.append(row)

    extra_keys = set(keys_by_pair) - seen_pairs
    if extra_keys:
        raise ValueError(f"private key has {len(extra_keys)} extra pair rows")
    extra_captions = set(captions_by_hash) - release_hashes
    if extra_captions:
        raise ValueError(f"caption store has {len(extra_captions)} hashes outside the release")
    return output
