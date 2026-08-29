"""Yozuv endpointlari — ishlar va materiallar."""

from datetime import UTC, date, datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DbSession, OwnedProject
from app.models import Entry, Project, ProjectPrice, User
from app.models.enums import EntryKind
from app.schemas.entry import EntryCreate, EntryRead, EntryUpdate

router = APIRouter(prefix="/api", tags=["entries"])


async def _owned_entry(entry_id: int, user: User, db: AsyncSession) -> Entry:
    """Yozuvni yuklaydi va uning loyihasi shu ustaga tegishliligini tekshiradi."""
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


@router.get(
    "/projects/{project_id}/entries", response_model=list[EntryRead]
)
async def list_entries(
    project: OwnedProject,
    db: DbSession,
    kind: EntryKind | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
):
    stmt = select(Entry).where(
        Entry.project_id == project.id,
        Entry.deleted_at.is_(None),
    )
    if kind is not None:
        stmt = stmt.where(Entry.kind == kind)
    if date_from is not None:
        stmt = stmt.where(Entry.entry_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Entry.entry_date <= date_to)
    stmt = stmt.order_by(Entry.entry_date.desc(), Entry.id.desc())
    return (await db.execute(stmt)).scalars().all()


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
    if payload.project_price_id is not None:
        pp = (
            await db.execute(
                select(ProjectPrice).where(
                    ProjectPrice.id == payload.project_price_id
                )
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
        # Frontend yuborgan nom/birlik/narxga ishonilmaydi — narxdan olinadi
        kind, name, unit, unit_price = pp.kind, pp.name, pp.unit, pp.price
    else:
        missing = [
            field
            for field in ("kind", "name", "unit", "unit_price")
            if getattr(payload, field) is None
        ]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Qo'lda yozuv uchun majburiy maydonlar: {', '.join(missing)}",
            )
        kind = payload.kind
        name = payload.name
        unit = payload.unit
        unit_price = payload.unit_price

    entry = Entry(
        project_id=project.id,
        project_price_id=payload.project_price_id,
        created_by_user_id=user.id,
        kind=kind,
        name=name,
        unit=unit,
        quantity=payload.quantity,
        unit_price=unit_price,
        paid_by=payload.paid_by,
        source=payload.source,
        note=payload.note,
        receipt_file_id=payload.receipt_file_id,
    )
    if payload.entry_date is not None:
        entry.entry_date = payload.entry_date

    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.patch("/entries/{entry_id}", response_model=EntryRead)
async def update_entry(
    entry_id: int, payload: EntryUpdate, user: CurrentUser, db: DbSession
):
    entry = await _owned_entry(entry_id, user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    await db.commit()
    await db.refresh(entry)  # amount (generated) qayta hisoblanadi
    return entry


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(entry_id: int, user: CurrentUser, db: DbSession):
    entry = await _owned_entry(entry_id, user, db)
    entry.deleted_at = datetime.now(UTC)
    await db.commit()
