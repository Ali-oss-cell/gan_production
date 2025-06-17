from django.conf import settings

# List of countries with payment restrictions
RESTRICTED_COUNTRIES = [
    'Syria',  # Add other countries as needed
]

# Function to check if a country has payment restrictions
def has_payment_restrictions(country):
    """
    Check if a country has payment restrictions.
    
    Args:
        country (str): The country name to check
        
    Returns:
        bool: True if the country has payment restrictions, False otherwise
    """
    if not country:
        return False
        
    return country.strip().lower() in [c.lower() for c in RESTRICTED_COUNTRIES]

# Function to check if a user has payment restrictions based on their country
def user_has_payment_restrictions(user):
    """
    Check if a user has payment restrictions based on their country.
    
    Args:
        user: The user object to check
        
    Returns:
        bool: True if the user has payment restrictions, False otherwise
    """
    if not user:
        return False
        
    # Check user's country field
    return has_payment_restrictions(user.country)