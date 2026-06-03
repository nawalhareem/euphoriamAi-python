from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.lead_email import generate_lead_email

router = APIRouter(prefix="/v1/lead-email", tags=["lead-email"])


class LeadEmailGenerateRequest(BaseModel):
    system_prompt: str = Field(..., min_length=20)
    lead_context: dict = Field(default_factory=dict)
    coaching_day: int | None = Field(default=None, ge=1, le=10)


@router.post("/generate")
def post_generate_lead_email(body: LeadEmailGenerateRequest):
    try:
        return generate_lead_email(
            system_prompt=body.system_prompt,
            lead_context=body.lead_context,
            coaching_day=body.coaching_day,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
