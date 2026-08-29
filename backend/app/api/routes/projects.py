"""Loyiha endpointlari."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Query, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, OwnedProject
from app.models import Project
from app.models.enums import ProjectStatus
from app.schemas.common import ProjectSummary
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.summary import build_project_summary

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
async def list_projects(
    user: CurrentUser,
    db: DbSession,
    status_: Annotated[ProjectStatus | None, Query(alias="status")] = None,
):
    stmt = select(Project).where(
        Project.user_id == user.id,
        Project.deleted_at.is_(None),
    )
    if status_ is not None:
        stmt = stmt.where(Project.status == status_)
    stmt = stmt.order_by(Project.created_at.desc())
    return (await db.execute(stmt)).scalars().all()


@router.post(
    "", response_model=ProjectRead, status_code=status.HTTP_201_CREATED
)
async def create_project(
    payload: ProjectCreate, user: CurrentUser, db: DbSession
):
    project = Project(user_id=user.id, **payload.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(project: OwnedProject):
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    payload: ProjectUpdate, project: OwnedProject, db: DbSession
):
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project: OwnedProject, db: DbSession):
    project.deleted_at = datetime.now(UTC)
    await db.commit()


@router.get("/{project_id}/summary", response_model=ProjectSummary)
async def project_summary(project: OwnedProject, db: DbSession):
    return await build_project_summary(db, project.id)
