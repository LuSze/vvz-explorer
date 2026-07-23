# VVZ Explorer — Semantic Search for ETH Zurich Course Catalogue

A semantic search engine for the ETH Zurich Vorlesungsverzeichnis (VVZ). Find lectures by meaning, not just keywords — using Nomic AI vector embeddings with a Django + Next.js frontend.

## Why this exists

| Official VVZ | VVZ Explorer |
|--------------|--------------|
| Keyword-only search | **Semantic search** — find lectures by meaning |
| No cross-semester search | **Cross-semester semantic search** |
| Rigid category tree | **Fuzzy category browsing** + semantic similarity |
| No "similar lectures" | **Lecture-to-lecture similarity** by number → vector → nearest neighbors |
| Rigid UI, slow navigation | **Instant search, infinite scroll, hover-expand cards, dark mode, usable on Smartphones** |

## Quick Start

```bash
cd vvz-explorer
docker compose --profile dev up
```

| Service | URL |
|---------|-----|
| App (frontend + API) | http://localhost:3000 |

The backend API is proxied through the Next.js frontend via rewrites — only port 3000 is needed.

## Documentation

| Topic | File |
|-------|------|
| Architecture | [docs/architecture.md](docs/architecture.md) |
| Crawler Pipeline | [docs/crawler-pipeline.md](docs/crawler-pipeline.md) |
| Deployment | [docs/deployment.md](docs/deployment.md) |
| Development | [docs/development.md](docs/development.md) |
| IPFS Data | [docs/ipfs.md](docs/ipfs.md) |

## Project Structure

```
vvz-explorer/
├── backend/                        # Django REST API
│   ├── backend/settings/           # base.py, dev.py, prod.py
│   ├── api/                        # DRF views, serializers, URLs
│   ├── scraper/                    # Crawl & embed scripts
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

# Generate embeddings (768-dim, nomic-embed-text-v1.5)
python backend/scraper/embed.py --semester 2026S

# Or use the helper script
./backend/embed.sh 2026S
```

## Tech Stack

- **Backend**: Django 5, DRF, Gunicorn, SQLite + sqlite-vec
- **Frontend**: Next.js 15 (App Router), Tailwind CSS v4, React 19
- **Embeddings**: sentence-transformers (nomic-embed-text-v1.5, 768-dim)
- **Vector Search**: sqlite-vec (all environments — dev and prod)
- **Infra**: Docker Compose with `dev`/`prod` profiles, Nginx reverse proxy

## Resource Requirements

Docker images (approximate sizes):

| Container | Size |
|-----------|------|
| Backend | ~1.5 GB (includes CPU-only PyTorch + sentence-transformers) |
| Frontend | ~300 MB (production standalone) / ~500 MB (dev) |
| Nginx | ~25 MB |

Total disk: ~2 GB for dev profile, ~2 GB for prod profile.
RAM: ~500 MB (frontend) + ~1 GB (backend, mainly for model loading).

## Data

Pre-crawled databases are available on IPFS for offline use or self-hosting. See [docs/ipfs.md](docs/ipfs.md).

## License

AGPLv3 — Free to use, modify, and distribute. Contributions must be contributed back to the public repository. Not affiliated with ETH Zurich.

## Links

- **Official VVZ**: https://vvz.ethz.ch
