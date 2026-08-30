"""Qayd endpointlari — erkin matn va belgilanadigan ro'yxat."""

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models import Note, NoteItem, Project, User
from app.schemas.note import (
    NoteCreate,
    NoteDetailRead,
    NoteItemCreate,
    NoteItemRead,
    NoteItemUpdate,
    NoteListRead,
    NoteRead,
    NoteUpdate,
)

router = APIRouter(prefix="/api/notes", tags=["notes"])


async def _owned_note(
    note_id: int, user: User, db: DbSession, *, with_items: bool = False
) -> Note:
    stmt = select(Note).where(
        Note.id == note_id,
        Note.user_id == user.id,
        Note.deleted_at.is_(None),
    )
    if with_items:
        stmt = stmt.options(selectinload(Note.items))
    note = (await db.execute(stmt)).scalar_one_or_none()
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Qayd topilmadi"
        )
    return note


async def _check_project(project_id: int, user: User, db: DbSession) -> None:
    owned = (
        await db.execute(
            select(Project.id).where(
                Project.id == project_id,
                Project.user_id == user.id,
                Project.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if owned is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loyiha topilmadi"
        )


@router.get("", response_model=list[NoteListRead])
async def list_notes(
    user: CurrentUser, db: DbSession, project_id: int | None = None
):
    """Bitta agregat so'rov: LEFT JOIN + GROUP BY bilan elementlar sanog'i."""
    items_total = func.count(NoteItem.id)
    items_done = func.count(NoteItem.id).filter(NoteItem.is_done.is_(True))

    stmt = (
        select(
            Note,
            items_total.label("items_total"),
            items_done.label("items_done"),
        )
        .outerjoin(NoteItem, NoteItem.note_id == Note.id)
        .where(Note.user_id == user.id, Note.deleted_at.is_(None))
        .group_by(Note.id)
        .order_by(Note.is_pinned.desc(), Note.created_at.desc())
    )
    if project_id is not None:
        stmt = stmt.where(Note.project_id == project_id)

    result = []
    for note, total, done in (await db.execute(stmt)).all():
        row = NoteListRead.model_validate(note)
        row.items_total = total
        row.items_done = done
        result.append(row)
    return result


@router.post(
    "", response_model=NoteDetailRead, status_code=status.HTTP_201_CREATED
)
async def create_note(
    payload: NoteCreate, user: CurrentUser, db: DbSession
):
    if payload.project_id is not None:
        await _check_project(payload.project_id, user, db)

    note = Note(
        user_id=user.id,
        project_id=payload.project_id,
        title=payload.title,
        body=payload.body,
    )
    for order, text in enumerate(payload.items):
        note.items.append(NoteItem(text=text, sort_order=order))
    db.add(note)
    await db.commit()
    await db.refresh(note, attribute_names=["items"])
    return note


@router.get("/{note_id}", response_model=NoteDetailRead)
async def get_note(note_id: int, user: CurrentUser, db: DbSession):
    return await _owned_note(note_id, user, db, with_items=True)


@router.patch("/{note_id}", response_model=NoteRead)
async def update_note(
    note_id: int, payload: NoteUpdate, user: CurrentUser, db: DbSession
):
    note = await _owned_note(note_id, user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(note, field, value)
    await db.commit()
    await db.refresh(note)
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(note_id: int, user: CurrentUser, db: DbSession):
    note = await _owned_note(note_id, user, db)
    note.deleted_at = datetime.now(UTC)
    await db.commit()


@router.post(
    "/{note_id}/items",
    response_model=NoteItemRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_note_item(
    note_id: int,
    payload: NoteItemCreate,
    user: CurrentUser,
    db: DbSession,
):
    note = await _owned_note(note_id, user, db, with_items=True)
    item = NoteItem(
        note_id=note.id,
        text=payload.text,
        sort_order=len(note.items),
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def _owned_note_item(
    note_id: int, item_id: int, user: User, db: DbSession
) -> NoteItem:
    item = (
        await db.execute(
            select(NoteItem)
            .join(Note, Note.id == NoteItem.note_id)
            .where(
                NoteItem.id == item_id,
                NoteItem.note_id == note_id,
                Note.user_id == user.id,
                Note.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ro'yxat qatori topilmadi",
        )
    return item


@router.patch("/{note_id}/items/{item_id}", response_model=NoteItemRead)
async def update_note_item(
    note_id: int,
    item_id: int,
    payload: NoteItemUpdate,
    user: CurrentUser,
    db: DbSession,
):
    item = await _owned_note_item(note_id, item_id, user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete(
    "/{note_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_note_item(
    note_id: int, item_id: int, user: CurrentUser, db: DbSession
):
    item = await _owned_note_item(note_id, item_id, user, db)
    await db.delete(item)
    await db.commit()
