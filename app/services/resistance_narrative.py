"""Post-process Map Resistance extraction with client-facing narrative fields."""

from __future__ import annotations

import re
from typing import Any


def _pick_goal_label(structure: dict, goal_context: dict) -> str:
    goal = (
        str(goal_context.get("specific_goal") or goal_context.get("goal_name") or structure.get("goal_title") or "")
        .strip()
    )
    outcome = (
        str(
            goal_context.get("measurable_outcome")
            or structure.get("desired_outcome")
            or (structure.get("milestones") or {}).get("day_90")
            or ""
        ).strip()
    )
    if goal and outcome and goal != outcome:
        return f"{goal} ({outcome})"
    return goal or outcome or "your goal"


def _pick_structure_label(structure: dict) -> str:
    fs = structure.get("failure_strategy") or {}
    if isinstance(fs, dict):
        title = str(fs.get("title") or "").strip()
        rule = str(fs.get("rule") or "").strip()
        if title and title != "Failure strategy":
            return title
        if rule:
            return rule
    for key in ("orbit_pattern", "protector_rule", "EO"):
        val = str(structure.get(key) or "").strip()
        if val:
            return val
    return "your protective structure"


def infer_structure_type(
    *,
    orbit_pattern: str = "",
    recovery_speed: str = "",
    contradiction_rate: str = "",
    current_loop: str = "",
    cl_estimate: Any = None,
) -> str:
    op = str(orbit_pattern or "").lower()
    cl = str(current_loop or "").lower()
    combined = f"{op} {cl}"

    self_blame = (
        "wrong with me",
        "broken",
        "shame",
        "self-blame",
        "self blame",
        "worthless",
        "not enough",
        "never enough",
        "failure",
        "defective",
        "fault",
        "my fault",
        "blame myself",
    )
    has_self_blame = any(kw in combined for kw in self_blame)
    try:
        cl_num = float(cl_estimate) if cl_estimate is not None and cl_estimate != "" else None
    except (TypeError, ValueError):
        cl_num = None
    is_very_low_cl = cl_num is not None and cl_num < 1.5
    is_high_contradiction = str(contradiction_rate or "").lower() == "high"

    if has_self_blame and (is_high_contradiction or is_very_low_cl):
        return "Something's Wrong With Me"

    towards_away = (
        r"attach.*withdraw",
        r"test.*withdraw",
        r"ask.*withdraw",
        r"announce.*withdraw",
        r"reach.*pull.?back",
        r"open.*close",
        r"connect.*retreat",
        r"approach.*retreat",
        r"engage.*disengage",
        r"start.*stop.*start",
        r"hide.*panic",
        r"ask.*panic",
    )
    if any(re.search(p, op) for p in towards_away):
        return "Towards & Away"

    snapback = (
        r"progress.*collapse",
        r"prove.*crash",
        r"overwork.*crash",
        r"succeed.*sabotage",
        r"almost.*then.*back",
        r"rise.*fall",
        r"up.*down.*up.*down",
    )
    if any(re.search(p, op) for p in snapback):
        return "Progress with Snapback"

    _ = recovery_speed
    return "Orbit"


def build_contradiction_statement(structure: dict, goal_context: dict) -> str:
    existing = str(structure.get("contradiction_statement") or "").strip()
    if existing:
        return existing

    goal = _pick_goal_label(structure, goal_context)
    structure_label = _pick_structure_label(structure)
    behaviours = structure.get("top_3_avoidance_behaviours") or []
    fs = structure.get("failure_strategy") or {}
    fs_behaviours = fs.get("behaviours") if isinstance(fs, dict) else []
    powering = (
        (behaviours[0] if behaviours else None)
        or (fs_behaviours[0] if fs_behaviours else None)
        or str(structure.get("orbit_pattern") or "").strip()
        or "avoidance"
    )
    return (
        f'You say you want {goal}, but your structure says "{structure_label}" '
        f"— so you power {powering} instead of progress."
    )


