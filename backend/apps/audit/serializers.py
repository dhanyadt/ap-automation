from rest_framework import serializers
from .models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.SerializerMethodField()
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'actor',
            'actor_email',
            'actor_name',
            'action',
            'entity_type',
            'entity_id',
            'changes',
            'ip_address',
            'created_at',
        ]
        read_only_fields = fields

    def get_actor_email(self, obj):
        return obj.actor.email if obj.actor else 'System'

    def get_actor_name(self, obj):
        return obj.actor.get_full_name() if obj.actor else 'Automated Process'
