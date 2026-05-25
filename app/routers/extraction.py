from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.map_resistance import extract_domain_structure

router = APIRouter(prefix="/v1/extraction", tags=["extraction"])


class DomainStructureRequest(BaseModel):
    transcript: list[dict] = Field(default_factory=list)
    active_goal_context: dict = Field(default_factory=dict)
    domain: str = "income"


@router.post("/domain-structure")
def post_domain_structure(body: DomainStructureRequest):
    structure = extract_domain_structure(
        transcript=body.transcript,
        active_goal_context=body.active_goal_context,
        domain=body.domain,
    )
    return {"structure": structure}
