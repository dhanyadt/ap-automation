import os
from django.core.management.base import BaseCommand
from apps.accounts.models import User

class Command(BaseCommand):
    help = 'Seeds initial development users for each RBAC role'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            type=str,
            default=os.getenv('SEED_USER_PASSWORD', 'Password123!'),
            help='Password to assign to seeded users'
        )

    def handle(self, *args, **options):
        password = options['password']

        users_data = [
            {
                'email': 'admin@apautomation.com',
                'first_name': 'Super',
                'last_name': 'Admin',
                'role': User.Role.ADMIN,
                'department': 'Information Technology',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'email': 'clerk@apautomation.com',
                'first_name': 'Priya',
                'last_name': 'Sharma',
                'role': User.Role.AP_CLERK,
                'department': 'Accounts Payable',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'email': 'approver@apautomation.com',
                'first_name': 'Rajesh',
                'last_name': 'Kumar',
                'role': User.Role.APPROVER,
                'department': 'Procurement & Operations',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'email': 'finance@apautomation.com',
                'first_name': 'Anita',
                'last_name': 'Deshmukh',
                'role': User.Role.FINANCE,
                'department': 'Corporate Finance',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'email': 'cfo@apautomation.com',
                'first_name': 'Vikram',
                'last_name': 'Mehta',
                'role': User.Role.CFO,
                'department': 'Executive Leadership',
                'is_staff': True,
                'is_superuser': False,
            },
            {
                'email': 'vendor@apautomation.com',
                'first_name': 'Sunil',
                'last_name': 'Patel',
                'role': User.Role.VENDOR,
                'department': 'Vendor Portal',
                'is_staff': False,
                'is_superuser': False,
            },
        ]

        self.stdout.write(self.style.MIGRATE_HEADING("Seeding RBAC users..."))

        for data in users_data:
            email = data['email']
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'role': data['role'],
                    'department': data['department'],
                    'is_staff': data['is_staff'],
                    'is_superuser': data['is_superuser'],
                    'is_active': True,
                }
            )

            user.set_password(password)
            user.role = data['role']
            user.department = data['department']
            user.is_staff = data['is_staff']
            user.is_superuser = data['is_superuser']
            user.save()

            status = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(
                f"  [{status}] {user.email} -> Role: {user.role} ({user.get_role_display()})"
            ))

        self.stdout.write(self.style.SUCCESS(f"\nSuccessfully seeded users! Default password: {password}"))
