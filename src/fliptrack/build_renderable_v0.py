from __future__ import annotations

import argparse
from pathlib import Path

from src.fliptrack.render_chart import generate_chart_pairs
from src.fliptrack.render_doc import generate_doc_pairs
from src.fliptrack.render_geometry import generate_geometry_pairs
from src.fliptrack.schema import write_jsonl


def build(out_dir: str | Path, n_per_family: int, seed: int) -> list[dict]:
    out_dir = Path(out_dir)
    rows = []
    rows.extend(generate_chart_pairs(out_dir / "chart", n_per_family, seed + 1))
    rows.extend(generate_doc_pairs(out_dir / "doc", n_per_family, seed + 2))
    rows.extend(generate_geometry_pairs(out_dir / "geometry", n_per_family, seed + 3))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="data/fliptrack_v0/renderable")
    parser.add_argument("--manifest", default="data/fliptrack_v0_manifest.jsonl")
    parser.add_argument("--n-per-family", type=int, default=10)
    parser.add_argument("--seed", type=int, default=23)
    args = parser.parse_args()
    rows = build(args.out_dir, args.n_per_family, args.seed)
    write_jsonl(args.manifest, rows)
    print(args.manifest)


if __name__ == "__main__":
    main()

