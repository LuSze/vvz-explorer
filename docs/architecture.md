# Architecture Overview

## System Components

```
┌─────────────────┐     ┌──────────────────────┐     ┌──────────────────────────┐
│  Crawler        │────▶│  Embedding Pipeline  │────▶│  Web App (Docker)        │
│  (BeautifulSoup)│     │  (sentence-transformers│     │  ┌────────────────────┐  │
│  → SQLite       │     │   + sqlite-vec)      │     │  │ Django REST + Postgres│  │
└─────────────────┘     └──────────────────────┘     │  │ Next.js 15 + pgvector │  │
                                                     └──────────────────────────┘
```

## Data Flow

1. **Crawler** (`backend/scraper/crawl.py`):
   - Scrapes ETH VVZ tables via BeautifulSoup
   - Handles hierarchical categories (levelIndicator PNG counting, depth 0-3)
   - Cleans `\xa0` (NBSP) → space
   - Outputs SQLite: `lectures_<semester>.db`

2. **Embeddings** (`backend/scraper/embed.py`):
   - Loads `all-MiniLM-L6-v2` (384-dim) via sentence-transformers
   - Embeds each text field separately (title, abstract, content, learning_objective, lecture_notes, literature)
   - Stores in `embeddings_<semester>.db` with sqlite-vec virtual table

3. **Web App**:
   - **Django REST API** (`backend/api/`): Text search, semantic search, autocomplete, category hierarchy
   - **Next.js 15 Frontend** (`frontend/app/`): Search UI, infinite scroll, hover-expand cards, dark mode
   - **PostgreSQL + pgvector** for production vector search

## Search Modes

| Mode | Endpoint | Description |
|------|----------|-------------|
| Text Search | `/api/lectures/?search=` | PostgreSQL full-text search with filters |
| Semantic Search | `/api/search/?q=` | Embed query → k-NN across all lectures |
| Similar Lectures | `/api/lectures/<nr>/similar/` | Lecture number → fetch its embeddings → k-NN per field → aggregate |
| Autocomplete | `/api/suggest/?q=` | Prefix suggestions for tracks, categories, lecturers, titles |

## Category Hierarchy

The VVZ uses separate FK columns per level (not generic junction):
- `LectureCategoryLink.lecture` → `Category` (level 1)
- `LectureCategoryLink.category_l1` → `Category` (level 2)
- `LectureCategoryLink.category_l2` → `Category` (level 3)

Frontend shows breadcrumb trail: Track › L1 › L2 › L3

## Deployment Profiles

- **Dev** (`docker compose --profile dev up`): SQLite, hot reload, CORS=*
- **Prod** (`docker compose --profile prod up -d`): PostgreSQL+pgvector, gunicorn, nginx, TLS