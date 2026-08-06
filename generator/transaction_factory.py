from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal
from random import Random

from .models import GoodsReceipt, Invoice, InvoiceAmounts, Item, PurchaseOrder, TransactionLine, Vendor
from .utils import money


def generate_purchase_order(
    rng: Random,
    vendor: Vendor,
    items: list[Item],
    index: int,
    currency: str,
    min_line_items: int,
    max_line_items: int,
) -> PurchaseOrder:
    selected_items = rng.sample(items, k=rng.randint(min_line_items, min(max_line_items, len(items))))
    lines: list[TransactionLine] = []
    for line_number, item in enumerate(selected_items, start=1):
        quantity = Decimal(rng.randint(4, 160))
        unit_price = item.unit_price
        lines.append(
            TransactionLine(
                line_number=line_number,
                item_id=item.item_id,
                sku=item.sku,
                description=item.description,
                quantity=quantity,
                uom=item.base_uom,
                unit_price=unit_price,
                tax_rate=item.tax_rate,
                line_total=money(quantity * unit_price),
            )
        )
    return PurchaseOrder(
        po_number=f"PO-{index:06d}",
        vendor_id=vendor.vendor_id,
        po_date=str(date(2026, 1, 1) + timedelta(days=index % 180)),
        currency=currency,
        lines=lines,
        total_amount=sum((line.line_total for line in lines), Decimal("0.00")),
    )


def generate_goods_receipt(
    rng: Random,
    purchase_order: PurchaseOrder,
    index: int,
    scenario: str,
    items: list[Item],
) -> GoodsReceipt | None:
    if scenario == "MISSING_GRN":
        return None
    receipt_lines = []
    missing_line_number: int | None = None
    partial_line_number: int | None = None
    wrong_line_number: int | None = None

    if scenario == "ITEMS_MISSING":
        missing_line_number = rng.choice(purchase_order.lines).line_number
    if scenario in {"QTY_OVER_BILLED", "PARTIAL_RECEIPT"}:
        partial_line_number = rng.choice(purchase_order.lines).line_number
    if scenario == "WRONG_ITEM_DELIVERED":
        wrong_line_number = rng.choice(purchase_order.lines).line_number

    for line in purchase_order.lines:
        if line.line_number == missing_line_number:
            continue

        received_quantity = line.quantity
        rejected_quantity = Decimal("0")
        status = "ACCEPTED"
        note = "Received as ordered"
        delivered_item = None

        if line.line_number == partial_line_number:
            shortfall = Decimal(rng.randint(1, max(1, int(line.quantity) // 3 or 1)))
            received_quantity = max(Decimal("0"), line.quantity - shortfall)
            status = "PARTIAL"
            note = f"Short received by {shortfall} {line.uom}"

        if line.line_number == wrong_line_number:
            candidates = [item for item in items if item.item_id != line.item_id]
            delivered_item = rng.choice(candidates) if candidates else None
            status = "WRONG_ITEM"
            note = f"Delivered {delivered_item.sku if delivered_item else 'alternate item'} instead of ordered SKU {line.sku}"

        receipt_lines.append(
            {
                "line_number": str(line.line_number),
                "ordered_item_id": line.item_id,
                "item_id": delivered_item.item_id if delivered_item else line.item_id,
                "ordered_sku": line.sku,
                "delivered_sku": delivered_item.sku if delivered_item else line.sku,
                "quantity_ordered": str(line.quantity),
                "quantity_received": str(received_quantity),
                "quantity_rejected": str(rejected_quantity),
                "uom": delivered_item.base_uom if delivered_item else line.uom,
                "receipt_status": status,
                "variance_note": note,
            }
        )

    condition_note = {
        "QTY_OVER_BILLED": "Partial delivery recorded; invoice still bills the ordered quantity.",
        "PARTIAL_RECEIPT": "Material partially received; balance is pending vendor dispatch.",
        "WRONG_ITEM_DELIVERED": "Receiving team recorded a delivered item mismatch.",
        "ITEMS_MISSING": "One ordered line was not present in the delivery.",
    }.get(scenario, "Synthetic goods received in acceptable condition")
    return GoodsReceipt(
        grn_number=f"GRN-{index:06d}",
        po_number=purchase_order.po_number,
        receipt_date=str(date.fromisoformat(purchase_order.po_date) + timedelta(days=4)),
        lines=receipt_lines,
        condition_note=condition_note,
    )


def generate_invoice(
    purchase_order: PurchaseOrder,
    goods_receipt: GoodsReceipt | None,
    vendor: Vendor,
    index: int,
    dataset_id: str,
) -> Invoice:
    invoice_date = date.fromisoformat(purchase_order.po_date) + timedelta(days=8)
    lines = deepcopy(purchase_order.lines)
    amounts = calculate_amounts(lines)
    return Invoice(
        dataset_id=dataset_id,
        document_id=f"DOC-{index:06d}",
        invoice_number=f"INV-{index:06d}",
        invoice_date=str(invoice_date),
        due_date=str(invoice_date + timedelta(days=30)),
        vendor=vendor,
        po_reference=purchase_order.po_number,
        grn_reference=goods_receipt.grn_number if goods_receipt else None,
        currency=purchase_order.currency,
        lines=lines,
        amounts=amounts,
    )


def clone_duplicate_invoice(template: Invoice, index: int) -> Invoice:
    duplicate = deepcopy(template)
    duplicate.document_id = f"DOC-{index:06d}"
    duplicate.duplicate_of_document_id = template.document_id
    duplicate.expected_exception_codes = ["DUPLICATE_CONFIRMED"]
    return duplicate


def calculate_amounts(lines: list[TransactionLine]) -> InvoiceAmounts:
    subtotal = money(sum((line.line_total for line in lines), Decimal("0.00")))
    tax = money(sum((line.line_total * line.tax_rate for line in lines), Decimal("0.00")))
    freight = Decimal("0.00")
    discount = Decimal("0.00")
    gross_total = money(subtotal + tax + freight - discount)
    return InvoiceAmounts(
        subtotal=subtotal,
        tax=tax,
        freight=freight,
        discount=discount,
        gross_total=gross_total,
    )


def recalculate_invoice(invoice: Invoice) -> Invoice:
    for line in invoice.lines:
        line.line_total = money(line.quantity * line.unit_price)
    printed = invoice.amounts.printed_gross_total
    invoice.amounts = calculate_amounts(invoice.lines)
    invoice.amounts.printed_gross_total = printed
    return invoice
