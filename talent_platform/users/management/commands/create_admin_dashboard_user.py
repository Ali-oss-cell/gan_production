import os
import getpass
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates an admin dashboard user for the talent platform'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username for the admin dashboard user')
        parser.add_argument('--password', type=str, help='Password for the admin dashboard user')
        parser.add_argument('--first_name', type=str, help='First name for the admin dashboard user')
        parser.add_argument('--last_name', type=str, help='Last name for the admin dashboard user')
        parser.add_argument('--non-interactive', action='store_true', help='Run without interactive prompts')

    @transaction.atomic
    def handle(self, *args, **options):
        # Check if admin dashboard user already exists
        admin_exists = User.objects.filter(is_dashboard=True, is_dashboard_admin=True).exists()
        if admin_exists:
            self.stdout.write(self.style.WARNING('An admin dashboard user already exists!'))
            proceed = 'y'
            if not options['non_interactive']:
                proceed = input('Do you want to create another admin dashboard user? (y/n): ')
            if proceed.lower() != 'y':
                self.stdout.write(self.style.SUCCESS('Operation cancelled.'))
                return

        # Get username
        username = options['username']
        if not username and not options['non_interactive']:
            username = input('Enter username: ')
        if not username:
            self.stdout.write(self.style.ERROR('Username is required'))
            return

        # Check if username already exists
        email = f"{username}@dashboard.internal"
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.ERROR(f'User with username {username} already exists'))
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
        if not first_name and not options['non_interactive']:
            first_name = input('Enter first name: ')
        if not first_name:
            self.stdout.write(self.style.ERROR('First name is required'))
            return

        # Get last name
        last_name = options['last_name']
        if not last_name and not options['non_interactive']:
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
                last_name=last_name
            )
            self.stdout.write(self.style.SUCCESS(f'Admin dashboard user {username} created successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to create admin dashboard user: {str(e)}'))