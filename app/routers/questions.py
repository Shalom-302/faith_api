# app/routers/questions.py
"""Routes du module QUESTIONS / RÉPONSES — CRUD complet."""
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


# --- Questions ---
@router.get(
    "", response_model=List[schemas.QuestionResponse],
    summary="Lister les questions de foi (filtrable par auteur)",
)
async def list_questions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    author_id: uuid.UUID | None = Query(
        None, description="Si fourni, ne renvoie que les questions de cet auteur."
    ),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.list_questions(
        db, skip=skip, limit=limit, author_id=author_id
    )


@router.post(
    "", response_model=schemas.QuestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Poser une question",
)
async def create_question(
    question_in: schemas.QuestionCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.create_question(db, current_user, question_in)


@router.put(
    "/{question_id}", response_model=schemas.QuestionResponse,
    summary="Modifier une question (auteur ou admin)",
)
async def update_question(
    question_id: uuid.UUID,
    question_in: schemas.QuestionUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.update_question(
        db, question_id, current_user, question_in
    )


@router.delete("/{question_id}", summary="Supprimer une question (auteur ou admin)")
async def delete_question(
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    await faith_service.delete_question(db, question_id, current_user)
    return {"detail": "Question supprimée."}


# --- Réponses ---
@router.get(
    "/{question_id}/answers", response_model=List[schemas.AnswerResponse],
    summary="Lister les réponses d'une question",
)
async def list_answers(
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.list_answers(db, question_id)


@router.post(
    "/{question_id}/answers", response_model=schemas.AnswerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Répondre à une question (prédicateur / évangéliste)",
)
async def add_answer(
    question_id: uuid.UUID,
    answer_in: schemas.AnswerCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.add_answer(db, question_id, current_user, answer_in)


@router.delete(
    "/{question_id}/answers/{answer_id}",
    summary="Supprimer une réponse (auteur ou admin)",
)
async def delete_answer(
    question_id: uuid.UUID,
    answer_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    await faith_service.delete_answer(db, answer_id, current_user)
    return {"detail": "Réponse supprimée."}
