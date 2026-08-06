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


# --------------------------------------------------------------------------- v2
#
# blind-gains.intervention-group.v2 (Track-4 premise-construct v2; registered in
# docs/registered_track4_premise_v2_design_v1.md). Additive: the v1 validator
# above is the frozen P0.3 artifact and is not modified. v2 adds
#
#   * intervention_type as a required group field;
#   * an optional group-level premise. When declared, per-member premise golds
#     are mandatory and structurally checked: the causal member carries a
#     boolean premise_transition flag that MUST agree with whether its premise
#     gold differs from the original's (a lying flag would score an
#     invariance-style item as a transition, or vice versa); an invariance
#     member's premise gold MUST equal the original's (a premise-moving twin is
#     a causal intervention mislabelled as a control); negative controls carry
#     no premise gold. Half-specified premise metadata fails closed in both
#     directions.
#   * blind_solvability.measurement_state: development batches are built
#     'pending' (q_real/q_blind null) because I14 makes blind solvability an
#     acceptance gate, not a build-time guess; only 'measured' groups pass
#     require_measured=True, which is the training loader's path -- so an
#     unmeasured group can never reach an optimizer step.
#
# Cross-version refusal is mutual and total (I15): the v1 loader refuses v2
# groups and the v2 loader refuses v1 groups, because the premise semantics
# differ (v1 has a single shared premise_answer that measures invariance; v2
# has per-member golds that can transition). Silent acceptance in either
# direction would change what the reward means.

SCHEMA_VERSION_V2 = "blind-gains.intervention-group.v2"

REQUIRED_GROUP_FIELDS_V2 = REQUIRED_GROUP_FIELDS | {"intervention_type"}
MEASUREMENT_STATES = {"pending", "measured"}
_PREMISE_MEMBER_FIELDS = ("premise_answer", "premise_transition")


def _premise_fields_present(record: dict[str, Any]) -> list[str]:
    return [k for k in _PREMISE_MEMBER_FIELDS if k in record]


def _nonempty_str(v: Any) -> bool:
    return isinstance(v, str) and v.strip() != ""


