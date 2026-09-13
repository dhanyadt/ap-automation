import uuid
from django.db import models
from common.models import TimeStampedModel
from common.utils import mask_bank_account

class Vendor(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PENDING_REVIEW = 'PENDING_REVIEW', 'Pending Review'
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        BLOCKED = 'BLOCKED', 'Blocked'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    gstin = models.CharField(max_length=15, db_index=True, blank=True, default='', help_text='15-character Indian GSTIN')
    pan = models.CharField(max_length=10, blank=True, default='', help_text='10-character Indian Permanent Account Number')
    email = models.EmailField(blank=True, default='')
    phone = models.CharField(max_length=20, blank=True, default='')
    address_line1 = models.CharField(max_length=255, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    pincode = models.CharField(max_length=10, blank=True, default='')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    msme_registered = models.BooleanField(default=False)
    payment_terms_days = models.PositiveIntegerField(default=30, help_text='Standard payment credit period in days')

    class Meta:
        db_table = 'ap_vendors'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class VendorBankAccount(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='bank_accounts')
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50, help_text='Plain account number for payments processing')
    ifsc_code = models.CharField(max_length=11, help_text='11-character Indian IFSC code')
    branch_name = models.CharField(max_length=255, blank=True, default='')
    is_primary = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=True)

    class Meta:
        db_table = 'ap_vendor_bank_accounts'

    @property
    def masked_account_number(self):
        return mask_bank_account(self.account_number)

    def __str__(self):
        return f"{self.bank_name} - {self.masked_account_number} ({self.vendor.name})"
