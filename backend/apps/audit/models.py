import uuid
from django.db import models
from apps.accounts.models import User

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_entries')
    action = models.CharField(max_length=100, db_index=True)
    entity_type = models.CharField(max_length=50, db_index=True)
    entity_id = models.CharField(max_length=100, db_index=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'ap_audit_logs'
        ordering = ['-created_at']

    def __str__(self):
        actor_str = self.actor.email if self.actor else 'System'
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {actor_str}: {self.action} on {self.entity_type} {self.entity_id}"
