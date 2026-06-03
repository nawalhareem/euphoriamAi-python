"""Personalised structural member email — LLM generation only (context built in Node)."""

from __future__ import annotations

import json
from typing import Any

from app.services.llm import chat_json

EMAIL_TYPE_PURPOSES: dict[str, str] = {
    "weekly_insight": "Biggest structural pattern from the last 7 days.",
    "progress": "Reflect wins, momentum, and proof evidence.",
    "stalled_pattern": "Notice avoidance, delay, inconsistency, or collapse.",
    "structural_reminder": "Reconnect with deeper goal and resistance structure.",
    "coach_follow_up": "Continue the in-app coach conversation outside the app.",
}


def _build_user_message(user_payload: dict[str, Any], correction_note: str | None) -> str:
    payload_json = json.dumps(user_payload, indent=2, ensure_ascii=False)
    if correction_note:
        return (
            f"{correction_note}\n\n"
            "Regenerate the email.\n\n"
            f"{payload_json}"
        )
    return f"Generate the personalised member email.\n\n{payload_json}"


def _normalize_parsed(parsed: dict[str, Any], requested_type: str) -> dict[str, Any]:
    subject = str(parsed.get("subject") or "").strip()
    body = str(parsed.get("body") or "").strip()
    email_type = str(parsed.get("emailType") or requested_type).strip() or requested_type
    raw_insights = parsed.get("generatedInsights") or []
    generated_insights = [
        str(x).strip() for x in raw_insights if str(x).strip()
    ] if isinstance(raw_insights, list) else []

    if not subject or not body:
        raise ValueError("Generated email missing subject or body")

    return {
        "subject": subject,
        "body": body,
        "emailType": email_type,
        "generatedInsights": generated_insights,
    }


def generate_member_email(
    *,
    system_prompt: str,
    email_type: str,
    member_context: dict[str, Any],
    generation_constraints: dict[str, Any] | None = None,
    correction_note: str | None = None,
) -> dict[str, Any]:
    """
    Generate one personalised member email from pre-built member_context (Node).

    Prompt text is loaded in Node from DB and passed as system_prompt.
    """
    user_payload: dict[str, Any] = {
        "email_type": email_type,
        "email_type_purpose": EMAIL_TYPE_PURPOSES.get(
            email_type, "Personalised structural insight for this member."
        ),
        "member_context": member_context,
        "generation_constraints": generation_constraints or {},
        "priority_instruction": (
            "Quote the member's own words (mandatory_verbatim_quotes) before interpreting. "
            "Follow writing_blueprint.narrative_beats."
        ),
    }

    user_message = _build_user_message(user_payload, correction_note)
    parsed = chat_json(
        system_prompt,
        user_message,
        temperature=0.32,
        max_completion_tokens=1600,
    )
    if not parsed:
        raise ValueError("LLM returned empty JSON for member email")
    return _normalize_parsed(parsed, email_type)
