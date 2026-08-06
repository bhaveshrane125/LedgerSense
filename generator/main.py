from __future__ import annotations

import argparse
from pathlib import Path
from random import Random

from .config import apply_overrides, config_to_dict, dump_yaml_like, load_config, validate_config
from .ground_truth import (
    save_goods_receipt_ground_truth,
    save_invoice_ground_truth,
    save_mock_erp_files,
    save_purchase_order_ground_truth,
)
from .manifest import create_manifest_record, save_dataset_summary, save_manifest
from .master_data import generate_items, generate_vendors, uom_conversion_table
from .models import GeneratorConfig, OutputPaths
from .pdf_renderer import render_goods_receipt_pdf, render_invoice_pdf, render_purchase_order_pdf
from .scenario_engine import choose_scenario, inject_scenario, validate_invoice_relationship
from .transaction_factory import (
    clone_duplicate_invoice,
    generate_goods_receipt,
    generate_invoice,
    generate_purchase_order,
)


class PdfCountMismatchError(RuntimeError):
    def __init__(self, requested: int, generated: int, missing: list[str]) -> None:
        super().__init__(
            f"Generated PDF count mismatch: requested={requested}, generated={generated}, "
            f"missing={', '.join(missing) or 'unknown'}"
        )


def create_output_directories(output_directory: str) -> OutputPaths:
    root = Path(output_directory)
    paths = OutputPaths(
        root=root.as_posix(),
        invoice_pdfs=(root / "pdfs" / "invoices").as_posix(),
        po_pdfs=(root / "pdfs" / "purchase_orders").as_posix(),
        grn_pdfs=(root / "pdfs" / "goods_receipts").as_posix(),
        invoice_truth=(root / "ground_truth" / "invoices").as_posix(),
        po_truth=(root / "ground_truth" / "purchase_orders").as_posix(),
        grn_truth=(root / "ground_truth" / "goods_receipts").as_posix(),
        mock_erp=(root / "mock_erp").as_posix(),
        manifest=(root / "manifest.jsonl").as_posix(),
        summary=(root / "dataset_summary.json").as_posix(),
        config_snapshot=(root / "config_snapshot.yaml").as_posix(),
    )
    for directory in [
        paths.invoice_pdfs,
        paths.po_pdfs,
        paths.grn_pdfs,
        paths.invoice_truth,
        paths.po_truth,
        paths.grn_truth,
        paths.mock_erp,
    ]:
        Path(directory).mkdir(parents=True, exist_ok=True)
    return paths


