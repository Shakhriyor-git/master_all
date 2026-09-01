"""Yozuv endpointlari — ishlar, materiallar, xarajatlar."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DbSession, OwnedProject
from app.models import (
    Category,
    Entry,
    MeasureUnit,
    PriceItem,
    Project,
    ProjectPrice,
    User,
)
from app.models.enums import EntryKind, PaidBy
from app.schemas.entry import (
    EntryCreate,
    EntryDetailRead,
    EntryPage,
    EntryRead,
    EntryUpdate,
)

router = APIRouter(prefix="/api", tags=["entries"])

_PAGE_SIZE = 20
_UNDO_WINDOW = timedelta(minutes=5)


async def _owned_entry(entry_id: int, user: User, db: AsyncSession) -> Entry:
    entry = (
        await db.execute(
            select(Entry)
            .join(Project, Project.id == Entry.project_id)
            .where(
                Entry.id == entry_id,
                Entry.deleted_at.is_(None),
                Project.user_id == user.id,
                Project.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Yozuv topilmadi"
        )
    return entry


async def _ensure_project_price(
    db: AsyncSession,
    project: Project,
    user_id: int,
    price_item_id: int,
    fallback_price: Decimal | None,
) -> int:
    """Katalog pozitsiyasi uchun loyiha narxini topadi yoki yaratadi."""
    item = (
        await db.execute(
            select(PriceItem).where(
                PriceItem.id == price_item_id,
                PriceItem.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Katalog pozitsiyasi topilmadi",
        )
    existing = (
        await db.execute(
            select(ProjectPrice).where(
                ProjectPrice.project_id == project.id,
                ProjectPrice.price_item_id == item.id,
                ProjectPrice.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing.id

    price = item.default_price
    if price <= 0 and fallback_price is not None and fallback_price > 0:
        price = fallback_price
    pp = ProjectPrice(
        project_id=project.id,
        price_item_id=item.id,
        name=item.name,
        kind=item.kind,
        unit=item.unit,
        price=price,
    )
    db.add(pp)
    await db.flush()
    return pp.id


def _detail(entry: Entry, cat_name: str | None, unit_label: str | None) -> EntryDetailRead:
    row = EntryDetailRead.model_validate(entry)
    row.category_name = cat_name
    row.unit_label = unit_label
    row.has_receipt = entry.receipt_file_id is not None
    return row


@router.get(
    "/projects/{project_id}/entries", response_model=EntryPage
)
async def list_entries(
    project: OwnedProject,
    db: DbSession,
    kind: EntryKind | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    paid_by: PaidBy | None = None,
    page: int = Query(default=1, ge=1),
):
    base = (
        select(Entry, Category.name, MeasureUnit.label)
        .outerjoin(ProjectPrice, ProjectPrice.id == Entry.project_price_id)
        .outerjoin(PriceItem, PriceItem.id == ProjectPrice.price_item_id)
        .outerjoin(Category, Category.id == PriceItem.category_id)
        .outerjoin(
            MeasureUnit,
            (MeasureUnit.user_id == project.user_id)
            & (MeasureUnit.code == Entry.unit),
        )
        .where(
            Entry.project_id == project.id,
            Entry.deleted_at.is_(None),
        )
    )
    if kind is not None:
        base = base.where(Entry.kind == kind)
    if date_from is not None:
        base = base.where(Entry.entry_date >= date_from)
    if date_to is not None:
        base = base.where(Entry.entry_date <= date_to)
    if paid_by is not None:
        base = base.where(Entry.paid_by == paid_by)

    total = (
        await db.execute(
            select(func.count()).select_from(base.order_by(None).subquery())
        )
    ).scalar_one()
    pages = max(1, (total + _PAGE_SIZE - 1) // _PAGE_SIZE)
    page = min(page, pages)

    rows = (
        await db.execute(
            base.order_by(Entry.entry_date.desc(), Entry.id.desc())
            .offset((page - 1) * _PAGE_SIZE)
            .limit(_PAGE_SIZE)
        )
    ).all()

    return EntryPage(
        items=[_detail(e, c, u) for e, c, u in rows],
        page=page,
        pages=pages,
        total=total,
    )


@router.post(
    "/projects/{project_id}/entries",
    response_model=EntryRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_entry(
    project: OwnedProject,
    payload: EntryCreate,
    user: CurrentUser,
    db: DbSession,
):
    project_price_id = payload.project_price_id

    # Mini App: katalog pozitsiyasi bo'yicha — kerak bo'lsa project_price yaratiladi
    if project_price_id is None and payload.price_item_id is not None:
        project_price_id = await _ensure_project_price(
            db, project, user.id, payload.price_item_id, payload.unit_price
        )

    if project_price_id is not None:
        pp = (
            await db.execute(
                select(ProjectPrice).where(ProjectPrice.id == project_price_id)
            )
        ).scalar_one_or_none()
        if pp is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loyiha narxi topilmadi",
            )
        if pp.project_id != project.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu narx boshqa loyihaga tegishli",
            )
        kind, name, unit, unit_price = pp.kind, pp.name, pp.unit, pp.price
        quantity = payload.quantity
    elif payload.kind == EntryKind.EXPENSE:
        # xarajat: quantity=1, unit='summa', unit_price = summa
        if payload.name is None or payload.unit_price is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Xarajat uchun nom va summa majburiy",
            )
        kind, name, unit = EntryKind.EXPENSE.value, payload.name, "summa"
        unit_price, quantity = payload.unit_price, Decimal("1")
    else:
        missing = [
            field
            for field in ("kind", "name", "unit", "unit_price")
            if getattr(payload, field) is None
        ]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Qo'lda yozuv uchun majburiy: {', '.join(missing)}",
            )
        kind, name = payload.kind, payload.name
        unit, unit_price = payload.unit, payload.unit_price
        quantity = payload.quantity

    entry = Entry(
        project_id=project.id,
        project_price_id=project_price_id,
        created_by_user_id=user.id,
        kind=kind,
        name=name,
        unit=unit,
        quantity=quantity,
        unit_price=unit_price,
        # aniq jami summa berilsa — o'shani saqlaymiz (yaxlatish drift'isiz),
        # aks holda listener quantity * unit_price ni yozadi
        amount=payload.amount,
        paid_by=payload.paid_by,
        is_rework=payload.is_rework,
        payment_method=payload.payment_method,
        vendor=payload.vendor,
        source=payload.source,
        note=payload.note,
        receipt_file_id=payload.receipt_file_id,
    )
    if payload.entry_date is not None:
        entry.entry_date = payload.entry_date

    db.add(entry)
    # model listener + DB CHECK pul qoidalarini majburlaydi
    await db.commit()
    await db.refresh(entry)
    return entry


@router.delete(
    "/projects/{project_id}/entries/last", response_model=EntryRead
)
async def delete_last_entry(project: OwnedProject, db: DbSession):
    """Oxirgi yozuvni bekor qiladi (soft delete). 5 daqiqadan eski bo'lsa 400."""
    entry = (
        await db.execute(
            select(Entry)
            .where(
                Entry.project_id == project.id,
                Entry.deleted_at.is_(None),
            )
            .order_by(Entry.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bekor qilinadigan yozuv yo'q",
        )
    if datetime.now(UTC) - entry.created_at > _UNDO_WINDOW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yozuv 5 daqiqadan eski — endi bekor qilib bo'lmaydi",
        )
    entry.deleted_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.get("/entries/{entry_id}", response_model=EntryDetailRead)
async def get_entry(entry_id: int, user: CurrentUser, db: DbSession):
    """Bitta yozuv — batafsil oyna uchun (JOIN bilan)."""
    row = (
        await db.execute(
            select(Entry, Category.name, MeasureUnit.label)
            .join(Project, Project.id == Entry.project_id)
            .outerjoin(ProjectPrice, ProjectPrice.id == Entry.project_price_id)
            .outerjoin(PriceItem, PriceItem.id == ProjectPrice.price_item_id)
            .outerjoin(Category, Category.id == PriceItem.category_id)
            .outerjoin(
                MeasureUnit,
                (MeasureUnit.user_id == user.id)
                & (MeasureUnit.code == Entry.unit),
            )
            .where(
                Entry.id == entry_id,
                Entry.deleted_at.is_(None),
                Project.user_id == user.id,
                Project.deleted_at.is_(None),
            )
        )
    ).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Yozuv topilmadi"
        )
    entry, cat_name, unit_label = row
    return _detail(entry, cat_name, unit_label)


@router.patch("/entries/{entry_id}", response_model=EntryRead)
async def update_entry(
    entry_id: int, payload: EntryUpdate, user: CurrentUser, db: DbSession
):
    entry = await _owned_entry(entry_id, user, db)
    fields = payload.model_dump(exclude_unset=True)
    for field, value in fields.items():
        setattr(entry, field, value)
    # amount aniq berilmagan bo'lsa, lekin miqdor yoki narx o'zgargan bo'lsa —
    # qayta hisoblaymiz
    if "amount" not in fields and ("quantity" in fields or "unit_price" in fields):
        entry.amount = (
            Decimal(entry.quantity) * Decimal(entry.unit_price)
        ).quantize(Decimal("0.01"))
    await db.commit()
    await db.refresh(entry)
    return entry


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(entry_id: int, user: CurrentUser, db: DbSession):
    entry = await _owned_entry(entry_id, user, db)
    entry.deleted_at = datetime.now(UTC)
    await db.commit()
