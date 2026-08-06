# LedgerSense Synthetic Data Generator — Implementation Plan

## 1. Objective

Build a standalone synthetic data generator for LedgerSense that creates fictional invoice PDFs together with their exact ground-truth JSON records.

The generator must allow the user to control:

- How many invoice PDFs are generated
- Which invoice layouts are used
- Which exception scenarios are included
- The number of line items per invoice
- The random seed for reproducibility
- The output directory

This generator is only responsible for creating synthetic test data. It does not perform document extraction, OpenAI API calls, invoice matching, RAG, policy checks, or ERP posting.

---

## 2. Main Requirement

The most important input is:

```text
pdf_count
```

`pdf_count` represents the exact number of invoice PDFs to generate.

Example:

```text
pdf_count = 50
```

Expected result:

```text
50 invoice PDF files
50 matching ground-truth JSON files
1 manifest.jsonl
1 dataset_summary.json
Mock vendor, item, PO, and GRN JSON files
```

The generator must verify that:

```text
generated_pdf_count == requested_pdf_count
```

If the counts do not match, the generator must fail clearly and report the missing or failed records.

---

## 3. Scope

### Included

- Synthetic vendors
- Synthetic items
- Synthetic purchase orders
- Synthetic goods receipt notes
- Synthetic invoice records
- Invoice PDF generation
- Multiple invoice layouts
- Configurable exception scenarios
- Ground-truth JSON for every invoice
- Dataset manifest
- Dataset summary
- Reproducible generation using a seed
- CLI-based controls
- Optional simple web form

### Not Included

- OpenAI API
- OCR
- Document extraction
- Semantic line matching
- RAG
- Contract retrieval
- Human approval workflow
- Real SAP or Oracle integration
- Database storage
- Vendor email generation

---

## 4. Recommended Technology

| Component | Technology |
|---|---|
| Language | Python 3.12 |
| Data models | Pydantic v2 |
| Fake company data | Faker |
| Financial calculations | Python `Decimal` |
| PDF generation | ReportLab |
| Configuration | YAML |
| Command-line interface | Typer or argparse |
| Testing | pytest |
| Property testing | hypothesis |

ReportLab is recommended for the first version because it can generate PDFs directly without requiring a browser-rendering engine.

---

## 5. Project Structure

```text
synthetic-data-generator/
├── generator/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── master_data.py
│   ├── transaction_factory.py
│   ├── scenario_engine.py
│   ├── pdf_renderer.py
│   ├── ground_truth.py
│   ├── manifest.py
│   └── utils.py
│
├── layouts/
│   ├── modern.py
│   ├── classic.py
│   ├── compact.py
│   ├── industrial.py
│   └── minimal.py
│
├── config/
│   └── default.yaml
│
├── output/
│
├── tests/
│   ├── test_config.py
│   ├── test_generator.py
│   ├── test_scenarios.py
│   ├── test_pdf_count.py
│   └── test_totals.py
│
├── requirements.txt
├── README.md
└── plan.md
```

---

## 6. Generator Inputs

### Required input

| Field | Type | Description |
|---|---|---|
| `pdf_count` | Integer | Exact number of invoice PDFs to create |

### Optional inputs

| Field | Type | Default | Description |
|---|---|---:|---|
| `output_directory` | String | `output/` | Dataset destination |
| `seed` | Integer | `42` | Reproducible random generation |
| `currency` | String | `INR` | Currency used in invoices |
| `locale` | String | `en_IN` | Faker locale |
| `min_line_items` | Integer | `1` | Minimum invoice lines |
| `max_line_items` | Integer | `8` | Maximum invoice lines |
| `layouts` | List | All | Enabled PDF layouts |
| `scenario_weights` | Object | Balanced | Percentage of each scenario |
| `vendor_count` | Integer | `5` | Number of fictional vendors |
| `item_count` | Integer | `30` | Size of item catalogue |
| `add_noise` | Boolean | `false` | Simulate scanned documents |
| `add_rotation` | Boolean | `false` | Slightly rotate selected pages |
| `render_po_pdfs` | Boolean | `false` | Also render PO PDFs |
| `render_grn_pdfs` | Boolean | `false` | Also render GRN PDFs |

---

## 7. Configuration File

Create:

```text
config/default.yaml
```

Example:

