from __future__ import annotations

from pathlib import Path

from contract_agent.enterprise.settings import Settings


class SecurityError(ValueError):
    """Raised when a request violates runtime guardrails."""


def resolve_allowed_path(raw_path: str, settings: Settings) -> Path:
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = settings.allowed_roots[0] / candidate
    resolved = candidate.resolve()
    if not any(is_relative_to(resolved, root) for root in settings.allowed_roots):
        raise SecurityError("Path is outside allowed roots")
    if not resolved.is_file():
        raise SecurityError(f"File does not exist: {resolved}")
    if resolved.stat().st_size > settings.max_file_bytes:
        raise SecurityError(f"File exceeds max size: {resolved}")
    return resolved


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def require_api_key(headers: dict[str, str], settings: Settings) -> None:
    if not settings.api_key:
        return
    provided = headers.get("authorization", "")
    expected = f"Bearer {settings.api_key}"
    if provided != expected:
        raise SecurityError("Invalid or missing API key")


def redact_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 6:
        return "***"
    return f"{value[:2]}***{value[-2:]}"
