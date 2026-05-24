from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.validations import router as validations_router


def cors_origins() -> list[str]:
    raw_value = os.environ.get(
        "DATA_CONTRACT_CORS_ORIGINS",
        "http://127.0.0.1:5173;http://localhost:5173",
    )
    return [item.strip() for item in raw_value.replace(",", ";").split(";") if item.strip()]


app = FastAPI(
    title="DataContract Guard API",
    version="0.1.0",
    description="Validate incoming data files against YAML data contracts.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(validations_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "datacontract-guard"}
