import pytest
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.vendors.models import Vendor, VendorBankAccount
from apps.purchase_orders.models import PurchaseOrder, POItem
from apps.goods_receipts.models import GoodsReceipt, GRNItem
from apps.invoices.models import Invoice

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(
        email='admin_test@apautomation.com',
        password='TestPassword123!',
        first_name='Admin',
        last_name='User',
        role=User.Role.ADMIN,
        is_staff=True,
        is_superuser=True
    )
    return user

@pytest.fixture
def ap_clerk_user(db):
    user = User.objects.create_user(
        email='clerk_test@apautomation.com',
        password='TestPassword123!',
        first_name='Priya',
        last_name='Clerk',
        role=User.Role.AP_CLERK,
        department='Accounts Payable'
    )
    return user

@pytest.fixture
def approver_user(db):
    user = User.objects.create_user(
        email='approver_test@apautomation.com',
        password='TestPassword123!',
        first_name='Rajesh',
        last_name='Approver',
        role=User.Role.APPROVER,
        department='Procurement'
    )
    return user

@pytest.fixture
def vendor_user(db):
    user = User.objects.create_user(
        email='vendor_rep@apautomation.com',
        password='TestPassword123!',
        first_name='Sunil',
        last_name='Vendor',
        role=User.Role.VENDOR,
        department='External'
    )
    return user

@pytest.fixture
def clerk_client(api_client, ap_clerk_user):
    api_client.force_authenticate(user=ap_clerk_user)
    return api_client

@pytest.fixture
def approver_client(api_client, approver_user):
    api_client.force_authenticate(user=approver_user)
    return api_client

@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client

@pytest.fixture
def sample_vendor(db):
    vendor = Vendor.objects.create(
        name='Tata Consultancy Services Ltd',
        code='VEND-TCS-001',
        gstin='27AAACT2727Q1ZW',
        pan='AAACT2727Q',
        email='billing@tcs.com',
        phone='+91 22 6778 9999',
        city='Mumbai',
        state='Maharashtra',
        status=Vendor.Status.ACTIVE,
        payment_terms_days=30
    )
    VendorBankAccount.objects.create(
        vendor=vendor,
        bank_name='State Bank of India',
        account_number='123456789012',
        ifsc_code='SBIN0001234',
        branch_name='Nariman Point',
        is_primary=True,
        is_verified=True
    )
    return vendor

@pytest.fixture
def sample_po(db, sample_vendor):
    from decimal import Decimal
    po = PurchaseOrder.objects.create(
        po_number='PO-2026-001',
        vendor=sample_vendor,
        status=PurchaseOrder.Status.ISSUED,
        issue_date='2026-04-10',
        subtotal=Decimal('10000.00'),
        tax_amount=Decimal('1800.00'),
        total_amount=Decimal('11800.00')
    )
    POItem.objects.create(
        po=po,
        line_number=1,
        item_code='SKU-LAPTOP-01',
        description='Dell Latitude Enterprise Laptop',
        quantity=Decimal('2.00'),
        unit_price=Decimal('5000.00'),
        tax_rate=Decimal('18.00'),
        line_total=Decimal('11800.00')
    )
    return po
