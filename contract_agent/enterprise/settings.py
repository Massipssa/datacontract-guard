from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    environment: str
    allowed_roots: tuple[Path, ...]
    max_file_bytes: int
    max_columns: int
    max_contract_columns: int
    api_key: str
    log_level: str
    max_data_rows: int = 1000
    docs_path: Path | None = None
    vector_store_path: Path | None = None
    enable_vector_store: bool = False
    mcp_url: str | None = None
    mcp_token: str | None = None

    @classmethod
    def from_env(cls, base_dir: Path) -> "Settings":
        allowed = os.environ.get("DATA_CONTRACT_ALLOWED_ROOTS")
        roots = tuple(resolve_roots(allowed, base_dir))
        return cls(
            environment=os.environ.get("DATA_CONTRACT_ENV", "local"),
            allowed_roots=roots,
            max_file_bytes=int(os.environ.get("DATA_CONTRACT_MAX_FILE_BYTES", str(5 * 1024 * 1024))),
            max_columns=int(os.environ.get("DATA_CONTRACT_MAX_COLUMNS", "500")),
            max_contract_columns=int(os.environ.get("DATA_CONTRACT_MAX_CONTRACT_COLUMNS", "500")),
            api_key=os.environ.get("DATA_CONTRACT_API_KEY", ""),
            log_level=os.environ.get("DATA_CONTRACT_LOG_LEVEL", "INFO"),
            max_data_rows=int(os.environ.get("DATA_CONTRACT_MAX_DATA_ROWS", "1000")),
            docs_path=Path(os.environ.get("DATA_CONTRACT_DOCS_PATH", str(base_dir / "docs"))) if os.environ.get("DATA_CONTRACT_DOCS_PATH") or (base_dir / "docs").exists() else None,
            vector_store_path=Path(os.environ.get("DATA_CONTRACT_VECTOR_STORE_PATH", str(base_dir / ".chroma_store"))),
            enable_vector_store=(os.environ.get("DATA_CONTRACT_ENABLE_VECTOR_STORE", "false").strip().lower() in {"1", "true", "yes"}),
            mcp_url=os.environ.get("DATA_CONTRACT_MCP_URL", None),
            mcp_token=os.environ.get("DATA_CONTRACT_MCP_TOKEN", None),
        )


def resolve_roots(raw_value: str | None, base_dir: Path) -> list[Path]:
    if not raw_value:
        return [base_dir.resolve()]
    return [Path(item).expanduser().resolve() for item in raw_value.split(";") if item.strip()]
