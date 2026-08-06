from __future__ import annotations

from pathlib import Path

from .models import GoodsReceipt, Invoice, PurchaseOrder, Vendor
from .utils import write_json


def invoice_ground_truth(invoice: Invoice, purchase_order: PurchaseOrder, scenario: str, layout: str) -> dict:
    return {
        "dataset_id": invoice.dataset_id,
        "document_id": invoice.document_id,
        "invoice_number": invoice.invoice_number,
        "scenario": scenario,
        "layout": layout,
        "vendor": {
            "vendor_id": invoice.vendor.vendor_id,
            "name": invoice.vendor.legal_name,
            "tax_id": invoice.vendor.tax_id,
        },
        "invoice": {
            "invoice_date": invoice.invoice_date,
            "due_date": invoice.due_date,
            "po_reference": invoice.po_reference,
            "grn_reference": invoice.grn_reference,
            "currency": invoice.currency,
        },
        "line_items": invoice.lines,
        "amounts": invoice.amounts,
        "expected_exception_codes": invoice.expected_exception_codes,
        "source_contains_intentional_error": invoice.source_contains_intentional_error,
        "duplicate_of_document_id": invoice.duplicate_of_document_id,
        "purchase_order": purchase_order,
    }


def save_invoice_ground_truth(
    invoice: Invoice,
    purchase_order: PurchaseOrder,
    scenario: str,
    layout: str,
    output_directory: Path,
) -> Path:
    path = output_directory / f"{invoice.document_id}.json"
    write_json(path, invoice_ground_truth(invoice, purchase_order, scenario, layout))
    return path


def purchase_order_ground_truth(purchase_order: PurchaseOrder, vendor: Vendor) -> dict:
    return {
        "document_type": "PURCHASE_ORDER",
        "po_number": purchase_order.po_number,
        "vendor": {
            "vendor_id": vendor.vendor_id,
            "name": vendor.legal_name,
            "tax_id": vendor.tax_id,
            "payment_terms": vendor.payment_terms,
        },
        "purchase_order": purchase_order,
    }


def save_purchase_order_ground_truth(
    purchase_order: PurchaseOrder,
    vendor: Vendor,
    output_directory: Path,
) -> Path:
    path = output_directory / f"{purchase_order.po_number}.json"
    write_json(path, purchase_order_ground_truth(purchase_order, vendor))
    return path


def goods_receipt_ground_truth(
    goods_receipt: GoodsReceipt,
    purchase_order: PurchaseOrder,
    vendor: Vendor,
) -> dict:
    return {
        "document_type": "GOODS_RECEIPT",
        "grn_number": goods_receipt.grn_number,
        "po_number": purchase_order.po_number,
        "vendor": {
            "vendor_id": vendor.vendor_id,
            "name": vendor.legal_name,
            "tax_id": vendor.tax_id,
        },
        "goods_receipt": goods_receipt,
    }


def save_goods_receipt_ground_truth(
    goods_receipt: GoodsReceipt,
    purchase_order: PurchaseOrder,
    vendor: Vendor,
    output_directory: Path,
) -> Path:
    path = output_directory / f"{goods_receipt.grn_number}.json"
    write_json(path, goods_receipt_ground_truth(goods_receipt, purchase_order, vendor))
    return path


def save_mock_erp_files(
    vendors: list,
    items: list,
    uom_conversions: dict,
    purchase_orders: list[PurchaseOrder],
    goods_receipts: list[GoodsReceipt],
    output_directory: Path,
) -> None:
    write_json(output_directory / "vendors.json", vendors)
    write_json(output_directory / "items.json", items)
    write_json(output_directory / "uom_conversions.json", uom_conversions)
    write_json(output_directory / "purchase_orders.json", purchase_orders)
    write_json(output_directory / "goods_receipts.json", goods_receipts)
