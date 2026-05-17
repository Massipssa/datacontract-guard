from __future__ import annotations

from fastapi import FastAPI

from app.routes.validations import router as validations_router


app = FastAPI(
    title="DataContract Guard API",
    version="0.1.0",
    description="Validate incoming data files against YAML data contracts.",
)

app.include_router(validations_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "datacontract-guard"}
