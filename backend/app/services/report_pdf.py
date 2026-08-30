"""Hisob-kitob PDF — to'g'ridan-to'g'ri bazadan, LLM'siz.

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


def _ensure_fonts() -> None:
    global _fonts_ready
    if _fonts_ready:
        return
    regular = os.path.join(_FONT_DIR, "DejaVuSans.ttf")
    bold = os.path.join(_FONT_DIR, "DejaVuSans-Bold.ttf")
    pdfmetrics.registerFont(TTFont(_FONT, regular))
    pdfmetrics.registerFont(TTFont(_FONT_BOLD, bold))
    pdfmetrics.registerFontFamily(
        _FONT, normal=_FONT, bold=_FONT_BOLD, italic=_FONT, boldItalic=_FONT_BOLD
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


@dataclass
class MaterialRow:
    day: date
    name: str
    qty: Decimal
    unit_label: str
    unit_price: Decimal
    amount: Decimal
    method: str | None = None


@dataclass
class ExpenseRow:
    day: date
    name: str
    amount: Decimal
    method: str | None = None


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
    expenses_client: list[ExpenseRow] = field(default_factory=list)
    payments: list[PaymentRow] = field(default_factory=list)

    # Bo'lim 5 — butun loyiha (Mini App bilan bir xil raqamlar)
    works_total: Decimal = Decimal(0)
    materials_by_master: Decimal = Decimal(0)
    paid_labor: Decimal = Decimal(0)
    client_owes: Decimal = Decimal(0)
    budget_given: Decimal = Decimal(0)
    budget_spent_materials: Decimal = Decimal(0)
    budget_spent_expenses: Decimal = Decimal(0)
    budget_balance: Decimal = Decimal(0)

    @property
    def is_empty(self) -> bool:
        return not (
            self.works
            or self.materials_master
            or self.materials_client
            or self.expenses_client
            or self.payments
        )


_METHOD_UZ = {"cash": "Naqd", "card": "Karta", "transfer": "O'tkazma"}
_PURPOSE_UZ = {"labor": "Ish haqi uchun", "budget": "Xarajat uchun"}


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


# --------------------------------------------------------------------------
# Bo'limlar
# --------------------------------------------------------------------------
def _section_works(data: ReportData, st: dict) -> list:
    if not data.works:
        return []
    normal = [w for w in data.works if not w.is_rework]
    rework = [w for w in data.works if w.is_rework]

    flow: list = [Paragraph("1. Bajarilgan ishlar", st["h2"])]
    widths = [20 * mm, 68 * mm, 24 * mm, 30 * mm, 32 * mm]
    total = Decimal(0)

    by_cat: dict[str, list[WorkRow]] = {}
    for w in normal:
        by_cat.setdefault(w.category or "Kategoriyasiz", []).append(w)

    for cat in sorted(by_cat):
        rows: list[list] = [
            ["Sana", "Ish nomi", "Miqdor", "Birlik narxi", "Summa"]
        ]
        sub = Decimal(0)
        for w in sorted(by_cat[cat], key=lambda r: r.day):
            rows.append([
                _dt(w.day), w.name, _qty(w.qty, w.unit_label),
                _money(w.unit_price), _money(w.amount),
            ])
            sub += w.amount
            total += w.amount
        rows.append(_subtotal_row(f"{cat} — oraliq jami", _money(sub), 5, 4))
        t = _table(rows, widths, right={2, 3, 4})
        t.setStyle(TableStyle([
            ("FONTNAME", (0, -1), (-1, -1), _FONT_BOLD),
            ("LINEABOVE", (0, -1), (-1, -1), 0.4, _GREY),
        ]))
        flow += [Paragraph(cat, st["h3"]), t, Spacer(1, 4)]

    if rework:
        rrows: list[list] = [
            ["Sana", "Ish nomi", "Miqdor", "Birlik narxi", "Summa"]
        ]
        for w in sorted(rework, key=lambda r: r.day):
            rrows.append([
                _dt(w.day),
                f"{w.name}  (brak — hisobga kirmadi)",
                _qty(w.qty, w.unit_label),
                _money(w.unit_price), _money(w.amount),
            ])
        rt = _table(rrows, widths, right={2, 3, 4})
        rt.setStyle(TableStyle([
            ("TEXTCOLOR", (0, 1), (-1, -1), _GREY),
        ]))
        flow += [Paragraph("Brak yozuvlari", st["h3"]), rt, Spacer(1, 4)]

    flow.append(Paragraph(
        f"<b>Ishlar jami: {_money_sum(total)}</b>", st["body"]
    ))
    return flow


def _material_table(rows_src: list[MaterialRow], st: dict) -> list:
    widths = [18 * mm, 46 * mm, 22 * mm, 28 * mm, 30 * mm, 30 * mm]
    rows: list[list] = [
        ["Sana", "Nomi", "Miqdor", "Birlik narxi", "Summa", "To'lov usuli"]
    ]
    sub = Decimal(0)
    for m in sorted(rows_src, key=lambda r: r.day):
        rows.append([
            _dt(m.day), m.name, _qty(m.qty, m.unit_label),
            _money(m.unit_price), _money(m.amount), _method(m.method),
        ])
        sub += m.amount
    rows.append(_subtotal_row("Oraliq jami", _money_sum(sub), 6, 4))
    t = _table(rows, widths, right={2, 3, 4})
    t.setStyle(TableStyle([
        ("FONTNAME", (0, -1), (-1, -1), _FONT_BOLD),
        ("LINEABOVE", (0, -1), (-1, -1), 0.4, _GREY),
    ]))
    return [t, Spacer(1, 4)]


def _section_materials(data: ReportData, st: dict) -> list:
    if not data.materials_master and not data.materials_client:
        return []
    flow: list = [Paragraph("2. Materiallar", st["h2"])]
    if data.materials_master:
        flow.append(Paragraph(
            "2.1. Usta hisobidan — mijozga hisoblanadi", st["h3"]
        ))
        flow += _material_table(data.materials_master, st)
    if data.materials_client:
        flow.append(Paragraph(
            "2.2. Mijoz hisobidan — mijoz budjetidan chiqdi", st["h3"]
        ))
        flow += _material_table(data.materials_client, st)
    return flow


def _section_expenses(data: ReportData, st: dict) -> list:
    if not data.expenses_client:
        return []
    widths = [24 * mm, 84 * mm, 36 * mm, 30 * mm]
    rows: list[list] = [["Sana", "Nomi", "Summa", "To'lov usuli"]]
    sub = Decimal(0)
    for e in sorted(data.expenses_client, key=lambda r: r.day):
        rows.append([_dt(e.day), e.name, _money(e.amount), _method(e.method)])
        sub += e.amount
    rows.append(_subtotal_row("Oraliq jami", _money_sum(sub), 4, 2))
    t = _table(rows, widths, right={2})
    t.setStyle(TableStyle([
        ("FONTNAME", (0, -1), (-1, -1), _FONT_BOLD),
        ("LINEABOVE", (0, -1), (-1, -1), 0.4, _GREY),
    ]))
    return [Paragraph("3. Xarajatlar (mijoz hisobidan)", st["h2"]), t]


def _section_payments(data: ReportData, st: dict) -> list:
    if not data.payments:
        return []
    widths = [28 * mm, 62 * mm, 42 * mm, 42 * mm]
    rows: list[list] = [["Sana", "Maqsad", "Usul", "Summa"]]
    total = Decimal(0)
    for p in sorted(data.payments, key=lambda r: r.day):
        rows.append([
            _dt(p.day), _PURPOSE_UZ.get(p.purpose, p.purpose),
            _method(p.method), _money(p.amount),
        ])
        total += p.amount
    rows.append(_subtotal_row("Jami", _money_sum(total), 4, 3))
    t = _table(rows, widths, right={3})
    t.setStyle(TableStyle([
        ("FONTNAME", (0, -1), (-1, -1), _FONT_BOLD),
        ("LINEABOVE", (0, -1), (-1, -1), 0.4, _GREY),
    ]))
    return [Paragraph("4. Mijoz to'lovlari", st["h2"]), t]


def _reckoning_block(title: str, lines: list[tuple[str, str]], st: dict,
                     *, last_red: bool = False) -> Table:
    rows = [[Paragraph(f"<b>{title}</b>", st["h3"]), ""]]
    rows += [[a, b] for a, b in lines]
    t = Table(rows, colWidths=[110 * mm, _USABLE - 110 * mm])
    style = [
        ("FONTNAME", (0, 0), (-1, -1), _FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LINEABOVE", (0, -1), (-1, -1), 0.6, _BLACK),
        ("FONTNAME", (0, -1), (-1, -1), _FONT_BOLD),
        ("TOPPADDING", (0, -1), (-1, -1), 5),
    ]
    if last_red:
        style.append(("TEXTCOLOR", (0, -1), (-1, -1), _RED))
    t.setStyle(TableStyle(style))
    return t


def _section_final(data: ReportData, st: dict) -> list:
    owes = data.client_owes
    if owes >= 0:
        owes_line = ("MIJOZ QARZI", _money_sum(owes))
    else:
        owes_line = ("MIJOZ AVANSI", _money_sum(-owes))
    labor = _reckoning_block(
        "1. ISH HAQI HISOBI",
        [
            ("Bajarilgan ishlar", _money(data.works_total)),
            ("Usta to'lagan material", f"+ {_money(data.materials_by_master)}"),
            ("Mijoz to'lagan ish haqi", f"− {_money(data.paid_labor)}"),
            owes_line,
        ],
        st,
    )

    bal = data.budget_balance
    if bal >= 0:
        bal_line = ("BUDJET QOLDIG'I", _money_sum(bal))
    else:
        bal_line = ("BUDJETDAN OSHDI", _money_sum(-bal))
    budget = _reckoning_block(
        "2. MIJOZ BUDJETI",
        [
            ("Mijoz bergan", _money(data.budget_given)),
            ("Material (mijoz hisobidan)",
             f"− {_money(data.budget_spent_materials)}"),
            ("Xarajatlar", f"− {_money(data.budget_spent_expenses)}"),
            bal_line,
        ],
        st,
        last_red=bal < 0,
    )
    return [
        Paragraph("5. Yakuniy hisob", st["h2"]),
        labor,
        Spacer(1, 8),
        budget,
    ]


def _header(data: ReportData, st: dict) -> list:
    period = "butun davr"
    if data.period_from or data.period_to:
        period = f"{_dt(data.period_from)} — {_dt(data.period_to)}"
    master = data.master_name
    if data.master_phone:
        master = f"{master} · {data.master_phone}"
    rows = [
        ["Obyekt:", data.project_title],
        ["Mijoz:", data.client_name or "—"],
        ["Usta:", master],
        ["Davr:", period],
        ["Sana:", _dt(data.generated_at)],
    ]
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
        Paragraph("HISOB-KITOB", st["title"]),
        Spacer(1, 8),
        t,
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=0.6, color=_GREY),
        Spacer(1, 4),
    ]


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
# Umumiy
# --------------------------------------------------------------------------
def _story(data: ReportData, st: dict) -> list:
    flow = _header(data, st)
    if data.is_empty:
        flow.append(Paragraph(
            "Bu obyekt bo'yicha bu davrda hali yozuv yo'q.", st["body"]
        ))
        return flow
    for section in (
        _section_works, _section_materials, _section_expenses,
        _section_payments,
    ):
        part = section(data, st)
        if part:
            flow += part
            flow.append(Spacer(1, 6))
    flow += _section_final(data, st)
    return flow


def _render(data: ReportData, sink: list | None = None) -> bytes:
    _ensure_fonts()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title="Hisob-kitob", author="Masters Pro",
    )
    doc.build(
        _story(data, _styles()),
        canvasmaker=lambda *a, **k: _NumberedCanvas(*a, page_sink=sink, **k),
    )
    return buf.getvalue()


def build_report_pdf(data: ReportData) -> bytes:
    """Hisob-kitob PDF'ini bayt ko'rinishida qaytaradi."""
    return _render(data)


def build_report_pdf_with_pages(data: ReportData) -> tuple[bytes, int]:
    """PDF + sahifalar soni (test uchun)."""
    sink: list[int] = []
    pdf = _render(data, sink)
    return pdf, (sink[-1] if sink else 0)
