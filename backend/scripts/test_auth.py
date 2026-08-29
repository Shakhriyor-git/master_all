"""Qo'lda autentifikatsiya testi.

Bot tokeni bilan to'g'ri imzolangan soxta initData yasaydi, uni /api/projects
ga yuboradi va 200 olishini tekshiradi. Imzoni buzib 401 kelishini ham.

Ishga tushirish:  docker compose exec api python scripts/test_auth.py
"""

import hashlib
import hmac
import json
import pathlib
import sys
import time
from urllib.parse import urlencode

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402

from app.core.config import settings  # noqa: E402

BASE_URL = "http://localhost:8000"
TEST_USER = {
    "id": 555_000_777,
    "first_name": "Auth",
    "last_name": "Test",
    "username": "auth_test",
    "language_code": "uz",
}


def make_init_data(bot_token: str, user: dict, auth_date: int | None = None) -> str:
    """Telegram Mini App initData qatorini yasaydi (to'g'ri imzo bilan)."""
    fields = {
        "auth_date": str(auth_date or int(time.time())),
        "query_id": "AAH_test_query_id",
        "user": json.dumps(user, separators=(",", ":"), ensure_ascii=False),
    }
    data_check_string = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))
    secret_key = hmac.new(
        b"WebAppData", bot_token.encode(), hashlib.sha256
    ).digest()
    fields["hash"] = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    return urlencode(fields)


def main() -> int:
    token = settings.bot_token
    failures: list[str] = []

    # 1. To'g'ri imzo -> 200
    good = make_init_data(token, TEST_USER)
    r = httpx.get(
        f"{BASE_URL}/api/projects",
        headers={"Authorization": f"tma {good}"},
        timeout=10,
    )
    if r.status_code == 200:
        print(f"OK   to'g'ri imzo -> 200, javob: {r.json()!r}")
    else:
        failures.append(f"to'g'ri imzo -> {r.status_code} ({r.text})")

    # 2. Buzilgan imzo (boshqa token bilan) -> 401
    bad = make_init_data(token + "_buzuq", TEST_USER)
    r = httpx.get(
        f"{BASE_URL}/api/projects",
        headers={"Authorization": f"tma {bad}"},
        timeout=10,
    )
    if r.status_code == 401:
        print("OK   buzilgan imzo -> 401")
    else:
        failures.append(f"buzilgan imzo -> {r.status_code} ({r.text})")

    # 3. Sarlavhasiz -> 401
    r = httpx.get(f"{BASE_URL}/api/projects", timeout=10)
    if r.status_code == 401:
        print("OK   sarlavhasiz -> 401")
    else:
        failures.append(f"sarlavhasiz -> {r.status_code} ({r.text})")

    # 4. Eskirgan auth_date -> 401
    stale = make_init_data(
        token, TEST_USER, auth_date=int(time.time()) - 90_000
    )
    r = httpx.get(
        f"{BASE_URL}/api/projects",
        headers={"Authorization": f"tma {stale}"},
        timeout=10,
    )
    if r.status_code == 401:
        print("OK   eskirgan auth_date -> 401")
    else:
        failures.append(f"eskirgan auth_date -> {r.status_code} ({r.text})")

    if failures:
        print("\nFAIL:")
        for line in failures:
            print(f"  - {line}")
        return 1
    print("\nHammasi joyida.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
