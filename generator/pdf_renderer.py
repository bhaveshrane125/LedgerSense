from __future__ import annotations

from pathlib import Path

from .models import GoodsReceipt, Invoice, PurchaseOrder, Vendor
from .utils import decimal_to_str


MARKING = "SYNTHETIC TEST DOCUMENT - NOT FOR PAYMENT"


def render_invoice_pdf(invoice: Invoice, layout: str, output_directory: Path) -> Path:
    output_directory.mkdir(parents=True, exist_ok=True)
    path = output_directory / f"{invoice.document_id}.pdf"
    lines = _invoice_lines(invoice, layout)
    _write_simple_pdf(path, lines)
    return path


def render_purchase_order_pdf(purchase_order: PurchaseOrder, vendor: Vendor, output_directory: Path) -> Path:
    output_directory.mkdir(parents=True, exist_ok=True)
    path = output_directory / f"{purchase_order.po_number}.pdf"
    lines = _purchase_order_lines(purchase_order, vendor)
    _write_simple_pdf(path, lines)
    return path


def render_goods_receipt_pdf(
    goods_receipt: GoodsReceipt,
    purchase_order: PurchaseOrder,
    vendor: Vendor,
    output_directory: Path,
) -> Path:
    output_directory.mkdir(parents=True, exist_ok=True)
    path = output_directory / f"{goods_receipt.grn_number}.pdf"
    lines = _goods_receipt_lines(goods_receipt, purchase_order, vendor)
    _write_simple_pdf(path, lines)
    return path


def _invoice_lines(invoice: Invoice, layout: str) -> list[str]:
    title = {
        "MODERN": "INVOICE",
        "CLASSIC": "TAX INVOICE",
        "COMPACT": "INVOICE SUMMARY",
        "INDUSTRIAL": "WAREHOUSE INVOICE",
        "MINIMAL": "INVOICE",
    }.get(layout, "INVOICE")
    divider = "=" * 78 if layout in {"CLASSIC", "INDUSTRIAL"} else "-" * 78
    printed_total = invoice.amounts.printed_gross_total or invoice.amounts.gross_total

    lines = [
        MARKING,
        title,
        divider,
        f"Vendor: {invoice.vendor.legal_name} ({invoice.vendor.vendor_id})",
        f"Tax ID: {invoice.vendor.tax_id}",
        f"Address: {invoice.vendor.address}",
        f"Invoice No: {invoice.invoice_number}    Document: {invoice.document_id}",
        f"Invoice Date: {invoice.invoice_date}    Due Date: {invoice.due_date}",
        f"PO: {invoice.po_reference}    GRN: {invoice.grn_reference or 'MISSING'}",
        f"Currency: {invoice.currency}    Scenario: {', '.join(invoice.expected_exception_codes) or 'CLEAN'}",
        divider,
        "Ln  SKU                  Description                       Qty      UOM   Unit       Line",
        divider,
    ]

    for line in invoice.lines:
        description = line.description[:31]
        lines.append(
            f"{line.line_number:<3} {line.sku[:20]:<20} {description:<31} "
            f"{str(line.quantity):>7} {line.uom:<5} {decimal_to_str(line.unit_price):>9} "
            f"{decimal_to_str(line.line_total):>10}"
        )

    lines.extend(
        [
            divider,
            f"Subtotal: {invoice.currency} {decimal_to_str(invoice.amounts.subtotal)}",
            f"Tax: {invoice.currency} {decimal_to_str(invoice.amounts.tax)}",
            f"Freight: {invoice.currency} {decimal_to_str(invoice.amounts.freight)}",
            f"Discount: {invoice.currency} {decimal_to_str(invoice.amounts.discount)}",
            f"Gross Total Printed: {invoice.currency} {decimal_to_str(printed_total)}",
            f"Calculated Gross Total: {invoice.currency} {decimal_to_str(invoice.amounts.gross_total)}",
        ]
    )
    if invoice.duplicate_of_document_id:
        lines.append(f"Duplicate of document: {invoice.duplicate_of_document_id}")
    if invoice.source_contains_intentional_error:
        lines.append("Source document intentionally contains an arithmetic error.")
    lines.append(MARKING)
    return lines


