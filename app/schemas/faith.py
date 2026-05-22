"""
Schémas Pydantic du domaine « Faith Social ».

Conventions (alignées sur `app/schemas/veille.py`) :
- `XBase`     : champs communs partagés.
- `XCreate`   : données reçues pour créer une ressource.
- `XUpdate`   : données reçues pour une mise à jour partielle (champs Optional).
- `XResponse` : données renvoyées, avec `model_config = ConfigDict(from_attributes=True)`.

Les `*Response` contiennent des champs calculés (`like_count`, `is_liked`,
`answer_count`...) construits par la couche service (`faith_service.py`).
"""
import datetime
import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Auteur (vue allégée d'un utilisateur, intégrée dans les autres réponses)
# ---------------------------------------------------------------------------
class UserMini(BaseModel):
    """Représentation minimale d'un utilisateur, pour l'affichage."""
    id: uuid.UUID
    username: str
    full_name: str
    avatar_url: Optional[str] = None
    role: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# SERMONS
# ---------------------------------------------------------------------------
class SermonBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    content: str = Field(..., min_length=1)
    media_url: Optional[str] = None


class SermonCreate(SermonBase):
    pass


class SermonUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    media_url: Optional[str] = None


class SermonResponse(SermonBase):
    id: uuid.UUID
    author: UserMini
    created_at: datetime.datetime
    like_count: int = 0
    comment_count: int = 0
    is_liked: bool = False

    model_config = ConfigDict(from_attributes=True)


# --- Commentaires de prédication ---
class CommentBase(BaseModel):
    content: str = Field(..., min_length=1)


class CommentCreate(CommentBase):
    pass


class CommentResponse(CommentBase):
    id: uuid.UUID
    author: UserMini
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# TÉMOIGNAGES
# ---------------------------------------------------------------------------
class TestimonyBase(BaseModel):
    content: str = Field(..., min_length=1)


class TestimonyCreate(TestimonyBase):
    pass


class TestimonyUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)


class TestimonyResponse(TestimonyBase):
    id: uuid.UUID
    author: UserMini
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# QUESTIONS / RÉPONSES
# ---------------------------------------------------------------------------
class QuestionBase(BaseModel):
    question_text: str = Field(..., min_length=5)


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = Field(None, min_length=5)


class QuestionResponse(QuestionBase):
    id: uuid.UUID
    author: UserMini
    is_answered: bool
    created_at: datetime.datetime
    answer_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class AnswerBase(BaseModel):
    answer_text: str = Field(..., min_length=1)


class AnswerCreate(AnswerBase):
    pass


class AnswerUpdate(BaseModel):
    answer_text: Optional[str] = Field(None, min_length=1)


class AnswerResponse(AnswerBase):
    id: uuid.UUID
    question_id: uuid.UUID
    author: UserMini
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# SOCIAL (amitiés)
# ---------------------------------------------------------------------------
class FriendRequestCreate(BaseModel):
    addressee_id: uuid.UUID


class FriendshipResponse(BaseModel):
    id: uuid.UUID
    requester: UserMini
    addressee: UserMini
    status: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# MESSAGERIE
# ---------------------------------------------------------------------------
class MessageBase(BaseModel):
    content: str = Field(..., min_length=1)


class MessageCreate(MessageBase):
    receiver_id: uuid.UUID


class MessageResponse(MessageBase):
    id: uuid.UUID
    sender: UserMini
    receiver_id: uuid.UUID
    is_read: bool
    sent_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    """Aperçu d'une conversation dans la liste de la messagerie."""
    other_user: UserMini
    last_message: str
    last_message_at: datetime.datetime
    unread_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# ADMINISTRATION
# ---------------------------------------------------------------------------
class AdminUserResponse(BaseModel):
    """Vue d'un utilisateur pour le panneau d'administration."""
    id: uuid.UUID
    username: str
    email: str
    full_name: str
    role: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class RoleUpdateRequest(BaseModel):
    """Requête de changement de rôle d'un utilisateur."""
    role: str = Field(
        ..., description="Nom du rôle : admin, predicateur, evangeliste, fidele, invite"
    )