def build_takeover_moment(structure: dict) -> dict:
    existing = structure.get("structure_takeover_moment")
    if isinstance(existing, dict):
        trigger = str(existing.get("trigger") or "").strip()
        rule = str(existing.get("rule_obeyed") or existing.get("rule") or "").strip()
        sabotage = str(existing.get("sabotage_sequence") or existing.get("sabotage") or "").strip()
        if trigger or rule or sabotage:
            return {
                "trigger": trigger or None,
                "rule_obeyed": rule or None,
                "sabotage_sequence": sabotage or None,
            }

    behaviours = [
        str(x).strip()
        for x in (structure.get("top_3_avoidance_behaviours") or [])
        if str(x).strip()
    ]
    fs = structure.get("failure_strategy") or {}
    rule = (
        str(structure.get("protector_rule") or "").strip()
        or (str(fs.get("rule") or "").strip() if isinstance(fs, dict) else "")
        or None
    )
    return {
        "trigger": (
            str(structure.get("core_fear") or "").strip()
            or str(structure.get("perceived_risk") or "").strip()
            or (behaviours[0] if behaviours else None)
        ),
        "rule_obeyed": rule,
        "sabotage_sequence": (
            str(structure.get("orbit_pattern") or "").strip()
            or (" → ".join(behaviours) if behaviours else None)
        ),
    }


def build_flip_projection(structure: dict, goal_context: dict) -> str:
    existing = str(structure.get("flip_90_day_projection") or "").strip()
    if existing:
        return existing

    ss = structure.get("success_strategy") or {}
    actions = []
    if isinstance(ss, dict):
        actions = [str(x).strip() for x in (ss.get("behaviours") or []) if str(x).strip()][:3]
    outcome = (
        str(goal_context.get("measurable_outcome") or "").strip()
        or str(structure.get("desired_outcome") or "").strip()
        or str(structure.get("proof_of_success") or "").strip()
        or "your 90-day outcome"
    )
    belief = str(ss.get("belief") or "").strip() if isinstance(ss, dict) else ""
    action_text = (
        ", ".join(actions)
        if actions
        else (str(ss.get("behaviour") or ss.get("success_rule") or "").strip() if isinstance(ss, dict) else "")
        or "the flip actions"
    )
    if belief:
        return (
            f'If you installed "{belief}" and took {action_text} for 90 days, '
            f"you'd be moving toward {outcome} with proof you can be seen without collapsing."
        )
    return f"If you lived the flip for 90 days — {action_text} — you'd be on track toward {outcome}."


def enrich_resistance_narrative(
    structure: dict,
    *,
    active_goal_context: dict | None = None,
) -> dict:
    if not isinstance(structure, dict):
        return structure

    goal_context = active_goal_context or {}
    out = dict(structure)

    contradiction_rate = str(out.get("contradiction_rate") or "").strip().lower()
    if contradiction_rate not in ("low", "medium", "high"):
        contradiction_rate = "high" if out.get("top_3_avoidance_behaviours") else "medium"
        out["contradiction_rate"] = contradiction_rate

    out["structure_type"] = str(out.get("structure_type") or "").strip() or infer_structure_type(
        orbit_pattern=str(out.get("orbit_pattern") or ""),
        recovery_speed=str(out.get("recovery_speed") or ""),
        contradiction_rate=contradiction_rate,
        current_loop=str(out.get("past_pattern") or ""),
        cl_estimate=out.get("CL_estimate") or out.get("cl_estimate"),
    )
    out["contradiction_statement"] = build_contradiction_statement(out, goal_context)
    out["structure_takeover_moment"] = build_takeover_moment(out)
    out["flip_90_day_projection"] = build_flip_projection(out, goal_context)

    ss = out.get("success_strategy")
    if isinstance(ss, dict):
        if not str(out.get("flip_belief") or "").strip() and str(ss.get("belief") or "").strip():
            out["flip_belief"] = str(ss["belief"]).strip()
        if not str(out.get("flip_rule") or "").strip():
            flip_rule = str(ss.get("success_rule") or ss.get("behaviour") or "").strip()
            if flip_rule:
                out["flip_rule"] = flip_rule

    return out
