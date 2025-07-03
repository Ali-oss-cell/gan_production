# 🚫 Restricted Countries Payment System

This guide explains how the system handles users from countries with payment restrictions.

## 🎯 **Overview**

The system automatically detects and blocks payment processing for users from countries that have:
- **Economic sanctions** (Syria, Iran, North Korea, Cuba)
- **Banking restrictions** (Venezuela, Myanmar, Afghanistan)
- **Limited payment infrastructure** (Somalia, Yemen, Libya)

## 🚫 **Current Restricted Countries**

### **Sanctions (High Restriction)**
- **Syria** - Economic sanctions
- **Iran** - Economic sanctions  
- **North Korea** - Economic sanctions
- **Cuba** - Economic sanctions
- **Sudan** - Economic sanctions
- **Belarus** - Economic sanctions
- **Crimea** - Economic sanctions
- **Donetsk** - Economic sanctions
- **Luhansk** - Economic sanctions

### **Banking Restrictions (Medium Restriction)**
- **Venezuela** - Banking restrictions
- **Myanmar** - Banking restrictions
- **Russia** - Banking restrictions (partial)
- **Afghanistan** - Banking restrictions
- **Yemen** - Banking restrictions
- **Libya** - Banking restrictions
- **Iraq** - Banking restrictions (partial)

### **Limited Infrastructure (Low Restriction)**
- **Somalia** - Limited banking infrastructure
- **Central African Republic** - Limited banking infrastructure
- **Democratic Republic of the Congo** - Limited banking infrastructure
- **South Sudan** - Limited banking infrastructure
- **Eritrea** - Limited banking infrastructure
- **Burundi** - Limited banking infrastructure
- **Zimbabwe** - Limited banking infrastructure
- **Mali** - Limited banking infrastructure
- **Burkina Faso** - Limited banking infrastructure
- **Niger** - Limited banking infrastructure
- **Chad** - Limited banking infrastructure
- **Guinea-Bissau** - Limited banking infrastructure
- **Guinea** - Limited banking infrastructure
- **Sierra Leone** - Limited banking infrastructure
- **Liberia** - Limited banking infrastructure
- **Comoros** - Limited banking infrastructure
- **Madagascar** - Limited banking infrastructure
- **Mauritania** - Limited banking infrastructure
- **Western Sahara** - Limited banking infrastructure

## 🔧 **How It Works**

### **1. Country Detection**
```python
# Frontend sends country code
region_code = "sy"  # Syria

# Backend converts to full name
country_name = CountryDetectionService.get_country_name_from_code("sy")
# Returns: "Syria"
```

### **2. Restriction Check**
```python
# Check if country is restricted
is_restricted = has_payment_restrictions("Syria")
# Returns: True
```

### **3. Payment Blocking**
```python
# If restricted, payment is blocked
if is_restricted:
    return Response({
        'error': 'Payment not available',
        'message': 'Payment processing is not available for users from Syria. Please contact support for assistance.',
        'country': 'Syria',
        'restricted': True
    }, status=403)
```

## 📋 **API Responses**

### **Restricted Country (Syria)**
```json
{
    "error": "Payment not available",
    "message": "Payment processing is not available for users from Syria. Please contact support for assistance.",
    "country": "Syria",
    "restricted": true
}
```
**Status**: `403 Forbidden`

### **Allowed Country (UAE)**
```json
{
    "session_id": "cs_xxx",
    "url": "https://checkout.stripe.com/xxx",
    "detected_region": "ae",
    "payment_methods": ["card", "apple_pay", "google_pay", "paypal", "mada", "unionpay"]
}
```
**Status**: `200 OK`

## 🛠️ **Implementation**

### **Frontend Integration**
```javascript
// Check country before sending payment request
const checkCountryEligibility = async (countryCode) => {
    try {
        const response = await fetch('/api/payments/subscriptions/create_checkout_session/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                plan_id: 1,
                region_code: countryCode
            })
        });
        
        if (response.status === 403) {
            const error = await response.json();
            if (error.restricted) {
                // Show restricted country message
                showRestrictedCountryMessage(error.message);
                return false;
            }
        }
        
        return true;
    } catch (error) {
        console.error('Payment error:', error);
        return false;
    }
};
```

