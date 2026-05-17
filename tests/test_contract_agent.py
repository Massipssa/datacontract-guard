import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from contract_agent.adapters.schema_reader import read_contract, read_source_schema
from contract_agent.core.agent import DataContractAgent
from contract_agent.core.data_quality import DataQualityAgent
from contract_agent.core.explainer import explain_report


class DataContractAgentTests(unittest.TestCase):
    def test_detects_missing_columns_and_type_changes(self):
        contract = read_contract(ROOT / "examples" / "customer_contract.yaml")
        source = read_source_schema(ROOT / "examples" / "source_schema.json")

        report = DataContractAgent().evaluate(source, contract)
        checks = {issue.check for issue in report.issues}

        self.assertEqual("FAIL", report.status)
        self.assertIn("column.missing", checks)
        self.assertIn("type.change", checks)

    def test_generates_corrections(self):
        contract = read_contract(ROOT / "examples" / "customer_contract.yaml")
        source = read_source_schema(ROOT / "examples" / "source_schema.json")

        report = DataContractAgent().evaluate(source, contract)
        actions = {correction.action for correction in report.corrections}

        self.assertIn("CAST_SOURCE_COLUMN", actions)
        self.assertIn("ADD_SOURCE_COLUMN", actions)
        self.assertIn("ADD_CONTRACT_COLUMN", actions)

    def test_reads_csv_source_schema(self):
        source = read_source_schema(ROOT / "examples" / "source_sample.csv")

        by_name = source.by_name()
        self.assertEqual("long", by_name["customer_id"].type)
        self.assertEqual("boolean", by_name["marketing_opt_in"].type)

    def test_detects_renamed_columns(self):
        contract = read_contract(ROOT / "examples" / "supplier_contract.yaml")
        source = read_source_schema(ROOT / "examples" / "supplier_bad.csv")

        report = DataContractAgent().evaluate(source, contract)
        checks = {issue.check for issue in report.issues}
        actions = {correction.action for correction in report.corrections}

        self.assertIn("column.renamed", checks)
        self.assertIn("RENAME_SOURCE_COLUMN", actions)

    def test_detects_data_quality_issues(self):
        contract = read_contract(ROOT / "examples" / "supplier_contract.yaml")
        rows = [
            {"customer_id": "123", "email": "test@gmail.com", "birth_date": "01/01/1990", "amount": "25.5"},
            {"customer_id": "124", "email": "invalid-email", "birth_date": "1991-02-03", "amount": "bad"},
        ]

        report = DataQualityAgent().evaluate_rows(rows, contract, "supplier.payment_file")
        checks = {issue.check for issue in report.issues}
        actions = {correction.action for correction in report.corrections}

        self.assertIn("value.format", checks)
        self.assertIn("value.pattern", checks)
        self.assertIn("value.type", checks)
        self.assertIn("NORMALIZE_DATE_FORMAT", actions)

    def test_detects_min_value_rule(self):
        contract = read_contract(ROOT / "examples" / "customers_contract.yaml")
        rows = [
            {"customer_id": "123", "email": "test@gmail.com", "birth_date": "1990-01-01", "amount": "-1"},
        ]

        report = DataQualityAgent().evaluate_rows(rows, contract, "customers")
        checks = {issue.check for issue in report.issues}
        actions = {correction.action for correction in report.corrections}

        self.assertIn("value.min", checks)
        self.assertIn("ENFORCE_MIN_VALUE", actions)

    def test_explainer_connects_rename_to_business_impact(self):
        contract = read_contract(ROOT / "examples" / "customers_contract.yaml")
        source = read_source_schema(ROOT / "examples" / "customers_bad.csv")
        report = DataContractAgent().evaluate(source, contract)

        analysis = explain_report(report)

        self.assertIn("Échec", analysis["status"])
        self.assertTrue(any("renommé" in item for item in analysis["probableCauses"]))
        self.assertTrue(any("RGPD" in item for item in analysis["impacts"]))


if __name__ == "__main__":
    unittest.main()
