import json
import re

from app.services.llm import chat_json, chat_text
from app.services.prompt_compose import compose_map_resistance_turn_system

WELCOME_TEMPLATE = """Hi {name}, we're mapping the resistance structure for your **{label}** goal — not a generic life diagnostic.

**Your goal:** {goal}
**90-day outcome:** {outcome}

About 12 questions, one at a time. Every question stays anchored to this goal.

**Q1 — Resistance when pursuing this goal**
When you move toward "{goal}", what do you usually do instead, avoid, or tell yourself first that slows you down?"""

# Distinct fallback angles if the model returns empty JSON (Q1 uses welcome template).
_FALLBACK_TOPICS: list[tuple[str, str]] = [
    (
        "Body and breath",
        'When you imagine taking the next visible step on "{goal}", what do you notice first in your body, breath, or energy?',
    ),
    (
        "Protector voice",
        'What inner voice or story shows up to talk you out of moving on "{goal}"?',
    ),
    (
        "Fear if you act",
        'If you actually moved forward on "{goal}" today, what are you afraid would happen?',
    ),
    (
        "Cost to the goal",
        'How does your usual avoidance limit the measurable outcome you want from "{goal}"?',
    ),
    (
        "Past pattern",
        'When you tried something similar to "{goal}" before, what happened — and what made you stop?',
    ),
    (
        "Hidden rule",
        'What unspoken rule are you obeying that says you cannot fully go for "{goal}" yet?',
    ),
    (
        "Avoidance behaviours",
        'Name 2–3 specific things you do instead of the next step on "{goal}" (delay, scroll, perfect, hide, people-please, etc.).',
    ),
    (
        "Identity risk",
        'Who would you have to become to complete "{goal}" — and what feels unsafe about that?',
    ),
    (
        "Visibility or judgement",
        'On "{goal}", do you avoid being seen, judged, wrong, or needy — which hits hardest and how?',
    ),
    (
        "Smallest disobedience",
        'What is the smallest action on "{goal}" that would disobey your usual avoidance — even if imperfect?',
    ),
    (
        "Proof in 7 days",
        'What proof would you accept from yourself in the next 7 days that you are serious about "{goal}"?',
    ),
    (
        "Recovery after action",
        'After you take a small step on "{goal}", what makes you collapse, overthink, or pull back?',
    ),
]


def _count_answered(transcript: list[dict]) -> int:
    count = 0
    for m in transcript:
        if m.get("role") != "user":
            continue
        content = (m.get("content") or "").strip()
        if len(content) >= 2:
            count += 1
    return count


def _last_q_number(transcript: list[dict]) -> int:
    n = 0
    for m in transcript:
        if m.get("role") != "assistant":
            continue
        match = re.search(r"\*\*Q(\d+)", m.get("content") or "", re.I)
        if match:
            n = max(n, int(match.group(1)))
    return n


def _next_question_number(transcript: list[dict], target_count: int) -> int:
    last = _last_q_number(transcript)
    answered = _count_answered(transcript)
    # After welcome (Q1), first user answer should trigger Q2
    if last <= 1 and answered >= 1:
        return min(target_count, 2)
    return min(target_count, max(last + 1, 1))


def _extract_assistant_message(parsed: dict) -> str:
    if not parsed:
        return ""
    for key in ("assistant_message", "message", "question", "reply", "content"):
        val = parsed.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def _fallback_question(q_num: int, goal: str) -> str:
    idx = max(0, min(q_num - 2, len(_FALLBACK_TOPICS) - 1))
    title, template = _FALLBACK_TOPICS[idx]
    body = template.format(goal=goal)
    return f"**Q{q_num} — {title}**\n{body}"


def _build_turn_user_payload(
    *,
    active_goal_context: dict,
    transcript: list[dict],
    target_count: int,
) -> str:
    goal = (
        active_goal_context.get("specific_goal")
        or active_goal_context.get("goal_name")
        or "your goal"
    )
    label = active_goal_context.get("domain_label") or active_goal_context.get("active_domain") or "this domain"
    answered = _count_answered(transcript)
    next_q = _next_question_number(transcript, target_count)
    last_user = ""
    for m in reversed(transcript):
        if m.get("role") == "user":
            last_user = (m.get("content") or "").strip()
            break

    instruction = (
        f'Ask exactly ONE new question labeled **Q{next_q} — <short topic>**. '
        f'It MUST be different from every prior assistant question. '
        f'Anchor to goal "{goal}" in the {label} domain. '
        f"Explore resistance, avoidance, protector, fear, or cost — pick a fresh angle."
    )
    if len(last_user) < 3:
        instruction = (
            f"The user's last reply was too short. Re-ask **Q{next_q}** in simpler words with one example. "
            f"Do not advance question number."
        )

    if answered >= target_count - 1:
        instruction = (
            f"User has answered {answered} questions (target {target_count}). "
            "Acknowledge completion briefly; tell them they can press Complete mapping. "
            "Do not ask another intake question. Set finalize_ready true."
        )

    return json.dumps(
        {
            "instruction": instruction,
            "next_question_number": next_q,
            "answered_count": answered,
            "target_count": target_count,
            "ACTIVE_GOAL_CONTEXT": active_goal_context,
            "transcript": transcript,
        },
        indent=2,
    )