def _purchase_order_lines(purchase_order: PurchaseOrder, vendor: Vendor) -> list[str]:
    divider = "=" * 78
    lines = [
        MARKING,
        "PURCHASE ORDER",
        divider,
        f"PO No: {purchase_order.po_number}    PO Date: {purchase_order.po_date}",
        f"Vendor: {vendor.legal_name} ({vendor.vendor_id})",
        f"Tax ID: {vendor.tax_id}    Payment Terms: {vendor.payment_terms}",
        f"Address: {vendor.address}",
        f"Currency: {purchase_order.currency}",
        divider,
        "Ln  SKU                  Description                       Ordered UOM   Unit       Line",
        divider,
    ]
    for line in purchase_order.lines:
        lines.append(
            f"{line.line_number:<3} {line.sku[:20]:<20} {line.description[:31]:<31} "
            f"{str(line.quantity):>7} {line.uom:<5} {decimal_to_str(line.unit_price):>9} "
            f"{decimal_to_str(line.line_total):>10}"
        )
    lines.extend(
        [
            divider,
            f"PO Total: {purchase_order.currency} {decimal_to_str(purchase_order.total_amount)}",
            MARKING,
        ]
    )
    return lines


def _goods_receipt_lines(goods_receipt: GoodsReceipt, purchase_order: PurchaseOrder, vendor: Vendor) -> list[str]:
    divider = "=" * 78
    lines = [
        MARKING,
        "GOODS RECEIPT NOTE",
        divider,
        f"GRN No: {goods_receipt.grn_number}    Receipt Date: {goods_receipt.receipt_date}",
        f"Linked PO: {goods_receipt.po_number}",
        f"Vendor: {vendor.legal_name} ({vendor.vendor_id})",
        f"Condition: {goods_receipt.condition_note}",
        divider,
        "Ln  Ordered Item  Delivered SKU        Recv     Rej  UOM   Status",
        divider,
    ]
    po_lines_by_number = {str(line.line_number): line for line in purchase_order.lines}
    for grn_line in goods_receipt.lines:
        po_line = po_lines_by_number.get(grn_line["line_number"])
        ordered_item = grn_line.get("ordered_item_id") or (po_line.item_id if po_line else grn_line["item_id"])
        delivered_sku = grn_line.get("delivered_sku") or (po_line.sku if po_line else grn_line["item_id"])
        status = grn_line.get("receipt_status", "ACCEPTED")
        lines.append(
            f"{grn_line['line_number']:<3} {ordered_item:<13} {delivered_sku[:20]:<20} "
            f"{grn_line['quantity_received']:>8} {grn_line['quantity_rejected']:>6} "
            f"{grn_line['uom']:<5} {status:<10}"
        )
        note = grn_line.get("variance_note")
        if note and note != "Received as ordered":
            lines.append(f"    Note: {note[:88]}")
    lines.extend([divider, MARKING])
    return lines


def _write_simple_pdf(path: Path, lines: list[str]) -> None:
    page_chunks = [lines[index : index + 42] for index in range(0, len(lines), 42)]
    page_streams = [_page_stream(chunk) for chunk in page_chunks]
    page_refs = [index * 2 + 1 for index in range(len(page_chunks))]
    content_refs = [index * 2 + 2 for index in range(len(page_chunks))]
    pages_ref = len(page_chunks) * 2 + 1
    font_ref = pages_ref + 1
    catalog_ref = font_ref + 1

    rebuilt: list[bytes] = []
    for page_number, stream in enumerate(page_streams):
        content_ref = content_refs[page_number]
        rebuilt.append(
            (
                f"<< /Type /Page /Parent {pages_ref} 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 {font_ref} 0 R >> >> "
                f"/Contents {content_ref} 0 R >>"
            ).encode("latin-1")
        )
        rebuilt.append(f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1") + stream + b"\nendstream")

    kids = " ".join(f"{page_ref} 0 R" for page_ref in page_refs)
    rebuilt.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_refs)} >>".encode("latin-1"))
    rebuilt.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    rebuilt.append(f"<< /Type /Catalog /Pages {pages_ref} 0 R >>".encode("latin-1"))

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, body in enumerate(rebuilt, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("latin-1"))
        pdf.extend(body)
        pdf.extend(b"\nendobj\n")
    xref_at = len(pdf)
    pdf.extend(f"xref\n0 {len(rebuilt) + 1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(
        (
            f"trailer\n<< /Size {len(rebuilt) + 1} /Root {catalog_ref} 0 R >>\n"
            f"startxref\n{xref_at}\n%%EOF\n"
        ).encode("latin-1")
    )
    path.write_bytes(bytes(pdf))


def _page_stream(lines: list[str]) -> bytes:
    commands = ["BT", "/F1 10 Tf", "50 750 Td", "14 TL"]
    for index, line in enumerate(lines):
        if index:
            commands.append("T*")
        commands.append(f"({_escape_pdf_text(line)}) Tj")
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
