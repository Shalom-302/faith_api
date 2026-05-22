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
from app.core.db import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.models.faith import FAITH_TABLES
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
DEMO_USERS = [
    ("predicateur", "predicateur@faith.test", "Predicateur123!",
     "Paul", "Prédicateur", "predicateur"),
    ("fidele", "fidele@faith.test", "Fidele123!",
     "Marie", "Fidèle", "fidele"),
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


def init_faith() -> None:
    """Point d'entrée unique de l'initialisation Faith Social."""
    try:
        create_faith_tables()
        seed_faith_roles()
        seed_demo_users()
        print("🟢 Faith Social : tables, rôles et comptes de démo initialisés.")
    except Exception as exc:  # noqa: BLE001 — on ne veut pas bloquer le démarrage
        print(f"⚠️ Faith Social : échec de l'initialisation ({exc}).")