### **Backend Processing**
```python
# In payment views
eligibility = CountryDetectionService.check_user_payment_eligibility(user, region_code)
if not eligibility['eligible']:
    return Response({
        'error': 'Payment not available',
        'message': eligibility['message'],
        'country': eligibility['country'],
        'restricted': eligibility['restricted']
    }, status=status.HTTP_403_FORBIDDEN)
```

## 📊 **Database Tracking**

### **RestrictedCountryUser Model**
When a user from a restricted country tries to make a payment:

```python
# Automatically created
RestrictedCountryUser.objects.create(
    user=user,
    country="Syria",
    is_approved=False,
    account_type='free',
    notes="User from restricted country"
)
```

### **Admin Interface**
Admins can:
- View all restricted country users
- Manually approve accounts
- Update account types
- Add notes and comments

## 🔄 **Workflow for Restricted Users**

### **1. User Registration**
- User selects country from dropdown
- System detects if country is restricted
- If restricted, user gets free account by default

### **2. Payment Attempt**
- User tries to make payment
- System blocks payment with 403 error
- Creates RestrictedCountryUser entry

### **3. Admin Review**
- Admin sees user in restricted country list
- Can manually review and approve
- Can upgrade account type if needed

### **4. Manual Processing**
- Admin can process payment manually
- Can provide alternative payment methods
- Can contact user for verification

## 🧪 **Testing**

### **Run Restricted Countries Test**
```bash
cd talent_platform
python payments/test_restricted_countries.py
```

### **Test Output Example**
```
🚫 Testing Restricted Countries
==================================================

1. Current Restricted Countries:
   🚫 Syria
   🚫 Iran
   🚫 North Korea
   ...

2. Country Restriction Tests:
   ✅ SY (Syria): RESTRICTED (expected: RESTRICTED)
   ✅ AE (United Arab Emirates): ALLOWED (expected: ALLOWED)
   ✅ US (United States): ALLOWED (expected: ALLOWED)

3. Payment Eligibility Tests:
   🚫 Syria - Should be blocked
      Eligible: False
      Country: Syria
      Restricted: True
      Message: Payment processing is not available for users from Syria...
```

## 🔒 **Security & Compliance**

### **Legal Compliance**
- Follows international sanctions
- Complies with banking regulations
- Prevents illegal transactions

### **Risk Management**
- Automatic detection and blocking
- Manual review process
- Audit trail for all decisions

### **User Experience**
- Clear error messages
- Alternative support channels
- Manual approval process

## 📞 **Support for Restricted Users**

### **Contact Information**
- Email: support@yoursite.com
- Phone: +1-XXX-XXX-XXXX
- Live Chat: Available during business hours

### **Alternative Solutions**
- Manual payment processing
- Alternative payment methods
- Account verification process
- Special approval workflows

## 🔄 **Adding New Restricted Countries**

### **Update Configuration**
```python
# In country_restrictions.py
RESTRICTED_COUNTRIES = [
    'Syria',
    'Iran',
    'New Country',  # Add new country here
]
```

### **Test the Addition**
```bash
python payments/test_restricted_countries.py
```

### **Update Documentation**
- Add country to this guide
- Update admin documentation
- Notify support team

## 📈 **Monitoring & Analytics**

### **Metrics to Track**
- Number of restricted country attempts
- Countries with highest restrictions
- Manual approval rates
- User support requests

### **Reports**
- Daily restricted country report
- Monthly compliance report
- Quarterly risk assessment

## 🚀 **Future Enhancements**

1. **Dynamic Restrictions**: Real-time updates based on sanctions
2. **Alternative Payments**: Cryptocurrency for restricted countries
3. **Regional Partners**: Local payment processors
4. **Compliance API**: Integration with compliance services
5. **Risk Scoring**: Automated risk assessment

---

**This system ensures compliance with international regulations while providing a clear path for legitimate users from restricted countries to access your services.** 🚫🌍✅ 