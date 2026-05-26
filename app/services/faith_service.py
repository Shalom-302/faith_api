"""
Couche service du domaine « Faith Social ».

Rôle de cette couche :
- appliquer la logique métier et les règles de permission par rôle ;
- orchestrer les appels CRUD ;
- construire les schémas de réponse (`*Response`) avec leurs champs calculés.

Règles de permission (cf. `faitharchi.txt`) :
- publier une prédication / répondre à une question → prédicateur, évangéliste, admin ;
- modifier ou supprimer un contenu → son auteur, ou un admin ;
- administration (gestion des rôles) → admin uniquement ;
- le reste (témoignages, questions, likes, commentaires, amis, messages) → tout
  utilisateur authentifié.
"""
import uuid
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.crud_faith import (
    crud_answer, crud_friendship, crud_message, crud_question, crud_sermon,
    crud_sermon_comment, crud_sermon_like, crud_testimony,
    crud_testimony_comment, crud_testimony_like,
)
from app.plugins.advanced_auth.models import Role, User
from app.schemas import faith as schemas

# Rôles autorisés à publier des prédications / à répondre aux questions.
PUBLISHER_ROLES = {"predicateur", "evangeliste", "admin"}


# ---------------------------------------------------------------------------
# Helpers : rôles & permissions
# ---------------------------------------------------------------------------
def _role_name(user) -> str:
    """Nom du rôle de l'utilisateur, en minuscules (chaîne vide si absent)."""
    role = getattr(user, "role", None)
    return role.name.lower() if role and role.name else ""


def _is_admin(user) -> bool:
    return getattr(user, "is_superuser", False) or _role_name(user) == "admin"


def _require_publisher(user) -> None:
    """Réservé aux prédicateurs / évangélistes (publication de prédications, réponses)."""
    if _is_admin(user) or _role_name(user) in PUBLISHER_ROLES:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Action réservée aux prédicateurs et évangélistes.",
    )


def _require_owner_or_admin(user, owner_id: uuid.UUID) -> None:
    """Autorise l'auteur du contenu ou un administrateur."""
    if user.id == owner_id or _is_admin(user):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Vous ne pouvez modifier que vos propres contenus.",
    )


def _require_admin(user) -> None:
    if _is_admin(user):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Accès réservé aux administrateurs.",
    )


# ---------------------------------------------------------------------------
# Helpers : construction des réponses
# ---------------------------------------------------------------------------
def _user_mini(user) -> schemas.UserMini:
    full_name = (
        f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username
    )
    return schemas.UserMini(
        id=user.id,
        username=user.username,
        full_name=full_name,
        avatar_url=user.profile_picture,
    )


def _to_sermon_response(sermon, current_user_id: uuid.UUID) -> schemas.SermonResponse:
    return schemas.SermonResponse(
        id=sermon.id,
        title=sermon.title,
        content=sermon.content,
        media_url=sermon.media_url,
        created_at=sermon.created_at,
        author=_user_mini(sermon.author),
        like_count=len(sermon.likes),
        comment_count=len(sermon.comments),
        is_liked=any(like.user_id == current_user_id for like in sermon.likes),
    )


# ===========================================================================
# SERMONS
# ===========================================================================
async def list_sermons(
    db: AsyncSession,
    current_user,
    skip: int = 0,
    limit: int = 100,
    author_id: uuid.UUID | None = None,
) -> List[schemas.SermonResponse]:
    sermons = await crud_sermon.get_all(
        db, skip=skip, limit=limit, author_id=author_id
    )
    return [_to_sermon_response(s, current_user.id) for s in sermons]


async def get_sermon(
    db: AsyncSession, sermon_id: uuid.UUID, current_user
) -> schemas.SermonResponse:
    sermon = await crud_sermon.get(db, sermon_id)
    if not sermon:
        raise HTTPException(status_code=404, detail="Prédication non trouvée.")
    return _to_sermon_response(sermon, current_user.id)


async def create_sermon(
    db: AsyncSession, current_user, sermon_in: schemas.SermonCreate
) -> schemas.SermonResponse:
    _require_publisher(current_user)
    sermon = await crud_sermon.create(db, user_id=current_user.id, sermon_in=sermon_in)
    sermon = await crud_sermon.get(db, sermon.id)  # recharge les relations
    return _to_sermon_response(sermon, current_user.id)


