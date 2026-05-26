# app/routers/sermons.py
"""Routes du module SERMONS (prédications) — CRUD complet."""
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


# --- READ ---
@router.get(
    "", response_model=List[schemas.SermonResponse],
    summary="Lister les prédications du feed (filtrable par auteur)",
)
async def list_sermons(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    author_id: uuid.UUID | None = Query(
        None, description="Si fourni, ne renvoie que les prédications de cet auteur."
    ),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.list_sermons(
        db, current_user, skip=skip, limit=limit, author_id=author_id
    )


@router.get(
    "/{sermon_id}", response_model=schemas.SermonResponse,
    summary="Détail d'une prédication",
)
async def get_sermon(
    sermon_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.get_sermon(db, sermon_id, current_user)


# --- CREATE ---
@router.post(
    "", response_model=schemas.SermonResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Publier une prédication (prédicateur / évangéliste)",
)
async def create_sermon(
    sermon_in: schemas.SermonCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.create_sermon(db, current_user, sermon_in)


# --- UPDATE ---
@router.put(
    "/{sermon_id}", response_model=schemas.SermonResponse,
    summary="Modifier une prédication (auteur ou admin)",
)
async def update_sermon(
    sermon_id: uuid.UUID,
    sermon_in: schemas.SermonUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.update_sermon(db, sermon_id, current_user, sermon_in)


# --- DELETE ---
@router.delete("/{sermon_id}", summary="Supprimer une prédication (auteur ou admin)")
async def delete_sermon(
    sermon_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    await faith_service.delete_sermon(db, sermon_id, current_user)
    return {"detail": "Prédication supprimée."}


# --- Likes & commentaires ---
@router.post("/{sermon_id}/like", summary="Aimer / ne plus aimer une prédication")
async def toggle_like(
    sermon_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.toggle_sermon_like(db, sermon_id, current_user)


@router.get(
    "/{sermon_id}/comments", response_model=List[schemas.CommentResponse],
    summary="Lister les commentaires d'une prédication",
)
async def list_comments(
    sermon_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.list_sermon_comments(db, sermon_id)


@router.post(
    "/{sermon_id}/comments", response_model=schemas.CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Commenter une prédication",
)
async def add_comment(
    sermon_id: uuid.UUID,
    comment_in: schemas.CommentCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.add_sermon_comment(
        db, sermon_id, current_user, comment_in
    )


@router.delete(
    "/{sermon_id}/comments/{comment_id}",
    summary="Supprimer un commentaire (auteur ou admin)",
)
async def delete_comment(
    sermon_id: uuid.UUID,
    comment_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    await faith_service.delete_sermon_comment(db, comment_id, current_user)
    return {"detail": "Commentaire supprimé."}
