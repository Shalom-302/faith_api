"""
Modèles SQLAlchemy du domaine « Faith Social ».

Couvre les 6 modules décrits dans `faitharchi.txt` : sermons, témoignages,
questions/réponses, social (amitiés) et messagerie.

Conventions (alignées sur `app/models/veille.py`) :
- SQLAlchemy 2.0 : annotations `Mapped[...]` + `mapped_column(...)`.
- On RÉUTILISE le modèle `User` du plugin `advanced_auth` (UUID + rôles) :
  toutes les clés étrangères « auteur » pointent vers la table `user`.
- Toutes les tables sont préfixées `faith_` pour ne jamais entrer en
  collision avec les tables des plugins du boilerplate Kaapi.
"""
import datetime
import uuid
from typing import List, Optional

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
# Le modèle User (plugin advanced_auth) est importé pour que les relations
# `Mapped["User"]` se résolvent sans ambiguïté. Aucun import circulaire :
# le plugin advanced_auth ne dépend pas de `app.models`.
from app.plugins.advanced_auth.models import User


# ---------------------------------------------------------------------------
# Module SERMONS
# ---------------------------------------------------------------------------
class Sermon(Base):
    """Une prédication publiée par un prédicateur ou un évangéliste."""
    __tablename__ = "faith_sermons"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    media_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # `lazy="selectin"` : la relation est chargée automatiquement par un SELECT
    # séparé. C'est la stratégie compatible avec les sessions ASYNC (la stratégie
    # paresseuse par défaut, elle, lèverait une erreur en contexte asynchrone).
    author: Mapped["User"] = relationship("User", lazy="selectin")
    likes: Mapped[List["SermonLike"]] = relationship(
        back_populates="sermon", cascade="all, delete-orphan", lazy="selectin"
    )
    comments: Mapped[List["SermonComment"]] = relationship(
        back_populates="sermon", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Sermon(id={self.id}, title='{self.title[:30]}...')>"


class SermonLike(Base):
    """Un « j'aime » posé par un utilisateur sur une prédication."""
    __tablename__ = "faith_sermon_likes"
    __table_args__ = (
        # Un utilisateur ne peut liker une prédication qu'une seule fois.
        UniqueConstraint("user_id", "sermon_id", name="uq_faith_sermon_like"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    sermon_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("faith_sermons.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    sermon: Mapped["Sermon"] = relationship(back_populates="likes")


class SermonComment(Base):
    """Un commentaire posté sur une prédication."""
    __tablename__ = "faith_sermon_comments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    sermon_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("faith_sermons.id"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    sermon: Mapped["Sermon"] = relationship(back_populates="comments")
    author: Mapped["User"] = relationship("User", lazy="selectin")


# ---------------------------------------------------------------------------
# Module TÉMOIGNAGES
# ---------------------------------------------------------------------------
class Testimony(Base):
    """Un témoignage partagé par un fidèle."""
    __tablename__ = "faith_testimonies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    author: Mapped["User"] = relationship("User", lazy="selectin")
    likes: Mapped[List["TestimonyLike"]] = relationship(
        back_populates="testimony", cascade="all, delete-orphan", lazy="selectin"
    )
    comments: Mapped[List["TestimonyComment"]] = relationship(
        back_populates="testimony", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Testimony(id={self.id})>"


class TestimonyLike(Base):
    """Un « j'aime » posé par un utilisateur sur un témoignage."""
    __tablename__ = "faith_testimony_likes"
    __table_args__ = (
        UniqueConstraint("user_id", "testimony_id", name="uq_faith_testimony_like"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    testimony_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("faith_testimonies.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    testimony: Mapped["Testimony"] = relationship(back_populates="likes")


class TestimonyComment(Base):
    """Un commentaire posté sur un témoignage."""
    __tablename__ = "faith_testimony_comments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    testimony_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("faith_testimonies.id"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    testimony: Mapped["Testimony"] = relationship(back_populates="comments")
    author: Mapped["User"] = relationship("User", lazy="selectin")


# ---------------------------------------------------------------------------
# Module QUESTIONS / RÉPONSES
# ---------------------------------------------------------------------------
class Question(Base):
    """Une question de foi posée par un fidèle."""
    __tablename__ = "faith_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_answered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    author: Mapped["User"] = relationship("User", lazy="selectin")
    answers: Mapped[List["Answer"]] = relationship(
        back_populates="question", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Question(id={self.id})>"


class Answer(Base):
    """Une réponse apportée par un prédicateur ou un évangéliste."""
    __tablename__ = "faith_answers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("faith_questions.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    question: Mapped["Question"] = relationship(back_populates="answers")
    author: Mapped["User"] = relationship("User", lazy="selectin")


# ---------------------------------------------------------------------------
# Module SOCIAL (amitiés)
# ---------------------------------------------------------------------------
class Friendship(Base):
    """
    Une relation d'amitié entre deux utilisateurs.

    `status` vaut « pending » (demande envoyée), « accepted » ou « rejected ».
    `requester_id` envoie la demande, `addressee_id` la reçoit.
    """
    __tablename__ = "faith_friendships"
    __table_args__ = (
        UniqueConstraint("requester_id", "addressee_id", name="uq_faith_friendship"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    requester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    addressee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Deux clés étrangères pointent vers `user` : il faut donc préciser
    # `foreign_keys` pour lever l'ambiguïté.
    requester: Mapped["User"] = relationship(
        "User", foreign_keys=[requester_id], lazy="selectin"
    )
    addressee: Mapped["User"] = relationship(
        "User", foreign_keys=[addressee_id], lazy="selectin"
    )


# ---------------------------------------------------------------------------
# Module MESSAGERIE
# ---------------------------------------------------------------------------
class Message(Base):
    """Un message privé envoyé d'un utilisateur à un autre."""
    __tablename__ = "faith_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    receiver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sent_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    sender: Mapped["User"] = relationship(
        "User", foreign_keys=[sender_id], lazy="selectin"
    )
    receiver: Mapped["User"] = relationship(
        "User", foreign_keys=[receiver_id], lazy="selectin"
    )


# Liste des tables Faith — utilisée pour la création ciblée du schéma
# (voir `app/faith_init.py`).
FAITH_TABLES = [
    Sermon.__table__,
    SermonLike.__table__,
    SermonComment.__table__,
    Testimony.__table__,
    TestimonyLike.__table__,
    TestimonyComment.__table__,
    Question.__table__,
    Answer.__table__,
    Friendship.__table__,
    Message.__table__,
]