async def update_sermon(
    db: AsyncSession, sermon_id: uuid.UUID, current_user,
    sermon_in: schemas.SermonUpdate,
) -> schemas.SermonResponse:
    sermon = await crud_sermon.get(db, sermon_id)
    if not sermon:
        raise HTTPException(status_code=404, detail="Prédication non trouvée.")
    _require_owner_or_admin(current_user, sermon.user_id)
    await crud_sermon.update(db, sermon, sermon_in)
    sermon = await crud_sermon.get(db, sermon_id)
    return _to_sermon_response(sermon, current_user.id)


async def delete_sermon(
    db: AsyncSession, sermon_id: uuid.UUID, current_user
) -> None:
    sermon = await crud_sermon.get(db, sermon_id)
    if not sermon:
        raise HTTPException(status_code=404, detail="Prédication non trouvée.")
    _require_owner_or_admin(current_user, sermon.user_id)
    await crud_sermon.remove(db, sermon)


async def toggle_sermon_like(
    db: AsyncSession, sermon_id: uuid.UUID, current_user
) -> dict:
    """Ajoute ou retire le « j'aime » de l'utilisateur sur une prédication."""
    sermon = await crud_sermon.get(db, sermon_id)
    if not sermon:
        raise HTTPException(status_code=404, detail="Prédication non trouvée.")

    existing = await crud_sermon_like.get(
        db, user_id=current_user.id, sermon_id=sermon_id
    )
    if existing:
        await crud_sermon_like.remove(db, existing)
        is_liked = False
    else:
        await crud_sermon_like.create(db, user_id=current_user.id, sermon_id=sermon_id)
        is_liked = True

    sermon = await crud_sermon.get(db, sermon_id)
    return {"is_liked": is_liked, "like_count": len(sermon.likes)}


async def list_sermon_comments(
    db: AsyncSession, sermon_id: uuid.UUID
) -> List[schemas.CommentResponse]:
    comments = await crud_sermon_comment.get_by_sermon(db, sermon_id)
    return [
        schemas.CommentResponse(
            id=c.id,
            content=c.content,
            created_at=c.created_at,
            author=_user_mini(c.author),
        )
        for c in comments
    ]


async def add_sermon_comment(
    db: AsyncSession, sermon_id: uuid.UUID, current_user,
    comment_in: schemas.CommentCreate,
) -> schemas.CommentResponse:
    sermon = await crud_sermon.get(db, sermon_id)
    if not sermon:
        raise HTTPException(status_code=404, detail="Prédication non trouvée.")
    comment = await crud_sermon_comment.create(
        db, user_id=current_user.id, sermon_id=sermon_id, content=comment_in.content
    )
    return schemas.CommentResponse(
        id=comment.id,
        content=comment.content,
        created_at=comment.created_at,
        author=_user_mini(current_user),
    )


