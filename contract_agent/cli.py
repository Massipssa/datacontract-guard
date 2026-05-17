from __future__ import annotations

import argparse
from pathlib import Path

from contract_agent.core.reporting import render_json, render_markdown
from contract_agent.enterprise.logging import configure_logging
from contract_agent.enterprise.runtime import evaluate_files
from contract_agent.enterprise.settings import Settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a source schema against a data contract.")
    parser.add_argument("--source-schema", required=True, type=Path, help="Source schema JSON or CSV sample.")
    parser.add_argument("--contract", required=True, type=Path, help="Data contract YAML or JSON.")
    parser.add_argument("--source-name", default="", help="Name to show in reports.")
    parser.add_argument("--output", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--report-file", type=Path, help="Optional path to write the report.")
    parser.add_argument("--data-file", type=Path, help="Optional CSV file to validate row values against the contract.")
    parser.add_argument("--skip-data-quality", action="store_true", help="Only validate schema compatibility.")
    parser.add_argument("--ignore-extra-columns", action="store_true", help="Do not report columns absent from the contract.")
    parser.add_argument("--no-safe-promotion", action="store_true", help="Treat safe type promotions as failures.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings.from_env(Path.cwd())
    configure_logging(settings.log_level)
    result = evaluate_files(
        source_schema_path=str(args.source_schema),
        contract_path=str(args.contract),
        settings=settings,
        source_name=args.source_name or None,
        allow_safe_promotion=not args.no_safe_promotion,
        warn_extra_columns=not args.ignore_extra_columns,
        data_path=str(args.data_file) if args.data_file else None,
        validate_data=not args.skip_data_quality,
    )
    rendered = (
        render_json(result)
        if args.output == "json"
        else render_markdown(result.report, result.agent.analysis, result.agent.generated_code)
    )
    if args.report_file:
        args.report_file.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return 1 if result.report.status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
