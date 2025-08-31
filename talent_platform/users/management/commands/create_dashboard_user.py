import os
import getpass
from datetime import date
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates dashboard users (regular or admin) for the talent platform'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Email for the dashboard user')
        parser.add_argument('--password', type=str, help='Password for the dashboard user')
        parser.add_argument('--first_name', type=str, help='First name for the dashboard user')
        parser.add_argument('--last_name', type=str, help='Last name for the dashboard user')
        parser.add_argument('--user_type', type=str, choices=['regular', 'admin'], help='Type of dashboard user to create')
        parser.add_argument('--non-interactive', action='store_true', help='Run without interactive prompts')
        parser.add_argument('--force', action='store_true', help='Force creation even if user exists')

    @transaction.atomic
    def handle(self, *args, **options):
        print("🎯 DASHBOARD USER CREATION TOOL")
        print("=" * 40)
        
        # Get user type
        user_type = options['user_type']
        if not user_type and not options['non_interactive']:
            print("\n📋 Choose user type:")
            print("1. Regular Dashboard User (limited permissions)")
            print("2. Admin Dashboard User (full admin access)")
            
            while True:
                choice = input("Enter choice (1 or 2): ").strip()
                if choice == '1':
                    user_type = 'regular'
                    break
                elif choice == '2':
                    user_type = 'admin'
                    break
                else:
                    print("❌ Invalid choice. Please enter 1 or 2.")
        
        if not user_type:
            self.stdout.write(self.style.ERROR('User type is required'))
            return

        # Get email
        username = options['username']
        if not username and not options['non_interactive']:
            username = input(f'Enter email for {user_type} dashboard user: ')
        if not username:
            self.stdout.write(self.style.ERROR('Email is required'))
            return

        # Check if email already exists
        email = username
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'User with email {email} already exists'))
            
            if not options['force']:
                update = 'y'
                if not options['non_interactive']:
                    update = input('Do you want to update this user to dashboard user? (y/n): ')
                if update.lower() != 'y':
                    self.stdout.write(self.style.SUCCESS('Operation cancelled.'))
                    return
            
            # Update existing user
            existing_user = User.objects.get(email=email)
            
            if user_type == 'admin':
                existing_user.is_dashboard = True
                existing_user.is_dashboard_admin = True
                existing_user.is_staff = False  # Custom dashboard only
                existing_user.is_superuser = False
            else:  # regular
                existing_user.is_dashboard = True
                existing_user.is_dashboard_admin = False
                existing_user.is_staff = False
                existing_user.is_superuser = False
            
            # Update password if provided
            if options['password']:
                existing_user.set_password(options['password'])
            
            existing_user.save()
            
            self.stdout.write(self.style.SUCCESS(f'Updated existing user {email} to {user_type} dashboard user'))
            self.stdout.write(self.style.SUCCESS(f'Dashboard User: {existing_user.is_dashboard}'))
            self.stdout.write(self.style.SUCCESS(f'Dashboard Admin: {existing_user.is_dashboard_admin}'))
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

        # Create dashboard user
        try:
            if user_type == 'admin':
                user = User.objects.create_admin_dashboard_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=False,  # Custom dashboard only, no Django admin
                    date_of_birth=date(1990, 1, 1),
                    gender='Prefer not to say',
                    country='System'
                )
                self.stdout.write(self.style.SUCCESS(f'👑 Admin dashboard user {email} created successfully'))
            else:  # regular
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_dashboard=True,
                    is_dashboard_admin=False,
                    is_staff=False,
                    is_superuser=False,
                    date_of_birth=date(1990, 1, 1),
                    gender='Prefer not to say',
                    country='System'
                )
                self.stdout.write(self.style.SUCCESS(f'🔧 Regular dashboard user {email} created successfully'))
            
            self.stdout.write(self.style.SUCCESS(f'Email: {email}'))
            self.stdout.write(self.style.SUCCESS(f'Dashboard User: {user.is_dashboard}'))
            self.stdout.write(self.style.SUCCESS(f'Dashboard Admin: {user.is_dashboard_admin}'))
            self.stdout.write(self.style.SUCCESS(f'User Type: {user_type.title()}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to create {user_type} dashboard user: {str(e)}'))
