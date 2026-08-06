from __future__ import annotations

from decimal import Decimal
from random import Random

from .models import Invoice, Item, PurchaseOrder
from .transaction_factory import recalculate_invoice
from .utils import money


def choose_scenario(rng: Random, weights: dict[str, float], allow_duplicate: bool = True) -> str:
    names = list(weights)
    values = list(weights.values())
    if not allow_duplicate and "DUPLICATE_CONFIRMED" in names:
        index = names.index("DUPLICATE_CONFIRMED")
        names.pop(index)
        values.pop(index)
        total = sum(values)
        values = [value / total for value in values]
    return rng.choices(names, weights=values, k=1)[0]


def inject_scenario(
    invoice: Invoice,
    purchase_order: PurchaseOrder,
    scenario: str,
    rng: Random,
    items_by_id: dict[str, Item],
) -> Invoice:
    if scenario == "CLEAN":
        invoice.expected_exception_codes = []
        return recalculate_invoice(invoice)

    invoice.expected_exception_codes = [scenario]

    if scenario == "PRICE_VARIANCE_OVER":
        first = invoice.lines[0]
        bump = Decimal(str(rng.choice(["1.05", "1.08", "1.10", "1.15"])))
        first.unit_price = money(first.unit_price * bump)
        return recalculate_invoice(invoice)

    if scenario == "QTY_OVER_BILLED":
        return recalculate_invoice(invoice)

    if scenario in {"PARTIAL_RECEIPT", "WRONG_ITEM_DELIVERED", "ITEMS_MISSING"}:
        return recalculate_invoice(invoice)

    if scenario == "MISSING_GRN":
        invoice.grn_reference = None
        return recalculate_invoice(invoice)

    if scenario == "UOM_MISMATCH":
        first = invoice.lines[0]
        item = items_by_id[first.item_id]
        conversion = item.uom_conversions.get("BOX")
        if conversion:
            first.uom = "BOX"
            first.quantity = money(first.quantity / conversion)
            first.unit_price = money(first.unit_price * conversion)
        else:
            first.uom = "ALT"
        return recalculate_invoice(invoice)

    if scenario == "ARITHMETIC_ERROR":
        recalculate_invoice(invoice)
        invoice.source_contains_intentional_error = True
        invoice.amounts.printed_gross_total = money(invoice.amounts.gross_total - Decimal("1.00"))
        return invoice

    return recalculate_invoice(invoice)


def validate_invoice_relationship(invoice: Invoice, purchase_order: PurchaseOrder, scenario: str) -> None:
    if invoice.vendor.vendor_id != purchase_order.vendor_id:
        raise ValueError(f"{invoice.document_id}: vendor does not match PO")
    if invoice.po_reference != purchase_order.po_number:
        raise ValueError(f"{invoice.document_id}: PO reference does not match")
    if scenario == "MISSING_GRN" and invoice.grn_reference is not None:
        raise ValueError(f"{invoice.document_id}: missing-GRN scenario created a GRN reference")
    for line in invoice.lines:
        if line.quantity <= 0:
            raise ValueError(f"{invoice.document_id}: quantity must be positive")
        if line.unit_price < 0:
            raise ValueError(f"{invoice.document_id}: unit price cannot be negative")
