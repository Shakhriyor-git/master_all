"""Mijozga uzatiladigan hisobotlar — to'g'ridan-to'g'ri bazadan, LLM'siz.

Ikkita alohida hujjat:
  * `build_labor_pdf`     — ISH HAQI HISOBOTI (bajarilgan ishlar + hisob-kitob)
  * `build_materials_pdf` — MATERIAL VA XARAJATLAR

`ReportData` ni `report_data.py` yig'adi (API va bot uchun bir xil), bu modul
faqat chizadi. A4, chetlari 18 mm, DejaVu shrifti (o' va g' harflari uchun).
"""

from __future__ import annotations

import io
import os
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import ParagraphStyle

# --------------------------------------------------------------------------
# Shrift
# --------------------------------------------------------------------------
_FONT = "DejaVuSans"
_FONT_BOLD = "DejaVuSans-Bold"
_FONT_DIR = "/usr/share/fonts/truetype/dejavu"
_fonts_ready = False


class FontMissingError(RuntimeError):
    """DejaVu shrifti topilmadi — Helvetica'ga qaytmaymiz (kirill chiqmaydi)."""


def _ensure_fonts() -> None:
    global _fonts_ready
    if _fonts_ready:
        return
    regular = os.path.join(_FONT_DIR, "DejaVuSans.ttf")
    bold = os.path.join(_FONT_DIR, "DejaVuSans-Bold.ttf")
    missing = [p for p in (regular, bold) if not os.path.isfile(p)]
    if missing:
        raise FontMissingError(
            "DejaVu shrifti topilmadi: fonts-dejavu-core o'rnatilmagan. "
            f"Kutilgan fayllar: {', '.join(missing)}. "
            "Kirill/o'zbek harflari (шлакаблок, o', g') uchun zarur — "
            "Helvetica'ga qaytmaymiz."
        )
    pdfmetrics.registerFont(TTFont(_FONT, regular))
    pdfmetrics.registerFont(TTFont(_FONT_BOLD, bold))
    # registerFont yetarli emas: ReportLab qalin/kursiv variantlarni oddiy
    # nom bilan bog'lay olishi uchun oila (family) ham ro'yxatga olinadi.
    pdfmetrics.registerFontFamily(
        _FONT,
        normal=_FONT,
        bold=_FONT_BOLD,
        italic=_FONT,
        boldItalic=_FONT_BOLD,
    )
    _fonts_ready = True


# --------------------------------------------------------------------------
# Ranglar — faqat qora, kulrang, bitta urg'u
# --------------------------------------------------------------------------
_BLACK = colors.HexColor("#1a1a1a")
_GREY = colors.HexColor("#6b7280")
_ROW_ALT = colors.HexColor("#f4f4f5")
_ACCENT = colors.HexColor("#334155")
_RED = colors.HexColor("#b3261e")

_USABLE = A4[0] - 36 * mm  # 210 - 2*18


# --------------------------------------------------------------------------
# Ma'lumot tuzilishi
# --------------------------------------------------------------------------
@dataclass
class WorkRow:
    day: date
    name: str
    category: str
    qty: Decimal
    unit_label: str
    unit_price: Decimal
    amount: Decimal
    is_rework: bool = False
    note: str | None = None


@dataclass
class MaterialRow:
    day: date
    name: str
    qty: Decimal
    unit_label: str
    unit_price: Decimal
    amount: Decimal
    method: str | None = None
    vendor: str | None = None
    note: str | None = None


@dataclass
class ExpenseRow:
    day: date
    name: str
    amount: Decimal
    method: str | None = None
    note: str | None = None


@dataclass
class PaymentRow:
    day: date
    purpose: str  # labor | budget
    method: str
    amount: Decimal


