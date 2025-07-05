from django.conf import settings

# List of countries with payment restrictions
RESTRICTED_COUNTRIES = [
    'Syria',           # Sanctions
    'Iran',            # Sanctions
    'North Korea',     # Sanctions
    'Cuba',            # Sanctions
    'Venezuela',       # Banking restrictions
    'Sudan',           # Sanctions
    'Myanmar',         # Banking restrictions
    'Belarus',         # Sanctions
    'Russia',          # Banking restrictions (partial)
    'Crimea',          # Sanctions
    'Donetsk',         # Sanctions
    'Luhansk',         # Sanctions
    'Afghanistan',     # Banking restrictions
    'Yemen',           # Banking restrictions
    'Libya',           # Banking restrictions
    'Iraq',            # Banking restrictions (partial)
    'Somalia',         # Banking restrictions
    'Central African Republic',  # Banking restrictions
    'Democratic Republic of the Congo',  # Banking restrictions
    'South Sudan',     # Banking restrictions
    'Eritrea',         # Banking restrictions
    'Burundi',         # Banking restrictions
    'Zimbabwe',        # Banking restrictions
    'Mali',            # Banking restrictions
    'Burkina Faso',    # Banking restrictions
    'Niger',           # Banking restrictions
    'Chad',            # Banking restrictions
    'Guinea-Bissau',   # Banking restrictions
    'Guinea',          # Banking restrictions
    'Sierra Leone',    # Banking restrictions
    'Liberia',         # Banking restrictions
    'Comoros',         # Banking restrictions
    'Madagascar',      # Banking restrictions
    'Mauritania',      # Banking restrictions
    'Western Sahara',  # Banking restrictions
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