async def delete_sermon_comment(
    db: AsyncSession, comment_id: uuid.UUID, current_user
) -> None:
    comment = await crud_sermon_comment.get(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Commentaire non trouvé.")
    _require_owner_or_admin(current_user, comment.user_id)
    await crud_sermon_comment.remove(db, comment)


# ===========================================================================
# TÉMOIGNAGES
# ===========================================================================
def _to_testimony_response(t, current_user_id: uuid.UUID) -> schemas.TestimonyResponse:
    return schemas.TestimonyResponse(
        id=t.id, content=t.content, created_at=t.created_at,
        author=_user_mini(t.author),
        like_count=len(t.likes),
        comment_count=len(t.comments),
        is_liked=any(like.user_id == current_user_id for like in t.likes),
    )


async def list_testimonies(
    db: AsyncSession,
    current_user,
    skip: int = 0,
    limit: int = 100,
    author_id: uuid.UUID | None = None,
) -> List[schemas.TestimonyResponse]:
    testimonies = await crud_testimony.get_all(
        db, skip=skip, limit=limit, author_id=author_id
    )
    return [_to_testimony_response(t, current_user.id) for t in testimonies]


async def get_testimony(
    db: AsyncSession, testimony_id: uuid.UUID, current_user
) -> schemas.TestimonyResponse:
    testimony = await crud_testimony.get(db, testimony_id)
    if not testimony:
        raise HTTPException(status_code=404, detail="Témoignage non trouvé.")
    return _to_testimony_response(testimony, current_user.id)


async def create_testimony(
    db: AsyncSession, current_user, testimony_in: schemas.TestimonyCreate
) -> schemas.TestimonyResponse:
    testimony = await crud_testimony.create(
        db, user_id=current_user.id, testimony_in=testimony_in
    )
    testimony = await crud_testimony.get(db, testimony.id)  # recharge les relations
    return _to_testimony_response(testimony, current_user.id)


async def update_testimony(
    db: AsyncSession, testimony_id: uuid.UUID, current_user,
    testimony_in: schemas.TestimonyUpdate,
) -> schemas.TestimonyResponse:
    testimony = await crud_testimony.get(db, testimony_id)
    if not testimony:
        raise HTTPException(status_code=404, detail="Témoignage non trouvé.")
    _require_owner_or_admin(current_user, testimony.user_id)
    testimony = await crud_testimony.update(db, testimony, testimony_in)
    testimony = await crud_testimony.get(db, testimony_id)
    return _to_testimony_response(testimony, current_user.id)


async def delete_testimony(
    db: AsyncSession, testimony_id: uuid.UUID, current_user
) -> None:
    testimony = await crud_testimony.get(db, testimony_id)
    if not testimony:
        raise HTTPException(status_code=404, detail="Témoignage non trouvé.")
    _require_owner_or_admin(current_user, testimony.user_id)
    await crud_testimony.remove(db, testimony)


async def toggle_testimony_like(
    db: AsyncSession, testimony_id: uuid.UUID, current_user
) -> dict:
    """Ajoute ou retire le « j'aime » de l'utilisateur sur un témoignage."""
    testimony = await crud_testimony.get(db, testimony_id)
    if not testimony:
        raise HTTPException(status_code=404, detail="Témoignage non trouvé.")

    existing = await crud_testimony_like.get(
        db, user_id=current_user.id, testimony_id=testimony_id
    )
    if existing:
        await crud_testimony_like.remove(db, existing)
        is_liked = False
    else:
        await crud_testimony_like.create(
            db, user_id=current_user.id, testimony_id=testimony_id
        )
        is_liked = True

    testimony = await crud_testimony.get(db, testimony_id)
    return {"is_liked": is_liked, "like_count": len(testimony.likes)}


async def list_testimony_comments(
    db: AsyncSession, testimony_id: uuid.UUID
) -> List[schemas.CommentResponse]:
    comments = await crud_testimony_comment.get_by_testimony(db, testimony_id)
    return [
        schemas.CommentResponse(
            id=c.id,
            content=c.content,
            created_at=c.created_at,
            author=_user_mini(c.author),
        )
        for c in comments
    ]


async def add_testimony_comment(
    db: AsyncSession, testimony_id: uuid.UUID, current_user,
    comment_in: schemas.CommentCreate,
) -> schemas.CommentResponse:
    testimony = await crud_testimony.get(db, testimony_id)
    if not testimony:
        raise HTTPException(status_code=404, detail="Témoignage non trouvé.")
    comment = await crud_testimony_comment.create(
        db, user_id=current_user.id, testimony_id=testimony_id,
        content=comment_in.content,
    )
    return schemas.CommentResponse(
        id=comment.id,
        content=comment.content,
        created_at=comment.created_at,
        author=_user_mini(current_user),
    )


async def delete_testimony_comment(
    db: AsyncSession, comment_id: uuid.UUID, current_user
) -> None:
    comment = await crud_testimony_comment.get(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Commentaire non trouvé.")
    _require_owner_or_admin(current_user, comment.user_id)
    await crud_testimony_comment.remove(db, comment)


# ===========================================================================
# QUESTIONS / RÉPONSES
# ===========================================================================
def _to_question_response(q) -> schemas.QuestionResponse:
    return schemas.QuestionResponse(
        id=q.id,
        question_text=q.question_text,
        is_answered=q.is_answered,
        created_at=q.created_at,
        author=_user_mini(q.author),
        answer_count=len(q.answers),
    )


async def list_questions(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    author_id: uuid.UUID | None = None,
) -> List[schemas.QuestionResponse]:
    questions = await crud_question.get_all(
        db, skip=skip, limit=limit, author_id=author_id
    )
    return [_to_question_response(q) for q in questions]


async def create_question(
    db: AsyncSession, current_user, question_in: schemas.QuestionCreate
) -> schemas.QuestionResponse:
    question = await crud_question.create(
        db, user_id=current_user.id, question_in=question_in
    )
    return schemas.QuestionResponse(
        id=question.id,
        question_text=question.question_text,
        is_answered=question.is_answered,
        created_at=question.created_at,
        author=_user_mini(current_user),
        answer_count=0,
    )


async def update_question(
    db: AsyncSession, question_id: uuid.UUID, current_user,
    question_in: schemas.QuestionUpdate,
) -> schemas.QuestionResponse:
    question = await crud_question.get(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question non trouvée.")
    _require_owner_or_admin(current_user, question.user_id)
    await crud_question.update(db, question, question_in)
    question = await crud_question.get(db, question_id)
    return _to_question_response(question)


async def delete_question(
    db: AsyncSession, question_id: uuid.UUID, current_user
) -> None:
    question = await crud_question.get(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question non trouvée.")
    _require_owner_or_admin(current_user, question.user_id)
    await crud_question.remove(db, question)


async def list_answers(
    db: AsyncSession, question_id: uuid.UUID
) -> List[schemas.AnswerResponse]:
    question = await crud_question.get(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question non trouvée.")
    answers = await crud_answer.get_by_question(db, question_id)
    return [_to_answer_response(a) for a in answers]


def _to_answer_response(a) -> schemas.AnswerResponse:
    return schemas.AnswerResponse(
        id=a.id,
        question_id=a.question_id,
        answer_text=a.answer_text,
        created_at=a.created_at,
        author=_user_mini(a.author),
    )


async def add_answer(
    db: AsyncSession, question_id: uuid.UUID, current_user,
    answer_in: schemas.AnswerCreate,
) -> schemas.AnswerResponse:
    _require_publisher(current_user)
    question = await crud_question.get(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question non trouvée.")

    answer = await crud_answer.create(
        db, user_id=current_user.id, question_id=question_id, answer_in=answer_in
    )
    if not question.is_answered:
        await crud_question.mark_answered(db, question)

    return schemas.AnswerResponse(
        id=answer.id,
        question_id=answer.question_id,
        answer_text=answer.answer_text,
        created_at=answer.created_at,
        author=_user_mini(current_user),
    )


async def delete_answer(
    db: AsyncSession, answer_id: uuid.UUID, current_user
) -> None:
    answer = await crud_answer.get(db, answer_id)
    if not answer:
        raise HTTPException(status_code=404, detail="Réponse non trouvée.")
    _require_owner_or_admin(current_user, answer.user_id)
    await crud_answer.remove(db, answer)


# ===========================================================================
# SOCIAL (amitiés)
# ===========================================================================
def _to_friendship_response(friendship) -> schemas.FriendshipResponse:
    return schemas.FriendshipResponse(
        id=friendship.id,
        requester=_user_mini(friendship.requester),
        addressee=_user_mini(friendship.addressee),
        status=friendship.status,
        created_at=friendship.created_at,
    )


async def send_friend_request(
    db: AsyncSession, current_user, request_in: schemas.FriendRequestCreate
) -> schemas.FriendshipResponse:
    if request_in.addressee_id == current_user.id:
        raise HTTPException(status_code=400, detail="Impossible de s'ajouter soi-même.")
    existing = await crud_friendship.get_between(
        db, current_user.id, request_in.addressee_id
    )
    if existing:
        raise HTTPException(
            status_code=409, detail="Une relation existe déjà avec cet utilisateur."
        )
    friendship = await crud_friendship.create(
        db, requester_id=current_user.id, addressee_id=request_in.addressee_id
    )
    friendship = await crud_friendship.get(db, friendship.id)
    return _to_friendship_response(friendship)


async def respond_friend_request(
    db: AsyncSession, friendship_id: uuid.UUID, current_user, accept: bool
) -> schemas.FriendshipResponse:
    friendship = await crud_friendship.get(db, friendship_id)
    if not friendship:
        raise HTTPException(status_code=404, detail="Demande non trouvée.")
    if friendship.addressee_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Cette demande ne vous est pas adressée."
        )
    new_status = "accepted" if accept else "rejected"
    friendship = await crud_friendship.update_status(db, friendship, new_status)
    return _to_friendship_response(friendship)


async def list_friends(
    db: AsyncSession, current_user
) -> List[schemas.FriendshipResponse]:
    friendships = await crud_friendship.get_for_user(
        db, current_user.id, status="accepted"
    )
    return [_to_friendship_response(f) for f in friendships]


async def list_pending_requests(
    db: AsyncSession, current_user
) -> List[schemas.FriendshipResponse]:
    friendships = await crud_friendship.get_for_user(
        db, current_user.id, status="pending"
    )
    return [_to_friendship_response(f) for f in friendships]


# ===========================================================================
# MESSAGERIE
# ===========================================================================
def _to_message_response(message) -> schemas.MessageResponse:
    return schemas.MessageResponse(
        id=message.id,
        sender=_user_mini(message.sender),
        receiver_id=message.receiver_id,
        content=message.content,
        is_read=message.is_read,
        sent_at=message.sent_at,
    )


async def send_message(
    db: AsyncSession, current_user, message_in: schemas.MessageCreate
) -> schemas.MessageResponse:
    if message_in.receiver_id == current_user.id:
        raise HTTPException(
            status_code=400, detail="Impossible de s'envoyer un message à soi-même."
        )
    await crud_message.create(db, sender_id=current_user.id, message_in=message_in)
    thread = await crud_message.get_conversation(
        db, current_user.id, message_in.receiver_id
    )
    # On renvoie le dernier message du fil (celui qu'on vient d'envoyer).
    return _to_message_response(thread[-1])


async def list_conversations(
    db: AsyncSession, current_user
) -> List[schemas.ConversationResponse]:
    """Regroupe tous les messages par interlocuteur pour la liste de la messagerie."""
    messages = await crud_message.get_for_user(db, current_user.id)  # tri décroissant
    conversations: dict = {}

    for msg in messages:
        is_sent = msg.sender_id == current_user.id
        other_user = msg.receiver if is_sent else msg.sender
        other_id = other_user.id

        if other_id not in conversations:
            conversations[other_id] = {
                "other_user": other_user,
                "last_message": msg,
                "unread_count": 0,
            }
        if msg.receiver_id == current_user.id and not msg.is_read:
            conversations[other_id]["unread_count"] += 1

    return [
        schemas.ConversationResponse(
            other_user=_user_mini(c["other_user"]),
            last_message=c["last_message"].content,
            last_message_at=c["last_message"].sent_at,
            unread_count=c["unread_count"],
        )
        for c in conversations.values()
    ]


async def get_conversation(
    db: AsyncSession, other_user_id: uuid.UUID, current_user
) -> List[schemas.MessageResponse]:
    """Renvoie le fil complet avec un utilisateur et marque ses messages comme lus."""
    messages = await crud_message.get_conversation(db, current_user.id, other_user_id)
    await crud_message.mark_read(db, reader_id=current_user.id, other_id=other_user_id)
    return [_to_message_response(m) for m in messages]


# ===========================================================================
# ADMINISTRATION
# ===========================================================================
def _to_admin_user(user) -> schemas.AdminUserResponse:
    full_name = (
        f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username
    )
    return schemas.AdminUserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=full_name,
        role=user.role.name if user.role else None,
        is_active=user.is_active,
    )


async def admin_list_users(
    db: AsyncSession, current_user
) -> List[schemas.AdminUserResponse]:
    """Liste tous les utilisateurs (réservé aux administrateurs)."""
    _require_admin(current_user)
    result = await db.execute(
        select(User).options(selectinload(User.role)).order_by(User.created_at.desc())
    )
    return [_to_admin_user(u) for u in result.scalars().all()]


async def admin_change_user_role(
    db: AsyncSession, user_id: uuid.UUID, current_user, role_name: str
) -> schemas.AdminUserResponse:
    """Change le rôle d'un utilisateur (réservé aux administrateurs)."""
    _require_admin(current_user)

    role_result = await db.execute(
        select(Role).filter(Role.name == role_name.lower())
    )
    role = role_result.scalars().first()
    if not role:
        raise HTTPException(status_code=404, detail=f"Rôle « {role_name} » inconnu.")

    user_result = await db.execute(
        select(User).options(selectinload(User.role)).filter(User.id == user_id)
    )
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")

    user.role_id = role.id
    await db.commit()

    # Rechargement pour renvoyer le rôle à jour.
    user_result = await db.execute(
        select(User).options(selectinload(User.role)).filter(User.id == user_id)
    )
    return _to_admin_user(user_result.scalars().first())
