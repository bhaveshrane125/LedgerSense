from pathlib import Path

content = """# LedgerSense Synthetic Data Generator — Implementation Plan

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