```yaml
dataset:
  name: ledgersense_synthetic_v1
  pdf_count: 40
  output_directory: output
  seed: 42

master_data:
  locale: en_IN
  currency: INR
  vendor_count: 5
  item_count: 30

invoice:
  min_line_items: 1
  max_line_items: 8
  layouts:
    - MODERN
    - CLASSIC
    - COMPACT
    - INDUSTRIAL
    - MINIMAL

scenarios:
  CLEAN: 0.35
  PRICE_VARIANCE_OVER: 0.20
  QTY_OVER_BILLED: 0.15
  MISSING_GRN: 0.10
  UOM_MISMATCH: 0.10
  DUPLICATE_CONFIRMED: 0.05
  ARITHMETIC_ERROR: 0.05

rendering:
  add_noise: false
  add_rotation: false
  render_po_pdfs: false
  render_grn_pdfs: false
```

All scenario weights must sum to `1.0`.

---

## 8. Command-Line Controls

### Generate 40 PDFs

```bash
python -m generator.main --pdf-count 40
```

### Generate 100 PDFs with a fixed seed

```bash
python -m generator.main   --pdf-count 100   --seed 2026   --output output/demo_100
```

### Use selected layouts

```bash
python -m generator.main   --pdf-count 50   --layouts MODERN,CLASSIC,INDUSTRIAL
```

### Generate only clean and price-variance cases

```bash
python -m generator.main   --pdf-count 60   --scenario CLEAN=0.50   --scenario PRICE_VARIANCE_OVER=0.50
```

### Use a YAML configuration

```bash
python -m generator.main   --config config/default.yaml   --pdf-count 200
```

CLI values should override YAML values.

---

## 9. Optional Web Form

A small Streamlit or FastAPI interface may be added later.

Suggested controls:

```text
Number of invoice PDFs: [40]

Random seed: [42]

Minimum line items: [1]
Maximum line items: [8]

Layouts:
[x] Modern
[x] Classic
[x] Compact
[x] Industrial
[x] Minimal

Scenarios:
Clean                  [35%]
Price variance         [20%]
Quantity over-billed   [15%]
Missing GRN            [10%]
UOM mismatch           [10%]
Duplicate               [5%]
Arithmetic error        [5%]

[Generate Dataset]
```

The page should display:

```text
Requested PDFs: 40
Generated PDFs: 40
Failed PDFs: 0
```

---

## 10. Synthetic Master Data

### Vendors

Generate fictional vendors containing:

- `vendor_id`
- Legal name
- Trading name
- GSTIN or fictional tax ID
- Address
- Email
- Payment terms
- Bank fingerprint
- Preferred invoice layout
- Vendor-specific item aliases

Example:

```json
{
  "vendor_id": "VEN-001",
  "legal_name": "Aarav Industrial Supplies Pvt Ltd",
  "tax_id": "27ABCDE1234F1Z5",
  "payment_terms": "NET 30",
  "preferred_layout": "INDUSTRIAL"
}
```

Use fictional names and identifiers only.

### Items

Generate a catalogue containing:

- `item_id`
- Internal SKU
- Canonical description
- Category
- Base UOM
- Unit price
- Tax rate
- Vendor aliases
- UOM conversions

Example:

```json
{
  "item_id": "ITEM-001",
  "sku": "BLT-M8-040-ZN",
  "description": "M8x40 Hex Bolt Zinc",
  "category": "FASTENERS",
  "base_uom": "EA",
  "unit_price": "10.00",
  "aliases": [
    "Bolt Hex Zn M8 40mm",
    "M8 X 40 HEX BOLT ZINC"
  ],
  "uom_conversions": {
    "BOX": "12"
  }
}
```

### Purchase Orders

Generate one PO for each synthetic invoice or reuse selected POs when testing partial invoices and duplicates.

PO fields:

- PO number
- Vendor ID
- PO date
- Currency
- Line items
- Ordered quantity
- UOM
- Unit price
- Tax rate
- Total amount

### Goods Receipts

Generate GRNs linked to PO lines.

GRN fields:

- GRN number
- PO number
- Receipt date
- Quantity received
- Quantity rejected
- UOM
- Condition note

For `MISSING_GRN`, no GRN should be generated for the related PO.

---

## 11. Invoice Generation

For every invoice:

1. Select a vendor.
2. Select one or more items.
3. Create a purchase order.
4. Create a GRN unless the scenario is `MISSING_GRN`.
5. Generate a clean invoice from the PO and GRN.
6. Select an exception scenario.
7. Modify the invoice according to the selected scenario.
8. Calculate totals with Python `Decimal`.
9. Select a PDF layout.
10. Render the invoice PDF.
11. Save the exact invoice object as ground-truth JSON.
12. Add the record to the manifest.

---

## 12. Supported Scenarios

### `CLEAN`

Invoice, PO, and GRN agree.

Expected label:

```text
CLEAN
```

### `PRICE_VARIANCE_OVER`

The invoice unit price is higher than the PO unit price.

