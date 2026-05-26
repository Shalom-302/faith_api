# app/routers/testimonies.py
"""Routes du module TÉMOIGNAGES — CRUD complet + likes + commentaires."""
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
    "", response_model=List[schemas.TestimonyResponse],
    summary="Lister les témoignages du feed (filtrable par auteur)",
)
async def list_testimonies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    author_id: uuid.UUID | None = Query(
        None, description="Si fourni, ne renvoie que les témoignages de cet auteur."
    ),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.list_testimonies(
        db, current_user, skip=skip, limit=limit, author_id=author_id
    )


@router.get(
    "/{testimony_id}", response_model=schemas.TestimonyResponse,
    summary="Détail d'un témoignage",
)
async def get_testimony(
    testimony_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.get_testimony(db, testimony_id, current_user)


# --- CREATE / UPDATE / DELETE ---
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


# --- Likes & commentaires ---
@router.post("/{testimony_id}/like", summary="Aimer / ne plus aimer un témoignage")
async def toggle_like(
    testimony_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.toggle_testimony_like(db, testimony_id, current_user)


@router.get(
    "/{testimony_id}/comments", response_model=List[schemas.CommentResponse],
    summary="Lister les commentaires d'un témoignage",
)
async def list_comments(
    testimony_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.list_testimony_comments(db, testimony_id)


@router.post(
    "/{testimony_id}/comments", response_model=schemas.CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Commenter un témoignage",
)
async def add_comment(
    testimony_id: uuid.UUID,
    comment_in: schemas.CommentCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.add_testimony_comment(
        db, testimony_id, current_user, comment_in
    )


@router.delete(
    "/{testimony_id}/comments/{comment_id}",
    summary="Supprimer un commentaire (auteur ou admin)",
)
async def delete_comment(
    testimony_id: uuid.UUID,
    comment_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    await faith_service.delete_testimony_comment(db, comment_id, current_user)
    return {"detail": "Commentaire supprimé."}
