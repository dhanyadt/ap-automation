# Accounts Payable (AP) Automation Software

An enterprise **Accounts Payable (AP) Automation Software** with OCR extraction, multi-tier validation, 2-way and 3-way PO matching, configurable approval matrix, payment lifecycle tracking, and an append-only audit trail.

---

## 1. Project Architecture

The software is structured as a **modular monolith** with a service-layer architecture and a decoupled React frontend:

- **Backend**: Python 3.12, Django 5, Django REST Framework, SimpleJWT, Celery, Redis, PostgreSQL (with SQLite zero-config local fallback).
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide React, Recharts.
- **Service Layer**: Pure business logic (OCR, validations, matching, approvals, payments) isolated in dedicated service classes.
- **Provider Abstractions**: Clean interfaces with realistic mocks for OCR, Banking/UTR, ERP exports, and GST validations.

```
ap-automation/
├── backend/
│   ├── config/             # Django settings (base, local), URLs, Celery, WSGI, ASGI
│   ├── common/             # Base models, permissions, exceptions, pagination, utils
│   ├── apps/
│   │   ├── accounts/       # Custom User model & RBAC (ADMIN, AP_CLERK, APPROVER, FINANCE, CFO, VENDOR)
│   │   ├── vendors/        # Vendor master & masked bank details
│   │   ├── purchase_orders/# PO master & items
│   │   ├── goods_receipts/ # GRN master & items
│   │   ├── invoices/       # Invoices, items, and multi-state lifecycle
│   │   ├── ocr/            # OCR extraction service & mock Indian invoice parser
│   │   ├── validations/    # Validation engine (mandatory, duplicates, GSTIN, math)
│   │   ├── matching/       # 2-way & 3-way matching engine
│   │   ├── approvals/      # Configurable approval matrix & workflow
│   │   ├── payments/       # Payment requests, mock UTR rail, advice
│   │   ├── audit/          # Append-only immutable audit trail
│   │   ├── dashboard/      # Real DB aggregations & aging analytics
│   │   ├── reports/        # AP aging, exceptions, GST reports with CSV export
│   │   └── erp/            # Lightweight ERP export adapter & sync logs
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/                # Components, pages, layout, services, types
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
├── ASSUMPTIONS.md
└── README.md
```

---

## 2. Core Demonstrable Flow (P0)

$$\text{Vendor} \longrightarrow \text{PO} \longrightarrow \text{GRN} \longrightarrow \text{Invoice Upload} \longrightarrow \text{OCR Extraction} \longrightarrow \text{Validation} \longrightarrow \text{3-Way Match} \longrightarrow \text{Approval Matrix} \longrightarrow \text{Payment Request} \longrightarrow \text{Payment Settlement} \longrightarrow \text{Dashboard \& Audit}$$

---

## 3. Quick Start Instructions

### Prerequisites
- Python 3.12+
- Node.js 20+ & npm
- Docker & Docker Compose (optional for containerized run)

### Running Locally (Without Docker)

#### 1. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```
- API Base: `http://localhost:8000/api/`
- Health Check: `http://localhost:8000/api/health/`
- Interactive Swagger UI: `http://localhost:8000/api/docs/`
- Admin Panel: `http://localhost:8000/admin/`

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- Frontend UI: `http://localhost:5173/`

---

### Running via Docker Compose

```bash
docker-compose up --build
```
This boots:
- PostgreSQL database (`ap_postgres` on port `5432`)
- Redis broker (`ap_redis` on port `6379`)
- Backend API (`ap_backend` on port `8000`)
- Celery worker (`ap_celery_worker`)
- Frontend application (`ap_frontend` on port `5173`)

---

## 4. Architectural Assumptions

Detailed assumptions regarding external provider mocks (OCR, Banking, ERP, GST verification) are documented in [`ASSUMPTIONS.md`](./ASSUMPTIONS.md).
