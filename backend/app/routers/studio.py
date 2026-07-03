"""
Router — Studio Dashboard e Task Management (Phase 5).
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.auth import User
from app.schemas.studio import (
    CompleteTaskIn,
    DashboardSummaryOut,
    StudioTaskCreate,
    StudioTaskOut,
    StudioTaskUpdate,
)
from app.services import studio_task_service, user_service

router = APIRouter(prefix="/api/v1", tags=["Studio"])


async def _get_task_or_404(db: AsyncSession, task_id: uuid.UUID):
    task = await studio_task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task non trovato")
    return task


async def _check_task_access(
    db: AsyncSession, task, current_user: User, require_write: bool = False
) -> None:
    if current_user.role == "admin" or task.client_entity_id is None:
        return
    if not await user_service.has_client_access(
        db, current_user.id, task.client_entity_id, require_write=require_write
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai accesso al cliente associato a questo task",
        )


@router.get("/dashboard", response_model=DashboardSummaryOut)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardSummaryOut:
    summary = await studio_task_service.get_dashboard_summary(db)
    return DashboardSummaryOut(**summary)


@router.post(
    "/tasks",
    response_model=StudioTaskOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    body: StudioTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudioTaskOut:
    if body.client_entity_id is not None and current_user.role != "admin":
        if not await user_service.has_client_access(
            db, current_user.id, body.client_entity_id, require_write=True
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Non hai i permessi di scrittura per questo cliente",
            )
    task = await studio_task_service.create_task(db, body, created_by=current_user.id)
    return StudioTaskOut.model_validate(task)


@router.get("/tasks", response_model=List[StudioTaskOut])
async def list_tasks(
    stato: Optional[str] = Query(default=None),
    tipo: Optional[str] = Query(default=None),
    client_entity_id: Optional[uuid.UUID] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[StudioTaskOut]:
    tasks = await studio_task_service.list_tasks(
        db, stato=stato, client_entity_id=client_entity_id, tipo=tipo
    )
    if current_user.role != "admin":
        accessible = await user_service.list_accessible_client_ids(db, current_user.id)
        tasks = [t for t in tasks if t.client_entity_id is None or t.client_entity_id in accessible]
    return [StudioTaskOut.model_validate(t) for t in tasks]


# NOTA: /tasks/generate-scadenzario deve essere registrato PRIMA di /tasks/{task_id}
#       per evitare ambiguità di routing (generate-scadenzario non è un UUID valido
#       quindi non matcha {task_id: UUID}, ma meglio essere espliciti).
@router.post(
    "/tasks/generate-scadenzario",
    response_model=List[StudioTaskOut],
)
async def generate_scadenzario(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[StudioTaskOut]:
    tasks = await studio_task_service.generate_scadenzario_tasks(db, created_by=current_user.id)
    return [StudioTaskOut.model_validate(t) for t in tasks]


@router.get("/tasks/{task_id}", response_model=StudioTaskOut)
async def get_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudioTaskOut:
    task = await _get_task_or_404(db, task_id)
    await _check_task_access(db, task, current_user)
    return StudioTaskOut.model_validate(task)


@router.put("/tasks/{task_id}", response_model=StudioTaskOut)
async def update_task(
    task_id: uuid.UUID,
    body: StudioTaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudioTaskOut:
    task = await _get_task_or_404(db, task_id)
    await _check_task_access(db, task, current_user, require_write=True)
    task = await studio_task_service.update_task(db, task, body)
    return StudioTaskOut.model_validate(task)


@router.post("/tasks/{task_id}/complete", response_model=StudioTaskOut)
async def complete_task(
    task_id: uuid.UUID,
    body: CompleteTaskIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudioTaskOut:
    task = await _get_task_or_404(db, task_id)
    await _check_task_access(db, task, current_user, require_write=True)
    task = await studio_task_service.complete_task(db, task, body.completato_il)
    return StudioTaskOut.model_validate(task)


@router.post("/tasks/{task_id}/cancel", response_model=StudioTaskOut)
async def cancel_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudioTaskOut:
    task = await _get_task_or_404(db, task_id)
    await _check_task_access(db, task, current_user, require_write=True)
    task = await studio_task_service.cancel_task(db, task)
    return StudioTaskOut.model_validate(task)
