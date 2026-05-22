"""
Création directe de tout le schéma de base de données — SANS Alembic.

À utiliser pour un **premier run de test rapide** : c'est la voie la plus
fiable pour avoir une base fonctionnelle sans dérouler les 16 migrations
Alembic historiques du boilerplate Kaapi.

Usage (depuis l'intérieur du conteneur api) :

    docker-compose exec api python -m app.create_db

Ce script :
1. importe tous les modèles (auth, plugins, Faith) pour les enregistrer ;
2. crée toutes les tables manquantes (`create_all` est idempotent) ;
3. sème les rôles et les 2 comptes de démonstration Faith Social.

Pour une gestion de schéma « propre » en production, utiliser Alembic
(voir README.md).
"""
from app.core.db import Base, engine

# Importer `app.models` enregistre TOUS les modèles (auth + 27 plugins + Faith)
# auprès de `Base.metadata`. L'import doit précéder `create_all`.
import app.models  # noqa: F401

from app.faith_init import init_faith


def main() -> None:
    print("🟢 Création de toutes les tables de la base de données...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables créées (ou déjà existantes).")

    # Rôles Faith + comptes de démonstration (prédicateur / fidèle).
    init_faith()
    print("✅ Base de données prête.")


if __name__ == "__main__":
    main()
