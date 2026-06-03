"""Plan A — post-diagnostic lead email (LLM only; context assembled in Node)."""

from __future__ import annotations

import json
from typing import Any

from app.services.llm import chat_json


def _build_user_message(lead_context: dict[str, Any]) -> str:
    return (
        "Generate the post-diagnostic personalised nurture email.\n\n"
        f"{json.dumps({'lead_context': lead_context}, indent=2, ensure_ascii=False)}"
    )


def _normalize_parsed(parsed: dict[str, Any]) -> dict[str, Any]:
    subject = str(parsed.get("subject") or "").strip()
    body = str(parsed.get("body") or "").strip()
    raw_insights = parsed.get("generatedInsights") or []
    generated_insights = (
        [str(x).strip() for x in raw_insights if str(x).strip()]
        if isinstance(raw_insights, list)
        else []
    )
    if not subject or not body:
        raise ValueError("Generated email missing subject or body")
    return {
        "subject": subject,
        "body": body,
        "generatedInsights": generated_insights,
    }


def generate_lead_email(
    *,
    system_prompt: str,
    lead_context: dict[str, Any],
    coaching_day: int | None = None,
) -> dict[str, Any]:
    """
    One personalised coaching email per day after funnel diagnostic completion.
    Each day focuses on a single angle (see lead_context.coaching_email).
    """
    ctx = dict(lead_context)
    if coaching_day is not None and "coaching_email" not in ctx:
        ctx["coaching_email"] = {"day": coaching_day}
    user_message = _build_user_message(ctx)
    parsed = chat_json(
        system_prompt,
        user_message,
        temperature=0.32,
        max_completion_tokens=1400,
    )
    if not parsed:
        raise ValueError("LLM returned empty JSON for lead email")
    return _normalize_parsed(parsed)
