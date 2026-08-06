import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from generator.main import generate_dataset
from generator.models import GeneratorConfig


class TotalsTests(unittest.TestCase):
    def test_clean_totals_reconcile(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate_dataset(
                GeneratorConfig(
                    pdf_count=1,
                    output_directory=tmp,
                    scenario_weights={"CLEAN": 1.0},
                )
            )
            truth = json.loads(next((Path(tmp) / "ground_truth" / "invoices").glob("*.json")).read_text())
            subtotal = Decimal(truth["amounts"]["subtotal"])
            tax = Decimal(truth["amounts"]["tax"])
            freight = Decimal(truth["amounts"]["freight"])
            discount = Decimal(truth["amounts"]["discount"])
            gross = Decimal(truth["amounts"]["gross_total"])
            self.assertEqual(subtotal + tax + freight - discount, gross)


if __name__ == "__main__":
    unittest.main()
