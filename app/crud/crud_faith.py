# app/crud/crud_faith.py
"""
Couche CRUD du domaine « Faith Social » (accès base de données).

Conventions (alignées sur `app/crud/crud_veille.py`) :
- Une classe `CRUDXxx` par entité, méthodes ASYNCHRONES (`AsyncSession`).
- Convention CRUD complète : **create / read / update / delete**.
- Requêtes via `select(...)` puis `await db.execute(...)`.
- Une instance prête à l'emploi est exposée en bas du fichier.
"""
import uuid
from typing import List, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.faith import (
    Answer, Friendship, Message, Question, Sermon, SermonComment, SermonLike,
    Testimony, TestimonyComment, TestimonyLike,
)
from app.schemas import faith as schemas


def _apply_update(db_obj, update_in) -> None:
    """Applique une mise à jour partielle : seuls les champs fournis sont modifiés."""
    for field, value in update_in.model_dump(exclude_unset=True).items():
        setattr(db_obj, field, value)


# ---------------------------------------------------------------------------
# SERMONS
# ---------------------------------------------------------------------------
class CRUDSermon:
    async def create(
        self, db: AsyncSession, *, user_id: uuid.UUID, sermon_in: schemas.SermonCreate
    ) -> Sermon:
        db_sermon = Sermon(
            user_id=user_id,
            title=sermon_in.title,
            content=sermon_in.content,
            media_url=sermon_in.media_url,
        )
        db.add(db_sermon)
        await db.commit()
        await db.refresh(db_sermon)
        return db_sermon

    async def get(self, db: AsyncSession, sermon_id: uuid.UUID) -> Optional[Sermon]:
        result = await db.execute(select(Sermon).filter(Sermon.id == sermon_id))
        return result.scalars().first()

    async def get_all(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[Sermon]:
        result = await db.execute(
            select(Sermon).order_by(Sermon.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def update(
        self, db: AsyncSession, db_sermon: Sermon, sermon_in: schemas.SermonUpdate
    ) -> Sermon:
        _apply_update(db_sermon, sermon_in)
        await db.commit()
        await db.refresh(db_sermon)
        return db_sermon

    async def remove(self, db: AsyncSession, db_sermon: Sermon) -> None:
        await db.delete(db_sermon)
        await db.commit()


class CRUDSermonLike:
    async def get(
        self, db: AsyncSession, *, user_id: uuid.UUID, sermon_id: uuid.UUID
    ) -> Optional[SermonLike]:
        result = await db.execute(
            select(SermonLike).filter(
                SermonLike.user_id == user_id, SermonLike.sermon_id == sermon_id
            )
        )
        return result.scalars().first()

    async def create(
        self, db: AsyncSession, *, user_id: uuid.UUID, sermon_id: uuid.UUID
    ) -> SermonLike:
        db_like = SermonLike(user_id=user_id, sermon_id=sermon_id)
        db.add(db_like)
        await db.commit()
        await db.refresh(db_like)
        return db_like

    async def remove(self, db: AsyncSession, db_like: SermonLike) -> None:
        await db.delete(db_like)
        await db.commit()


class CRUDSermonComment:
    async def create(
        self, db: AsyncSession, *, user_id: uuid.UUID, sermon_id: uuid.UUID, content: str
    ) -> SermonComment:
        db_comment = SermonComment(
            user_id=user_id, sermon_id=sermon_id, content=content
        )
        db.add(db_comment)
        await db.commit()
        await db.refresh(db_comment)
        return db_comment

    async def get(
        self, db: AsyncSession, comment_id: uuid.UUID
    ) -> Optional[SermonComment]:
        result = await db.execute(
            select(SermonComment).filter(SermonComment.id == comment_id)
        )
        return result.scalars().first()

    async def get_by_sermon(
        self, db: AsyncSession, sermon_id: uuid.UUID
    ) -> List[SermonComment]:
        result = await db.execute(
            select(SermonComment)
            .filter(SermonComment.sermon_id == sermon_id)
            .order_by(SermonComment.created_at.asc())
        )
        return list(result.scalars().all())

    async def remove(self, db: AsyncSession, db_comment: SermonComment) -> None:
        await db.delete(db_comment)
        await db.commit()


# ---------------------------------------------------------------------------
# TÉMOIGNAGES
# ---------------------------------------------------------------------------
class CRUDTestimony:
    async def create(
        self, db: AsyncSession, *, user_id: uuid.UUID,
        testimony_in: schemas.TestimonyCreate,
    ) -> Testimony:
        db_testimony = Testimony(user_id=user_id, content=testimony_in.content)
        db.add(db_testimony)
        await db.commit()
        await db.refresh(db_testimony)
        return db_testimony

    async def get(
        self, db: AsyncSession, testimony_id: uuid.UUID
    ) -> Optional[Testimony]:
        result = await db.execute(
            select(Testimony).filter(Testimony.id == testimony_id)
        )
        return result.scalars().first()

    async def get_all(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[Testimony]:
        result = await db.execute(
            select(Testimony)
            .order_by(Testimony.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(
        self, db: AsyncSession, db_testimony: Testimony,
        testimony_in: schemas.TestimonyUpdate,
    ) -> Testimony:
        _apply_update(db_testimony, testimony_in)
        await db.commit()
        await db.refresh(db_testimony)
        return db_testimony

    async def remove(self, db: AsyncSession, db_testimony: Testimony) -> None:
        await db.delete(db_testimony)
        await db.commit()


class CRUDTestimonyLike:
    async def get(
        self, db: AsyncSession, *, user_id: uuid.UUID, testimony_id: uuid.UUID
    ) -> Optional[TestimonyLike]:
        result = await db.execute(
            select(TestimonyLike).filter(
                TestimonyLike.user_id == user_id,
                TestimonyLike.testimony_id == testimony_id,
            )
        )
        return result.scalars().first()

    async def create(
        self, db: AsyncSession, *, user_id: uuid.UUID, testimony_id: uuid.UUID
    ) -> TestimonyLike:
        db_like = TestimonyLike(user_id=user_id, testimony_id=testimony_id)
        db.add(db_like)
        await db.commit()
        await db.refresh(db_like)
        return db_like

    async def remove(self, db: AsyncSession, db_like: TestimonyLike) -> None:
        await db.delete(db_like)
        await db.commit()


class CRUDTestimonyComment:
    async def create(
        self, db: AsyncSession, *, user_id: uuid.UUID, testimony_id: uuid.UUID,
        content: str,
    ) -> TestimonyComment:
        db_comment = TestimonyComment(
            user_id=user_id, testimony_id=testimony_id, content=content
        )
        db.add(db_comment)
        await db.commit()
        await db.refresh(db_comment)
        return db_comment

    async def get(
        self, db: AsyncSession, comment_id: uuid.UUID
    ) -> Optional[TestimonyComment]:
        result = await db.execute(
            select(TestimonyComment).filter(TestimonyComment.id == comment_id)
        )
        return result.scalars().first()

    async def get_by_testimony(
        self, db: AsyncSession, testimony_id: uuid.UUID
    ) -> List[TestimonyComment]:
        result = await db.execute(
            select(TestimonyComment)
            .filter(TestimonyComment.testimony_id == testimony_id)
            .order_by(TestimonyComment.created_at.asc())
        )
        return list(result.scalars().all())

    async def remove(self, db: AsyncSession, db_comment: TestimonyComment) -> None:
        await db.delete(db_comment)
        await db.commit()


# ---------------------------------------------------------------------------
# QUESTIONS / RÉPONSES
# ---------------------------------------------------------------------------
class CRUDQuestion:
    async def create(
        self, db: AsyncSession, *, user_id: uuid.UUID,
        question_in: schemas.QuestionCreate,
    ) -> Question:
        db_question = Question(
            user_id=user_id, question_text=question_in.question_text
        )
        db.add(db_question)
        await db.commit()
        await db.refresh(db_question)
        return db_question

    async def get(self, db: AsyncSession, question_id: uuid.UUID) -> Optional[Question]:
        result = await db.execute(select(Question).filter(Question.id == question_id))
        return result.scalars().first()

    async def get_all(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[Question]:
        result = await db.execute(
            select(Question)
            .order_by(Question.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(
        self, db: AsyncSession, db_question: Question,
        question_in: schemas.QuestionUpdate,
    ) -> Question:
        _apply_update(db_question, question_in)
        await db.commit()
        await db.refresh(db_question)
        return db_question

    async def mark_answered(self, db: AsyncSession, db_question: Question) -> Question:
        db_question.is_answered = True
        await db.commit()
        await db.refresh(db_question)
        return db_question

    async def remove(self, db: AsyncSession, db_question: Question) -> None:
        await db.delete(db_question)
        await db.commit()


class CRUDAnswer:
    async def create(
        self, db: AsyncSession, *, user_id: uuid.UUID, question_id: uuid.UUID,
        answer_in: schemas.AnswerCreate,
    ) -> Answer:
        db_answer = Answer(
            user_id=user_id,
            question_id=question_id,
            answer_text=answer_in.answer_text,
        )
        db.add(db_answer)
        await db.commit()
        await db.refresh(db_answer)
        return db_answer

    async def get(self, db: AsyncSession, answer_id: uuid.UUID) -> Optional[Answer]:
        result = await db.execute(select(Answer).filter(Answer.id == answer_id))
        return result.scalars().first()

    async def get_by_question(
        self, db: AsyncSession, question_id: uuid.UUID
    ) -> List[Answer]:
        result = await db.execute(
            select(Answer)
            .filter(Answer.question_id == question_id)
            .order_by(Answer.created_at.asc())
        )
        return list(result.scalars().all())

    async def update(
        self, db: AsyncSession, db_answer: Answer, answer_in: schemas.AnswerUpdate
    ) -> Answer:
        _apply_update(db_answer, answer_in)
        await db.commit()
        await db.refresh(db_answer)
        return db_answer

    async def remove(self, db: AsyncSession, db_answer: Answer) -> None:
        await db.delete(db_answer)
        await db.commit()


# ---------------------------------------------------------------------------
# SOCIAL (amitiés)
# ---------------------------------------------------------------------------
class CRUDFriendship:
    async def get(
        self, db: AsyncSession, friendship_id: uuid.UUID
    ) -> Optional[Friendship]:
        result = await db.execute(
            select(Friendship).filter(Friendship.id == friendship_id)
        )
        return result.scalars().first()

    async def get_between(
        self, db: AsyncSession, user_a: uuid.UUID, user_b: uuid.UUID
    ) -> Optional[Friendship]:
        """Renvoie la relation d'amitié entre deux utilisateurs (peu importe le sens)."""
        result = await db.execute(
            select(Friendship).filter(
                or_(
                    (Friendship.requester_id == user_a)
                    & (Friendship.addressee_id == user_b),
                    (Friendship.requester_id == user_b)
                    & (Friendship.addressee_id == user_a),
                )
            )
        )
        return result.scalars().first()

    async def create(
        self, db: AsyncSession, *, requester_id: uuid.UUID, addressee_id: uuid.UUID
    ) -> Friendship:
        db_friendship = Friendship(
            requester_id=requester_id, addressee_id=addressee_id, status="pending"
        )
        db.add(db_friendship)
        await db.commit()
        await db.refresh(db_friendship)
        return db_friendship

    async def update_status(
        self, db: AsyncSession, db_friendship: Friendship, status: str
    ) -> Friendship:
        db_friendship.status = status
        await db.commit()
        await db.refresh(db_friendship)
        return db_friendship

    async def remove(self, db: AsyncSession, db_friendship: Friendship) -> None:
        await db.delete(db_friendship)
        await db.commit()

    async def get_for_user(
        self, db: AsyncSession, user_id: uuid.UUID, status: Optional[str] = None
    ) -> List[Friendship]:
        """Liste les relations où l'utilisateur est impliqué (filtrées par statut)."""
        query = select(Friendship).filter(
            or_(
                Friendship.requester_id == user_id,
                Friendship.addressee_id == user_id,
            )
        )
        if status is not None:
            query = query.filter(Friendship.status == status)
        result = await db.execute(query.order_by(Friendship.created_at.desc()))
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# MESSAGERIE
# ---------------------------------------------------------------------------
class CRUDMessage:
    async def create(
        self, db: AsyncSession, *, sender_id: uuid.UUID,
        message_in: schemas.MessageCreate,
    ) -> Message:
        db_message = Message(
            sender_id=sender_id,
            receiver_id=message_in.receiver_id,
            content=message_in.content,
        )
        db.add(db_message)
        await db.commit()
        await db.refresh(db_message)
        return db_message

    async def get_for_user(self, db: AsyncSession, user_id: uuid.UUID) -> List[Message]:
        """Tous les messages où l'utilisateur est expéditeur ou destinataire."""
        result = await db.execute(
            select(Message)
            .filter(
                or_(Message.sender_id == user_id, Message.receiver_id == user_id)
            )
            .order_by(Message.sent_at.desc())
        )
        return list(result.scalars().all())

    async def get_conversation(
        self, db: AsyncSession, user_a: uuid.UUID, user_b: uuid.UUID
    ) -> List[Message]:
        """Le fil de messages échangés entre deux utilisateurs (ordre chronologique)."""
        result = await db.execute(
            select(Message)
            .filter(
                or_(
                    (Message.sender_id == user_a) & (Message.receiver_id == user_b),
                    (Message.sender_id == user_b) & (Message.receiver_id == user_a),
                )
            )
            .order_by(Message.sent_at.asc())
        )
        return list(result.scalars().all())

    async def mark_read(
        self, db: AsyncSession, *, reader_id: uuid.UUID, other_id: uuid.UUID
    ) -> int:
        """Marque comme lus les messages reçus de `other_id`. Renvoie le nombre traité."""
        messages = await self.get_conversation(db, reader_id, other_id)
        count = 0
        for msg in messages:
            if msg.receiver_id == reader_id and not msg.is_read:
                msg.is_read = True
                count += 1
        if count:
            await db.commit()
        return count


# --- Instances prêtes à l'emploi ---
crud_sermon = CRUDSermon()
crud_sermon_like = CRUDSermonLike()
crud_sermon_comment = CRUDSermonComment()
crud_testimony = CRUDTestimony()
crud_testimony_like = CRUDTestimonyLike()
crud_testimony_comment = CRUDTestimonyComment()
crud_question = CRUDQuestion()
crud_answer = CRUDAnswer()
crud_friendship = CRUDFriendship()
crud_message = CRUDMessage()
