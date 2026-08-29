"""Telegram Mini App initData imzosini tekshirish (HMAC-SHA256).

Frontenddan kelgan user_id ga ishonilmaydi — faqat shu yerda imzosi
tekshirilgan initData ichidan chiqqan user.id ishlatiladi.
"""

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl


class InvalidInitDataError(Exception):
    """initData buzuq yoki imzo mos kelmadi."""


def validate_init_data(
    init_data: str,
    bot_token: str,
    max_age_seconds: int = 86400,
) -> dict:
    """initData qatorini tekshiradi va ichidagi maydonlarni qaytaradi.

    `user` maydoni JSON dan Python dict ga aylantirilgan holda qaytadi.
    Xato bo'lsa `InvalidInitDataError` ko'tariladi.
    """
    # Bo'sh token bilan ham HMAC hisoblanaveradi — ya'ni istalgan odam
    # bo'sh kalit bilan yaroqli imzo yasay oladi. Shuning uchun to'xtatamiz.
    if not bot_token:
        raise InvalidInitDataError("BOT_TOKEN sozlanmagan")

    if not init_data:
        raise InvalidInitDataError("initData bo'sh")

    try:
        # keep_blank_values=True majburiy: Telegram "start_param=" kabi
        # bo'sh qiymatli maydonlarni ham hashga qo'shadi. Tashlab yuborsak,
        # imzo mos kelmay qoladi va haqiqiy foydalanuvchi 401 oladi.
        pairs = parse_qsl(init_data, strict_parsing=True, keep_blank_values=True)
    except ValueError as exc:
        raise InvalidInitDataError("initData formati buzuq") from exc

    fields = dict(pairs)

    received_hash = fields.pop("hash", None)
    if not received_hash:
        raise InvalidInitDataError("hash maydoni yo'q")

    # Qolgan maydonlar alifbo tartibida "key=value" va "\n" bilan
    data_check_string = "\n".join(
        f"{key}={fields[key]}" for key in sorted(fields)
    )

    secret_key = hmac.new(
        b"WebAppData", bot_token.encode(), hashlib.sha256
    ).digest()
    computed = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    # Oddiy == emas — timing hujumidan himoya
    if not hmac.compare_digest(computed, received_hash):
        raise InvalidInitDataError("imzo mos kelmadi")

    auth_date_raw = fields.get("auth_date")
    if not auth_date_raw:
        raise InvalidInitDataError("auth_date yo'q")
    try:
        auth_date = int(auth_date_raw)
    except ValueError as exc:
        raise InvalidInitDataError("auth_date noto'g'ri") from exc
    if max_age_seconds > 0 and time.time() - auth_date > max_age_seconds:
        raise InvalidInitDataError("initData muddati o'tgan")

    user_raw = fields.get("user")
    if not user_raw:
        raise InvalidInitDataError("user maydoni yo'q")
    try:
        fields["user"] = json.loads(user_raw)
    except json.JSONDecodeError as exc:
        raise InvalidInitDataError("user JSON buzuq") from exc

    return fields