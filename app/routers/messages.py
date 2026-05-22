# app/routers/messages.py
"""Routes du module MESSAGERIE."""
import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_db
from app.core.security import get_current_user
from app.plugins.advanced_auth.models import User
from app.schemas import faith as schemas
from app.services import faith_service

router = APIRouter()


@router.get(
    "/conversations", response_model=List[schemas.ConversationResponse],
    summary="Lister ses conversations",
)
async def list_conversations(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.list_conversations(db, current_user)


@router.get(
    "/conversations/{other_user_id}", response_model=List[schemas.MessageResponse],
    summary="Lire le fil de messages avec un utilisateur",
)
async def get_conversation(
    other_user_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.get_conversation(db, other_user_id, current_user)


@router.post(
    "/", response_model=schemas.MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Envoyer un message",
)
async def send_message(
    message_in: schemas.MessageCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.send_message(db, current_user, message_in)
