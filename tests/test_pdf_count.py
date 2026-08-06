import tempfile
import unittest
from pathlib import Path

from generator.main import generate_dataset
from generator.models import GeneratorConfig


class PdfCountTests(unittest.TestCase):
    def test_one_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate_dataset(GeneratorConfig(pdf_count=1, output_directory=tmp))
            self.assertEqual(len(list((Path(tmp) / "pdfs" / "invoices").glob("*.pdf"))), 1)


if __name__ == "__main__":
    unittest.main()
