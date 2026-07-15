#!/usr/bin/env python3
"""Build a portable, contact-sheet-aligned FlipTrack human-audit bundle."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tempfile
from typing import Any, Iterable
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


JsonRow = dict[str, Any]
_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[JsonRow]:
    rows: list[JsonRow] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} must contain a JSON object")
            rows.append(value)
    if not rows:
        raise ValueError(f"{path} contains no JSONL rows")
    return rows


def _required_text(row: JsonRow, field: str, context: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context} has no nonempty {field}")
    return value


def _unique_index(rows: Iterable[JsonRow], field: str, label: str) -> dict[str, JsonRow]:
    result: dict[str, JsonRow] = {}
    for row in rows:
        key = _required_text(row, field, label)
        if key in result:
            raise ValueError(f"duplicate {label} {field}: {key}")
        result[key] = row
    return result


def select_contact_sheet_rows(
    source_rows: list[JsonRow],
    release_rows: list[JsonRow],
    key_rows: list[JsonRow],
    pairs_per_template: int,
) -> tuple[list[JsonRow], list[JsonRow], Counter[str]]:
    """Select source-order rows, then map them to opaque release IDs via the private key."""
    if pairs_per_template <= 0:
        raise ValueError("pairs_per_template must be positive")

    release_by_pair = _unique_index(release_rows, "pair_id", "release")
    key_by_source = _unique_index(key_rows, "source_pair_id", "answer-key")
    seen_source_ids: set[str] = set()
    selected_release: list[JsonRow] = []
    selected_keys: list[JsonRow] = []
    counts: Counter[str] = Counter()

    for source in source_rows:
        source_pair_id = _required_text(source, "pair_id", "source row")
        if source_pair_id in seen_source_ids:
            raise ValueError(f"duplicate source pair_id: {source_pair_id}")
        seen_source_ids.add(source_pair_id)
        template_id = _required_text(source, "template_id", source_pair_id)
        if counts[template_id] >= pairs_per_template:
            continue

        key = key_by_source.get(source_pair_id)
        if key is None:
            raise ValueError(f"answer key has no source_pair_id: {source_pair_id}")
        key_template = _required_text(key, "template_id", source_pair_id)
        if key_template != template_id:
            raise ValueError(
                f"template mismatch for {source_pair_id}: source={template_id} key={key_template}"
            )
        opaque_pair_id = _required_text(key, "pair_id", source_pair_id)
        release = release_by_pair.get(opaque_pair_id)
        if release is None:
            raise ValueError(f"release manifest has no pair_id: {opaque_pair_id}")

        selected_release.append(release)
        selected_keys.append(key)
        counts[template_id] += 1

    all_templates = {
        _required_text(row, "template_id", "source row") for row in source_rows
    }
    incomplete = {
        template: counts[template]
        for template in sorted(all_templates)
        if counts[template] != pairs_per_template
    }
    if incomplete:
        raise ValueError(
            f"source/key/release inputs cannot supply {pairs_per_template} pairs per template: "
            f"{incomplete}"
        )
    return selected_release, selected_keys, counts


def _safe_relative_path(raw: Any, context: str) -> PurePosixPath:
    if not isinstance(raw, str) or not raw:
        raise ValueError(f"{context} is not a nonempty path")
    normalized = raw.replace("\\", "/")
    parts = normalized.split("/")
    if (
        normalized.startswith("/")
        or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", normalized)
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise ValueError(f"unsafe relative path for {context}: {raw}")
    return PurePosixPath(*parts)


def _jsonl_bytes(rows: Iterable[JsonRow]) -> bytes:
    text = "".join(
        f"{json.dumps(row, sort_keys=True, separators=(',', ':'), ensure_ascii=True)}\n"
        for row in rows
    )
    return text.encode("utf-8")


def _write_bytes(root: Path, relative: PurePosixPath, data: bytes) -> None:
    destination = root.joinpath(*relative.parts)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)


def _copy_selected_images(
    release_rows: list[JsonRow], package_dir: Path, bundle_root: Path
) -> list[PurePosixPath]:
    copied: dict[PurePosixPath, str] = {}
    package_root = package_dir.resolve()
    for release in release_rows:
        pair_id = _required_text(release, "pair_id", "release row")
        members = release.get("members")
        if not isinstance(members, list) or len(members) != 2:
            raise ValueError(f"release pair {pair_id} must have exactly two members")
        for member in members:
            if not isinstance(member, dict):
                raise ValueError(f"release pair {pair_id} contains a non-object member")
            image_path = _safe_relative_path(member.get("image_path"), f"{pair_id} image")
            expected_sha = _required_text(member, "image_sha256", pair_id).lower()
            if not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
                raise ValueError(f"invalid image_sha256 for {pair_id}: {expected_sha}")
            previous_sha = copied.get(image_path)
            if previous_sha is not None:
                if previous_sha != expected_sha:
                    raise ValueError(f"conflicting hashes for repeated image path: {image_path}")
                continue

            source = package_root.joinpath(*image_path.parts).resolve()
            if not source.is_relative_to(package_root) or not source.is_file():
                raise ValueError(f"package image is missing or unsafe: {image_path}")
            data = source.read_bytes()
            found_sha = _sha256_bytes(data)
            if found_sha != expected_sha:
                raise ValueError(
                    f"image hash mismatch for {image_path}: expected={expected_sha} found={found_sha}"
                )
            _write_bytes(bundle_root, PurePosixPath("package") / image_path, data)
            copied[image_path] = expected_sha
    return sorted(copied)


def _write_deterministic_zip(source_dir: Path, output_zip: Path, bundle_name: str) -> None:
    with ZipFile(output_zip, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(item for item in source_dir.rglob("*") if item.is_file()):
            relative = path.relative_to(source_dir).as_posix()
            info = ZipInfo(f"{bundle_name}/{relative}", date_time=_ZIP_TIMESTAMP)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=ZIP_DEFLATED, compresslevel=9)


def build_bundle(
    *,
    source_manifest: Path,
    release_manifest: Path,
    answer_key: Path,
    package_dir: Path,
    viewer: Path,
    guide: Path,
    output_zip: Path,
    bundle_name: str,
    pairs_per_template: int = 20,
) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9._-]+", bundle_name):
        raise ValueError("bundle_name may contain only letters, digits, dot, underscore, and hyphen")
    if output_zip.exists():
        raise FileExistsError(f"refusing to overwrite bundle: {output_zip}")
    if output_zip.suffix.lower() != ".zip":
        raise ValueError("output_zip must end in .zip")
    for path in (source_manifest, release_manifest, answer_key, viewer, guide):
        if not path.is_file():
            raise FileNotFoundError(path)
    if not package_dir.is_dir():
        raise NotADirectoryError(package_dir)

    source_rows = read_jsonl(source_manifest)
    release_rows = read_jsonl(release_manifest)
    key_rows = read_jsonl(answer_key)
    selected_release, selected_keys, counts = select_contact_sheet_rows(
        source_rows, release_rows, key_rows, pairs_per_template
    )

    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="human_audit_bundle_", dir=output_zip.parent) as temporary:
        root = Path(temporary)
        _write_bytes(root, PurePosixPath("package/manifest.jsonl"), _jsonl_bytes(selected_release))
        _write_bytes(root, PurePosixPath("private/answer_key.jsonl"), _jsonl_bytes(selected_keys))
        _write_bytes(root, PurePosixPath("human_audit_viewer.html"), viewer.read_bytes())
        _write_bytes(root, PurePosixPath("REVIEWER_GUIDE.md"), guide.read_bytes())
        copied_images = _copy_selected_images(selected_release, package_dir, root)

        readme = f"""Blind Gains portable human audit: {bundle_name}

