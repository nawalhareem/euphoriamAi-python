"""Compose system prompts from DB payloads sent by Node (with code fallbacks)."""

from app.services.prompts import (
    MAP_RESISTANCE_EXTRACT,
    MAP_RESISTANCE_TURN_RULES,
    STAGE1_DAILY_COACH,
    STAGE1_FRICTION,
    STAGE1_MAP_RESISTANCE,
)

# Live Q&A turns: keep system prompt small so the model returns JSON reliably.
_MAX_TURN_SECTION_CHARS = 8_000


def _section(title: str, body: str) -> str:
    return f"--- {title} ---\n{body.strip()}"


def compose_coach_system(prompts: dict | None) -> str:
    """Coach Brain + Brain (+ optional stage1_daily_coach from admin)."""
    from app.services.prompts import _COACH_CONTEXT_RULES

    prompts = prompts or {}
    parts: list[str] = [_COACH_CONTEXT_RULES]
    if prompts.get("coach_brain_prompt"):
        parts.append(_section("COACH BRAIN PROMPT (Goal-Specific OS)", prompts["coach_brain_prompt"]))
    if prompts.get("brain_prompt"):
        parts.append(
            _section(
                "BRAIN PROMPT (Canonical library — signatures, reps, UC routing)",
                prompts["brain_prompt"],
            )
        )
    if prompts.get("stage1_daily_coach"):
        parts.append(_section("DAILY COACH TURN RULES (admin)", prompts["stage1_daily_coach"]))
    return "\n\n".join(parts) if len(parts) > 1 else STAGE1_DAILY_COACH


def compose_friction_system(prompts: dict | None) -> str:
    prompts = prompts or {}
    parts: list[str] = []
    if prompts.get("coach_brain_prompt"):
        parts.append(_section("COACH BRAIN PROMPT", prompts["coach_brain_prompt"]))
    if prompts.get("brain_prompt"):
        parts.append(_section("BRAIN PROMPT", prompts["brain_prompt"]))
    if prompts.get("stage1_friction_rescue"):
        parts.append(_section("FRICTION RESCUE RULES", prompts["stage1_friction_rescue"]))
    return "\n\n".join(parts) if parts else STAGE1_FRICTION


def _truncate(body: str, max_chars: int = _MAX_TURN_SECTION_CHARS) -> str:
    body = (body or "").strip()
    if len(body) <= max_chars:
        return body
    return (
        body[:max_chars]
        + "\n\n[... section truncated for map-resistance chat turn; full text used at finalize ...]"
    )


def compose_map_resistance_turn_system(prompts: dict | None) -> str:
    """
    Live Map Resistance: technical turn rules + Coach Brain (+ optional stage1_map_resistance).
    Full Brain Prompt is used at finalize, not every chat turn (token limit).
    """
    prompts = prompts or {}
    parts: list[str] = [MAP_RESISTANCE_TURN_RULES]
    if prompts.get("coach_brain_prompt"):
        parts.append(
            _section("COACH BRAIN PROMPT", _truncate(prompts["coach_brain_prompt"], 6_000))
        )
    if prompts.get("stage1_map_resistance"):
        parts.append(_section("MAP RESISTANCE (admin)", _truncate(prompts["stage1_map_resistance"])))
    elif prompts.get("brain_prompt"):
        # If no stage1_map_resistance row, include a slice of Brain for Q&A framing
        parts.append(_section("BRAIN PROMPT (truncated)", _truncate(prompts["brain_prompt"], 4_000)))
    if len(parts) == 1:
        parts.append(STAGE1_MAP_RESISTANCE)
    return "\n\n".join(parts)


def compose_map_resistance_system(prompts: dict | None) -> str:
    """Alias for turn system (finalize uses compose_map_extract_system)."""
    return compose_map_resistance_turn_system(prompts)


def compose_map_extract_system(prompts: dict | None) -> str:
    prompts = prompts or {}
    parts: list[str] = []
    if prompts.get("coach_brain_prompt"):
        parts.append(_section("COACH BRAIN PROMPT", prompts["coach_brain_prompt"]))
    if prompts.get("brain_prompt"):
        parts.append(_section("BRAIN PROMPT", prompts["brain_prompt"]))
    if prompts.get("stage1_map_resistance"):
        parts.append(_section("EXTRACTION RULES", prompts["stage1_map_resistance"]))
    return "\n\n".join(parts) if parts else MAP_RESISTANCE_EXTRACT