def generate_dataset(config: GeneratorConfig) -> dict:
    validate_config(config)
    rng = Random(config.seed)
    paths = create_output_directories(config.output_directory)
    root = Path(paths.root)
    dump_yaml_like(Path(paths.config_snapshot), config_to_dict(config))

    vendors = generate_vendors(rng, config.vendor_count)
    items = generate_items(rng, config.item_count)
    items_by_id = {item.item_id: item for item in items}
    purchase_orders = {}
    goods_receipts = {}
    po_pdf_paths = {}
    po_truth_paths = {}
    grn_pdf_paths = {}
    grn_truth_paths = {}
    manifest_rows = []
    prior_invoices = []
    dataset_id = "DS-001"

    for index in range(1, config.pdf_count + 1):
        scenario = choose_scenario(rng, config.scenario_weights, allow_duplicate=bool(prior_invoices))
        layout = rng.choice(config.layouts)

        if scenario == "DUPLICATE_CONFIRMED" and prior_invoices:
            template_invoice, template_po, template_grn = rng.choice(prior_invoices)
            invoice = clone_duplicate_invoice(template_invoice, index)
            po = template_po
            grn = template_grn
        else:
            vendor = rng.choice(vendors)
            po = generate_purchase_order(
                rng=rng,
                vendor=vendor,
                items=items,
                index=index,
                currency=config.currency,
                min_line_items=config.min_line_items,
                max_line_items=config.max_line_items,
            )
            grn = generate_goods_receipt(rng, po, index, scenario, items)
            invoice = generate_invoice(po, grn, vendor, index, dataset_id)
            invoice = inject_scenario(invoice, po, scenario, rng, items_by_id)

        validate_invoice_relationship(invoice, po, scenario)

        purchase_orders[po.po_number] = po
        if grn is not None:
            goods_receipts[grn.grn_number] = grn

        if config.render_po_pdfs and po.po_number not in po_pdf_paths:
            po_pdf_path = render_purchase_order_pdf(po, invoice.vendor, Path(paths.po_pdfs))
            po_truth_path = save_purchase_order_ground_truth(po, invoice.vendor, Path(paths.po_truth))
            if not po_pdf_path.exists() or po_pdf_path.stat().st_size == 0:
                raise RuntimeError(f"{po.po_number}: PO PDF was not created correctly")
            if not po_truth_path.exists():
                raise RuntimeError(f"{po.po_number}: PO ground-truth JSON was not created")
            po_pdf_paths[po.po_number] = po_pdf_path
            po_truth_paths[po.po_number] = po_truth_path

        if config.render_grn_pdfs and grn is not None and grn.grn_number not in grn_pdf_paths:
            grn_pdf_path = render_goods_receipt_pdf(grn, po, invoice.vendor, Path(paths.grn_pdfs))
            grn_truth_path = save_goods_receipt_ground_truth(grn, po, invoice.vendor, Path(paths.grn_truth))
            if not grn_pdf_path.exists() or grn_pdf_path.stat().st_size == 0:
                raise RuntimeError(f"{grn.grn_number}: GRN PDF was not created correctly")
            if not grn_truth_path.exists():
                raise RuntimeError(f"{grn.grn_number}: GRN ground-truth JSON was not created")
            grn_pdf_paths[grn.grn_number] = grn_pdf_path
            grn_truth_paths[grn.grn_number] = grn_truth_path

        pdf_path = render_invoice_pdf(invoice, layout, Path(paths.invoice_pdfs))
        truth_path = save_invoice_ground_truth(invoice, po, scenario, layout, Path(paths.invoice_truth))
        if not pdf_path.exists() or pdf_path.stat().st_size == 0:
            raise RuntimeError(f"{invoice.document_id}: PDF was not created correctly")
        if not truth_path.exists():
            raise RuntimeError(f"{invoice.document_id}: ground-truth JSON was not created")

        manifest_rows.append(
            create_manifest_record(
                index=index,
                invoice=invoice,
                purchase_order=po,
                goods_receipt=grn,
                scenario=scenario,
                layout=layout,
                pdf_path=pdf_path,
                truth_path=truth_path,
                po_pdf_path=po_pdf_paths.get(po.po_number),
                po_truth_path=po_truth_paths.get(po.po_number),
                grn_pdf_path=grn_pdf_paths.get(grn.grn_number) if grn else None,
                grn_truth_path=grn_truth_paths.get(grn.grn_number) if grn else None,
                dataset_root=root,
                seed=config.seed,
            )
        )
        if scenario != "DUPLICATE_CONFIRMED":
            prior_invoices.append((invoice, po, grn))

    save_mock_erp_files(
        vendors=vendors,
        items=items,
        uom_conversions=uom_conversion_table(items),
        purchase_orders=list(purchase_orders.values()),
        goods_receipts=list(goods_receipts.values()),
        output_directory=Path(paths.mock_erp),
    )
    save_manifest(Path(paths.manifest), manifest_rows)

    generated_pdfs = sorted(Path(paths.invoice_pdfs).glob("*.pdf"))
    generated_count = len(generated_pdfs)
    if generated_count != config.pdf_count:
        expected_names = {f"DOC-{index:06d}.pdf" for index in range(1, config.pdf_count + 1)}
        actual_names = {path.name for path in generated_pdfs}
        raise PdfCountMismatchError(config.pdf_count, generated_count, sorted(expected_names - actual_names))

    generated_po_pdf_count = len(po_pdf_paths)
    generated_grn_pdf_count = len(grn_pdf_paths)
    if config.render_po_pdfs and generated_po_pdf_count != len(purchase_orders):
        raise RuntimeError(
            f"PO PDF count mismatch: expected={len(purchase_orders)}, generated={generated_po_pdf_count}"
        )
    if config.render_grn_pdfs and generated_grn_pdf_count != len(goods_receipts):
        raise RuntimeError(
            f"GRN PDF count mismatch: expected={len(goods_receipts)}, generated={generated_grn_pdf_count}"
        )

    return save_dataset_summary(
        path=Path(paths.summary),
        dataset_id=dataset_id,
        seed=config.seed,
        requested_pdf_count=config.pdf_count,
        generated_pdf_count=generated_count,
        generated_po_pdf_count=generated_po_pdf_count,
        generated_grn_pdf_count=generated_grn_pdf_count,
        generated_po_truth_count=len(po_truth_paths),
        generated_grn_truth_count=len(grn_truth_paths),
        manifest_rows=manifest_rows,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate synthetic LedgerSense invoice PDFs and ground truth.")
    parser.add_argument("--config", help="Path to YAML config file")
    parser.add_argument("--pdf-count", type=int, help="Exact number of invoice PDFs to generate")
    parser.add_argument("--seed", type=int, help="Random seed for reproducible output")
    parser.add_argument("--output", help="Output directory")
    parser.add_argument("--layouts", help="Comma-separated layouts, e.g. MODERN,CLASSIC")
    parser.add_argument("--render-po-pdfs", action="store_true", help="Render matching purchase order PDFs")
    parser.add_argument("--render-grn-pdfs", action="store_true", help="Render matching goods receipt PDFs")
    parser.add_argument(
        "--scenario",
        action="append",
        default=[],
        help="Scenario weight override, e.g. CLEAN=0.50. May be passed multiple times.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config)
    config = apply_overrides(
        config,
        pdf_count=args.pdf_count,
        seed=args.seed,
        output=args.output,
        layouts=args.layouts,
        scenarios=args.scenario,
        render_po_pdfs=args.render_po_pdfs,
        render_grn_pdfs=args.render_grn_pdfs,
    )
    summary = generate_dataset(config)
    print(f"Requested PDFs: {summary['requested_pdf_count']}")
    print(f"Generated PDFs: {summary['generated_pdf_count']}")
    print(f"Generated PO PDFs: {summary['generated_po_pdf_count']}")
    print(f"Generated GRN PDFs: {summary['generated_grn_pdf_count']}")
    print(f"Failed PDFs: {summary['failed_pdf_count']}")
    print(f"Output: {Path(config.output_directory).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
