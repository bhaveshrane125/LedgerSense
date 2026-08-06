import json
import tempfile
import unittest
from pathlib import Path

from generator.main import generate_dataset
from generator.models import GeneratorConfig


class ScenarioTests(unittest.TestCase):
    def _single_scenario_truth(self, scenario):
        with tempfile.TemporaryDirectory() as tmp:
            generate_dataset(
                GeneratorConfig(
                    pdf_count=1,
                    output_directory=tmp,
                    scenario_weights={scenario: 1.0},
                )
            )
            truth_path = next((Path(tmp) / "ground_truth" / "invoices").glob("*.json"))
            return json.loads(truth_path.read_text())

    def test_missing_grn_has_no_grn_reference(self):
        truth = self._single_scenario_truth("MISSING_GRN")
        self.assertIsNone(truth["invoice"]["grn_reference"])

    def test_arithmetic_error_is_flagged(self):
        truth = self._single_scenario_truth("ARITHMETIC_ERROR")
        self.assertTrue(truth["source_contains_intentional_error"])
        self.assertNotEqual(truth["amounts"]["gross_total"], truth["amounts"]["printed_gross_total"])

    def test_missing_grn_renders_no_grn_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            summary = generate_dataset(
                GeneratorConfig(
                    pdf_count=3,
                    output_directory=tmp,
                    render_po_pdfs=True,
                    render_grn_pdfs=True,
                    scenario_weights={"MISSING_GRN": 1.0},
                )
            )
            self.assertEqual(summary["generated_pdf_count"], 3)
            self.assertEqual(summary["generated_po_pdf_count"], 3)
            self.assertEqual(summary["generated_grn_pdf_count"], 0)
            self.assertEqual(len(list((Path(tmp) / "pdfs" / "goods_receipts").glob("*.pdf"))), 0)

    def test_partial_receipt_marks_short_delivery_on_grn(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate_dataset(
                GeneratorConfig(
                    pdf_count=1,
                    output_directory=tmp,
                    scenario_weights={"PARTIAL_RECEIPT": 1.0},
                    render_grn_pdfs=True,
                )
            )
            grns = json.loads((Path(tmp) / "mock_erp" / "goods_receipts.json").read_text())
            partial_lines = [
                line for line in grns[0]["lines"] if line["receipt_status"] == "PARTIAL"
            ]
            self.assertEqual(len(partial_lines), 1)
            self.assertLess(
                int(partial_lines[0]["quantity_received"]),
                int(partial_lines[0]["quantity_ordered"]),
            )

    def test_wrong_item_delivery_marks_delivered_sku_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate_dataset(
                GeneratorConfig(
                    pdf_count=1,
                    output_directory=tmp,
                    scenario_weights={"WRONG_ITEM_DELIVERED": 1.0},
                    render_grn_pdfs=True,
                )
            )
            grns = json.loads((Path(tmp) / "mock_erp" / "goods_receipts.json").read_text())
            mismatches = [
                line for line in grns[0]["lines"] if line["receipt_status"] == "WRONG_ITEM"
            ]
            self.assertEqual(len(mismatches), 1)
            self.assertNotEqual(mismatches[0]["ordered_item_id"], mismatches[0]["item_id"])

    def test_items_missing_omits_a_grn_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate_dataset(
                GeneratorConfig(
                    pdf_count=1,
                    output_directory=tmp,
                    min_line_items=3,
                    max_line_items=3,
                    scenario_weights={"ITEMS_MISSING": 1.0},
                    render_grn_pdfs=True,
                )
            )
            grns = json.loads((Path(tmp) / "mock_erp" / "goods_receipts.json").read_text())
            purchase_orders = json.loads((Path(tmp) / "mock_erp" / "purchase_orders.json").read_text())
            self.assertEqual(len(purchase_orders[0]["lines"]), 3)
            self.assertEqual(len(grns[0]["lines"]), 2)


if __name__ == "__main__":
    unittest.main()