@dataclass
class ReportData:
    project_title: str
    client_name: str | None
    master_name: str
    master_phone: str | None
    generated_at: date
    period_from: date | None = None
    period_to: date | None = None

    works: list[WorkRow] = field(default_factory=list)
    materials_master: list[MaterialRow] = field(default_factory=list)
    materials_client: list[MaterialRow] = field(default_factory=list)
    expenses_master: list[ExpenseRow] = field(default_factory=list)
    expenses_client: list[ExpenseRow] = field(default_factory=list)
    payments: list[PaymentRow] = field(default_factory=list)

    # Butun loyiha bo'yicha (Mini App bilan bir xil raqamlar)
    works_total: Decimal = Decimal(0)
    materials_by_master: Decimal = Decimal(0)
    paid_labor: Decimal = Decimal(0)
    client_owes: Decimal = Decimal(0)
    budget_given: Decimal = Decimal(0)
    budget_spent_materials: Decimal = Decimal(0)
    budget_spent_expenses: Decimal = Decimal(0)
    budget_balance: Decimal = Decimal(0)


_METHOD_UZ = {"cash": "Naqd", "card": "Karta", "transfer": "O'tkazma"}


# --------------------------------------------------------------------------
# Formatlash
# --------------------------------------------------------------------------
def _money(value: object) -> str:
    n = int(Decimal(str(value or 0)).quantize(Decimal("1")))
    return f"{abs(n):,}".replace(",", " ") if n >= 0 else (
        "-" + f"{abs(n):,}".replace(",", " ")
    )


def _money_sum(value: object) -> str:
    return f"{_money(value)} so'm"


def _qty(value: object, unit: str) -> str:
    d = Decimal(str(value or 0))
    s = format(d.normalize(), "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    s = s.replace(".", ",")
    return f"{s} {unit}".strip()


def _dt(value: date | None) -> str:
    return value.strftime("%d.%m.%Y") if value else "—"


def _method(code: str | None) -> str:
    return _METHOD_UZ.get(code or "", "—")


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )


class _Num:
    """Ketma-ket bo'lim raqamlari — 1, 2, 3… (bo'sh bo'limlar sakramaydi)."""

    def __init__(self) -> None:
        self._n = 0

    def __call__(self) -> int:
        self._n += 1
        return self._n


# --------------------------------------------------------------------------
# Stillar
# --------------------------------------------------------------------------
def _styles() -> dict[str, ParagraphStyle]:
    return {
        "title": ParagraphStyle(
            "title", fontName=_FONT_BOLD, fontSize=17, leading=21,
            textColor=_BLACK,
        ),
        "h2": ParagraphStyle(
            "h2", fontName=_FONT_BOLD, fontSize=11, leading=15,
            textColor=_ACCENT, spaceBefore=10, spaceAfter=4,
        ),
        "h3": ParagraphStyle(
            "h3", fontName=_FONT_BOLD, fontSize=9.5, leading=13,
            textColor=_BLACK, spaceBefore=6, spaceAfter=2,
        ),
        "body": ParagraphStyle(
            "body", fontName=_FONT, fontSize=9, leading=12, textColor=_BLACK,
        ),
        "muted": ParagraphStyle(
            "muted", fontName=_FONT, fontSize=8.5, leading=11, textColor=_GREY,
        ),
        "note": ParagraphStyle(
            "note", fontName=_FONT, fontSize=7.5, leading=10, textColor=_GREY,
        ),
    }


