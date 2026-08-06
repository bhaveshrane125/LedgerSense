from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


LAYOUTS = ("MODERN", "CLASSIC", "COMPACT", "INDUSTRIAL", "MINIMAL")
SCENARIOS = (
    "CLEAN",
    "PRICE_VARIANCE_OVER",
    "QTY_OVER_BILLED",
    "MISSING_GRN",
    "UOM_MISMATCH",
    "DUPLICATE_CONFIRMED",
    "ARITHMETIC_ERROR",
    "PARTIAL_RECEIPT",
    "WRONG_ITEM_DELIVERED",
    "ITEMS_MISSING",
)


@dataclass(frozen=True)
class Vendor:
    vendor_id: str
    legal_name: str
    trading_name: str
    tax_id: str
    address: str
    email: str
    payment_terms: str
    bank_fingerprint: str
    preferred_layout: str


@dataclass(frozen=True)
class Item:
    item_id: str
    sku: str
    description: str
    category: str
    base_uom: str
    unit_price: Decimal
    tax_rate: Decimal
    aliases: list[str]
    uom_conversions: dict[str, Decimal]


@dataclass
class TransactionLine:
    line_number: int
    item_id: str
    sku: str
    description: str
    quantity: Decimal
    uom: str
    unit_price: Decimal
    tax_rate: Decimal
    line_total: Decimal


@dataclass
class PurchaseOrder:
    po_number: str
    vendor_id: str
    po_date: str
    currency: str
    lines: list[TransactionLine]
    total_amount: Decimal


@dataclass
class GoodsReceipt:
    grn_number: str
    po_number: str
    receipt_date: str
    lines: list[dict[str, str]]
    condition_note: str


@dataclass
class InvoiceAmounts:
    subtotal: Decimal
    tax: Decimal
    freight: Decimal
    discount: Decimal
    gross_total: Decimal
    printed_gross_total: Decimal | None = None


@dataclass
class Invoice:
    dataset_id: str
    document_id: str
    invoice_number: str
    invoice_date: str
    due_date: str
    vendor: Vendor
    po_reference: str
    grn_reference: str | None
    currency: str
    lines: list[TransactionLine]
    amounts: InvoiceAmounts
    expected_exception_codes: list[str] = field(default_factory=list)
    source_contains_intentional_error: bool = False
    duplicate_of_document_id: str | None = None


@dataclass(frozen=True)
class GeneratorConfig:
    dataset_name: str = "ledgersense_synthetic_v1"
    pdf_count: int = 40
    output_directory: str = "data/output"
    seed: int = 42
    locale: str = "en_IN"
    currency: str = "INR"
    vendor_count: int = 5
    item_count: int = 30
    min_line_items: int = 1
    max_line_items: int = 8
    layouts: tuple[str, ...] = LAYOUTS
    scenario_weights: dict[str, float] = field(
        default_factory=lambda: {
            "CLEAN": 0.25,
            "PRICE_VARIANCE_OVER": 0.15,
            "QTY_OVER_BILLED": 0.15,
            "MISSING_GRN": 0.10,
            "UOM_MISMATCH": 0.08,
            "DUPLICATE_CONFIRMED": 0.04,
            "ARITHMETIC_ERROR": 0.04,
            "PARTIAL_RECEIPT": 0.08,
            "WRONG_ITEM_DELIVERED": 0.06,
            "ITEMS_MISSING": 0.05,
        }
    )
    add_noise: bool = False
    add_rotation: bool = False
    render_po_pdfs: bool = False
    render_grn_pdfs: bool = False


@dataclass(frozen=True)
class OutputPaths:
    root: str
    invoice_pdfs: str
    po_pdfs: str
    grn_pdfs: str
    invoice_truth: str
    po_truth: str
    grn_truth: str
    mock_erp: str
    manifest: str
    summary: str
    config_snapshot: str
