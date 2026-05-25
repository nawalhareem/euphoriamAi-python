from openai import OpenAI

from app.config import settings

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def chat_json(system: str, user: str, *, model: str | None = None) -> dict:
    client = get_client()
    res = client.chat.completions.create(
        model=model or settings.openai_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_completion_tokens=2000,
    )
    import json

    raw = res.choices[0].message.content or "{}"
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def chat_text(system: str, messages: list[dict], *, model: str | None = None) -> str:
    client = get_client()
    res = client.chat.completions.create(
        model=model or settings.openai_model,
        messages=[{"role": "system", "content": system}, *messages],
        temperature=0.4,
        max_completion_tokens=1200,
    )
    return (res.choices[0].message.content or "").strip()