1. Extract this ZIP on the reviewing computer.
2. Read REVIEWER_GUIDE.md, or use Reviewer guide inside the viewer.
3. Open human_audit_viewer.html in Chromium or Firefox.
4. For the package folder, choose: package
5. For the private answer key, choose: private/answer_key.jsonl
6. Select Open human audit. This portable {len(selected_release)}-pair package defaults to All loaded pairs.
7. Complete all six checks for every loaded pair.
8. Export failures JSON when all pairs are reviewed.

This bundle contains the first {pairs_per_template} source-order pairs from each frozen template.
Keep the private answer key and exported audit record within the research team.
"""
        _write_bytes(root, PurePosixPath("README.txt"), readme.encode("utf-8"))

        file_hashes = {
            path.relative_to(root).as_posix(): sha256_file(path)
            for path in sorted(item for item in root.rglob("*") if item.is_file())
        }
        metadata = {
            "schema_version": "blind-gains.human-audit-bundle.v1",
            "selection": {
                "strategy": "first_n_per_template_in_source_manifest_order",
                "pairs_per_template": pairs_per_template,
                "pair_count": len(selected_release),
                "template_counts": dict(sorted(counts.items())),
                "opaque_pair_ids": [str(row["pair_id"]) for row in selected_release],
                "source_pair_ids": [str(row["source_pair_id"]) for row in selected_keys],
            },
            "source_sha256": {
                "source_manifest": sha256_file(source_manifest),
                "release_manifest": sha256_file(release_manifest),
                "answer_key": sha256_file(answer_key),
                "viewer": sha256_file(viewer),
                "reviewer_guide": sha256_file(guide),
            },
            "copied_image_count": len(copied_images),
            "bundled_file_sha256": file_hashes,
        }
        _write_bytes(
            root,
            PurePosixPath("bundle_manifest.json"),
            (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        )
        _write_deterministic_zip(root, output_zip, bundle_name)

    return {
        "output_zip": str(output_zip.resolve()),
        "output_sha256": sha256_file(output_zip),
        "output_bytes": output_zip.stat().st_size,
        "pair_count": len(selected_release),
        "image_count": len(copied_images),
        "template_counts": dict(sorted(counts.items())),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--release-manifest", type=Path, required=True)
    parser.add_argument("--answer-key", type=Path, required=True)
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--viewer", type=Path, required=True)
    parser.add_argument("--guide", type=Path, required=True)
    parser.add_argument("--output-zip", type=Path, required=True)
    parser.add_argument("--bundle-name", required=True)
    parser.add_argument("--pairs-per-template", type=int, default=20)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_bundle(
        source_manifest=args.source_manifest,
        release_manifest=args.release_manifest,
        answer_key=args.answer_key,
        package_dir=args.package_dir,
        viewer=args.viewer,
        guide=args.guide,
        output_zip=args.output_zip,
        bundle_name=args.bundle_name,
        pairs_per_template=args.pairs_per_template,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
