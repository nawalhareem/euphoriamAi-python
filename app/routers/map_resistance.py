from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.map_resistance import extract_domain_structure, map_resistance_turn

router = APIRouter(prefix="/v1/map-resistance", tags=["map-resistance"])


class TurnRequest(BaseModel):
    active_goal_context: dict = Field(default_factory=dict)
    transcript: list[dict] = Field(default_factory=list)
    messages: list[dict] | None = None
    target_count: int = 12
    user_name: str = "there"
    prompts: dict | None = None


@router.post("/turn")
def post_turn(body: TurnRequest):
    transcript = body.transcript or body.messages or []
    return map_resistance_turn(
        active_goal_context=body.active_goal_context,
        transcript=transcript,
        target_count=body.target_count,
        user_name=body.user_name,
        prompts=body.prompts,
    )


class FinalizeRequest(BaseModel):
    active_goal_context: dict = Field(default_factory=dict)
    transcript: list[dict] = Field(default_factory=list)
    domain: str = "income"
    prompts: dict | None = None


@router.post("/finalize")
def post_finalize(body: FinalizeRequest):
    structure = extract_domain_structure(
        transcript=body.transcript,
        active_goal_context=body.active_goal_context,
        domain=body.domain,
        prompts=body.prompts,
    )
    return {"structure": structure, "domain_structure": structure}
