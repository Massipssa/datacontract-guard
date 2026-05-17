from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import uvicorn

app = FastAPI()

BASE = Path(__file__).resolve().parents[1] / "data"


@app.get("/contracts")
def get_contract(ref: str):
    # ref can be like 'example.yaml' or 'repo:example.yaml'
    part = ref.split(":", 1)[1] if ":" in ref else ref
    candidate = BASE / "contracts" / part
    if not candidate.exists():
        raise HTTPException(status_code=404, detail="contract not found")
    return {"content": candidate.read_text(encoding="utf-8")}


@app.get("/schema")
def get_schema(datasource: str, table: str):
    candidate = BASE / "schemas" / datasource / f"{table}.json"
    if not candidate.exists():
        raise HTTPException(status_code=404, detail="schema not found")
    import json

    return json.loads(candidate.read_text(encoding="utf-8"))


@app.get("/objects")
def list_objects(bucket: str, prefix: str = ""):
    bucket_dir = BASE / "objects" / bucket
    if not bucket_dir.exists():
        return []
    results = []
    for p in bucket_dir.rglob(f"{prefix}*"):
        results.append({"path": str(p.relative_to(bucket_dir)), "size": p.stat().st_size})
    return results


@app.post("/alerts")
def create_alert(payload: dict):
    # lightweight mock: accept anything and return an id
    return JSONResponse({"status": "ok", "id": "mock-alert-1"})


def run(port: int = 8001):
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    run()
