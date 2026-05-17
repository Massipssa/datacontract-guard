from __future__ import annotations

import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any

from contract_agent.enterprise.runtime import evaluate_files
from contract_agent.enterprise.settings import Settings


DATA_SUFFIXES = {".csv", ".json", ".parquet"}
CONTRACT_SUFFIXES = {".yaml", ".yml", ".json"}
CHUNK_SIZE = 1024 * 1024


class ValidationService:
    async def validate_uploads(
        self,
        data_file: Any,
        contract_file: Any,
        source_name: str,
    ) -> dict[str, Any]:
        settings = Settings.from_env(Path.cwd())
        with tempfile.TemporaryDirectory(prefix="datacontract-guard-") as tmp:
            tmp_dir = Path(tmp).resolve()
            data_path = tmp_dir / upload_filename(data_file, "data", DATA_SUFFIXES)
            contract_path = tmp_dir / upload_filename(contract_file, "contract", CONTRACT_SUFFIXES)

            await save_upload(data_file, data_path, settings.max_file_bytes)
            await save_upload(contract_file, contract_path, settings.max_file_bytes)

            upload_settings = replace(settings, allowed_roots=(tmp_dir,))
            result = evaluate_files(
                source_schema_path=str(data_path),
                contract_path=str(contract_path),
                settings=upload_settings,
                source_name=source_name or data_path.stem,
                data_path=str(data_path),
                validate_data=True,
            )
            return result.as_dict()


def upload_filename(upload: Any, stem: str, allowed_suffixes: set[str]) -> str:
    original_name = str(getattr(upload, "filename", "") or "")
    suffix = Path(original_name).suffix.lower()
    if suffix not in allowed_suffixes:
        allowed = ", ".join(sorted(allowed_suffixes))
        raise ValueError(f"{stem}_file must use one of these extensions: {allowed}")
    return f"{stem}{suffix}"


async def save_upload(upload: Any, target: Path, max_bytes: int) -> None:
    written = 0
    with target.open("wb") as handle:
        while True:
            chunk = await upload.read(CHUNK_SIZE)
            if not chunk:
                break
            written += len(chunk)
            if written > max_bytes:
                raise ValueError(f"Uploaded file exceeds max size of {max_bytes} bytes")
            handle.write(chunk)
    if written == 0:
        raise ValueError("Uploaded file is empty")
