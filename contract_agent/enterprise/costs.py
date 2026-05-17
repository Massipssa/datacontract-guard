from __future__ import annotations

from dataclasses import dataclass

from contract_agent.core.models import DataContract, Schema
from contract_agent.enterprise.settings import Settings


@dataclass(frozen=True)
class CostSummary:
    source_columns: int
    contract_columns: int
    data_rows: int
    estimated_units: int
    max_columns: int
    max_contract_columns: int
    max_data_rows: int

    def as_dict(self) -> dict[str, int]:
        return {
            "sourceColumns": self.source_columns,
            "contractColumns": self.contract_columns,
            "dataRows": self.data_rows,
            "estimatedUnits": self.estimated_units,
            "maxColumns": self.max_columns,
            "maxContractColumns": self.max_contract_columns,
            "maxDataRows": self.max_data_rows,
        }


def estimate_cost(source: Schema, contract: DataContract, settings: Settings, data_rows: int = 0) -> CostSummary:
    source_columns = len(source.columns)
    contract_columns = len(contract.columns)
    return CostSummary(
        source_columns=source_columns,
        contract_columns=contract_columns,
        data_rows=data_rows,
        estimated_units=(source_columns * contract_columns) + (data_rows * contract_columns),
        max_columns=settings.max_columns,
        max_contract_columns=settings.max_contract_columns,
        max_data_rows=settings.max_data_rows,
    )


def enforce_budget(source: Schema, contract: DataContract, settings: Settings, data_rows: int = 0) -> CostSummary:
    summary = estimate_cost(source, contract, settings, data_rows=data_rows)
    if summary.source_columns > settings.max_columns:
        raise ValueError("Source schema exceeds max column budget")
    if summary.contract_columns > settings.max_contract_columns:
        raise ValueError("Contract exceeds max column budget")
    if summary.data_rows > settings.max_data_rows:
        raise ValueError("Source data exceeds max row budget")
    return summary
