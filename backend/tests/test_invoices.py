import pytest
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.invoices.models import Invoice
from apps.audit.models import AuditLog

@pytest.mark.django_db
class TestInvoices:
    def test_upload_invoice_pdf(self, clerk_client, sample_vendor):
        pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 595 842]>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n0000000101 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n162\n%%EOF\n"
        fake_pdf = SimpleUploadedFile("tax_invoice_test.pdf", pdf_content, content_type="application/pdf")

        response = clerk_client.post('/api/v1/invoices/upload/', {
            'file': fake_pdf,
            'vendor': str(sample_vendor.id),
            'po_number': 'PO-2026-001'
        }, format='multipart')

        assert response.status_code == 201
        data = response.data['data']
        assert data['original_filename'] == 'tax_invoice_test.pdf'
        assert data['processing_status'] == 'UPLOADED'
        assert data['ocr_status'] == 'PENDING'
        assert data['validation_status'] == 'PENDING'
        assert data['po_number'] == 'PO-2026-001'
        assert str(data['vendor']) == str(sample_vendor.id)

        # Verify audit record
        audit = AuditLog.objects.filter(entity_type='INVOICE', entity_id=data['id']).first()
        assert audit is not None
        assert audit.action == 'INVOICE_UPLOADED'

    def test_upload_invalid_file_extension(self, clerk_client):
        bad_file = SimpleUploadedFile("malicious_script.sh", b"echo 'hacked'", content_type="text/plain")
        response = clerk_client.post('/api/v1/invoices/upload/', {
            'file': bad_file
        }, format='multipart')
        assert response.status_code == 400

    def test_duplicate_invoice_business_rule(self, clerk_client, sample_vendor):
        # Create first invoice in FY2026-27
        res1 = clerk_client.post('/api/v1/invoices/', {
            'vendor': str(sample_vendor.id),
            'invoice_number': 'INV-TEST-001',
            'fiscal_year': 'FY2026-27',
            'invoice_date': '2026-05-15',
            'subtotal': '10000.00',
            'tax_amount': '1800.00',
            'total_amount': '11800.00',
        }, format='json')
        assert res1.status_code == 201

        # Attempt to create exact duplicate with same vendor + invoice_number + fiscal_year
        res2 = clerk_client.post('/api/v1/invoices/', {
            'vendor': str(sample_vendor.id),
            'invoice_number': 'INV-TEST-001',
            'fiscal_year': 'FY2026-27',
            'invoice_date': '2026-05-15',
            'total_amount': '11800.00',
        }, format='json')
        assert res2.status_code == 400
        assert 'invoice_number' in res2.data['error']['details']

        # Allow same invoice_number in a DIFFERENT fiscal year (e.g. FY2027-28)
        res3 = clerk_client.post('/api/v1/invoices/', {
            'vendor': str(sample_vendor.id),
            'invoice_number': 'INV-TEST-001',
            'fiscal_year': 'FY2027-28',
            'invoice_date': '2027-05-15',
            'total_amount': '11800.00',
        }, format='json')
        assert res3.status_code == 201

    def test_create_invoice_with_items(self, clerk_client, sample_vendor):
        payload = {
            'vendor': str(sample_vendor.id),
            'invoice_number': 'INV-ITEMS-001',
            'fiscal_year': 'FY2026-27',
            'invoice_date': '2026-06-01',
            'subtotal': '50000.00',
            'tax_amount': '9000.00',
            'total_amount': '59000.00',
            'items': [
                {
                    'line_number': 1,
                    'description': 'Software License Subscription',
                    'quantity': '1.00',
                    'unit_price': '50000.00',
                    'tax_rate': '18.00',
                    'tax_amount': '9000.00',
                    'line_total': '59000.00'
                }
            ]
        }
        res = clerk_client.post('/api/v1/invoices/', payload, format='json')
        assert res.status_code == 201
        data = res.data
        assert data['invoice_number'] == 'INV-ITEMS-001'
        assert len(data['items']) == 1
        assert Decimal(data['items'][0]['line_total']) == Decimal('59000.00')