def validate_group_v2(
    group: dict[str, Any], *, require_measured: bool = False
) -> dict[str, Any]:
    """Validate one v2 intervention group. Returns it unchanged, or raises."""
    _require(isinstance(group, dict), "group must be a mapping")

    # version first, shape second: a group of another version must be refused
    # AS that (the cross-version property I15 pins), not as a shape complaint
    _require(group.get("schema_version") == SCHEMA_VERSION_V2,
             f"schema_version {group.get('schema_version')!r} != "
             f"{SCHEMA_VERSION_V2!r}; the v2 loader refuses groups of any other "
             "version")

    missing = REQUIRED_GROUP_FIELDS_V2 - set(group)
    _require(not missing, f"group missing required fields: {sorted(missing)}")

    _require(_nonempty_str(group["intervention_type"]),
             f"intervention_type must be a non-empty string, got "
             f"{group['intervention_type']!r}")

    original = group["original"]
    _require(isinstance(original, dict), "original must be a mapping")
    om = REQUIRED_ORIGINAL_FIELDS - set(original)
    _require(not om, f"original missing required fields: {sorted(om)}")

    members = group["members"]
    _require(isinstance(members, list) and members, "members must be a non-empty list")

    premise = group.get("premise")
    has_premise = premise is not None
    if has_premise:
        _require(isinstance(premise, dict) and _nonempty_str(premise.get("question")),
                 "premise must be a mapping with a non-empty question")
        _require(_nonempty_str(original.get("premise_answer")),
                 "premise group: original must carry a non-empty premise_answer")
    else:
        stray = _premise_fields_present(original)
        _require(not stray,
                 f"original carries premise fields {stray} but the group declares "
                 "no premise")

    orig_answer = _norm(original["answer"])
    orig_premise = _norm(original["premise_answer"]) if has_premise else None

    seen_uids = {original.get("member_uid", "__original__")}
    kinds: list[str] = []

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

        if not has_premise:
            stray = _premise_fields_present(m)
            _require(not stray,
                     f"{where} carries premise fields {stray} but the group "
                     "declares no premise")

        answer = _norm(m["answer"])
        if kind == CAUSAL:
            _require(answer != orig_answer,
                     f"{where} is causal but its answer equals the original's "
                     f"({m['answer']!r}); R_causal would reduce to ordinary answer "
                     "reward on a duplicated item")
            _require("image_path" in m and "image_sha256" in m,
                     f"{where} causal member needs image_path and image_sha256")
            if has_premise:
                _require(_nonempty_str(m.get("premise_answer")),
                         f"{where} must carry a non-empty premise_answer in a "
                         "premise group")
                flag = m.get("premise_transition")
                _require(isinstance(flag, bool),
                         f"{where} causal member in a premise group must carry a "
                         "boolean premise_transition flag")
                transitions = _norm(m["premise_answer"]) != orig_premise
                _require(flag == transitions,
                         f"{where} premise_transition flag ({flag}) disagrees with "
                         f"the premise golds (member {m['premise_answer']!r} vs "
                         f"original {original['premise_answer']!r}); a lying flag "
                         "silently redefines the transition metric")
        elif kind == INVARIANCE:
            _require(answer == orig_answer,
                     f"{where} is invariance but its answer {m['answer']!r} differs "
                     f"from the original's {original['answer']!r}; the invariance "
                     "relation is then unsatisfiable by construction")
            _require("image_path" in m and "image_sha256" in m,
                     f"{where} invariance member needs image_path and image_sha256")
            if has_premise:
                _require(_nonempty_str(m.get("premise_answer")),
                         f"{where} must carry a non-empty premise_answer in a "
                         "premise group")
                _require(_norm(m["premise_answer"]) == orig_premise,
                         f"{where} is invariance but its premise_answer "
                         f"{m['premise_answer']!r} differs from the original's "
                         f"{original['premise_answer']!r}; a premise-moving twin "
                         "is a causal intervention mislabelled as a control")
                _require(m.get("premise_transition") in (None, False),
                         f"{where} invariance member cannot flag a premise "
                         "transition")
        else:  # negative_control
            cond = m.get("condition")
            _require(cond in NEGATIVE_CONDITIONS,
                     f"{where} negative_control condition {cond!r} not in "
                     f"{sorted(NEGATIVE_CONDITIONS)}")
            _require("premise_answer" not in m and "premise_transition" not in m,
                     f"{where} negative_control must not carry premise_answer or "
                     "premise_transition; controls have no premise gold by "
                     "construction")
            if cond == "no_image":
                _require("image_path" not in m and "image_sha256" not in m,
                         f"{where} no_image control must not carry an image "
                         "(image_path/image_sha256)")
            elif cond == "mismatched_real":
                _require("image_path" in m and "image_sha256" in m,
                         f"{where} mismatched_real control needs image_path and "
                         "image_sha256")
            else:  # gray, caption
                _require(("image_path" in m) == ("image_sha256" in m),
                         f"{where} {cond} control must carry image_path and "
                         "image_sha256 together or neither")

    _require(CAUSAL in kinds, "group has no causal member")
    _require(INVARIANCE in kinds,
             "group has no invariance member; causal-only reward is satisfiable by "
             "a change-detector heuristic (I5)")

    bs = group["blind_solvability"]
    _require(isinstance(bs, dict), "blind_solvability must be a mapping")
    state = bs.get("measurement_state")
    _require(state in MEASUREMENT_STATES,
             "blind_solvability must carry measurement_state 'pending' or "
             f"'measured', got {state!r}")
    if require_measured:
        _require(state == "measured",
                 f"the training loader refuses groups whose blind_solvability is "
                 f"{state!r}; only measured groups may reach an optimizer step (I14)")
    if state == "pending":
        for k in ("q_real", "q_blind", "delta_q"):
            v = bs.get(k)
            _require(v is None,
                     f"pending blind_solvability.{k} must be null, got {v!r}")
    else:
        _require({"q_real", "q_blind"} <= set(bs),
                 "measured blind_solvability must carry q_real and q_blind")
        for k in ("q_real", "q_blind"):
            v = bs[k]
            _require(isinstance(v, (int, float)) and not isinstance(v, bool)
                     and 0.0 <= float(v) <= 1.0,
                     f"blind_solvability.{k} must be a probability, got {v!r}")
        if bs.get("delta_q") is not None:
            _require(abs(float(bs["delta_q"])
                         - (float(bs["q_real"]) - float(bs["q_blind"]))) < 1e-9,
                     "blind_solvability.delta_q disagrees with q_real - q_blind")

    diff = group["difficulty"]
    _require(isinstance(diff, dict) and diff, "difficulty must be a non-empty mapping")

    return group


def validate_batch_v2(
    groups: list[dict[str, Any]], *, require_measured: bool = False
) -> list[dict[str, Any]]:
    """Validate a v2 batch and reject duplicate group_uids across it."""
    seen = set()
    for i, g in enumerate(groups):
        validate_group_v2(g, require_measured=require_measured)
        uid = g["group_uid"]
        _require(uid not in seen, f"groups[{i}] duplicate group_uid {uid!r}")
        seen.add(uid)
    return groups