Example:

```text
PO price:      ₹100.00
Invoice price: ₹110.00
```

Expected label:

```text
PRICE_VARIANCE_OVER
```

### `QTY_OVER_BILLED`

Invoice quantity exceeds received quantity.

Example:

```text
Ordered: 100
Received: 80
Invoiced: 100
```

Expected label:

```text
QTY_OVER_BILLED
```

### `MISSING_GRN`

A PO exists, but no GRN exists.

Expected label:

```text
MISSING_GRN
```

### `UOM_MISMATCH`

PO and invoice use different units.

Example:

```text
PO:      10 BOX
Invoice: 120 EA
```

The scenario may include either:

- A valid conversion
- A deliberately missing conversion

Expected label:

```text
UOM_MISMATCH
```

### `DUPLICATE_CONFIRMED`

Generate a second invoice with the same:

- Vendor
- Invoice number
- Invoice date
- Gross amount
- Line items

Expected label:

```text
DUPLICATE_CONFIRMED
```

### `ARITHMETIC_ERROR`

The amount printed on the source PDF intentionally fails to reconcile.

Example:

```text
Calculated gross total: ₹1,416.00
Printed gross total:    ₹1,415.00
```

Expected label:

```text
ARITHMETIC_ERROR
```

The ground-truth JSON must clearly indicate that the source document intentionally contains the error.

---

## 13. PDF Layouts

Start with five layouts.

### Modern

- Large vendor header
- Clean two-column metadata
- Coloured or shaded table header
- Totals aligned right

### Classic

- Traditional invoice appearance
- Bordered sections
- Dense metadata
- Standard line-item table

### Compact

- Small margins
- Tight line spacing
- Minimal decoration
- Suitable for many line items

### Industrial

- Bold PO and invoice references
- Warehouse-style table
- Item codes prominently shown

### Minimal

- Mostly text
- Few borders
- Simple alignment
- Good test for layout variation

Each layout must show the same underlying invoice data differently.

---

## 14. PDF Marking

Every generated PDF must visibly contain:

```text
SYNTHETIC TEST DOCUMENT — NOT FOR PAYMENT
```

This avoids accidental use as a real financial document.

Do not use:

- Real company logos
- Real bank account details
- Real GSTINs
- Real supplier identities
- Real customer data

---

## 15. Output Structure

```text
output/
└── dataset_2026_001/
    ├── config_snapshot.yaml
    ├── dataset_summary.json
    ├── manifest.jsonl
    │
    ├── pdfs/
    │   ├── invoices/
    │   │   ├── INV-000001.pdf
    │   │   ├── INV-000002.pdf
    │   │   └── ...
    │   ├── purchase_orders/
    │   └── goods_receipts/
    │
    ├── ground_truth/
    │   ├── invoices/
    │   │   ├── INV-000001.json
    │   │   ├── INV-000002.json
    │   │   └── ...
    │   ├── purchase_orders/
    │   └── goods_receipts/
    │
    └── mock_erp/
        ├── vendors.json
        ├── items.json
        ├── uom_conversions.json
        ├── purchase_orders.json
        └── goods_receipts.json
```

---

## 16. Ground-Truth JSON

Each invoice PDF must have a matching JSON file.

Example:

```json
{
  "dataset_id": "DS-001",
  "document_id": "DOC-000001",
  "invoice_number": "INV-000001",
  "scenario": "PRICE_VARIANCE_OVER",
  "layout": "INDUSTRIAL",
  "vendor": {
    "vendor_id": "VEN-001",
    "name": "Aarav Industrial Supplies Pvt Ltd"
  },
  "invoice": {
    "invoice_date": "2026-08-01",
    "po_reference": "PO-000001",
    "currency": "INR"
  },
  "line_items": [
    {
      "line_number": 1,
      "sku": "BLT-M8-040-ZN",
      "description": "Bolt Hex Zn M8 40mm",
      "quantity": "120",
      "uom": "EA",
      "unit_price": "11.00",
      "line_total": "1320.00"
    }
  ],
  "amounts": {
    "subtotal": "1320.00",
    "tax": "237.60",
    "freight": "0.00",
    "discount": "0.00",
    "gross_total": "1557.60"
  },
  "expected_exception_codes": [
    "PRICE_VARIANCE_OVER"
  ],
  "source_contains_intentional_error": false
}
```

---

## 17. Manifest

Use JSONL so each line represents one generated invoice.

Example:

