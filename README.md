# VVZ Explorer — Semantic Search for ETH Zurich Course Catalogue

A semantic search engine for the ETH Zurich Vorlesungsverzeichnis (VVZ). Find lectures by meaning, not just keywords — using vector embeddings with a Django + Next.js frontend.

## Why this exists

| Official VVZ | VVZ Explorer |
|--------------|--------------|
| Keyword-only search | **Semantic search** — find lectures by meaning |
| No cross-semester search | **Cross-semester semantic search** |
| Rigid category tree | **Fuzzy category browsing** + semantic similarity |
| No "similar lectures" | **Lecture-to-lecture similarity** by number → vector → nearest neighbors |
| Rigid UI, slow navigation | **Instant search, infinite scroll, hover-expand cards, dark mode** |

## Quick Start

```bash
cd vvz-explorer
docker compose --profile dev up
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api/ |

## Documentation

| Topic | File |
|-------|------|
| Architecture | [docs/architecture.md](docs/architecture.md) |
| Crawler Pipeline | [docs/crawler-pipeline.md](docs/crawler-pipeline.md) |
| Deployment | [docs/deployment.md](docs/deployment.md) |
| Development | [docs/development.md](docs/development.md) |

## Project Structure

```
vvz-explorer/
├── backend/                        # Django REST API
│   ├── backend/settings/           # base.py, dev.py, prod.py
│   ├── api/                        # DRF views, serializers, URLs
│   ├── scraper/                    # Crawl & embed scripts (simple, no mgmt cmds)
│   └── manage.py
├── frontend/                       # Next.js 15 App Router
│   └── app/                        # Pages, components, styles
├── crawler/                        # Archived Jupyter notebooks (read-only)
├── data/                           # SQLite DBs (gitignored)
├── docs/                           # Documentation
├── docker-compose.yml              # Dev + Prod profiles
├── .env.example                    # Environment template
└── README.md                       # This file
```

## Key Scripts

```bash
# Crawl VVZ for FS2026
python backend/scraper/crawl.py --semester 2026S

# Generate embeddings (384-dim, all-MiniLM-L6-v2)
python backend/scraper/embed.py --semester 2026S

# Re-embed with Nomic (768-dim, higher quality)
python backend/reembed.py

# Or use the helper script
./backend/embed.sh 2026S
```

## Tech Stack

- **Backend**: Django 5, DRF, Gunicorn, PostgreSQL + pgvector (prod) / SQLite (dev)
- **Frontend**: Next.js 15 (App Router), Tailwind CSS v4, React 19
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2 / nomic-embed-text-v1.5)
- **Vector Search**: sqlite-vec (dev), pgvector (prod)
- **Infra**: Docker Compose with `dev`/`prod` profiles, Nginx reverse proxy

## License

MIT — Free to use, modify, and distribute. Not affiliated with ETH Zurich or VSETH.

## Links

- **GitHub**: https://github.com/yourusername/vvz-crawler-semantic-search
- **Official VVZ**: https://vvz.ethz.ch
- **VSETH**: https://vseth.ethz.ch