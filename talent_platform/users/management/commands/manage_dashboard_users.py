import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Manage dashboard users - list, view, delete, and update permissions'

    def add_arguments(self, parser):
        parser.add_argument('--action', type=str, choices=['list', 'view', 'delete', 'promote', 'demote'], 
                          help='Action to perform on dashboard users')
        parser.add_argument('--email', type=str, help='Email of the user to manage')
        parser.add_argument('--non-interactive', action='store_true', help='Run without interactive prompts')

    @transaction.atomic
    def handle(self, *args, **options):
        action = options['action']
        
        if not action and not options['non_interactive']:
            print("🎯 DASHBOARD USER MANAGEMENT TOOL")
            print("=" * 40)
            print("1. List all dashboard users")
            print("2. View specific user details")
            print("3. Delete a dashboard user")
            print("4. Promote user to admin")
            print("5. Demote admin to regular user")
            
            while True:
                choice = input("Enter choice (1-5): ").strip()
                if choice == '1':
                    action = 'list'
                    break
                elif choice == '2':
                    action = 'view'
                    break
                elif choice == '3':
                    action = 'delete'
                    break
                elif choice == '4':
                    action = 'promote'
                    break
                elif choice == '5':
                    action = 'demote'
                    break
                else:
                    print("❌ Invalid choice. Please enter 1-5.")

        if action == 'list':
            self.list_dashboard_users()
        elif action == 'view':
            self.view_user(options)
        elif action == 'delete':
            self.delete_user(options)
        elif action == 'promote':
            self.promote_user(options)
        elif action == 'demote':
            self.demote_user(options)

    def list_dashboard_users(self):
        """List all dashboard users"""
        print("\n📋 DASHBOARD USERS:")
        print("-" * 80)
        
        dashboard_users = User.objects.filter(is_dashboard=True).order_by('email')
        
        if not dashboard_users.exists():
            print("❌ No dashboard users found!")
            return
        
        print(f"{'Email':<30} {'Type':<15} {'Active':<8} {'Staff':<8} {'Super':<8}")
        print("-" * 80)
        
        for user in dashboard_users:
            user_type = "👑 Admin" if user.is_dashboard_admin else "🔧 Regular"
            active = "✅" if user.is_active else "❌"
            staff = "✅" if user.is_staff else "❌"
            superuser = "✅" if user.is_superuser else "❌"
            
            print(f"{user.email:<30} {user_type:<15} {active:<8} {staff:<8} {superuser:<8}")
        
        print(f"\nTotal: {dashboard_users.count()} dashboard users")

    def view_user(self, options):
        """View details of a specific user"""
        email = options['email']
        if not email and not options['non_interactive']:
            email = input("Enter user email: ")
        
        if not email:
            self.stdout.write(self.style.ERROR('Email is required'))
            return
        
        try:
            user = User.objects.get(email=email)
            if not user.is_dashboard:
                self.stdout.write(self.style.ERROR(f'User {email} is not a dashboard user'))
                return
            
            print(f"\n👤 USER DETAILS: {email}")
            print("=" * 50)
            print(f"Name: {user.first_name} {user.last_name}")
            print(f"Email: {user.email}")
            print(f"Active: {'✅ Yes' if user.is_active else '❌ No'}")
            print(f"Dashboard User: {'✅ Yes' if user.is_dashboard else '❌ No'}")
            print(f"Dashboard Admin: {'✅ Yes' if user.is_dashboard_admin else '❌ No'}")
            print(f"Django Staff: {'✅ Yes' if user.is_staff else '❌ No'}")
            print(f"Django Superuser: {'✅ Yes' if user.is_superuser else '❌ No'}")
            print(f"Date Joined: {user.date_joined}")
            print(f"Last Login: {user.last_login or 'Never'}")
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {email} not found'))

    def delete_user(self, options):
        """Delete a dashboard user"""
        email = options['email']
        if not email and not options['non_interactive']:
            email = input("Enter user email to delete: ")
        
        if not email:
            self.stdout.write(self.style.ERROR('Email is required'))
            return
        
        try:
            user = User.objects.get(email=email)
            if not user.is_dashboard:
                self.stdout.write(self.style.ERROR(f'User {email} is not a dashboard user'))
                return
            
            if not options['non_interactive']:
                confirm = input(f"Are you sure you want to delete {email}? (yes/no): ")
                if confirm.lower() != 'yes':
                    self.stdout.write(self.style.SUCCESS('Deletion cancelled'))
                    return
            
            user.delete()
            self.stdout.write(self.style.SUCCESS(f'User {email} deleted successfully'))
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {email} not found'))

    def promote_user(self, options):
        """Promote a regular dashboard user to admin"""
        email = options['email']
        if not email and not options['non_interactive']:
            email = input("Enter user email to promote to admin: ")
        
        if not email:
            self.stdout.write(self.style.ERROR('Email is required'))
            return
        
        try:
            user = User.objects.get(email=email)
            if not user.is_dashboard:
                self.stdout.write(self.style.ERROR(f'User {email} is not a dashboard user'))
                return
            
            if user.is_dashboard_admin:
                self.stdout.write(self.style.WARNING(f'User {email} is already an admin'))
                return
            
            user.is_dashboard_admin = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'User {email} promoted to admin successfully'))
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {email} not found'))

    def demote_user(self, options):
        """Demote an admin to regular dashboard user"""
        email = options['email']
        if not email and not options['non_interactive']:
            email = input("Enter user email to demote from admin: ")
        
        if not email:
            self.stdout.write(self.style.ERROR('Email is required'))
            return
        
        try:
            user = User.objects.get(email=email)
            if not user.is_dashboard:
                self.stdout.write(self.style.ERROR(f'User {email} is not a dashboard user'))
                return
            
            if not user.is_dashboard_admin:
                self.stdout.write(self.style.WARNING(f'User {email} is not an admin'))
                return
            
            user.is_dashboard_admin = False
            user.save()
            self.stdout.write(self.style.SUCCESS(f'User {email} demoted to regular user successfully'))
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {email} not found'))
