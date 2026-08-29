import random
from django.core.cache import cache

OTP_CODE_LENGTH = 4
OTP_TTL_SECONDS = 120
OTP_RESEND_COOLDOWN_SECONDS = 30

def generate_otp(phone):
    # Check cooldown
    if cache.get(f"otp_cooldown_{phone}"):
        return None, "Please wait before requesting another OTP."
    
    otp = str(random.randint(1000, 9999))
    cache.set(f"otp_{phone}", otp, OTP_TTL_SECONDS)
    cache.set(f"otp_cooldown_{phone}", True, OTP_RESEND_COOLDOWN_SECONDS)
    
    print(f"OTP for {phone}: {otp}")
    return otp, None

def verify_otp(phone, code):
    cached_otp = cache.get(f"otp_{phone}")
    if cached_otp and cached_otp == code:
        cache.delete(f"otp_{phone}")
        return True
    return False
