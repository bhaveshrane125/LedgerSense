from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .models import GoodsReceipt, Invoice, PurchaseOrder
from .utils import append_jsonl, relative_to, sha256_file, write_json


def create_manifest_record(
    index: int,
    invoice: Invoice,
    purchase_order: PurchaseOrder,
    goods_receipt: GoodsReceipt | None,
    scenario: str,
    layout: str,
    pdf_path: Path,
    truth_path: Path,
    po_pdf_path: Path | None,
    po_truth_path: Path | None,
    grn_pdf_path: Path | None,
    grn_truth_path: Path | None,
    dataset_root: Path,
    seed: int,
) -> dict[str, Any]:
    return {
        "generation_index": index,
        "document_id": invoice.document_id,
        "invoice_number": invoice.invoice_number,
        "po_number": purchase_order.po_number,
        "grn_number": goods_receipt.grn_number if goods_receipt else None,
        "scenario": scenario,
        "layout": layout,
        "pdf_path": relative_to(pdf_path, dataset_root),
        "ground_truth_path": relative_to(truth_path, dataset_root),
        "sha256": sha256_file(pdf_path),
        "po_pdf_path": relative_to(po_pdf_path, dataset_root) if po_pdf_path else None,
        "po_ground_truth_path": relative_to(po_truth_path, dataset_root) if po_truth_path else None,
        "po_pdf_sha256": sha256_file(po_pdf_path) if po_pdf_path else None,
        "grn_pdf_path": relative_to(grn_pdf_path, dataset_root) if grn_pdf_path else None,
        "grn_ground_truth_path": relative_to(grn_truth_path, dataset_root) if grn_truth_path else None,
        "grn_pdf_sha256": sha256_file(grn_pdf_path) if grn_pdf_path else None,
        "seed": seed,
    }


def save_manifest(path: Path, rows: list[dict[str, Any]]) -> None:
    append_jsonl(path, rows)


def save_dataset_summary(
    path: Path,
    dataset_id: str,
    seed: int,
    requested_pdf_count: int,
    generated_pdf_count: int,
    generated_po_pdf_count: int,
    generated_grn_pdf_count: int,
    generated_po_truth_count: int,
    generated_grn_truth_count: int,
    manifest_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    failed_pdf_count = requested_pdf_count - generated_pdf_count
    summary = {
        "dataset_id": dataset_id,
        "generator_version": "0.1.0",
        "seed": seed,
        "requested_pdf_count": requested_pdf_count,
        "generated_pdf_count": generated_pdf_count,
        "generated_po_pdf_count": generated_po_pdf_count,
        "generated_grn_pdf_count": generated_grn_pdf_count,
        "generated_po_ground_truth_count": generated_po_truth_count,
        "generated_grn_ground_truth_count": generated_grn_truth_count,
        "missing_grn_count": sum(1 for row in manifest_rows if row["grn_number"] is None),
        "failed_pdf_count": failed_pdf_count,
        "layout_distribution": dict(Counter(row["layout"] for row in manifest_rows)),
        "scenario_distribution": dict(Counter(row["scenario"] for row in manifest_rows)),
    }
    write_json(path, summary)
    return summary
