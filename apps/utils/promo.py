import random
import string

from apps.models import PromoCode


def generate_promo_code(length=8):
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choices(chars, k=length))
        if not PromoCode.objects.filter(code=code).exists():
            return code
