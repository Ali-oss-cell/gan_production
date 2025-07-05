import requests
import json
from typing import Optional
from django.http import HttpRequest
from users.models import BaseUser
from .country_restrictions import has_payment_restrictions, RESTRICTED_COUNTRIES
from .models_restrictions import RestrictedCountryUser

class CountryDetectionService:
    """
    Service for detecting user's country for payment method selection
    """
    
    # Country code mapping for common variations
    COUNTRY_CODE_MAPPING = {
        'united states': 'us',
        'usa': 'us',
        'united states of america': 'us',
        'uae': 'ae',
        'united arab emirates': 'ae',
        'uk': 'gb',
        'united kingdom': 'gb',
        'great britain': 'gb',
        'england': 'gb',
        'scotland': 'gb',
        'wales': 'gb',
        'northern ireland': 'gb',
        'canada': 'ca',
        'australia': 'au',
        'germany': 'de',
        'france': 'fr',
        'spain': 'es',
        'italy': 'it',
        'netherlands': 'nl',
        'belgium': 'be',
        'switzerland': 'ch',
        'austria': 'at',
        'sweden': 'se',
        'norway': 'no',
        'denmark': 'dk',
        'finland': 'fi',
        'poland': 'pl',
        'czech republic': 'cz',
        'hungary': 'hu',
        'romania': 'ro',
        'bulgaria': 'bg',
        'greece': 'gr',
        'portugal': 'pt',
        'ireland': 'ie',
        'new zealand': 'nz',
        'japan': 'jp',
        'south korea': 'kr',
        'china': 'cn',
        'india': 'in',
        'brazil': 'br',
        'mexico': 'mx',
        'argentina': 'ar',
        'chile': 'cl',
        'colombia': 'co',
        'peru': 'pe',
        'venezuela': 've',
        'uruguay': 'uy',
        'paraguay': 'py',
        'ecuador': 'ec',
        'bolivia': 'bo',
        'guyana': 'gy',
        'suriname': 'sr',
        'french guiana': 'gf',
        'falkland islands': 'fk',
        'south africa': 'za',
        'nigeria': 'ng',
        'kenya': 'ke',
        'egypt': 'eg',
        'morocco': 'ma',
        'tunisia': 'tn',
        'algeria': 'dz',
        'libya': 'ly',
        'sudan': 'sd',
        'ethiopia': 'et',
        'uganda': 'ug',
        'tanzania': 'tz',
        'ghana': 'gh',
        'ivory coast': 'ci',
        'senegal': 'sn',
        'mali': 'ml',
        'burkina faso': 'bf',
        'niger': 'ne',
        'chad': 'td',
        'cameroon': 'cm',
        'central african republic': 'cf',
        'congo': 'cg',
        'democratic republic of the congo': 'cd',
        'angola': 'ao',
        'zambia': 'zm',
        'zimbabwe': 'zw',
        'botswana': 'bw',
        'namibia': 'na',
        'mozambique': 'mz',
        'madagascar': 'mg',
        'mauritius': 'mu',
        'seychelles': 'sc',
        'comoros': 'km',
        'mayotte': 'yt',
        'reunion': 're',
        'saudi arabia': 'sa',
        'kuwait': 'kw',
        'qatar': 'qa',
        'bahrain': 'bh',
        'oman': 'om',
        'yemen': 'ye',
        'jordan': 'jo',
        'lebanon': 'lb',
        'syria': 'sy',
        'iraq': 'iq',
        'iran': 'ir',
        'afghanistan': 'af',
        'pakistan': 'pk',
        'bangladesh': 'bd',
        'sri lanka': 'lk',
        'nepal': 'np',
        'bhutan': 'bt',
        'myanmar': 'mm',
        'thailand': 'th',
        'laos': 'la',
        'cambodia': 'kh',
        'vietnam': 'vn',
        'malaysia': 'my',
        'singapore': 'sg',
        'indonesia': 'id',
        'philippines': 'ph',
        'brunei': 'bn',
        'east timor': 'tl',
        'papua new guinea': 'pg',
        'fiji': 'fj',
        'vanuatu': 'vu',
        'new caledonia': 'nc',
        'solomon islands': 'sb',
        'samoa': 'ws',
        'tonga': 'to',
        'tuvalu': 'tv',
        'kiribati': 'ki',
        'marshall islands': 'mh',
        'micronesia': 'fm',
        'palau': 'pw',
        'northern mariana islands': 'mp',
        'guam': 'gu',
        'american samoa': 'as',
        'cook islands': 'ck',
        'niue': 'nu',
        'tokelau': 'tk',
        'pitcairn': 'pn',
        'wallis and futuna': 'wf',
        'french polynesia': 'pf',
        'russia': 'ru',
        'ukraine': 'ua',
        'belarus': 'by',
        'moldova': 'md',
        'latvia': 'lv',
        'lithuania': 'lt',
        'estonia': 'ee',
        'georgia': 'ge',
        'armenia': 'am',
        'azerbaijan': 'az',
        'kazakhstan': 'kz',
        'uzbekistan': 'uz',
        'turkmenistan': 'tm',
        'tajikistan': 'tj',
        'kyrgyzstan': 'kg',
        'mongolia': 'mn',
        'north korea': 'kp',
        'taiwan': 'tw',
        'hong kong': 'hk',
        'macau': 'mo',
        'vatican city': 'va',
        'san marino': 'sm',
        'monaco': 'mc',
        'liechtenstein': 'li',
        'andorra': 'ad',
        'malta': 'mt',
        'cyprus': 'cy',
        'iceland': 'is',
        'faroe islands': 'fo',
        'greenland': 'gl',
        'albania': 'al',
        'macedonia': 'mk',
        'kosovo': 'xk',
        'montenegro': 'me',
        'bosnia and herzegovina': 'ba',
        'croatia': 'hr',
        'slovenia': 'si',
        'slovakia': 'sk',
        'serbia': 'rs',
        'turkey': 'tr',
        'israel': 'il',
        'palestine': 'ps',
    }
    
    @staticmethod
    def get_user_country(user: BaseUser, request: HttpRequest = None) -> str:
        """
        Get user's country using multiple detection methods in order of priority:
        1. User profile country (most accurate)
        2. IP address detection (fallback)
        3. Browser language detection (fallback)
        4. Default to UAE
        """
        # Method 1: Check user profile country
        country = CountryDetectionService._get_country_from_profile(user)
        if country and country != 'country':  # Check if it's not the default value
            return country
        
        # Method 2: IP address detection (if request is available)
        if request:
            country = CountryDetectionService._get_country_from_ip(request)
            if country:
                return country
        
        # Method 3: Browser language detection (if request is available)
        if request:
            country = CountryDetectionService._get_country_from_browser(request)
            if country:
                return country
        
        # Method 4: Default to UAE
        return 'ae'
    
    @staticmethod
    def _get_country_from_profile(user: BaseUser) -> Optional[str]:
        """Get country from user profile"""
        try:
            # Check if user has a talent profile
            if hasattr(user, 'talent_user') and user.talent_user:
                country = user.talent_user.country
                if country and country.lower() != 'country':
                    return CountryDetectionService._normalize_country_code(country)
            
            # Check if user has a background profile
            if hasattr(user, 'background_profile') and user.background_profile:
                country = user.background_profile.country
                if country and country.lower() != 'country':
                    return CountryDetectionService._normalize_country_code(country)
                    
        except Exception as e:
            print(f"Error getting country from profile: {e}")
        
        return None
    
    @staticmethod
    def _get_country_from_ip(request: HttpRequest) -> Optional[str]:
        """Get country from IP address using free ipapi.co service"""
        try:
            # Get client IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            
            if not ip or ip in ['127.0.0.1', 'localhost', '::1']:
                return None
            
            # Use free ipapi.co service
            response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    country_code = data.get('countryCode', '').lower()
                    if country_code:
                        return country_code
                        
        except Exception as e:
            print(f"Error getting country from IP: {e}")
        
        return None
    
    @staticmethod
    def _get_country_from_browser(request: HttpRequest) -> Optional[str]:
        """Get country from browser language settings"""
        try:
            # Get Accept-Language header
            accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
            if accept_language:
                # Parse the first language code
                primary_lang = accept_language.split(',')[0].strip()
                if '-' in primary_lang:
                    country_code = primary_lang.split('-')[1].lower()
                    return country_code
                elif '_' in primary_lang:
                    country_code = primary_lang.split('_')[1].lower()
                    return country_code
                    
        except Exception as e:
            print(f"Error getting country from browser: {e}")
        
        return None
    
    @staticmethod
    def _normalize_country_code(country_name: str) -> str:
        """Convert country name to ISO country code"""
        if not country_name:
            return 'ae'
        
        # Convert to lowercase for comparison
        country_lower = country_name.lower().strip()
        
        # Check if it's already a 2-letter code
        if len(country_lower) == 2 and country_lower.isalpha():
            return country_lower
        
        # Look up in mapping
        return CountryDetectionService.COUNTRY_CODE_MAPPING.get(country_lower, 'ae')
    
    @staticmethod
    def get_country_name_from_code(country_code: str) -> str:
        """Convert country code to full country name"""
        if not country_code:
            return 'United Arab Emirates'
        
        # Create reverse mapping
        reverse_mapping = {v: k.title() for k, v in CountryDetectionService.COUNTRY_CODE_MAPPING.items()}
        
        # Special cases for common countries
        special_names = {
            'ae': 'United Arab Emirates',
            'us': 'United States',
            'gb': 'United Kingdom',
            'uk': 'United Kingdom',
            'cn': 'China',
            'in': 'India',
            'br': 'Brazil',
            'ru': 'Russia',
            'de': 'Germany',
            'fr': 'France',
            'es': 'Spain',
            'it': 'Italy',
            'sa': 'Saudi Arabia',
            'kw': 'Kuwait',
            'qa': 'Qatar',
            'bh': 'Bahrain',
            'om': 'Oman',
        }
        
        return special_names.get(country_code.lower(), reverse_mapping.get(country_code.lower(), 'United Arab Emirates'))
    
    @staticmethod
    def save_country_to_user_profile(user: BaseUser, country_code: str) -> bool:
        """Save full country name to user profile based on country code"""
        try:
            country_name = CountryDetectionService.get_country_name_from_code(country_code)
            
            # Check if country is restricted
            if has_payment_restrictions(country_name):
                print(f"⚠️  Restricted country detected: {country_name}")
                # Create restricted country user entry
                RestrictedCountryUser.create_for_user(user, country_name)
                print(f"Created restricted country entry for user {user.id} from {country_name}")
                return False  # Don't allow payment processing
            
            # Save to talent profile if exists
            if hasattr(user, 'talent_user') and user.talent_user:
                user.talent_user.country = country_name
                user.talent_user.save(update_fields=['country'])
                print(f"Saved country '{country_name}' to talent profile for user {user.id}")
                return True
            
            # Save to background profile if exists
            if hasattr(user, 'background_profile') and user.background_profile:
                user.background_profile.country = country_name
                user.background_profile.save(update_fields=['country'])
                print(f"Saved country '{country_name}' to background profile for user {user.id}")
                return True
                
        except Exception as e:
            print(f"Error saving country to profile: {e}")
        
        return False
    
    @staticmethod
    def is_country_restricted(country_code: str) -> bool:
        """Check if a country code corresponds to a restricted country"""
        country_name = CountryDetectionService.get_country_name_from_code(country_code)
        return has_payment_restrictions(country_name)
    
    @staticmethod
    def get_restricted_countries_list() -> list:
        """Get list of all restricted countries"""
        return RESTRICTED_COUNTRIES
    
    @staticmethod
    def check_user_payment_eligibility(user: BaseUser, country_code: str = None) -> dict:
        """
        Check if user is eligible for payment processing based on their country
        
        Returns:
            dict: {
                'eligible': bool,
                'country': str,
                'restricted': bool,
                'message': str
            }
        """
        try:
            # Get country from parameter or user profile
            if country_code:
                country_name = CountryDetectionService.get_country_name_from_code(country_code)
            else:
                country_name = CountryDetectionService._get_country_from_profile(user)
                if not country_name:
                    country_name = "United Arab Emirates"  # Default
            
            # Check if country is restricted
            is_restricted = has_payment_restrictions(country_name)
            
            if is_restricted:
                return {
                    'eligible': False,
                    'country': country_name,
                    'restricted': True,
                    'message': f'Payment processing is not available for users from {country_name}. Please contact support for assistance.'
                }
            
            return {
                'eligible': True,
                'country': country_name,
                'restricted': False,
                'message': f'Payment processing available for {country_name}'
            }
            
        except Exception as e:
            return {
                'eligible': False,
                'country': 'Unknown',
                'restricted': False,
                'message': f'Error checking payment eligibility: {str(e)}'
            } 