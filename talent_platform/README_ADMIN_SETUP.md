# Admin Dashboard User Setup Guide

## Initial Admin Setup

For security reasons, admin dashboard users can only be created through a management command. This ensures that the admin creation process is secure and can only be performed by someone with server access.

### Creating the First Admin Dashboard User

To create the first admin dashboard user, run the following command from the project root directory:

```bash
python manage.py create_admin_dashboard_user
```

You will be prompted to enter:
- Username (will be converted to email format: username@dashboard.internal)
- Password (entered securely without displaying characters)
- First name
- Last name

### Non-interactive Mode

You can also create an admin user in non-interactive mode by providing all required parameters:

```bash
python manage.py create_admin_dashboard_user --username=admin --password=securepassword --first_name=Admin --last_name=User --non-interactive
```

## Security Considerations

1. **Admin Creation**: Admin dashboard users can ONLY be created through the management command, not through the API.

2. **Dashboard User Creation**: Regular dashboard users can only be created by admin dashboard users through the protected API endpoint.

3. **Authentication**: All dashboard operations require proper authentication using JWT tokens.

## Managing Dashboard Users

Once you have created an admin dashboard user, you can log in and manage regular dashboard users through the following API endpoints:

### Creating Dashboard Users (Admin Only)

```
POST /api/dashboard/users/create/
```

Required fields:
- username
- password
- confirm_password
- first_name
- last_name

### Listing Dashboard Users (Admin Only)

```
GET /api/dashboard/users/
```

### Getting Dashboard User Details (Admin Only)

```
GET /api/dashboard/users/{user_id}/
```

### Deleting Dashboard Users (Admin Only)

```
DELETE /api/dashboard/users/{user_id}/
```

## Best Practices

1. Use strong, unique passwords for admin accounts
2. Regularly rotate admin credentials
3. Limit the number of admin users to only those who absolutely need admin privileges
4. Monitor admin user activity through logs
5. Implement IP restrictions for admin access if possible