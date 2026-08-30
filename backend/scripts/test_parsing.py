"""parse_money / parse_quantity uchun tekshiruv.

Ishga tushirish:  docker compose exec api python scripts/test_parsing.py
"""

import pathlib
import sys
from decimal import Decimal

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.bot.utils import parse_money, parse_quantity  # noqa: E402

D = Decimal

MONEY_CASES: list[tuple[str, Decimal | None]] = [
    ("20000", D(20000)),
    ("20,000", D(20000)),
    ("20 000", D(20000)),
    ("20 000", D(20000)),
    ("20.000", D(20000)),
    ("2,000,000", D(2000000)),
    ("1 250 000", D(1250000)),
    ("25000 so'm", D(25000)),
    ("1,250,000.00", D(1250000)),
    ("1 250 000 so'm", D(1250000)),
    ("abc", None),
    ("", None),
    ("-5", None),
    ("0", None),
    ("0.00", None),
]

QTY_CASES: list[tuple[str, Decimal | None]] = [
    ("11", D("11")),
    ("11.5", D("11.5")),
    ("11,5", D("11.5")),
    ("0.5", D("0.5")),
    ("1,25", D("1.25")),
    ("1,500", D("1500")),
    ("12,75", D("12.75")),
    ("1.250,75", D("1250.75")),
    ("abc", None),
    ("", None),
    ("0", None),
    ("-3", None),
]


def _run(name, fn, cases) -> list[str]:
    fails = []
    for raw, want in cases:
        got = fn(raw)
        ok = got == want
        print(f"  {'OK  ' if ok else 'FAIL'} {name}({raw!r}) -> {got!r}")
        if not ok:
            fails.append(f"{name}({raw!r}): kutilgan {want!r}, olindi {got!r}")
    return fails


def main() -> int:
    print("== pul (parse_money) ==")
    fails = _run("money", parse_money, MONEY_CASES)
    print("== miqdor (parse_quantity) ==")
    fails += _run("qty", parse_quantity, QTY_CASES)

    if fails:
        print("\nFAIL:")
        for line in fails:
            print(f"  - {line}")
        return 1
    print("\nHammasi joyida.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
