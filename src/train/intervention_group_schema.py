"""Intervention-group schema, versioned and validated (P0.3, invariant I15).

PAPER2 §4 Layer C: every training group carries the original image, a causal
twin, one or more invariance twins, a mismatched image, a no-image/gray control,
premise labels, final answers, hard negatives, blind-solvability metadata, a
scene-program id, an intervention type and difficulty metadata. I15 requires the
schema to be versioned and validated by the training loader with a fixture, so
that schema drift cannot silently change what a group contains -- and therefore
what the reward means.

The validator is deliberately strict and fails closed. Two structural rules exist
because violating them silently changes the objective rather than raising:

  * a causal member's answer MUST differ from the original's, and an invariance
    member's answer MUST equal it. If a causal twin shares the original answer,
    R_causal degenerates into ordinary answer reward on a duplicated item.
  * every group MUST carry at least one invariance member. PAPER2 §2 C2 states
    that causal-only reward is satisfiable by a change-detector heuristic
    (notice a difference, flip the answer); invariance groups are the control
    that forbids it, and I5 forbids training causal groups without them.
"""
from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "blind-gains.intervention-group.v1"

CAUSAL = "causal"
INVARIANCE = "invariance"
NEGATIVE_CONTROL = "negative_control"
MEMBER_KINDS = {CAUSAL, INVARIANCE, NEGATIVE_CONTROL}

# negative-control conditions live INSIDE the group (I3) rather than being scored
# separately, so they are enumerated here rather than in the training config
NEGATIVE_CONDITIONS = {"mismatched_real", "gray", "no_image", "caption"}

REQUIRED_GROUP_FIELDS = {
    "schema_version", "group_uid", "scene_program_id", "question",
    "original", "members", "difficulty", "blind_solvability",
}
REQUIRED_ORIGINAL_FIELDS = {"image_path", "image_sha256", "answer"}
REQUIRED_MEMBER_FIELDS = {"member_uid", "kind", "answer"}


class InterventionGroupSchemaError(ValueError):
    """Raised on any schema violation. Never downgraded to a warning."""


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise InterventionGroupSchemaError(msg)


def _norm(v: Any) -> str:
    return str(v).strip().lower()


def validate_group(group: dict[str, Any]) -> dict[str, Any]:
    """Validate one intervention group. Returns it unchanged, or raises."""
    _require(isinstance(group, dict), "group must be a mapping")

    missing = REQUIRED_GROUP_FIELDS - set(group)
    _require(not missing, f"group missing required fields: {sorted(missing)}")

    _require(group["schema_version"] == SCHEMA_VERSION,
             f"schema_version {group['schema_version']!r} != {SCHEMA_VERSION!r}; "
             "the loader refuses groups of an unknown version")

    original = group["original"]
    _require(isinstance(original, dict), "original must be a mapping")
    om = REQUIRED_ORIGINAL_FIELDS - set(original)
    _require(not om, f"original missing required fields: {sorted(om)}")

    members = group["members"]
    _require(isinstance(members, list) and members, "members must be a non-empty list")

    seen_uids = {original.get("member_uid", "__original__")}
    kinds: list[str] = []
    orig_answer = _norm(original["answer"])

    for i, m in enumerate(members):
        where = f"members[{i}]"
        _require(isinstance(m, dict), f"{where} must be a mapping")
        mm = REQUIRED_MEMBER_FIELDS - set(m)
        _require(not mm, f"{where} missing required fields: {sorted(mm)}")

        uid = m["member_uid"]
        _require(uid not in seen_uids, f"{where} duplicate member_uid {uid!r}")
        seen_uids.add(uid)

        kind = m["kind"]
        _require(kind in MEMBER_KINDS,
                 f"{where} kind {kind!r} not in {sorted(MEMBER_KINDS)}")
        kinds.append(kind)

        answer = _norm(m["answer"])
        if kind == CAUSAL:
            _require(answer != orig_answer,
                     f"{where} is causal but its answer equals the original's "
                     f"({m['answer']!r}); R_causal would reduce to ordinary answer "
                     "reward on a duplicated item")
            _require("image_path" in m and "image_sha256" in m,
                     f"{where} causal member needs image_path and image_sha256")
        elif kind == INVARIANCE:
            _require(answer == orig_answer,
                     f"{where} is invariance but its answer {m['answer']!r} differs "
                     f"from the original's {original['answer']!r}; the invariance "
                     "relation is then unsatisfiable by construction")
            _require("image_path" in m and "image_sha256" in m,
                     f"{where} invariance member needs image_path and image_sha256")
        else:
            cond = m.get("condition")
            _require(cond in NEGATIVE_CONDITIONS,
                     f"{where} negative_control condition {cond!r} not in "
                     f"{sorted(NEGATIVE_CONDITIONS)}")

    _require(CAUSAL in kinds, "group has no causal member")
    _require(INVARIANCE in kinds,
             "group has no invariance member; causal-only reward is satisfiable by "
             "a change-detector heuristic (I5)")

    bs = group["blind_solvability"]
    _require(isinstance(bs, dict) and {"q_real", "q_blind"} <= set(bs),
             "blind_solvability must carry q_real and q_blind")
    for k in ("q_real", "q_blind"):
        v = bs[k]
        _require(isinstance(v, (int, float)) and 0.0 <= float(v) <= 1.0,
                 f"blind_solvability.{k} must be a probability, got {v!r}")
    # delta_q is what C1 samples on; derive it rather than trusting a stored copy
    _require("delta_q" not in bs or
             abs(float(bs["delta_q"]) - (float(bs["q_real"]) - float(bs["q_blind"]))) < 1e-9,
             "blind_solvability.delta_q disagrees with q_real - q_blind")

    diff = group["difficulty"]
    _require(isinstance(diff, dict) and diff, "difficulty must be a non-empty mapping")

    return group


def validate_batch(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate a batch and reject duplicate group_uids across it."""
    seen = set()
    for i, g in enumerate(groups):
        validate_group(g)
        uid = g["group_uid"]
        _require(uid not in seen, f"groups[{i}] duplicate group_uid {uid!r}")
        seen.add(uid)
    return groups
