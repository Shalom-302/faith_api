# Faith Social — Backend (FastAPI)

Backend du réseau social chrétien **Faith Social**, construit sur le
boilerplate « Kaapi ». Le domaine métier (sermons, témoignages, questions,
social, messagerie, administration) est ajouté dans `app/` ; l'authentification
réutilise le plugin `advanced_auth` (utilisateur, rôles, JWT).

> Détail de l'architecture du domaine : voir la section « Domaine Faith » plus bas.

---

## ✅ Prérequis

- **Docker** + **Docker Compose**.
- Le port **8002** libre sur l'hôte (l'API y est exposée).

---

## 🚀 Lancer le backend — premier run (pas à pas)

### 1. Construire et démarrer les conteneurs

```bash
cd backend
docker-compose up -d --build
```

Cela démarre l'API (`kaapi-api`), PostgreSQL (`kaapi-db`), Redis, Vault, MinIO…
L'API écoute sur **http://localhost:8002**.

Vérifier que l'API a bien démarré :

```bash
docker-compose logs -f api
```

> ⚠️ Si le conteneur `api` redémarre en boucle, lis les logs : c'est presque
> toujours un import de plugin ou une variable d'environnement manquante.

### 2. Créer le schéma de base de données

La base est vide au premier démarrage. **Deux méthodes** :

#### 🅰️ Méthode rapide (recommandée pour tester) — création directe

```bash
docker-compose exec api python -m app.create_db
```

Ce script crée **toutes les tables** (auth + plugins + `faith_*`), puis sème
les **5 rôles** et les **2 comptes de démonstration**. La base est prête
immédiatement. (`create_db` est idempotent : on peut le relancer sans risque.)

#### 🅱️ Méthode « propre » — migrations Alembic

```bash
docker-compose exec api alembic upgrade head
docker-compose restart api      # init_faith crée alors les tables faith_*
```

Les migrations historiques (`migrations/versions/`) datent du projet d'origine.
Pour repartir sur une base propre dédiée à Faith :

```bash
docker-compose exec api alembic revision --autogenerate -m "faith schema"
docker-compose exec api alembic upgrade head
```

### 3. C'est prêt

- Documentation interactive (Swagger) : **http://localhost:8002/docs**
- Les tables `faith_*` et les rôles sont (re)vérifiés à **chaque démarrage**
  de l'API par `app/faith_init.py` (opération idempotente).

---

## 👥 Comptes de démonstration

Semés automatiquement (par `create_db` ou `init_faith`). Ils servent à tester
la **différence d'expérience entre les rôles** :

| Rôle        | Email                     | Mot de passe       |
|-------------|---------------------------|--------------------|
| Prédicateur | `predicateur@faith.test`  | `Predicateur123!`  |
| Fidèle      | `fidele@faith.test`       | `Fidele123!`       |

- Le **prédicateur** publie des prédications et répond aux questions.
- Le **fidèle** consulte, aime, commente et pose des questions.

> ⚠️ Un compte créé via `/auth/register` reçoit le rôle `admin` par défaut
> (comportement du plugin Kaapi). Pour observer la séparation des rôles,
> connecte-toi avec les **comptes de démo** ci-dessus, pas avec un compte créé.

---

## 🧩 Domaine Faith — fichiers ajoutés

Découpage **modèle → schéma → CRUD → service → router** :

| Couche   | Fichier(s)                                            |
|----------|-------------------------------------------------------|
| Modèles  | `app/models/faith.py` (SQLAlchemy 2.0 `mapped_column`) |
| Schémas  | `app/schemas/faith.py` (Pydantic v2)                  |
| CRUD     | `app/crud/crud_faith.py` (async, create/read/update/delete) |
| Service  | `app/services/faith_service.py` (logique + permissions par rôle) |
| Routers  | `app/routers/{sermons,testimonies,questions,social,messages,admin}.py` |
| Init     | `app/faith_init.py` · `app/create_db.py`              |

Tables préfixées `faith_` ; aucune collision avec les tables des plugins Kaapi.

### Endpoints (préfixe global `/api`)

| Méthode            | Chemin                                  | Accès |
|--------------------|-----------------------------------------|-------|
| POST               | `/auth/register` · `/auth/login`        | public |
| GET                | `/auth/me`                              | authentifié |
| GET/POST/PUT/DELETE| `/sermons` · `/sermons/{id}`            | POST/PUT: prédicateur · DELETE: auteur/admin |
| POST/GET/DELETE    | `/sermons/{id}/like` · `/sermons/{id}/comments` | authentifié |
| GET/POST/PUT/DELETE| `/testimonies` · `/testimonies/{id}`    | PUT/DELETE: auteur/admin |
| GET/POST/PUT/DELETE| `/questions` · `/questions/{id}`        | PUT/DELETE: auteur/admin |
| GET/POST/DELETE    | `/questions/{id}/answers`               | POST: prédicateur |
| GET/POST           | `/social/friends` · `/social/requests`  | authentifié |
| GET/POST           | `/messages/conversations` · `/messages` | authentifié |
| GET/PUT            | `/admin/users` · `/admin/users/{id}/role` | admin uniquement |

---

## 🛠️ Dépannage du premier run

| Symptôme | Cause probable | Solution |
|----------|----------------|----------|
| `relation "faith_sermons" does not exist` | Schéma non créé | Lancer `python -m app.create_db` (étape 2) |
| `relation "user" does not exist` | Tables d'auth absentes | Idem — `app.create_db` crée tout |
| Le conteneur `api` redémarre en boucle | Import de plugin / `.env` | `docker-compose logs api` pour la trace exacte |
| `403` à la publication d'une prédication | Compte sans rôle prédicateur | Se connecter avec `predicateur@faith.test` |
| Connexion mobile impossible | Mauvaise URL | Émulateur Android = `http://10.0.2.2:8002/api` |

Le port hôte est défini dans `docker-compose.yml` (`8002:8000`).
