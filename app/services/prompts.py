"""
Technical fallbacks for euphoriam-ai — NOT the product prompts.

Coaching content lives in Postgres (admin Prompts tab) and is loaded by Node:
  - Coach Brain Prompt  → V2 goal-specific OS
  - Brain Prompt        → canonical library (48 signatures, reps, UC routing)
  - stage1_map_resistance / stage1_daily_coach / stage1_friction_rescue → optional turn/output rules
  - Diagnostic / Diagnostic Chat → Node diagnostics only (not this Python service)

Node passes active rows on each request via stage1Prompts.js → prompts={...}.

This file only provides:
  1. MAP_RESISTANCE_TURN_RULES — small runtime guard (JSON shape, one Q per turn, no repeats)
  2. One-line fallbacks if a DB row is missing (dev / misconfiguration)
"""

# Map Resistance live turns: always prepended so the model returns JSON even when DB text is huge.
MAP_RESISTANCE_TURN_RULES = """MAP RESISTANCE — technical turn rules (content comes from Coach Brain + admin prompts above).

1. Ask exactly ONE question per turn: **Q{n} — topic** where n = next_question_number in the user JSON.
2. Never repeat prior assistant question text; each Q explores a new angle (resistance, protector, fear, cost, etc.).
3. Anchor every question to the user's specific goal in ACTIVE_GOAL_CONTEXT.
4. If the last user reply was too short, re-ask the same Q with simpler wording.
5. When answered_count >= target_count - 1, set finalize_ready true; tell user to press Complete mapping.

Return JSON only:
{
  "assistant_message": "full question starting with **Q{n} — topic**",
  "answered_count": number,
  "last_question_number": number,
  "pending_question": boolean,
  "finalize_ready": boolean
}"""

# Used only when finalize runs and no DB prompts were passed.
MAP_RESISTANCE_EXTRACT_FALLBACK = (
    "Extract goal-scoped structure from the Map Resistance transcript. "
    "Return JSON with signature_id, EO, lack_channel, avoid_type, failure_strategy, "
    "success_strategy, daily_rep, top_3_avoidance_behaviours, protector_rule, recovery_speed."
)

_COACH_FALLBACK = (
    "You are Euphoriam Daily Coach for one active goal. "
    "Return JSON: assistant_message, green_rep, detected_failure_strategy, writeback_hints. "
    "Load Coach Brain Prompt and Brain Prompt from admin — this stub means DB rows are missing."
)

_MAP_FALLBACK = (
    "Goal-scoped Map Resistance Q&A (~12 questions). "
    "Load Coach Brain Prompt, Brain Prompt, and stage1_map_resistance from admin — DB rows missing."
)

_FRICTION_FALLBACK = (
    "Short friction rescue grounded in failure_strategy. "
    "Return JSON: assistant_message, green_rep. Load prompts from admin — DB rows missing."
)

# Legacy names kept for imports in prompt_compose.py
STAGE1_DAILY_COACH = _COACH_FALLBACK
STAGE1_MAP_RESISTANCE = _MAP_FALLBACK
STAGE1_FRICTION = _FRICTION_FALLBACK
MAP_RESISTANCE_EXTRACT = MAP_RESISTANCE_EXTRACT_FALLBACK
