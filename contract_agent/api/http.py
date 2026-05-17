from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from contract_agent.enterprise.logging import configure_logging
from contract_agent.enterprise.runtime import evaluate_files
from contract_agent.enterprise.security import SecurityError, require_api_key
from contract_agent.enterprise.settings import Settings


BASE_DIR = Path(__file__).resolve().parents[2]
MAX_BODY_BYTES = 64 * 1024


class ContractServer(ThreadingHTTPServer):
    def __init__(
        self,
        address: tuple[str, int],
        handler: type[BaseHTTPRequestHandler],
        settings: Settings,
    ) -> None:
        super().__init__(address, handler)
        self.settings = settings


class Handler(BaseHTTPRequestHandler):
    server: ContractServer

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.write_json(
                {
                    "status": "ok",
                    "tool": "data-contract-agent",
                    "environment": self.server.settings.environment,
                    "authRequired": bool(self.server.settings.api_key),
                }
            )
            return
        self.write_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/evaluate":
            self.write_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")
            return
        try:
            require_api_key(headers={key.lower(): value for key, value in self.headers.items()}, settings=self.server.settings)
            payload = self.read_json_body()
            result = evaluate_request(payload, self.server.settings)
            self.write_json(result)
        except SecurityError as exc:
            self.write_error(HTTPStatus.FORBIDDEN, str(exc), code="security_error")
        except ValueError as exc:
            self.write_error(HTTPStatus.BAD_REQUEST, str(exc), code="invalid_request")
        except Exception as exc:  # pragma: no cover - API last line of defense.
            self.write_error(HTTPStatus.INTERNAL_SERVER_ERROR, f"Internal error: {exc}", code="internal_error")

    def read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        if length > MAX_BODY_BYTES:
            raise ValueError("Request body exceeds max size")
        raw = self.rfile.read(length).decode("utf-8")
        if not raw.strip():
            return {}
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object")
        return payload

    def write_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def write_error(self, status: HTTPStatus, message: str, code: str = "error") -> None:
        self.write_json({"error": {"code": code, "message": message}}, status)

    def log_message(self, format: str, *args: Any) -> None:
        return


def evaluate_request(payload: dict[str, Any], settings: Settings) -> dict[str, Any]:
    source_schema = payload.get("sourceSchemaPath")
    contract = payload.get("contractPath")
    if not source_schema or not contract:
        raise ValueError("sourceSchemaPath and contractPath are required")
    result = evaluate_files(
        source_schema_path=str(source_schema),
        contract_path=str(contract),
        settings=settings,
        source_name=payload.get("sourceName"),
        allow_safe_promotion=as_bool(payload.get("allowSafePromotion", True)),
        warn_extra_columns=as_bool(payload.get("warnExtraColumns", True)),
        data_path=payload.get("dataFilePath"),
        validate_data=as_bool(payload.get("validateData", True)),
    )
    return result.as_dict()


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in {"false", "0", "no", "off"}
    return bool(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Data Contract Agent API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8093)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings.from_env(BASE_DIR)
    configure_logging(settings.log_level)
    server = ContractServer((args.host, args.port), Handler, settings=settings)
    print(f"Data Contract Agent API listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server")
    finally:
        server.server_close()
    return 0
