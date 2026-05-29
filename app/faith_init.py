"""
Initialisation du domaine « Faith Social ».

Appelée au démarrage de l'application (voir `main.py`). Trois rôles :
1. créer les tables `faith_*` si elles n'existent pas encore ;
2. semer (seed) les 5 rôles métier décrits dans `faitharchi.txt` ;
3. semer 2 utilisateurs de démonstration (un prédicateur, un fidèle) pour
   pouvoir tester immédiatement la différence d'expérience entre les rôles.

Note : on crée UNIQUEMENT les tables Faith (paramètre `tables=`), sans
toucher au schéma géré par les migrations Alembic du boilerplate Kaapi.
"""
import datetime

from app.core.db import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.models.faith import (
    FAITH_TABLES,
    Question,
    Sermon,
    SermonComment,
    SermonLike,
    Testimony,
    TestimonyComment,
    TestimonyLike,
)
from app.plugins.advanced_auth.models import Role, User

# Les 5 rôles du domaine (cf. faitharchi.txt).
FAITH_ROLES = [
    ("admin", "Administrateur : supervise les utilisateurs et modère les contenus."),
    ("predicateur", "Prédicateur : publie des prédications et répond aux questions."),
    ("evangeliste", "Évangéliste : publie des prédications et répond aux questions."),
    ("fidele", "Fidèle : publie témoignages, pose des questions, interagit."),
    ("invite", "Invité : accès en lecture aux prédications et témoignages."),
]

# Comptes de démonstration : (username, email, mot de passe, prénom, nom, rôle).
# Les deux premiers sont les comptes de test « officiels » ; les suivants
# peuplent la communauté pour que les feeds (témoignages, amis) soient vivants.
DEMO_USERS = [
    ("predicateur", "predicateur@faith.test", "Predicateur123!",
     "Paul", "Prédicateur", "predicateur"),
    ("fidele", "fidele@faith.test", "Fidele123!",
     "Marie", "Fidèle", "fidele"),
    # 2e prédicateur : pour qu'un prédicateur voie aussi les prédications de
    # ses confrères (le feed des sermons est commun à tous les rôles).
    ("emmanuel", "emmanuel@faith.test", "Emmanuel123!",
     "Emmanuel", "Pasteur", "predicateur"),
    ("sarah", "sarah@faith.test", "Sarah123!",
     "Sarah", "Miller", "fidele"),
    ("daniel", "daniel@faith.test", "Daniel123!",
     "Daniel", "Okafor", "fidele"),
]


def create_faith_tables() -> None:
    """Crée les tables `faith_*` (sans effet si elles existent déjà)."""
    Base.metadata.create_all(bind=engine, tables=FAITH_TABLES)


def seed_faith_roles() -> None:
    """Insère les rôles Faith manquants dans la table `auth_role`."""
    db = SessionLocal()
    try:
        for name, description in FAITH_ROLES:
            exists = db.query(Role).filter(Role.name == name).first()
            if not exists:
                db.add(Role(name=name, description=description, is_system_role=True))
        db.commit()
    finally:
        db.close()


def seed_demo_users() -> None:
    """Crée les 2 comptes de démonstration s'ils n'existent pas déjà."""
    db = SessionLocal()
    try:
        for username, email, password, first_name, last_name, role_name in DEMO_USERS:
            if db.query(User).filter(User.email == email).first():
                continue  # déjà présent
            role = db.query(Role).filter(Role.name == role_name).first()
            if not role:
                continue  # rôle absent : on ne peut pas créer le compte
            db.add(
                User(
                    username=username,
                    email=email,
                    hashed_password=get_password_hash(password),
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True,
                    is_verified=True,
                    role_id=role.id,
                    primary_auth_provider="email",
                )
            )
        db.commit()
    finally:
        db.close()


