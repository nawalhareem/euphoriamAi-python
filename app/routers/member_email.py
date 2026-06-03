from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.member_email import generate_member_email

router = APIRouter(prefix="/v1/member-email", tags=["member-email"])


class MemberEmailGenerateRequest(BaseModel):
    system_prompt: str = Field(..., min_length=20)
    email_type: str
    member_context: dict = Field(default_factory=dict)
    generation_constraints: dict | None = None
    correction_note: str | None = None


@router.post("/generate")
def post_generate_member_email(body: MemberEmailGenerateRequest):
    try:
        return generate_member_email(
            system_prompt=body.system_prompt,
            email_type=body.email_type,
            member_context=body.member_context,
            generation_constraints=body.generation_constraints,
            correction_note=body.correction_note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
