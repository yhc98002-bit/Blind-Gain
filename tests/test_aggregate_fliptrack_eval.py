from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "aggregate_fliptrack_eval.py"


def _run(tmp_path: Path, pattern: str, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--inputs",
            pattern,
            "--output",
            str(output),
            "--bootstrap",
            "2",
            "--permutations",
            "2",
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )


def test_aggregate_rejects_empty_input_glob(tmp_path: Path) -> None:
    output = tmp_path / "metrics.json"
    result = _run(tmp_path, "missing-*.jsonl", output)
    assert result.returncode != 0
    assert "matched no nonempty rows" in result.stderr
    assert not output.exists()


def test_aggregate_refuses_to_overwrite_output(tmp_path: Path) -> None:
    row = {
        "pair_id": "p1",
        "template_id": "template",
        "answer_a": "1",
        "answer_b": "2",
        "prediction_a": "<answer>1</answer>",
        "prediction_b": "<answer>2</answer>",
    }
    (tmp_path / "rows.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    output = tmp_path / "metrics.json"
    output.write_text("existing\n", encoding="utf-8")
    result = _run(tmp_path, "rows.jsonl", output)
    assert result.returncode != 0
    assert "refusing to overwrite" in result.stderr
    assert output.read_text(encoding="utf-8") == "existing\n"