# Belles photos libres (Unsplash) pour illustrer les prédications.
_IMG = "https://images.unsplash.com/"
SERMON_PHOTOS = {
    "candle": f"{_IMG}photo-1504052434569-70ad5836ab65?w=900&q=80",   # bougie
    "sunrise": f"{_IMG}photo-1438232992991-995b7058bbb3?w=900&q=80",  # lever de soleil
    "church": f"{_IMG}photo-1507692049790-de58290a4334?w=900&q=80",   # intérieur d'église
    "bible": f"{_IMG}photo-1490127252417-7c393f993ee4?w=900&q=80",    # Bible ouverte
}

# Vidéo d'exemple publique (mp4 court avec audio) pour tester la lecture vidéo.
# Le frontend détecte l'extension `.mp4` et affiche un lecteur au lieu d'une image.
SERMON_VIDEO = (
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/"
    "sample/ForBiggerBlazes.mp4"
)


def seed_demo_content() -> None:
    """Sème prédications, témoignages et questions de démonstration.

    Idempotent **par élément** : chaque prédication (clé = titre), témoignage
    (clé = contenu) et question (clé = texte) n'est créé que s'il n'existe pas
    déjà. On peut donc relancer cette fonction à chaque démarrage, même sur une
    base déjà peuplée, sans créer de doublon ni avoir à vider la base.
    """
    db = SessionLocal()
    try:
        users = {u.email: u for u in db.query(User).all()}
        paul = users.get("predicateur@faith.test")
        marie = users.get("fidele@faith.test")
        emmanuel = users.get("emmanuel@faith.test") or paul
        sarah = users.get("sarah@faith.test")
        daniel = users.get("daniel@faith.test")
        if not paul or not marie:
            return  # comptes de démo absents : rien à rattacher

        now = datetime.datetime.utcnow()

        def ago(hours: float) -> datetime.datetime:
            """Horodatage situé `hours` heures dans le passé (pour l'ordre du feed)."""
            return now - datetime.timedelta(hours=hours)

        # --- Prédications (réparties entre Paul et Emmanuel) ---
        # (auteur, titre, contenu, photo/vidéo, heures dans le passé)
        sermons_data = [
            (
                paul,
                "La Foi en Action : Vivre sa Croyance au Quotidien",
                "Une réflexion sur la mise en pratique de la foi chaque jour, "
                "dans les petites comme les grandes décisions. La foi sans les "
                "œuvres est morte (Jacques 2:17) : laissons notre confiance en "
                "Dieu transformer nos gestes les plus ordinaires.",
                SERMON_PHOTOS["candle"], 2,
            ),
            (
                emmanuel,
                "Le Pardon : Libérer son Cœur",
                "Comment le pardon libère d'abord celui qui pardonne, et ouvre "
                "le chemin de la paix. Pardonner n'efface pas le passé, mais il "
                "nous délivre de son emprise.",
                SERMON_PHOTOS["sunrise"], 26,
            ),
            (
                emmanuel,
                "Marcher dans la Lumière",
                "Dieu est lumière, et il n'y a point en lui de ténèbres "
                "(1 Jean 1:5). Marcher dans la lumière, c'est avancer dans la "
                "vérité, la transparence et l'amour fraternel.",
                SERMON_PHOTOS["church"], 50,
            ),
            (
                paul,
                "La Puissance de la Prière (vidéo)",
                "La prière n'est pas un dernier recours, mais notre première "
                "force. Priez sans cesse (1 Thessaloniciens 5:17) : découvrons "
                "ensemble comment bâtir une vie de prière constante et joyeuse.",
                SERMON_VIDEO, 74,
            ),
        ]
        # On ne crée que les prédications absentes ; `created` mémorise celles
        # qu'on vient d'ajouter (pour n'y attacher likes/commentaires qu'une fois).
        sermons: dict[str, Sermon] = {}
        created: set[str] = set()
        for author, title, content, media, hours in sermons_data:
            existing = db.query(Sermon).filter(Sermon.title == title).first()
            if existing:
                sermons[title] = existing
                continue
            sermon = Sermon(
                user_id=author.id,
                title=title,
                content=content,
                media_url=media,
                created_at=ago(hours),
            )
            db.add(sermon)
            sermons[title] = sermon
            created.add(title)
        db.flush()  # pour disposer des id avant de créer likes/commentaires

        likers = [u for u in (marie, sarah, daniel) if u]
        # Likes + commentaire sur « La Foi en Action » (seulement si on vient
        # de la créer, pour ne pas violer la contrainte d'unicité des likes).
        foi = "La Foi en Action : Vivre sa Croyance au Quotidien"
        if foi in created:
            for liker in likers:
                db.add(SermonLike(user_id=liker.id, sermon_id=sermons[foi].id))
            db.add(SermonComment(
                user_id=marie.id,
                sermon_id=sermons[foi].id,
                content="Amen ! Cette prédication m'a vraiment touchée. 🙏",
                created_at=ago(1),
            ))
        pardon = "Le Pardon : Libérer son Cœur"
        if pardon in created:
            db.add(SermonLike(user_id=marie.id, sermon_id=sermons[pardon].id))

        # --- Témoignages (Marie en publie pour pouvoir « se voir ») ---
        # (auteur, contenu, heures dans le passé)
        promo = (
            "Aujourd'hui, j'ai reçu une promotion au travail pour laquelle je "
            "priais depuis des mois. C'est un témoignage des bénédictions dans "
            "ma vie. Merci Seigneur, pour ta grâce et ta force. #blessed"
        )
        testimonies_data = [
            (marie, promo, 2),
            (daniel or marie,
             "Après des semaines difficiles, ma famille a retrouvé la paix. "
             "Dieu est fidèle, Il n'abandonne jamais les siens. Gloire à Lui !", 20),
            (sarah or marie,
             "Guérie d'une longue maladie. Les médecins ne comprenaient pas, "
             "mais moi je sais : c'est la main de Dieu. Alléluia !", 96),
            (marie,
             "Reconnaissante pour chaque jour que le Seigneur m'accorde. "
             "Sa fidélité est nouvelle chaque matin (Lamentations 3:23).", 120),
        ]
        promo_testimony: Testimony | None = None
        promo_created = False
        for author, content, hours in testimonies_data:
            existing = (
                db.query(Testimony).filter(Testimony.content == content).first()
            )
            if existing:
                if content == promo:
                    promo_testimony = existing
                continue
            testimony = Testimony(
                user_id=author.id, content=content, created_at=ago(hours)
            )
            db.add(testimony)
            if content == promo:
                promo_testimony = testimony
                promo_created = True
        db.flush()

        # Likes + un commentaire sur le témoignage « promotion » de Marie
        # (seulement s'il vient d'être créé).
        if promo_created and promo_testimony is not None:
            for liker in likers:
                db.add(TestimonyLike(
                    user_id=liker.id, testimony_id=promo_testimony.id))
            db.add(TestimonyComment(
                user_id=daniel.id if daniel else paul.id,
                testimony_id=promo_testimony.id,
                content="Gloire à Dieu ! Tellement heureux pour toi. 🙌",
                created_at=ago(1),
            ))

        # --- Questions posées par Marie (fidèle) ---
        questions = [
            "Comment renforcer ma foi pendant les moments difficiles ?",
            "Quel est le rôle de la prière dans la vie d'un chrétien ?",
        ]
        for i, text in enumerate(questions):
            if db.query(Question).filter(Question.question_text == text).first():
                continue
            db.add(Question(
                user_id=marie.id,
                question_text=text,
                is_answered=False,
                created_at=ago(5 + i * 25),
            ))

        db.commit()
    finally:
        db.close()


def init_faith() -> None:
    """Point d'entrée unique de l'initialisation Faith Social."""
    try:
        create_faith_tables()
        seed_faith_roles()
        seed_demo_users()
        seed_demo_content()
        print("🟢 Faith Social : tables, rôles, comptes et contenu de démo initialisés.")
    except Exception as exc:  # noqa: BLE001 — on ne veut pas bloquer le démarrage
        print(f"⚠️ Faith Social : échec de l'initialisation ({exc}).")
