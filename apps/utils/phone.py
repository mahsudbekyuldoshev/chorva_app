import re


def normalize_phone(phone: str) -> str:
    """O'zbekiston telefon raqamini 998XXXXXXXXX (12 raqam) shakliga
    keltiradi. Noma'lum formatlar tozalangan holda qaytariladi."""
    if not phone:
        return ""
    digits = re.sub(r"\D", "", str(phone))
    if digits.startswith("998") and len(digits) == 12:
        return digits
    if len(digits) == 9:
        return "998" + digits
    return digits
