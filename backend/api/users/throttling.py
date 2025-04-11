from rest_framework.throttling import SimpleRateThrottle

class PhoneNumberRateThrottle(SimpleRateThrottle):
    """
    Throttle class to limit verification code requests per phone number.
    
    Limits the rate at which verification codes can be sent to a single 
    phone number to prevent abuse.
    """
    scope = 'phone_verification'
    
    # Set rate to 5 requests per minute
    rate = '5/min'
    
    def get_cache_key(self, request, view):
        """
        Generate a unique cache key based on the phone number in the request.
        
        If no phone number is provided, fall back to the user's IP.
        """
        phone_number = request.data.get('phone_number', None)
        if phone_number:
            return self.cache_format % {
                'scope': self.scope,
                'ident': phone_number
            }
        else:
            # Fall back to IP if no phone number is provided
            return self.get_ident(request)