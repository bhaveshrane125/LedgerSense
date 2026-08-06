# LedgerSense Synthetic Data Generator

Standalone synthetic invoice data generator for LedgerSense.

## Generate Data

```bash
python -m generator.main --pdf-count 40 --seed 42 --output data/output/demo
```

The generator creates:

- invoice PDFs in `pdfs/invoices/`
- matching ground-truth JSON files in `ground_truth/invoices/`
- mock ERP JSON files in `mock_erp/`
- `manifest.jsonl`
- `dataset_summary.json`
- `config_snapshot.yaml`

Receiving-side scenarios include partial receipts, missing delivered items, and wrong-item deliveries so the PO -> GRN -> invoice chain contains realistic operational mismatches.

Generated sample datasets live under `data/output/` so the repository can grow with application code, docs, and future experiments outside the data folder.

## Examples

```bash
python -m generator.main --pdf-count 100 --seed 2026 --output data/output/demo_100
python -m generator.main --pdf-count 50 --layouts MODERN,CLASSIC,INDUSTRIAL
python -m generator.main --pdf-count 60 --scenario CLEAN=0.50 --scenario PRICE_VARIANCE_OVER=0.50
python -m generator.main --config config/default.yaml --pdf-count 200
python -m generator.main --pdf-count 40 --output data/output/demo_docs --render-po-pdfs --render-grn-pdfs
```

CLI values override YAML configuration values.

Every PDF contains `SYNTHETIC TEST DOCUMENT - NOT FOR PAYMENT`.
