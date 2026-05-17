import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from contract_agent.agents.llm_explanation_agent import LLMExplanationAgent
from contract_agent.agents.orchestrator import AgentOrchestrator, AgentRunRequest
from contract_agent.api.http import evaluate_request
from contract_agent.enterprise.runtime import evaluate_files
from contract_agent.enterprise.security import SecurityError, require_api_key, resolve_allowed_path
from contract_agent.enterprise.settings import Settings
from contract_agent.evaluation import run_eval_file


class EnterpriseRuntimeTests(unittest.TestCase):
    def settings(self):
        return Settings.from_env(ROOT)

    def test_runtime_adds_trace_and_cost(self):
        result = evaluate_files(
            "examples/source_schema.json",
            "examples/customer_contract.yaml",
            self.settings(),
        )
        payload = result.as_dict()

        self.assertIn("trace", payload)
        self.assertIn("cost", payload)
        self.assertEqual("FAIL", payload["status"])

    def test_runtime_validates_csv_data_quality(self):
        result = evaluate_files(
            "examples/supplier_bad.csv",
            "examples/supplier_contract.yaml",
            self.settings(),
            source_name="supplier.payment_file",
        )
        checks = {issue["check"] for issue in result.as_dict()["issues"]}

        self.assertIn("column.renamed", checks)
        self.assertIn("value.format", checks)
        self.assertIn("value.type", checks)

    def test_runtime_returns_agent_analysis(self):
        result = evaluate_files(
            "examples/customers_bad.csv",
            "examples/customers_contract.yaml",
            self.settings(),
            source_name="customers",
        )
        payload = result.as_dict()

        self.assertEqual("Échec", payload["analysis"]["status"])
        self.assertTrue(any("mail" in item for item in payload["analysis"]["problems"]))
        self.assertTrue(any("customer_id" in item for item in payload["analysis"]["correctionPlan"]))

    def test_runtime_exposes_agent_outputs(self):
        result = evaluate_files(
            "examples/customers_bad.csv",
            "examples/customers_contract.yaml",
            self.settings(),
            source_name="customers",
        )
        payload = result.as_dict()

        self.assertEqual("orchestrated_multi_agent", payload["agent"]["mode"])
        self.assertTrue(any(item["language"] == "pyspark" for item in payload["generatedCode"]))
        self.assertEqual("FAIL", payload["llmExplanation"]["status"])
        self.assertEqual("validation_engine", payload["llmExplanation"]["statusSource"])
        self.assertIn("supplierMessage", payload["llmExplanation"])

    def test_orchestrator_runs_specialized_agents(self):
        run = AgentOrchestrator().run(
            AgentRunRequest(
                source_path=ROOT / "examples" / "customers_bad.csv",
                contract_path=ROOT / "examples" / "customers_contract.yaml",
                source_name="customers",
            )
        )
        step_names = {step.name for step in run.steps}

        self.assertIn("Agent Orchestrator", step_names)
        self.assertIn("Schema Agent", step_names)
        self.assertIn("Contract Agent", step_names)
        self.assertIn("Quality Agent", step_names)
        self.assertIn("Report Generator", step_names)
        self.assertIn("LLM Explanation Agent", step_names)
        self.assertTrue(any(snippet["language"] == "pyspark" for snippet in run.generated_code))

    def test_llm_explanation_agent_cannot_override_engine_status(self):
        report_payload = {
            "source": "customers",
            "status": "FAIL",
            "analysis": {
                "problems": ["email is missing"],
                "impacts": ["PII checks may be skipped"],
                "correctionPlan": ["rename mail to email"],
            },
        }

        result = LLMExplanationAgent(
            provider=lambda _: {
                "status": "PASS",
                "explanation": "Everything is fine",
                "businessImpact": "No impact",
                "proposedCorrection": "No fix",
                "supplierMessage": "Accepted",
            }
        ).generate(report_payload)

        self.assertEqual("FAIL", result.explanation.status)
        self.assertEqual("validation_engine", result.explanation.status_source)

    def test_api_request_uses_guardrails(self):
        payload = evaluate_request(
            {
                "sourceSchemaPath": "examples/source_schema.json",
                "contractPath": "examples/customer_contract.yaml",
            },
            self.settings(),
        )

        self.assertEqual("FAIL", payload["status"])
        self.assertIn("trace", payload)

    def test_path_outside_allowed_root_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                environment="test",
                allowed_roots=(Path(tmp).resolve(),),
                max_file_bytes=1024,
                max_columns=10,
                max_contract_columns=10,
                api_key="",
                log_level="INFO",
            )
            with self.assertRaises(SecurityError):
                resolve_allowed_path(str(ROOT / "examples" / "source_schema.json"), settings)

    def test_api_key_is_required_when_configured(self):
        settings = Settings(
            environment="test",
            allowed_roots=(ROOT,),
            max_file_bytes=1024,
            max_columns=10,
            max_contract_columns=10,
            api_key="secret",
            log_level="INFO",
        )

        require_api_key({"authorization": "Bearer secret"}, settings)
        with self.assertRaises(SecurityError):
            require_api_key({}, settings)

    def test_column_budget_is_enforced(self):
        settings = Settings(
            environment="test",
            allowed_roots=(ROOT,),
            max_file_bytes=1024 * 1024,
            max_columns=1,
            max_contract_columns=10,
            max_data_rows=1000,
            api_key="",
            log_level="INFO",
        )

        with self.assertRaises(ValueError):
            evaluate_files(
                "examples/source_schema.json",
                "examples/customer_contract.yaml",
                settings,
            )

    def test_evaluation_cases_pass(self):
        result = run_eval_file(ROOT / "examples" / "evaluation_cases.json", self.settings())

        self.assertTrue(result["passed"])


if __name__ == "__main__":
    unittest.main()
