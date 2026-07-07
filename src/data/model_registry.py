from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


REGISTRY_PATH = Path("experiments/manifests/model_registry.jsonl")


@dataclass(frozen=True)
class ModelArtifact:
    name: str
    source: str
    source_url: str
    revision: str
    license: str
    local_path: str
    redistribution: str
    sha256: str | None = None
    notes: str = ""


def sha256_tree(path: str | Path) -> str:
    path = Path(path)
    digest = hashlib.sha256()
    if path.is_file():
        files = [path]
    else:
        files = sorted(p for p in path.rglob("*") if p.is_file())
    for file_path in files:
        digest.update(str(file_path.relative_to(path if path.is_dir() else path.parent)).encode("utf-8"))
        with file_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def append_artifact(artifact: ModelArtifact, registry_path: str | Path = REGISTRY_PATH) -> None:
    registry_path = Path(registry_path)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with registry_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(artifact), sort_keys=True, ensure_ascii=True) + "\n")


def load_registry(registry_path: str | Path = REGISTRY_PATH) -> list[dict[str, Any]]:
    path = Path(registry_path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_license_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["name", "source", "source_url", "revision", "license", "local_path", "redistribution", "sha256", "notes"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default=str(REGISTRY_PATH))
    parser.add_argument("--license-csv", default="reports/license_log.csv")
    args = parser.parse_args()
    rows = load_registry(args.registry)
    write_license_csv(args.license_csv, rows)
    print(args.license_csv)


if __name__ == "__main__":
    main()

