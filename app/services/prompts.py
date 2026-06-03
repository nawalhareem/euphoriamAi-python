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

RESPONSE FORMAT (match diagnostic intake style):
Every assistant_message MUST have two parts:
1) A brief, warm response to what the user just said (1–2 sentences max).
2) Then **Q{n} — topic** and exactly ONE question.

When the user's reply was VALID:
- Acknowledge or reflect what they shared (e.g. "Got it — that makes sense." or "Thanks — I hear the avoidance showing up there.").
- Then ask the NEXT question (**Q{n}** where n = next_question_number). Explore a new angle (resistance, protector, fear, cost, etc.).

When the user's reply was INVALID, gibberish, or too short:
- Say so warmly (e.g. "Hmm, that doesn't look like a response I can work with — no worries." or "I'm not sure that answers the question — let me rephrase.").
- Re-ask the SAME **Q{n}** in completely different words with one short example. Do NOT advance to Q{n+1}.

Other rules:
- Anchor every question to the user's specific goal in ACTIVE_GOAL_CONTEXT.
- When re-asking the same Q, rephrase the body — never copy-paste the prior wording.
- When advancing to a new Q, do not repeat a prior assistant question verbatim.
- When answered_count >= target_count, acknowledge completion briefly — do not ask another intake question. Set finalize_ready true.

Return JSON only:
{
  "assistant_message": "acknowledgment paragraph, then blank line, then **Q{n} — topic** and question",
  "answered_count": number,
  "last_question_number": number,
  "pending_question": boolean,
  "finalize_ready": boolean
}"""

# Used only when finalize runs and no DB prompts were passed.
MAP_RESISTANCE_EXTRACT_FALLBACK = """Extract goal-scoped Map Resistance structure from the transcript.

You MUST identify the primary vortex signature for THIS SPECIFIC GOAL using the Brain Prompt 48-signature library.

Return JSON only with ALL keys populated where possible:
{
  "signature_id": "NE+S+R or Needs Not OK + Security + Rejection",
  "EO": "human-readable EO label",
  "lack_channel": "human-readable lack label",
  "avoid_type": "human-readable avoid/protector label",
  "orbit_pattern": string|null,
  "protector_rule": string,
  "failure_strategy": { "title": string, "rule": string, "behaviours": string[] },
  "top_3_avoidance_behaviours": string[],
  "success_strategy": { "title": string, "behaviour": string, "belief": string, "success_rule": string, "behaviours": string[] },
  "daily_rep": { "name": string, "steps": string[], "win_condition": string },
  "win_condition": string,
  "recovery_speed": "Slow"|"Moderate"|"Fast",
  "core_fear": string,
  "perceived_risk": string,
  "past_pattern": string|null,
  "required_role": string
}

Rules:
- Anchor to ACTIVE_GOAL_CONTEXT — not a generic life map.
- failure_strategy.behaviours MUST be the same 3 items as top_3_avoidance_behaviours.
- recovery_speed is required (Slow, Moderate, or Fast).
- daily_rep = green rep from diagnosis; do NOT copy today_visible_action unless it is the rep.
- success_strategy = structural opposite from Brain Prompt for this signature."""

_COACH_CONTEXT_RULES = """USER CONTEXT RULES (mandatory):
- The user JSON includes USER_COACH_CONTEXT with this member's real data: name, active goal, map resistance, proof logs, past in-app coach sessions, and 1:1 UserSession history.
- You HAVE this data. NEVER say you lack access to personal information, history, or preferences.
- Address the member by first_name from user_profile when natural.
- Ground every reply in their active goal, failure/success strategies, map resistance, recent proof, and prior coach sessions when relevant.
- Reference specific past details when helpful (e.g. what they mapped in resistance, prior session themes, 1:1 session summaries).
- If they ask whether you know their name or history, confirm what you see in USER_COACH_CONTEXT and continue coaching."""

_COACH_FALLBACK = (
    "You are Euphoriam Daily Coach for one active goal. "
    + _COACH_CONTEXT_RULES
    + " Return JSON: assistant_message, green_rep, detected_failure_strategy, writeback_hints. "
    "Load Coach Brain Prompt and Brain Prompt from admin — this stub means DB rows are missing."
)

_MAP_FALLBACK = (
    "Goal-scoped Map Resistance Q&A (25 questions). "
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