```json
{
  "generation_index": 1,
  "invoice_number": "INV-000001",
  "po_number": "PO-000001",
  "grn_number": "GRN-000001",
  "scenario": "PRICE_VARIANCE_OVER",
  "layout": "INDUSTRIAL",
  "pdf_path": "pdfs/invoices/INV-000001.pdf",
  "ground_truth_path": "ground_truth/invoices/INV-000001.json",
  "sha256": "a94d...",
  "seed": 42
}
```

---

## 18. Dataset Summary

Create:

```text
dataset_summary.json
```

Example:

```json
{
  "dataset_id": "DS-001",
  "generator_version": "0.1.0",
  "seed": 42,
  "requested_pdf_count": 40,
  "generated_pdf_count": 40,
  "failed_pdf_count": 0,
  "layout_distribution": {
    "MODERN": 8,
    "CLASSIC": 8,
    "COMPACT": 8,
    "INDUSTRIAL": 8,
    "MINIMAL": 8
  },
  "scenario_distribution": {
    "CLEAN": 14,
    "PRICE_VARIANCE_OVER": 8,
    "QTY_OVER_BILLED": 6,
    "MISSING_GRN": 4,
    "UOM_MISMATCH": 4,
    "DUPLICATE_CONFIRMED": 2,
    "ARITHMETIC_ERROR": 2
  }
}
```

---

## 19. Generation Algorithm

```text
Read configuration
       ↓
Validate pdf_count
       ↓
Validate scenario weights
       ↓
Set random seed
       ↓
Create output directories
       ↓
Generate vendors
       ↓
Generate item catalogue
       ↓
Repeat exactly pdf_count times
       ↓
Generate PO
       ↓
Generate GRN if applicable
       ↓
Generate clean invoice
       ↓
Inject selected scenario
       ↓
Validate totals and relationships
       ↓
Render PDF
       ↓
Save ground-truth JSON
       ↓
Append manifest entry
       ↓
Count generated invoice PDFs
       ↓
Verify count equals pdf_count
       ↓
Write dataset summary
```

---

## 20. Pseudocode

```python
def generate_dataset(config: GeneratorConfig) -> DatasetSummary:
    validate_config(config)

    rng = Random(config.seed)
    paths = create_output_directories(config.output_directory)

    vendors = generate_vendors(
        rng=rng,
        count=config.vendor_count,
        locale=config.locale,
    )

    items = generate_items(
        rng=rng,
        count=config.item_count,
        currency=config.currency,
    )

    purchase_orders = []
    goods_receipts = []
    manifest = []

    for index in range(1, config.pdf_count + 1):
        vendor = rng.choice(vendors)
        scenario = choose_scenario(rng, config.scenario_weights)

        po = generate_purchase_order(
            rng=rng,
            vendor=vendor,
            items=items,
            index=index,
        )

        grn = generate_goods_receipt(
            rng=rng,
            purchase_order=po,
            scenario=scenario,
        )

        invoice = generate_invoice(
            rng=rng,
            purchase_order=po,
            goods_receipt=grn,
            index=index,
        )

        invoice = inject_scenario(
            invoice=invoice,
            purchase_order=po,
            goods_receipt=grn,
            scenario=scenario,
            rng=rng,
        )

        validate_ground_truth(
            invoice=invoice,
            purchase_order=po,
            goods_receipt=grn,
            scenario=scenario,
        )

        layout = rng.choice(config.layouts)

        pdf_path = render_invoice_pdf(
            invoice=invoice,
            layout=layout,
            output_directory=paths.invoice_pdfs,
        )

        truth_path = save_ground_truth(
            invoice=invoice,
            purchase_order=po,
            goods_receipt=grn,
            scenario=scenario,
            layout=layout,
            output_directory=paths.invoice_ground_truth,
        )

        manifest.append(
            create_manifest_record(
                index=index,
                invoice=invoice,
                purchase_order=po,
                goods_receipt=grn,
                scenario=scenario,
                layout=layout,
                pdf_path=pdf_path,
                truth_path=truth_path,
            )
        )

        purchase_orders.append(po)

        if grn is not None:
            goods_receipts.append(grn)

    save_mock_erp_files(
        vendors=vendors,
        items=items,
        purchase_orders=purchase_orders,
        goods_receipts=goods_receipts,
        output_directory=paths.mock_erp,
    )

    save_manifest(manifest, paths.manifest)

    generated_count = count_pdfs(paths.invoice_pdfs)

    if generated_count != config.pdf_count:
        raise PdfCountMismatchError(
            requested=config.pdf_count,
            generated=generated_count,
        )

    return save_dataset_summary(
        config=config,
        manifest=manifest,
        generated_count=generated_count,
        output_path=paths.summary,
    )
```

---

## 21. Validation Rules

Before rendering an invoice:

