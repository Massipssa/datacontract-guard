from __future__ import annotations

import os
import requests
from typing import Any


class MCPAdapter:
    """Minimal MCP adapter that talks to a central MCP HTTP server.

    Supports optional token-based authentication via constructor or
    `DATA_CONTRACT_MCP_TOKEN` environment variable. The adapter expects the MCP
    base URL to implement endpoints such as:
      - GET /contracts?ref=<repo:path>
      - GET /schema?datasource=<name>&table=<table>
      - GET /objects?bucket=<bucket>&prefix=<prefix>
      - POST /alerts

    This is intentionally small; adapt to your MCP API in production.
    """

    def __init__(self, base_url: str, token: str | None = None, timeout: int = 10) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        # token can be passed directly or read from env var
        self.token = token or os.environ.get("DATA_CONTRACT_MCP_TOKEN")

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def get_contract(self, ref: str) -> str:
        url = f"{self.base_url}/contracts"
        resp = requests.get(url, params={"ref": ref}, timeout=self.timeout, headers=self._headers())
        resp.raise_for_status()
        data = resp.json()
        # expect {'content': '...'} or {'files':[{'path':'...','content':'...'}]}
        if isinstance(data, dict) and data.get("content"):
            return data["content"]
        if isinstance(data, dict) and data.get("files"):
            files = data["files"]
            if files and isinstance(files, list):
                return files[0].get("content", "")
        raise ValueError("Invalid contract response from MCP")

    def get_schema(self, datasource: str, table: str) -> dict[str, Any]:
        url = f"{self.base_url}/schema"
        resp = requests.get(
            url, params={"datasource": datasource, "table": table}, timeout=self.timeout, headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()

    def list_objects(self, bucket: str, prefix: str) -> list[dict[str, Any]]:
        url = f"{self.base_url}/objects"
        resp = requests.get(url, params={"bucket": bucket, "prefix": prefix}, timeout=self.timeout, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def create_alert(self, channel: str, title: str, message: str) -> dict[str, Any]:
        url = f"{self.base_url}/alerts"
        resp = requests.post(
            url, json={"channel": channel, "title": title, "text": message}, timeout=self.timeout, headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()


class LocalMCPAdapter:
    """Local adapter implementing the same minimal interface as MCPAdapter.

    This is useful for offline development and tests: it reads files from a
    local `base_dir` under `tests/mocks/data` by default.
    """

    def __init__(self, base_dir: str | None = None):
        from pathlib import Path

        root = Path(base_dir) if base_dir else (Path(__file__).resolve().parents[2] / "tests" / "mocks" / "data")
        self.base_dir = root

    def get_contract(self, ref: str) -> str:
        from pathlib import Path

        # if ref contains a colon, use the part after the colon as a path
        part = ref.split(":", 1)[1] if ":" in ref else ref
        candidate = Path(self.base_dir) / "contracts" / part
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
        # try as direct path
        candidate = Path(part)
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
        raise FileNotFoundError(f"Local contract not found: {ref}")

    def get_schema(self, datasource: str, table: str) -> dict[str, Any]:
        from pathlib import Path
        import json

        candidate = Path(self.base_dir) / "schemas" / datasource / f"{table}.json"
        if candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8"))
        # fallback: check for a single schema file
        raise FileNotFoundError(f"Local schema not found: {datasource}.{table}")

    def list_objects(self, bucket: str, prefix: str) -> list[dict[str, Any]]:
        from pathlib import Path

        bucket_dir = Path(self.base_dir) / "objects" / bucket
        if not bucket_dir.exists():
            return []
        results = []
        for p in bucket_dir.rglob(f"{prefix}*"):
            results.append({"path": str(p.relative_to(bucket_dir)), "size": p.stat().st_size})
        return results

    def create_alert(self, channel: str, title: str, message: str) -> dict[str, Any]:
        # Append to a local alerts log for manual inspection
        import json
        from pathlib import Path

        log = Path(self.base_dir) / "alerts.log"
        entry = {"channel": channel, "title": title, "text": message}
        with log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
        return {"status": "created", "channel": channel, "title": title}