def _generate_question(
    *,
    system: str,
    user_payload: str,
    next_q: int,
    goal: str,
) -> tuple[str, dict]:
    parsed: dict = {}
    content = ""

    try:
        parsed = chat_json(system, user_payload)
        content = _extract_assistant_message(parsed)
    except Exception:
        parsed = {}

    if not content or not re.search(rf"\*\*Q{next_q}\b", content, re.I):
        try:
            text = chat_text(
                system
                + "\n\nReply with ONLY the next assistant question text (markdown). "
                f"Start with **Q{next_q} — topic** then the question. One question only.",
                [{"role": "user", "content": user_payload}],
            )
            if text.strip():
                content = text.strip()
                parsed = {**parsed, "assistant_message": content}
        except Exception:
            pass

    if not content or not re.search(r"\*\*Q\d+", content, re.I):
        content = _fallback_question(next_q, goal)
        parsed = {
            **parsed,
            "assistant_message": content,
            "last_question_number": next_q,
            "pending_question": True,
        }

    return content, parsed


def map_resistance_turn(
    *,
    active_goal_context: dict,
    transcript: list[dict] | None = None,
    target_count: int = 12,
    user_name: str = "there",
    prompts: dict | None = None,
) -> dict:
    transcript = list(transcript or [])
    domain = active_goal_context.get("active_domain") or "income"
    label = active_goal_context.get("domain_label") or domain
    goal = (
        active_goal_context.get("specific_goal")
        or active_goal_context.get("goal_name")
        or "your goal"
    )
    outcome = active_goal_context.get("measurable_outcome") or "your 90-day outcome"

    if not transcript:
        welcome = WELCOME_TEMPLATE.format(
            name=user_name,
            label=label,
            goal=goal,
            outcome=outcome,
        )
        assistant = {"role": "assistant", "content": welcome}
        full = [assistant]
        return _pack_turn(full, target_count, pending_question=True)

    system = compose_map_resistance_turn_system(prompts)
    user_payload = _build_turn_user_payload(
        active_goal_context=active_goal_context,
        transcript=transcript,
        target_count=target_count,
    )
    next_q = _next_question_number(transcript, target_count)
    content, parsed = _generate_question(
        system=system,
        user_payload=user_payload,
        next_q=next_q,
        goal=goal,
    )

    full = [*transcript, {"role": "assistant", "content": content}]
    answered = int(parsed.get("answered_count") or _count_answered(transcript))
    last_q = int(parsed.get("last_question_number") or _last_q_number(full))
    pending = bool(parsed.get("pending_question", True))
    finalize_ready = bool(parsed.get("finalize_ready")) or (
        answered >= target_count - 1 and not pending
    )

    return _pack_turn(
        full,
        target_count,
        answered_count=answered,
        last_question_number=last_q,
        pending_question=pending,
        finalize_ready=finalize_ready,
    )


def _pack_turn(
    transcript: list[dict],
    target_count: int,
    *,
    answered_count: int | None = None,
    last_question_number: int | None = None,
    pending_question: bool = False,
    finalize_ready: bool = False,
) -> dict:
    answered = answered_count if answered_count is not None else _count_answered(transcript)
    last_q = last_question_number if last_question_number is not None else _last_q_number(transcript)
    last_assistant = next(
        (m for m in reversed(transcript) if m.get("role") == "assistant"),
        None,
    )
    return {
        "nextMessage": last_assistant,
        "transcript": transcript,
        "messages": transcript,
        "answeredCount": answered,
        "pendingQuestion": pending_question,
        "progress": {
            "answered": answered,
            "total": target_count,
            "currentQuestion": last_q,
        },
        "intakeState": {
            "transcript": transcript,
            "answeredCount": answered,
            "lastQuestionNumber": last_q,
            "pendingQuestion": pending_question,
            "mode": "map_resistance",
        },
        "finalize_ready": finalize_ready,
    }


def extract_domain_structure(
    *,
    transcript: list[dict],
    active_goal_context: dict,
    domain: str,
    prompts: dict | None = None,
) -> dict:
    from app.services.prompt_compose import compose_map_extract_system

    payload = json.dumps(
        {
            "ACTIVE_GOAL_CONTEXT": active_goal_context,
            "domain": domain,
            "transcript": transcript,
        },
        indent=2,
    )
    system = compose_map_extract_system(prompts)
    parsed = chat_json(system, payload)
    parsed["map_resistance_complete"] = True
    return parsed
