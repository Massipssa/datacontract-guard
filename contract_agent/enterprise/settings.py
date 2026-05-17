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
        )


def resolve_roots(raw_value: str | None, base_dir: Path) -> list[Path]:
    if not raw_value:
        return [base_dir.resolve()]
    return [Path(item).expanduser().resolve() for item in raw_value.split(";") if item.strip()]
