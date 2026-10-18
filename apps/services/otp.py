import random

from django.core.cache import cache

from apps.utils.phone import normalize_phone

OTP_CODE_LENGTH = 4
OTP_TTL_SECONDS = 120
OTP_RESEND_COOLDOWN_SECONDS = 30

def generate_otp(phone):
    norm_phone = normalize_phone(phone)
    # Check cooldown
    if cache.get(f"otp_cooldown_{norm_phone}"):
        return None, "Please wait before requesting another OTP."
    
    otp = str(random.randint(1000, 9999))
    cache.set(f"otp_{norm_phone}", otp, OTP_TTL_SECONDS)
    cache.set(f"otp_cooldown_{norm_phone}", True, OTP_RESEND_COOLDOWN_SECONDS)
    
    print(f"OTP for {norm_phone}: {otp}")
    return otp, None

def verify_otp(phone, code):
    norm_phone = normalize_phone(phone)
    cached_otp = cache.get(f"otp_{norm_phone}")
    if cached_otp and cached_otp == code:
        cache.delete(f"otp_{norm_phone}")
        return True
    return False
