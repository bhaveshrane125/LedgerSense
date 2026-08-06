import json
import tempfile
import unittest
from pathlib import Path

from generator.main import generate_dataset
from generator.models import GeneratorConfig


class GeneratorTests(unittest.TestCase):
    def test_generates_exact_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = GeneratorConfig(pdf_count=10, output_directory=tmp, seed=123)
            summary = generate_dataset(config)
            self.assertEqual(summary["requested_pdf_count"], 10)
            self.assertEqual(summary["generated_pdf_count"], 10)
            self.assertEqual(len(list((Path(tmp) / "pdfs" / "invoices").glob("*.pdf"))), 10)
            self.assertEqual(len(list((Path(tmp) / "ground_truth" / "invoices").glob("*.json"))), 10)
            self.assertEqual(len((Path(tmp) / "manifest.jsonl").read_text().splitlines()), 10)

    def test_same_seed_reproduces_manifest_scenarios_and_layouts(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            generate_dataset(GeneratorConfig(pdf_count=8, output_directory=first, seed=99))
            generate_dataset(GeneratorConfig(pdf_count=8, output_directory=second, seed=99))
            first_rows = [json.loads(line) for line in (Path(first) / "manifest.jsonl").read_text().splitlines()]
            second_rows = [json.loads(line) for line in (Path(second) / "manifest.jsonl").read_text().splitlines()]
            self.assertEqual(
                [(row["invoice_number"], row["scenario"], row["layout"]) for row in first_rows],
                [(row["invoice_number"], row["scenario"], row["layout"]) for row in second_rows],
            )

    def test_renders_po_and_grn_pdfs_when_enabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            summary = generate_dataset(
                GeneratorConfig(
                    pdf_count=6,
                    output_directory=tmp,
                    seed=12,
                    render_po_pdfs=True,
                    render_grn_pdfs=True,
                )
            )
            po_pdf_count = len(list((Path(tmp) / "pdfs" / "purchase_orders").glob("*.pdf")))
            grn_pdf_count = len(list((Path(tmp) / "pdfs" / "goods_receipts").glob("*.pdf")))
            self.assertEqual(summary["generated_po_pdf_count"], po_pdf_count)
            self.assertEqual(summary["generated_grn_pdf_count"], grn_pdf_count)
            self.assertGreater(po_pdf_count, 0)
            self.assertGreater(grn_pdf_count, 0)
            rows = [json.loads(line) for line in (Path(tmp) / "manifest.jsonl").read_text().splitlines()]
            self.assertTrue(any(row["po_pdf_path"] for row in rows))
            self.assertTrue(any(row["grn_pdf_path"] for row in rows))


if __name__ == "__main__":
    unittest.main()
