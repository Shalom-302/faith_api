# app/routers/testimonies.py
"""Routes du module TÉMOIGNAGES — CRUD complet."""
import uuid
from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_db
from app.core.security import get_current_user
from app.plugins.advanced_auth.models import User
from app.schemas import faith as schemas
from app.services import faith_service

router = APIRouter()


@router.get(
    "", response_model=List[schemas.TestimonyResponse],
    summary="Lister les témoignages du feed",
)
async def list_testimonies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.list_testimonies(db, skip=skip, limit=limit)


@router.post(
    "", response_model=schemas.TestimonyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Publier un témoignage",
)
async def create_testimony(
    testimony_in: schemas.TestimonyCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.create_testimony(db, current_user, testimony_in)


@router.put(
    "/{testimony_id}", response_model=schemas.TestimonyResponse,
    summary="Modifier un témoignage (auteur ou admin)",
)
async def update_testimony(
    testimony_id: uuid.UUID,
    testimony_in: schemas.TestimonyUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.update_testimony(
        db, testimony_id, current_user, testimony_in
    )


@router.delete("/{testimony_id}", summary="Supprimer un témoignage (auteur ou admin)")
async def delete_testimony(
    testimony_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    await faith_service.delete_testimony(db, testimony_id, current_user)
    return {"detail": "Témoignage supprimé."}
