# Architectural Assumptions & Design Decisions

This document outlines key architectural assumptions, scope boundaries, and integration abstractions for the **Accounts Payable (AP) Automation Software**.

---

### 1. OCR & Document AI Provider
- **Design Decision**: The system defines an abstract interface `BaseOCRProvider`. When no external cloud credentials (e.g., AWS Textract, Azure Form Recognizer, Google Document AI) are supplied, the application defaults to `MockOCRProvider`.
- **Implementation**: The mock provider produces deterministic, realistic extraction data based on real-world Indian tax invoice structures (including GSTIN, PAN, HSN codes, multi-line items, subtotal, CGST/SGST/IGST, and grand totals) and attaches per-field confidence scores.
- **Accuracy Metric**: The "OCR Accuracy" shown on the dashboard represents the mathematically aggregated confidence score of the extracted fields/invoices stored in the database, not an externally audited OCR metric.

---

### 2. Banking & Payment Execution
- **Design Decision**: In accordance with project requirements and financial security boundaries, no live banking API integration is used.
- **Implementation**: A clean `BasePaymentGateway` abstraction is provided. The `MockPaymentGateway` simulates the end-to-end payment lifecycle (`REQUESTED` $\rightarrow$ `PROCESSING` $\rightarrow$ `PAID`), generates mock bank UTR (Unique Transaction Reference) numbers, records timestamps, and creates downloadable Payment Advice records.

---

### 3. ERP & Accounting Integration
- **Design Decision**: The core AP domain is strictly decoupled from external ERP schemas (SAP S/4HANA, NetSuite, Oracle ERP Cloud, Tally).
- **Implementation**: A lightweight adapter interface `BaseERPAdapter` formats standardized journal vouchers and AP invoice export payloads. The `MockERPAdapter` generates export payloads, logs synchronization history in `ERPSyncLog`, and returns simulated ERP voucher numbers without requiring external ERP software.

---

### 4. Indian GST Verification
- **Design Decision**: The system performs offline structural validation, state code verification, alphanumeric structure checks, and vendor master cross-referencing.
- **Boundary**: No direct connection to the Government GSTN portal is assumed or claimed. Invoices are validated against known vendor GSTINs, standard tax rates (5%, 12%, 18%, 28%), and arithmetic reconciliation (Subtotal + Tax = Total).

---

### 5. Duplicate Invoice Business Rule
- **Design Decision**: The system models an explicit `fiscal_year` field (e.g. `FY2026-27`) following the Indian financial year (April 1 – March 31).
- **Uniqueness**: Duplicate detection enforces uniqueness across `(vendor, invoice_number, fiscal_year)`. This prevents false duplicate rejections if vendors reset their invoice sequence annually in a new financial year.

---

### 6. Email Ingestion
- **Design Decision**: A clean interface `BaseEmailIngestion` provides the contract for processing inbound invoice emails.
- **Implementation**: A mock email ingestion adapter simulates incoming emails with invoice attachments and feeds them into the standard invoice capture pipeline.

---

### 7. Mobile Approval Experience
- **Design Decision**: No native mobile application is built.
- **Implementation**: The React approval queue and approval detail screens are designed to be responsive across mobile viewports, enabling managers and CFOs to review invoice details, inspect 3-way matching, and execute `APPROVE` or `REJECT` actions with comments directly on smartphone browsers.

---

### 8. Configurable Approval Matrix
- **Design Decision**: Threshold tiers (e.g., $< ₹50,000$, $₹50,000 - ₹500,000$, $> ₹500,000$) are database records in `ApprovalMatrixRule`, not hardcoded in Python code.
- **Support**: Supports role-based sequential and parallel approval steps, role delegation, escalation paths, and complete audit logging.