def _table(rows: list[list], widths: list[float], *, right: set[int]) -> Table:
    t = Table(rows, colWidths=widths, repeatRows=1)
    style = [
        ("FONTNAME", (0, 0), (-1, -1), _FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TEXTCOLOR", (0, 0), (-1, -1), _BLACK),
        ("FONTNAME", (0, 0), (-1, 0), _FONT_BOLD),
        ("TEXTCOLOR", (0, 0), (-1, 0), _ACCENT),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, _ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ROW_ALT]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    for col in right:
        style.append(("ALIGN", (col, 0), (col, -1), "RIGHT"))
    t.setStyle(TableStyle(style))
    return t


def _subtotal_row(label: str, value: str, ncols: int, value_col: int) -> list:
    row = [""] * ncols
    row[0] = label
    row[value_col] = value
    return row


def _note_style_for(rows: list, extra: list, ncols: int, st: dict) -> None:
    """Oxirgi qo'shilgan qatorni izoh (chekdagi mollar) sifatida bezaydi:
    to'liq kenglik, 8 mm surilgan, kichik kulrang shrift."""
    r = len(rows) - 1
    extra += [
        ("SPAN", (0, r), (-1, r)),
        ("LEFTPADDING", (0, r), (0, r), 8 * mm),
        ("TOPPADDING", (0, r), (-1, r), 0),
        ("BOTTOMPADDING", (0, r), (-1, r), 3),
        ("BACKGROUND", (0, r), (-1, r), colors.white),
    ]


def _reckoning(title: str, lines: list[tuple[str, str]], st: dict,
               *, rule_at: set[int], red_at: set[int] | None = None) -> Table:
    """`lines` — (yozuv, qiymat) juftliklari. `rule_at` — qalin qilinadigan va
    ustidan chiziq tortiladigan qatorlar (0 dan)."""
    red_at = red_at or set()
    # h3 uslubi allaqachon qalin — <b> ichma-ich yozilmaydi
    rows = [[Paragraph(title, st["h3"]), ""]]
    rows += [[a, b] for a, b in lines]
    t = Table(rows, colWidths=[110 * mm, _USABLE - 110 * mm])
    style = [
        ("FONTNAME", (0, 0), (-1, -1), _FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]
    for i in rule_at:
        r = i + 1  # sarlavha qatori uchun +1
        style += [
            ("LINEABOVE", (0, r), (-1, r), 0.6, _BLACK),
            ("FONTNAME", (0, r), (-1, r), _FONT_BOLD),
            ("TOPPADDING", (0, r), (-1, r), 5),
        ]
    for i in red_at:
        style.append(("TEXTCOLOR", (0, i + 1), (-1, i + 1), _RED))
    t.setStyle(TableStyle(style))
    return t


# --------------------------------------------------------------------------
# Sarlavha bloki (ikkala hujjatda bir xil)
# --------------------------------------------------------------------------
def _header(data: ReportData, st: dict, title: str) -> list:
    master = data.master_name
    if data.master_phone:
        master = f"{master} · {data.master_phone}"
    rows = [
        ["Obyekt:", data.project_title],
        ["Mijoz:", data.client_name or "—"],
        ["Usta:", master],
    ]
    # Sana filtri berilmagan bo'lsa "Davr" qatori umuman chiqmaydi
    if data.period_from or data.period_to:
        rows.append(
            ["Davr:", f"{_dt(data.period_from)} — {_dt(data.period_to)}"]
        )
    rows.append(["Sana:", _dt(data.generated_at)])

    t = Table(rows, colWidths=[22 * mm, _USABLE - 22 * mm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), _FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (0, -1), _GREY),
        ("TEXTCOLOR", (1, 0), (1, -1), _BLACK),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return [
        Paragraph(title, st["title"]),
        Spacer(1, 8),
        t,
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=0.6, color=_GREY),
        Spacer(1, 4),
    ]


# --------------------------------------------------------------------------
# ISH HAQI HISOBOTI
# --------------------------------------------------------------------------
def _labor_works(data: ReportData, st: dict, num: _Num) -> list:
    if not data.works:
        return []
    normal = [w for w in data.works if not w.is_rework]
    rework = [w for w in data.works if w.is_rework]

    flow: list = [Paragraph(f"{num()}. Bajarilgan ishlar", st["h2"])]
    widths = [20 * mm, 68 * mm, 24 * mm, 30 * mm, 32 * mm]
    total = Decimal(0)

    by_cat: dict[str, list[WorkRow]] = {}
    for w in normal:
        by_cat.setdefault(w.category or "Kategoriyasiz", []).append(w)

    for cat in sorted(by_cat):
        rows: list[list] = [
            ["Sana", "Ish nomi", "Miqdor", "Birlik narxi", "Summa"]
        ]
        extra: list = []
        sub = Decimal(0)
        for w in sorted(by_cat[cat], key=lambda r: r.day):
            rows.append([
                _dt(w.day), w.name, _qty(w.qty, w.unit_label),
                _money(w.unit_price), _money(w.amount),
            ])
            if w.note:
                rows.append([Paragraph(_esc(w.note), st["note"]), "", "", "", ""])
                _note_style_for(rows, extra, 5, st)
            sub += w.amount
            total += w.amount
        rows.append(_subtotal_row(f"{cat} — oraliq jami", _money(sub), 5, 4))
        t = _table(rows, widths, right={2, 3, 4})
        t.setStyle(TableStyle([
            ("FONTNAME", (0, -1), (-1, -1), _FONT_BOLD),
            ("LINEABOVE", (0, -1), (-1, -1), 0.4, _GREY),
            *extra,
        ]))
        flow += [Paragraph(cat, st["h3"]), t, Spacer(1, 4)]

    if rework:
        rrows: list[list] = [
            ["Sana", "Ish nomi", "Miqdor", "Birlik narxi", "Summa"]
        ]
        rextra: list = []
        for w in sorted(rework, key=lambda r: r.day):
            rrows.append([
                _dt(w.day),
                f"{w.name}  (brak — hisobga kirmadi)",
                _qty(w.qty, w.unit_label),
                _money(w.unit_price), _money(w.amount),
            ])
            if w.note:
                rrows.append(
                    [Paragraph(_esc(w.note), st["note"]), "", "", "", ""]
                )
                _note_style_for(rrows, rextra, 5, st)
        rt = _table(rrows, widths, right={2, 3, 4})
        rt.setStyle(TableStyle([
            ("TEXTCOLOR", (0, 1), (-1, -1), _GREY),
            *rextra,
        ]))
        flow += [Paragraph("Brak yozuvlari", st["h3"]), rt, Spacer(1, 4)]

    flow.append(Paragraph(
        f"<b>Ishlar jami: {_money_sum(total)}</b>", st["body"]
    ))
    return flow


def _labor_reckoning(data: ReportData, st: dict, num: _Num) -> list:
    works = data.works_total
    paid = data.paid_labor
    left = works - paid
    left_label = "QOLDIQ" if left >= 0 else "MIJOZ AVANSI"
    return [
        _reckoning(
            f"{num()}. Hisob-kitob",
            [
                ("Bajarilgan ishlar", _money(works)),
                ("Mijoz to'lagan", f"− {_money(paid)}"),
                (left_label, _money_sum(abs(left))),
            ],
            st,
            rule_at={2},
        )
    ]


def _labor_story(data: ReportData, st: dict) -> list:
    _ensure_fonts()  # Paragraph qurishdan oldin — family xaritasi kerak
    flow = _header(data, st, "ISH HAQI HISOBOTI")
    num = _Num()
    works_part = _labor_works(data, st, num)
    if not works_part and data.works_total == 0 and data.paid_labor == 0:
        flow.append(Paragraph(
            "Bu obyekt bo'yicha bu davrda ish yozuvi yo'q.", st["body"]
        ))
        return flow
    if works_part:
        flow += works_part
        flow.append(Spacer(1, 8))
    flow += _labor_reckoning(data, st, num)
    return flow


# --------------------------------------------------------------------------
# MATERIAL VA XARAJATLAR
# --------------------------------------------------------------------------
def _material_name(m: MaterialRow) -> str:
    return f"{m.name} ({m.vendor})" if m.vendor else m.name


def _mat_materials(data: ReportData, st: dict, num: _Num) -> list:
    if not data.materials_master:
        return []
    widths = [18 * mm, 46 * mm, 22 * mm, 28 * mm, 30 * mm, 30 * mm]
    rows: list[list] = [
        ["Sana", "Nomi (sotuvchi)", "Miqdor", "Narxi", "Summa", "Usul"]
    ]
    extra: list = []
    sub = Decimal(0)
    for m in sorted(data.materials_master, key=lambda r: r.day):
        rows.append([
            _dt(m.day), _material_name(m), _qty(m.qty, m.unit_label),
            _money(m.unit_price), _money(m.amount), _method(m.method),
        ])
        if m.note:
            rows.append(
                [Paragraph(_esc(m.note), st["note"]), "", "", "", "", ""]
            )
            _note_style_for(rows, extra, 6, st)
        sub += m.amount
    rows.append(_subtotal_row("Oraliq jami", _money_sum(sub), 6, 4))
    t = _table(rows, widths, right={2, 3, 4})
    t.setStyle(TableStyle([
        ("FONTNAME", (0, -1), (-1, -1), _FONT_BOLD),
        ("LINEABOVE", (0, -1), (-1, -1), 0.4, _GREY),
        *extra,
    ]))
    return [Paragraph(f"{num()}. Materiallar", st["h2"]), t]


def _mat_expenses(data: ReportData, st: dict, num: _Num) -> list:
    # Bo'sh bo'lsa bo'lim umuman chiqmaydi
    if not data.expenses_master:
        return []
    widths = [24 * mm, 84 * mm, 36 * mm, 30 * mm]
    rows: list[list] = [["Sana", "Nomi", "Summa", "To'lov usuli"]]
    extra: list = []
    sub = Decimal(0)
    for e in sorted(data.expenses_master, key=lambda r: r.day):
        rows.append([_dt(e.day), e.name, _money(e.amount), _method(e.method)])
        if e.note:
            rows.append([Paragraph(_esc(e.note), st["note"]), "", "", ""])
            _note_style_for(rows, extra, 4, st)
        sub += e.amount
    rows.append(_subtotal_row("Oraliq jami", _money_sum(sub), 4, 2))
    t = _table(rows, widths, right={2})
    t.setStyle(TableStyle([
        ("FONTNAME", (0, -1), (-1, -1), _FONT_BOLD),
        ("LINEABOVE", (0, -1), (-1, -1), 0.4, _GREY),
        *extra,
    ]))
    return [Paragraph(f"{num()}. Xarajatlar", st["h2"]), t]


def _mat_reckoning(data: ReportData, st: dict, num: _Num) -> list:
    mat_sum = sum((m.amount for m in data.materials_master), Decimal(0))
    exp_sum = sum((e.amount for e in data.expenses_master), Decimal(0))
    total = mat_sum + exp_sum
    given = data.budget_given
    left = total - given
    left_label = "QOLDIQ" if left >= 0 else "MIJOZ AVANSI"

    lines: list[tuple[str, str]] = [("Materiallar", _money(mat_sum))]
    if data.expenses_master:
        lines.append(("Xarajatlar", f"+ {_money(exp_sum)}"))
    jami_idx = len(lines)
    lines.append(("JAMI", _money(total)))
    lines.append(("Mijoz bergan", f"− {_money(given)}"))
    left_idx = len(lines)
    lines.append((left_label, _money_sum(abs(left))))
    return [
        _reckoning(
            f"{num()}. Hisob-kitob", lines, st,
            rule_at={jami_idx, left_idx},
        )
    ]


def _mat_client_info(data: ReportData, st: dict, num: _Num) -> list:
    if not data.materials_client and not data.expenses_client:
        return []
    widths = [22 * mm, 90 * mm, 32 * mm, 30 * mm]
    rows: list[list] = [["Sana", "Nomi", "Miqdor", "Summa"]]
    sub = Decimal(0)
    for m in sorted(data.materials_client, key=lambda r: r.day):
        rows.append([
            _dt(m.day), _material_name(m), _qty(m.qty, m.unit_label),
            _money(m.amount),
        ])
        sub += m.amount
    for e in sorted(data.expenses_client, key=lambda r: r.day):
        rows.append([_dt(e.day), e.name, "—", _money(e.amount)])
        sub += e.amount
    rows.append(_subtotal_row("Jami", _money_sum(sub), 4, 3))
    t = _table(rows, widths, right={3})
    t.setStyle(TableStyle([
        ("FONTNAME", (0, -1), (-1, -1), _FONT_BOLD),
        ("LINEABOVE", (0, -1), (-1, -1), 0.4, _GREY),
    ]))
    return [
        Paragraph(f"{num()}. Mijoz o'zi olgan", st["h2"]),
        Paragraph(
            "Faqat ma'lumot uchun — yuqoridagi JAMI ga kirmaydi.", st["muted"]
        ),
        Spacer(1, 3),
        t,
    ]


def _materials_story(data: ReportData, st: dict) -> list:
    _ensure_fonts()  # Paragraph qurishdan oldin — family xaritasi kerak
    flow = _header(data, st, "MATERIAL VA XARAJATLAR")
    num = _Num()
    empty = (
        not data.materials_master
        and not data.expenses_master
        and not data.materials_client
        and not data.expenses_client
        and data.budget_given == 0
    )
    if empty:
        flow.append(Paragraph(
            "Bu obyekt bo'yicha bu davrda material yoki xarajat yo'q.",
            st["body"],
        ))
        return flow
    for section in (_mat_materials, _mat_expenses):
        part = section(data, st, num)
        if part:
            flow += part
            flow.append(Spacer(1, 6))
    flow += _mat_reckoning(data, st, num)
    info = _mat_client_info(data, st, num)
    if info:
        flow.append(Spacer(1, 10))
        flow += info
    return flow


# --------------------------------------------------------------------------
# Kolontitul
# --------------------------------------------------------------------------
class _NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, page_sink: list | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._pages: list[dict] = []
        self._sink = page_sink

    def showPage(self) -> None:
        self._pages.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        total = len(self._pages)
        if self._sink is not None:
            self._sink.append(total)
        for state in self._pages:
            self.__dict__.update(state)
            self._footer(total)
            super().showPage()
        super().save()

    def _footer(self, total: int) -> None:
        self.setFont(_FONT, 7)
        self.setFillColor(_GREY)
        self.drawCentredString(
            A4[0] / 2, 10 * mm,
            f"Masters Pro · sahifa {self._pageNumber} / {total}",
        )


# --------------------------------------------------------------------------
# Render
# --------------------------------------------------------------------------
def _render(flow: list, title: str, sink: list | None = None) -> bytes:
    _ensure_fonts()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title=title, author="Masters Pro",
    )
    doc.build(
        flow,
        canvasmaker=lambda *a, **k: _NumberedCanvas(*a, page_sink=sink, **k),
    )
    return buf.getvalue()


def build_labor_pdf(data: ReportData) -> bytes:
    """ISH HAQI HISOBOTI — bayt ko'rinishida."""
    return _render(_labor_story(data, _styles()), "Ish haqi hisoboti")


def build_materials_pdf(data: ReportData) -> bytes:
    """MATERIAL VA XARAJATLAR — bayt ko'rinishida."""
    return _render(_materials_story(data, _styles()), "Material va xarajatlar")


def build_labor_pdf_with_pages(data: ReportData) -> tuple[bytes, int]:
    sink: list[int] = []
    pdf = _render(_labor_story(data, _styles()), "Ish haqi hisoboti", sink)
    return pdf, (sink[-1] if sink else 0)


def build_materials_pdf_with_pages(data: ReportData) -> tuple[bytes, int]:
    sink: list[int] = []
    pdf = _render(
        _materials_story(data, _styles()), "Material va xarajatlar", sink
    )
    return pdf, (sink[-1] if sink else 0)