- Vendor must exist
- PO must exist
- Every invoice line must reference a valid item
- Quantities must be positive
- Unit prices must be non-negative
- Currency must be present
- Clean invoices must reconcile exactly
- Defective invoices must contain only the intended defect unless multi-defect mode is enabled
- Duplicate records must reference an earlier invoice
- Missing-GRN records must not create a GRN
- All money calculations must use `Decimal`

After rendering:

- PDF must exist
- PDF must be non-empty
- Ground-truth JSON must exist
- PDF SHA-256 must be stored
- Manifest entry must exist
- Final invoice PDF count must equal `pdf_count`

---

## 22. Testing Plan

### Unit Tests

- Reject `pdf_count = 0`
- Reject negative `pdf_count`
- Reject non-integer `pdf_count`
- Scenario weights must sum to `1.0`
- `min_line_items` cannot exceed `max_line_items`
- Same seed produces the same synthetic records
- Decimal totals reconcile
- Each scenario changes the intended field
- Generated filenames are unique

### Integration Tests

Generate:

```text
1 PDF
10 PDFs
40 PDFs
100 PDFs
```

For each run verify:

```text
number of invoice PDFs == requested pdf_count
number of invoice JSON files == requested pdf_count
manifest records == requested pdf_count
```

### Scenario Tests

- Clean invoice has no exception
- Price variance changes price only
- Quantity over-billed changes quantity only
- Missing GRN creates no GRN
- UOM mismatch changes unit representation
- Duplicate references an existing invoice
- Arithmetic error fails reconciliation intentionally

### PDF Tests

- PDF opens successfully
- Required fields are visible
- Synthetic watermark is present
- Each layout renders correctly
- Long descriptions wrap correctly
- Multi-line invoices do not overflow the page

---

## 23. Implementation Phases

### Phase 1 — Core Models

Build:

- Configuration model
- Vendor model
- Item model
- PO model
- GRN model
- Invoice model
- Money helpers using `Decimal`

### Phase 2 — Master Data

Build:

- Vendor generator
- Item generator
- UOM conversion generator

### Phase 3 — Transaction Generator

Build:

- Purchase-order generator
- GRN generator
- Clean invoice generator

### Phase 4 — Scenario Engine

Implement:

- `CLEAN`
- `PRICE_VARIANCE_OVER`
- `QTY_OVER_BILLED`
- `MISSING_GRN`
- `UOM_MISMATCH`
- `DUPLICATE_CONFIRMED`
- `ARITHMETIC_ERROR`

### Phase 5 — PDF Renderer

Build:

- One initial layout
- Synthetic watermark
- Invoice table
- Totals section
- Multi-page support

Then expand to five layouts.

### Phase 6 — Output Files

Build:

- Ground-truth JSON
- Mock ERP JSON
- Manifest JSONL
- Dataset summary
- SHA-256 calculation

### Phase 7 — Count Control

Build:

- `--pdf-count`
- Final count assertion
- Failure reporting
- Exact output summary

### Phase 8 — Testing

Build:

- Unit tests
- Integration tests
- Scenario tests
- PDF rendering tests

---

## 24. Acceptance Criteria

The synthetic data generator is complete when:

1. The user can specify the exact number of invoice PDFs.
2. The system generates exactly that number.
3. Every PDF has a matching ground-truth JSON file.
4. Every invoice references valid synthetic vendor and PO data.
5. GRNs are generated correctly except for missing-GRN scenarios.
6. At least five layouts are available.
7. At least seven scenarios are available.
8. The same seed reproduces the same underlying data.
9. All financial calculations use `Decimal`.
10. Every PDF contains the synthetic test-document marking.
11. A manifest records every generated file.
12. A summary reports requested, generated, and failed counts.
13. No real personal, vendor, tax, or banking data is used.

---

## 25. First Demonstrable Version

The first working version should support:

```text
Inputs:
- pdf_count
- seed
- output directory

Layouts:
- MODERN

Scenarios:
- CLEAN
- PRICE_VARIANCE_OVER
- QTY_OVER_BILLED
- MISSING_GRN
```

Example command:

```bash
python -m generator.main   --pdf-count 40   --seed 42   --output output/demo
```

Required result:

```text
40 invoice PDFs
40 invoice ground-truth JSON files
Mock vendors, items, POs, and GRNs
1 manifest.jsonl
1 dataset_summary.json
```

---

## 26. Final Deliverable

> A standalone Python application that accepts the number of required invoice PDFs, generates exactly that many synthetic invoice documents across configurable layouts and exception scenarios, creates corresponding mock PO/GRN data and ground-truth JSON records, and produces a manifest and summary for reliable testing of LedgerSense.
