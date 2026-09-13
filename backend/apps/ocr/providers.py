from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List

from apps.invoices.models import Invoice


@dataclass(frozen=True)
class OCRExtraction:
    fields: Dict[str, Any]
    items: List[Dict[str, Any]]
    raw_text: str
    average_confidence: Decimal


class BaseOCRProvider:
    def extract(self, invoice: Invoice) -> OCRExtraction:
        raise NotImplementedError


class MockOCRProvider(BaseOCRProvider):
    """Deterministic local OCR substitute based on the invoice's known PO context."""

    def extract(self, invoice: Invoice) -> OCRExtraction:
        purchase_order = invoice.purchase_order
        vendor = invoice.vendor or (purchase_order.vendor if purchase_order else None)
        po_items = list(purchase_order.items.all()) if purchase_order else []

        invoice_number = invoice.invoice_number or self._invoice_number(invoice)
        invoice_date = invoice.invoice_date or (
            purchase_order.issue_date if purchase_order else date.today()
        )
        if isinstance(invoice_date, datetime):
            invoice_date = invoice_date.date()
        elif isinstance(invoice_date, str):
            invoice_date = date.fromisoformat(invoice_date[:10])
        items = [
            {
                'line_number': item.line_number,
                'description': item.description,
                'hsn_sac_code': '',
                'quantity': item.quantity,
                'unit_of_measure': item.unit_of_measure,
                'unit_price': item.unit_price,
                'tax_rate': item.tax_rate,
                'tax_amount': self._tax(item.quantity, item.unit_price, item.tax_rate),
                'line_total': self._line_total(item.quantity, item.unit_price, item.tax_rate),
                'confidence_score': Decimal('98.00'),
            }
            for item in po_items
        ]

        if not items:
            items = [{
                'line_number': 1,
                'description': 'Managed services and support',
                'hsn_sac_code': '9983',
                'quantity': Decimal('1.00'),
                'unit_of_measure': 'NOS',
                'unit_price': Decimal('10000.00'),
                'tax_rate': Decimal('18.00'),
                'tax_amount': Decimal('1800.00'),
                'line_total': Decimal('11800.00'),
                'confidence_score': Decimal('96.00'),
            }]

        subtotal = sum(
            (Decimal(str(item['quantity'])) * Decimal(str(item['unit_price'])) for item in items),
            Decimal('0.00'),
        )
        tax_amount = sum((Decimal(str(item['tax_amount'])) for item in items), Decimal('0.00'))
        total_amount = subtotal + tax_amount
        fields = {
            'invoice_number': invoice_number,
            'invoice_date': invoice_date.isoformat(),
            'vendor_name': vendor.name if vendor else invoice.vendor_name_extracted or 'Acme Technologies India Pvt Ltd',
            'vendor_gstin': vendor.gstin if vendor else invoice.vendor_gstin_extracted or '27AABCU9603R1ZM',
            'po_number': purchase_order.po_number if purchase_order else invoice.po_number,
            'subtotal': subtotal,
            'tax_amount': tax_amount,
            'total_amount': total_amount,
            'confidence': {
                'invoice_number': 99.0,
                'invoice_date': 97.0,
                'vendor_name': 98.0,
                'vendor_gstin': 97.0,
                'po_number': 96.0,
                'subtotal': 99.0,
                'tax_amount': 99.0,
                'total_amount': 99.0,
            },
        }
        raw_text = (
            f"Tax Invoice {invoice_number}\n"
            f"Vendor: {fields['vendor_name']} GSTIN: {fields['vendor_gstin']}\n"
            f"PO: {fields['po_number']}\n"
            f"Subtotal: {subtotal} Tax: {tax_amount} Total: {total_amount}"
        )
        return OCRExtraction(fields, items, raw_text, Decimal('98.00'))

    @staticmethod
    def _invoice_number(invoice: Invoice) -> str:
        stem = invoice.original_filename.rsplit('.', 1)[0] if invoice.original_filename else 'MOCK'
        return ''.join(char if char.isalnum() else '-' for char in stem).upper()[:100] or 'MOCK-INV'

    @staticmethod
    def _tax(quantity: Decimal, unit_price: Decimal, tax_rate: Decimal) -> Decimal:
        return (quantity * unit_price * tax_rate / Decimal('100')).quantize(Decimal('0.01'))

    @classmethod
    def _line_total(cls, quantity: Decimal, unit_price: Decimal, tax_rate: Decimal) -> Decimal:
        subtotal = (quantity * unit_price).quantize(Decimal('0.01'))
        return subtotal + cls._tax(quantity, unit_price, tax_rate)
