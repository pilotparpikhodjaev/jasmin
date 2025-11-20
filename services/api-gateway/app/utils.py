import math


def calculate_parts(message: str, coding: str = "0") -> int:
    if not message:
        return 1

    is_gsm = coding == "0"
    single = 160 if is_gsm else 70
    multipart = 153 if is_gsm else 67

    if len(message) <= single:
        return 1

    return math.ceil(len(message) / multipart)

