# app/routers/social.py
"""Routes du module SOCIAL (demandes d'amitié, liste d'amis)."""
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
    "/friends", response_model=List[schemas.FriendshipResponse],
    summary="Lister ses amis",
)
async def list_friends(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.list_friends(db, current_user)


@router.get(
    "/requests", response_model=List[schemas.FriendshipResponse],
    summary="Lister les demandes d'amitié en attente",
)
async def list_pending_requests(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.list_pending_requests(db, current_user)


@router.post(
    "/requests", response_model=schemas.FriendshipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Envoyer une demande d'amitié",
)
async def send_friend_request(
    request_in: schemas.FriendRequestCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.send_friend_request(db, current_user, request_in)


@router.post(
    "/requests/{friendship_id}/respond",
    response_model=schemas.FriendshipResponse,
    summary="Accepter ou refuser une demande d'amitié",
)
async def respond_friend_request(
    friendship_id: uuid.UUID,
    accept: bool = Query(..., description="true pour accepter, false pour refuser"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.respond_friend_request(
        db, friendship_id, current_user, accept
    )
