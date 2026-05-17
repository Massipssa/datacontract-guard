from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.services.validation_service import ValidationService
from contract_agent.enterprise.security import SecurityError


router = APIRouter(tags=["validations"])


class ValidationReport(BaseModel):
    contract: str
    source: str
    status: str
    counts: dict[str, int]
    issues: list[dict[str, Any]]
    corrections: list[dict[str, Any]]
    analysis: dict[str, Any]
    recommendations: list[str]
    generated_code: list[dict[str, Any]] = Field(alias="generatedCode")
    llm_explanation: dict[str, Any] = Field(alias="llmExplanation")
    agent: dict[str, Any]
    trace: dict[str, Any]
    cost: dict[str, Any]


@router.post("/validate", response_model=ValidationReport)
async def validate(
    data_file: UploadFile = File(...),
    contract_file: UploadFile = File(...),
    source_name: str = Form("uploaded_dataset"),
) -> dict[str, Any]:
    try:
        return await ValidationService().validate_uploads(
            data_file=data_file,
            contract_file=contract_file,
            source_name=source_name,
        )
    except SecurityError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
