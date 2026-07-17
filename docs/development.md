# Development Setup

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (for containerized dev)
- Git

## Quick Start (Docker)

```bash
cd vvz-explorer
docker compose --profile dev up
```

- Frontend: http://localhost:3000 (hot reload)
- Backend: http://localhost:8000 (auto-reload)

## Manual Setup (Without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set up Django
cp ../.env.example .env  # Edit as needed
python manage.py migrate
python manage.py createsuperuser

# Run server
python manage.py runserver 0.0.0.0:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Database (Development)

SQLite databases in `data/` (gitignored):
- `lectures_FS2026.db` - scraped course data
- `embeddings_FS2026.db` - vector embeddings

**To regenerate:**
```bash
# Crawl VVZ
python backend/scraper/crawl.py --semester 2026S

# Generate embeddings
python backend/scraper/embed.py --semester 2026S

# Or use the helper script
./backend/embed.sh 2026S
```

## Project Structure

```
vvz-explorer/
├── backend/              # Django REST API
│   ├── backend/          # Django project settings
│   ├── api/              # DRF views, serializers, URLs
│   ├── scraper/          # Crawler & embedding scripts
│   └── manage.py
├── frontend/             # Next.js 15 App Router
│   └── app/              # Pages & components
├── crawler/              # Archived Jupyter notebooks
├── data/                 # SQLite DBs (gitignored)
├── docs/                 # Documentation
├── docker-compose.yml    # Dev + Prod profiles
└── .env.example
```

## Key Commands

| Task | Command |
|------|---------|
| Start dev | `docker compose --profile dev up` |
| Rebuild images | `docker compose --profile dev up --build` |
| Django shell | `docker compose exec backend-dev python manage.py shell` |
| Run migrations | `docker compose exec backend-dev python manage.py migrate` |
| Create superuser | `docker compose exec backend-dev python manage.py createsuperuser` |
| Crawl VVZ | `docker compose exec backend-dev python backend/scraper/crawl.py --semester 2026S` |
| Generate embeddings | `docker compose exec backend-dev python backend/scraper/embed.py --semester 2026S` |
| Frontend lint | `cd frontend && npm run lint` |
| Frontend build | `cd frontend && npm run build` |

## API Endpoints (Dev)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/search/?q=` | GET | Semantic search |
| `/api/lectures/` | GET | Text search + filters |
| `/api/lectures/<number>/` | GET | Lecture detail |
| `/api/lectures/<number>/similar/` | GET | Similar lectures |
| `/api/suggest/?q=` | GET | Autocomplete |
| `/api/study-tracks/` | GET | List study tracks |
| `/api/categories/level1/` | GET | Level 1 categories |
| `/api/categories/level2/` | GET | Level 2 categories |
| `/api/categories/level3/` | GET | Level 3 categories |

## Testing

```bash
# Backend tests
cd backend && python manage.py test

# Frontend tests
cd frontend && npm test
```

## IDE Setup

### VS Code

Recommended extensions:
- Python
- Pylance
- ESLint
- Prettier
- Tailwind CSS IntelliSense
- Docker

### PyCharm

- Mark `backend` as Sources Root
- Configure Django server: `manage.py runserver`
- Python interpreter: `.venv/bin/python`

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `sqlite_vec` not found | `pip install sqlite-vec` in backend venv |
| Port 8000/3000 in use | Change ports in `docker-compose.yml` |
| Frontend can't reach API | Check `NEXT_PUBLIC_API_URL` in frontend env |
| Embeddings empty | Run `embed.py` after `crawl.py` |
| Migration errors | Delete `db.sqlite3` and re-run migrations |

## Useful Links

- [Django REST Framework](https://www.django-rest-framework.org/)
- [Next.js 15 App Router](https://nextjs.org/docs/app)
- [Tailwind CSS v4](https://tailwindcss.com/docs)
- [sqlite-vec](https://github.com/asg017/sqlite-vec)
- [pgvector](https://github.com/pgvector/pgvector)