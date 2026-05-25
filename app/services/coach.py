import json

from app.services.llm import chat_json, chat_text
from app.services.prompt_compose import compose_coach_system, compose_friction_system

STATE_LABELS = {
    "abducted": "Abducted by Vortex",
    "high_gravity": "High Gravity",
    "clear": "Clear + Able",
    "progress": "Progress",
}


def _build_coach_user_payload(
    domain_map: dict,
    checkin: dict,
    messages: list[dict],
    user_message: str | None,
) -> str:
    return json.dumps(
        {
            "domain_map": domain_map,
            "COACH_CHECKIN": checkin,
            "messages": messages,
            "user_message": user_message,
        },
        indent=2,
    )


def coach_reply(
    *,
    domain_map: dict,
    checkin: dict,
    messages: list[dict] | None = None,
    user_message: str | None = None,
    prompts: dict | None = None,
) -> dict:
    messages = messages or []
    state = checkin.get("current_state") or checkin.get("state") or "clear"
    checkin = {
        **checkin,
        "current_state": state,
        "state_label": STATE_LABELS.get(state, state),
    }

    if user_message:
        messages = [*messages, {"role": "user", "content": user_message}]

    system = compose_coach_system(prompts)
    try:
        parsed = chat_json(
            system,
            _build_coach_user_payload(domain_map, checkin, messages, user_message),
        )
        if parsed.get("assistant_message"):
            return _normalize_coach_response(parsed, domain_map)
    except Exception:
        pass

    # Fallback: conversational path
    system = (
        f"{system}\n\n"
        f"domain_map:\n{json.dumps(domain_map, indent=2)}\n\n"
        f"checkin:\n{json.dumps(checkin, indent=2)}"
    )
    llm_messages = [{"role": m["role"], "content": m["content"]} for m in messages if m.get("content")]
    text = chat_text(system, llm_messages)
    daily_rep = domain_map.get("daily_rep") or {}
    green_rep = None
    if isinstance(daily_rep, dict) and daily_rep.get("name"):
        green_rep = {
            "name": daily_rep["name"],
            "steps": daily_rep.get("steps") or [],
            "win_condition": daily_rep.get("win_condition") or domain_map.get("win_condition"),
        }
    elif domain_map.get("today_visible_action"):
        green_rep = {
            "name": domain_map["today_visible_action"],
            "steps": [],
            "win_condition": domain_map.get("win_condition") or "",
        }

    return {
        "assistant_message": text,
        "green_rep": green_rep,
        "detected_failure_strategy": None,
        "writeback_hints": {},
    }


def friction_rescue(
    *,
    domain_map: dict,
    checkin: dict,
    messages: list[dict] | None = None,
    user_message: str | None = None,
    prompts: dict | None = None,
) -> dict:
    messages = messages or []
    if user_message:
        messages = [*messages, {"role": "user", "content": user_message}]
    payload = json.dumps(
        {"domain_map": domain_map, "checkin": checkin, "messages": messages},
        indent=2,
    )
    system = compose_friction_system(prompts)
    try:
        parsed = chat_json(system, payload)
        if parsed.get("assistant_message"):
            return {
                "assistant_message": parsed["assistant_message"],
                "green_rep": parsed.get("green_rep"),
            }
    except Exception:
        pass

    text = chat_text(
        system + "\n\n" + payload,
        [{"role": m["role"], "content": m["content"]} for m in messages],
        model=None,
    )
    return {"assistant_message": text, "green_rep": None}


def _normalize_coach_response(parsed: dict, domain_map: dict) -> dict:
    green_rep = parsed.get("green_rep")
    if not green_rep:
        daily_rep = domain_map.get("daily_rep")
        if isinstance(daily_rep, dict) and daily_rep.get("name"):
            green_rep = {
                "name": daily_rep["name"],
                "steps": daily_rep.get("steps") or [],
                "win_condition": daily_rep.get("win_condition") or "",
            }
    return {
        "assistant_message": parsed.get("assistant_message", ""),
        "green_rep": green_rep,
        "detected_failure_strategy": parsed.get("detected_failure_strategy"),
        "writeback_hints": parsed.get("writeback_hints") or {},
    }
