"""Pre-freeze cleanup fixtures: the coord footer fix and the registered
in-image text policy. The v1 footer stated the L2 task procedure inside every
layer's image; these tests pin (1) the hier-owned renderer differs from the
frozen renderer ONLY inside the footer strip, (2) the registered strings are
layer-neutral, (3) the policy screen fails on the v1 footer."""
from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.hier_v1_lib import (  # noqa: E402
    COORD_FOOTER,
    COORD_FOOTER_BOX,
    PROCEDURE_TOKENS,
    REGISTERED_TEXT,
    _render_hier_coordinate_register,
)
from src.fliptrack.build_v02 import (  # noqa: E402
    _render_high_entropy_coordinate_register,
)

SPEC = importlib.util.spec_from_file_location(
    "verify_hier_dev_batch", ROOT / "scripts/verify_hier_dev_batch.py")
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)

POINTS = {"B8": (-2, -5), "F6": (4, -4), "K6": (6, 4), "L8": (1, 2)}
V1_FOOTER = ("Locate the requested label, then read its coordinate from the "
             "numbered axes.")


def test_renderers_differ_only_in_footer_strip():
    frozen = np.asarray(_render_high_entropy_coordinate_register(POINTS))
    hier = np.asarray(_render_hier_coordinate_register(POINTS))
    assert frozen.shape == hier.shape
    diff = np.any(frozen != hier, axis=2)
    left, top, right, bottom = COORD_FOOTER_BOX
    outside = diff.copy()
    outside[top:bottom, left:right] = False
    assert not outside.any(), "renderers differ outside the footer strip"
    assert diff[top:bottom, left:right].any(), "footer strip did not change"


def test_hier_renderer_sources_are_pinned():
    hier_src = inspect.getsource(_render_hier_coordinate_register)
    assert "COORD_FOOTER" in hier_src
    assert "Locate the requested" not in hier_src
    frozen_src = inspect.getsource(_render_high_entropy_coordinate_register)
    assert "Locate the requested" in frozen_src  # frozen module untouched


def test_registered_text_is_layer_neutral():
    assert VERIFY.registered_text_policy_problems() == []
    for texts in REGISTERED_TEXT.values():
        for text in texts.values():
            assert not any(tok in text.lower() for tok in PROCEDURE_TOKENS)


def test_policy_screen_fails_the_v1_footer(monkeypatch):
    doctored = {"hier_coord_v1": {"title": "Coordinate Survey Register",
                                  "footer": V1_FOOTER}}
    monkeypatch.setattr(VERIFY, "REGISTERED_TEXT", doctored)
    problems = VERIFY.registered_text_policy_problems()
    assert problems, "v1 procedural footer must fail the policy screen"
    assert any("procedure token" in p for p in problems)


def test_new_footer_is_the_registered_string():
    assert REGISTERED_TEXT["hier_coord_v1"]["footer"] == COORD_FOOTER
    assert COORD_FOOTER == "Each point is identified by its printed label."
