import os
import getpass
from datetime import date
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates an admin dashboard user for the talent platform'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Email for the admin dashboard user')
        parser.add_argument('--password', type=str, help='Password for the admin dashboard user')
        parser.add_argument('--first_name', type=str, help='First name for the admin dashboard user')
        parser.add_argument('--last_name', type=str, help='Last name for the admin dashboard user')
        parser.add_argument('--non-interactive', action='store_true', help='Run without interactive prompts')
        parser.add_argument('--force', action='store_true', help='Force creation even if user exists')

    @transaction.atomic
    def handle(self, *args, **options):
        # Get email
        username = options['username']
        if not username and not options['non_interactive']:
            username = input('Enter email: ')
        if not username:
            self.stdout.write(self.style.ERROR('Email is required'))
            return

        # Check if email already exists
        email = username  # Use the username as email directly
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'User with email {email} already exists'))
            
            if not options['force']:
                update = 'y'
                if not options['non-interactive']:
                    update = input('Do you want to update this user to dashboard admin? (y/n): ')
                if update.lower() != 'y':
                    self.stdout.write(self.style.SUCCESS('Operation cancelled.'))
                    return
            
            # Update existing user
            existing_user = User.objects.get(email=email)
            existing_user.is_dashboard = True
            existing_user.is_dashboard_admin = True
            existing_user.is_staff = False  # Custom dashboard only, no Django admin
            existing_user.is_superuser = False
            
            # Update password if provided
            if options['password']:
                existing_user.set_password(options['password'])
            
            existing_user.save()
            
            self.stdout.write(self.style.SUCCESS(f'Updated existing user {email} to dashboard admin'))
            self.stdout.write(self.style.SUCCESS(f'Dashboard Admin: {existing_user.is_dashboard_admin}'))
            self.stdout.write(self.style.SUCCESS(f'Dashboard User: {existing_user.is_dashboard}'))
            return

        # Get password
        password = options['password']
        if not password and not options['non_interactive']:
            password = getpass.getpass('Enter password: ')
            password_confirm = getpass.getpass('Confirm password: ')
            if password != password_confirm:
                self.stdout.write(self.style.ERROR('Passwords do not match'))
                return
        if not password:
            self.stdout.write(self.style.ERROR('Password is required'))
            return

        # Get first name
        first_name = options['first_name']
        if not first_name and not options['non-interactive']:
            first_name = input('Enter first name: ')
        if not first_name:
            self.stdout.write(self.style.ERROR('First name is required'))
            return

        # Get last name
        last_name = options['last_name']
        if not last_name and not options['non-interactive']:
            last_name = input('Enter last name: ')
        if not last_name:
            self.stdout.write(self.style.ERROR('Last name is required'))
            return

        # Create admin dashboard user
        try:
            user = User.objects.create_admin_dashboard_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=False,  # Custom dashboard only, no Django admin
                date_of_birth=date(1990, 1, 1),  # Default date for admin users
                gender='Prefer not to say',
                country='System'
            )
            self.stdout.write(self.style.SUCCESS(f'Admin dashboard user {email} created successfully'))
            self.stdout.write(self.style.SUCCESS(f'Email: {email}'))
            self.stdout.write(self.style.SUCCESS(f'Dashboard Admin: {user.is_dashboard_admin}'))
            self.stdout.write(self.style.SUCCESS(f'Dashboard User: {user.is_dashboard}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to create admin dashboard user: {str(e)}'))