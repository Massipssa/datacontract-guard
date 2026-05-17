import asyncio
import sys
import unittest
from io import BytesIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.validation_service import ValidationService


class FakeUpload:
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self._stream = BytesIO(content)

    async def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)


class FastAPIValidationServiceTests(unittest.TestCase):
    def test_validate_uploads_returns_validation_report(self):
        data = (ROOT / "examples" / "customers_bad.csv").read_bytes()
        contract = (ROOT / "examples" / "customers_contract.yaml").read_bytes()

        report = asyncio.run(
            ValidationService().validate_uploads(
                data_file=FakeUpload("customers_bad.csv", data),
                contract_file=FakeUpload("customers_contract.yaml", contract),
                source_name="customers",
            )
        )

        self.assertEqual("FAIL", report["status"])
        self.assertIn("analysis", report)
        self.assertIn("generatedCode", report)
        self.assertIn("llmExplanation", report)
        self.assertEqual("validation_engine", report["llmExplanation"]["statusSource"])
        self.assertEqual("orchestrated_multi_agent", report["agent"]["mode"])


if __name__ == "__main__":
    unittest.main()
