# Ma Liste d'Anniversaire

Application web de liste de cadeaux d'anniversaire. Le créateur de la liste se connecte avec Google, ajoute ses cadeaux, puis partage un lien avec ses proches. Les visiteurs peuvent réserver des cadeaux pour éviter les doublons.

## Fonctionnalités

- **Connexion Google** — le propriétaire de la liste se connecte une seule fois
- **Gestion des cadeaux** — ajout avec titre, lien, image, prix et description
- **Lien partageable** — URL unique `/list/[slug]` à envoyer à ses proches
- **Réservation** — les visiteurs entrent leur prénom et réservent un cadeau
- **Libération** — un visiteur peut annuler sa réservation
- **Tableau de bord admin** — voir tous les cadeaux, qui a réservé quoi, marquer un cadeau comme offert
- **Interface 100% en français**

## Stack technique

| Couche | Technologie |
|--------|------------|
| Frontend | Vue 3 + Vite + TypeScript |
| Styles | Tailwind CSS v4 + shadcn-vue |
| Backend | Python FastAPI |
| Base de données | PostgreSQL (SQLAlchemy async + Alembic) |
| Auth | Google OAuth 2.0 + JWT (cookies httpOnly) |

## Structure du projet

```
BirthdayGift/
├── src/                        # Frontend Vue 3
│   ├── pages/
│   │   ├── HomePage.vue        # Page de connexion
│   │   ├── OAuthCallbackPage.vue
│   │   ├── DashboardPage.vue   # Tableau de bord admin
│   │   └── ListPage.vue        # Liste publique partageable
│   ├── composables/
│   │   ├── useAuth.ts          # Gestion de session Google
│   │   └── useVisitor.ts       # Identité visiteur (localStorage)
│   ├── services/api.ts         # Client API
│   ├── router/index.ts
│   └── style.css
├── backend/                    # Backend FastAPI
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── auth.py         # Routes Google OAuth + session
│   │   │   └── gifts.py        # CRUD cadeaux + réservation
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   └── gift.py
│   │   ├── schemas/
│   │   ├── services/auth.py    # OAuth Google
│   │   ├── core/               # Sécurité, logs, middleware
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py
│   └── alembic/               # Migrations DB
└── README.md
```

## Installation

### Prérequis

- Node.js 18+
- Python 3.12+
- PostgreSQL

### Frontend

```bash
# Installer les dépendances
npm install

# Lancer en développement
npm run dev

# Build production
npm run build
```

### Backend

```bash
cd backend

# Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -e .

# Copier et remplir les variables d'environnement
cp .env.example .env

# Créer la base de données PostgreSQL
createdb birthday_gift

# Appliquer les migrations
alembic upgrade head

# Lancer le serveur
uvicorn app.main:app --reload
```

### Variables d'environnement (backend/.env)

```env
ENVIRONMENT=dev
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/birthday_gift
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
JWT_SECRET_KEY=votre-cle-secrete-longue-au-moins-32-caracteres
FRONTEND_URL=http://localhost:5173
```

### Variable d'environnement (frontend .env.local)

```env
VITE_API_URL=http://localhost:8000/api/v1
```

### Configuration Google OAuth

1. Aller sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créer un projet ou en sélectionner un existant
3. Activer l'API Google+ / People
4. Créer des identifiants OAuth 2.0
5. Ajouter `http://localhost:8000/api/v1/auth/google/callback` comme URI de redirection autorisé
6. Copier `Client ID` et `Client Secret` dans `.env`

## Roadmap

- [x] Connexion Google OAuth
- [x] Tableau de bord admin (ajouter, modifier, supprimer des cadeaux)
- [x] Lien partageable unique par liste
- [x] Page publique avec dialogue de saisie du prénom
- [x] Réservation et libération de cadeaux (lié au visiteur)
- [x] Statuts : Disponible / Réservé / Offert
- [ ] Notifications email quand un cadeau est réservé
- [ ] Uploader une image (plutôt qu'une URL)
- [ ] Récupération automatique de l'image depuis l'URL du produit
