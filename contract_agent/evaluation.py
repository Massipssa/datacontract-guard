from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from contract_agent.enterprise.runtime import evaluate_files
from contract_agent.enterprise.settings import Settings


@dataclass(frozen=True)
class EvalResult:
    name: str
    passed: bool
    failures: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "passed": self.passed, "failures": self.failures}


def run_eval_file(path: Path, settings: Settings) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    results = [run_case(item, settings) for item in payload.get("cases", [])]
    return {
        "passed": all(result.passed for result in results),
        "caseCount": len(results),
        "results": [result.as_dict() for result in results],
    }


def run_case(payload: dict[str, Any], settings: Settings) -> EvalResult:
    name = str(payload.get("name") or "unnamed")
    result = evaluate_files(
        source_schema_path=str(payload["sourceSchemaPath"]),
        contract_path=str(payload["contractPath"]),
        settings=settings,
        source_name=payload.get("sourceName"),
        data_path=payload.get("dataFilePath"),
        validate_data=payload.get("validateData", True),
    )
    report = result.report.as_dict()
    expected = payload.get("expected") or {}
    failures = []
    if expected.get("status") and report["status"] != expected["status"]:
        failures.append(f"status expected {expected['status']} got {report['status']}")
    checks = {issue["check"] for issue in report["issues"]}
    for check in expected.get("checks", []):
        if check not in checks:
            failures.append(f"missing check {check}")
    actions = {correction["action"] for correction in report["corrections"]}
    for action in expected.get("corrections", []):
        if action not in actions:
            failures.append(f"missing correction {action}")
    return EvalResult(name=name, passed=not failures, failures=failures)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate Data Contract Agent responses.")
    parser.add_argument("--eval-file", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings.from_env(Path.cwd())
    result = run_eval_file(args.eval_file, settings)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
