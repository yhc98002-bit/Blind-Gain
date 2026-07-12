from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
VIEWER = ROOT / "tools" / "human_audit_viewer.html"


class _DocumentShape(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.inline_scripts = 0
        self.external_scripts: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            self.ids.add(element_id)
        if tag == "script":
            source = values.get("src")
            if source:
                self.external_scripts.append(source)
            else:
                self.inline_scripts += 1


def _source() -> str:
    return VIEWER.read_text(encoding="utf-8")


def _inline_javascript(source: str) -> str:
    scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", source, re.DOTALL)
    assert len(scripts) == 1
    return scripts[0]


def test_viewer_is_single_file_local_only_and_has_required_controls() -> None:
    source = _source()
    shape = _DocumentShape()
    shape.feed(source)

    assert shape.inline_scripts == 1
    assert shape.external_scripts == []
    assert "connect-src 'none'" in source
    assert not re.search(r"https?://", source, re.IGNORECASE)
    for network_api in ("fetch(", "XMLHttpRequest", "WebSocket", "EventSource", "sendBeacon"):
        assert network_api not in source

    required_ids = {
        "manifestFile",
        "answerKeyFile",
        "imageDirectory",
        "loadButton",
        "previousButton",
        "nextButton",
        "memberImage1",
        "memberImage2",
        "questionText",
        "memberAnswer1",
        "memberAnswer2",
        "exportButton",
    }
    assert required_ids <= shape.ids
    assert "webkitdirectory" in source


def test_viewer_pins_six_registered_checks_and_failure_only_export() -> None:
    source = _source()
    check_ids = re.findall(r'^\s+id: "([a-z0-9_]+)",$', source, re.MULTILINE)

    assert check_ids == [
        "visual_necessity",
        "single_answer_changing_difference",
        "legible_without_popout",
        "unambiguous_labels_and_wording",
        "artifact_parity",
        "answer_key_exact",
    ]
    assert 'for (const value of ["pass", "fail"])' in source
    assert 'schema_version: "blind-gains.human-audit-failures.v1"' in source
    assert "pair_id: pair.pairId" in source
    assert "failed_checks: failedChecks" in source
    assert "unreviewed_pair_ids: unreviewedPairIds" in source

    export_function = source.split("function exportFailures()", 1)[1].split(
        "function resetProgress()", 1
    )[0]
    assert "pair.members" not in export_function
    assert not re.search(r"\banswer\s*:", export_function)


def test_viewer_joins_answers_by_member_id_and_rejects_unsafe_inputs() -> None:
    source = _source()

    assert "key.memberAnswers.has(memberId)" in source
    assert "answer: key.memberAnswers.get(memberId)" in source
    assert "source_side" not in source
    assert 'row.members.length !== 2' in source
    assert 'parts.some((part) => part === ".." || part === "")' in source
    assert "validateImageCoverage(pairs, nextImageIndex)" in source
    assert source.index("validateImageCoverage(pairs, nextImageIndex)") < source.index(
        "state.imageIndex = nextImageIndex"
    )
    assert "found === member.imageSha256" in source
    assert "count < 20" in source
    assert "localStorage.setItem" in source


def test_viewer_contains_no_model_result_vocabulary() -> None:
    source = _source()
    forbidden = re.compile(
        r"\b(model|accuracy|prediction|reward|benchmark|metric|leaderboard)\b",
        re.IGNORECASE,
    )

    assert forbidden.search(source) is None


def test_inline_javascript_has_valid_syntax(tmp_path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is unavailable")
    script = tmp_path / "human_audit_viewer.js"
    script.write_text(_inline_javascript(_source()), encoding="utf-8")

    result = subprocess.run(
        [node, "--check", str(script)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_core_joins_randomized_members_and_rejects_path_traversal(tmp_path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is unavailable")
    javascript = _inline_javascript(_source())
    start = javascript.index("function parseRecords")
    end = javascript.index("function addImageIndexEntry")
    core = javascript[start:end]
    harness = r'''
const assert = require("node:assert/strict");
const manifest = [{
  pair_id: "pair-1",
  question: "Which value is shown?",
  members: [
    {member_id: "member-b", image_path: "images/b.png", image_sha256: "b".repeat(64)},
    {member_id: "member-a", image_path: "images/a.png", image_sha256: "a".repeat(64)}
  ]
}];
const key = [{
  pair_id: "pair-1",
  template_id: "template-1",
  category: "category-1",
  members: [
    {member_id: "member-a", answer: "ALPHA", source_side: "a"},
    {member_id: "member-b", answer: "BETA", source_side: "b"}
  ]
}];
const parsed = parseRecords(manifest.map(JSON.stringify).join("\n"), "manifest");
const pairs = buildPairs(parsed, key);
assert.equal(pairs[0].members[0].memberId, "member-b");
assert.equal(pairs[0].members[0].answer, "BETA");
assert.equal(pairs[0].members[1].answer, "ALPHA");
assert.throws(
  () => normalizeManifestPath("../private/key.jsonl", "image_path"),
  /safe relative path/
);
assert.throws(
  () => buildPairs(manifest, []),
  /missing manifest pair_id/
);
'''
    script = tmp_path / "human_audit_viewer_core_test.js"
    script.write_text(core + harness, encoding="utf-8")

    result = subprocess.run(
        [node, str(script)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
