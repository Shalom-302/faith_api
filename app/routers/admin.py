# app/routers/admin.py
"""
Routes du module ADMINISTRATION.

Réservées aux administrateurs (rôle `admin` ou superutilisateur). Permettent
de « coordonner » la communauté : voir tous les membres et gérer leurs rôles
(promouvoir un membre prédicateur, par exemple).

La modération des contenus (suppression) passe par les routes `DELETE` de
chaque module : un admin y est toujours autorisé.
"""
import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_db
from app.core.security import get_current_user
from app.plugins.advanced_auth.models import User
from app.schemas import faith as schemas
from app.services import faith_service

router = APIRouter()


@router.get(
    "/users", response_model=List[schemas.AdminUserResponse],
    summary="Lister tous les utilisateurs (admin)",
)
async def list_users(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.admin_list_users(db, current_user)


@router.put(
    "/users/{user_id}/role", response_model=schemas.AdminUserResponse,
    summary="Changer le rôle d'un utilisateur (admin)",
)
async def change_user_role(
    user_id: uuid.UUID,
    payload: schemas.RoleUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await faith_service.admin_change_user_role(
        db, user_id, current_user, payload.role
    )
