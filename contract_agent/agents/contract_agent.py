from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from contract_agent.adapters.schema_reader import read_contract
from contract_agent.agents.base import AgentStep, ok_step
from contract_agent.core.agent import DataContractAgent
from contract_agent.core.models import ContractReport, DataContract, Schema


@dataclass(frozen=True)
class ContractLoadResult:
    contract: DataContract
    step: AgentStep


@dataclass(frozen=True)
class ContractCompareResult:
    report: ContractReport
    step: AgentStep


class ContractAgent:
    name = "Contract Agent"

    def load(self, contract_path: Path | str, mcp_adapter: Any | None = None) -> ContractLoadResult:
        # If contract_path is a string and mcp_adapter is provided, fetch content from MCP
        if isinstance(contract_path, str) and mcp_adapter is not None:
            try:
                content = mcp_adapter.get_contract(contract_path)
                from contract_agent.adapters.mini_yaml import parse_contract_yaml
                from contract_agent.core.contract import contract_from_mapping

                contract = contract_from_mapping(parse_contract_yaml(content))
            except Exception:
                # if MCP fails, raise to signal inability to load contract
                raise
        else:
            contract = read_contract(contract_path) if isinstance(contract_path, Path) else read_contract(Path(str(contract_path)))
        step = ok_step(
            self.name,
            "YAML contract loaded and normalized.",
            contract=str(contract_path),
            contractName=contract.name,
            version=contract.version,
            owner=contract.owner,
            columnCount=len(contract.columns),
        )
        return ContractLoadResult(contract=contract, step=step)

    def compare(
        self,
        schema: Schema,
        contract: DataContract,
        allow_safe_promotion: bool = True,
        warn_extra_columns: bool = True,
    ) -> ContractCompareResult:
        report = DataContractAgent(
            allow_safe_promotion=allow_safe_promotion,
            warn_extra_columns=warn_extra_columns,
        ).evaluate(schema, contract)
        step = ok_step(
            self.name,
            "Source schema compared with the contract.",
            status=report.status,
            issueCount=len(report.issues),
            correctionCount=len(report.corrections),
        )
        return ContractCompareResult(report=report, step=step)
