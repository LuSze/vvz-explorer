# Crawler Pipeline

## Overview

The crawler pipeline extracts ETH VVZ course data and generates embeddings for semantic search.

## Components

### 1. VVZ Crawler (`backend/scraper/crawl.py`)

Scrapes the ETH VVZ website for a given semester.

```bash
# FS2026 (Spring 2026)
python backend/scraper/crawl.py --semester 2026S

# HS2026 (Fall 2026)
python backend/scraper/crawl.py --semester 2026W

# Custom output directory
python backend/scraper/crawl.py --semester 2026S --output-dir /tmp/dbs
```

**Output:** `data/lectures_<SEMESTER>.db` (e.g., `data/lectures_FS2026.db`)

**Database Schema:**
- `lectures` - Course information
- `lecturers` - Instructor names/URLs
- `lecture_lecturer_link` - Many-to-many
- `study_tracks` - Study programs
- `arrow_one/two/three_categories` - Category hierarchy (3 levels)
- `lecture_category_link` - Links lectures to categories per study track

### 2. Embedding Generator (`backend/scraper/embed.py`)

Generates 768-dim vector embeddings for each lecture's text fields using `nomic-embed-text-v1.5`.

```bash
python backend/scraper/embed.py --semester 2026S
```

**Output:** `data/embeddings_<SEMESTER>.db` with:
- `embeddings` table (BLOB backup)
- `vss_embeddings` virtual table (sqlite-vec for fast k-NN)

### 3. Embedding Helper Script (`backend/embed.sh`)

Convenience script that sets up a virtual environment and runs the embedding pipeline.

```bash
# FS2026 (default)
./backend/embed.sh

# HS2026
./backend/embed.sh 2026W
```

## Usage Flow

```bash
# 1. Crawl VVZ for FS2026
python backend/scraper/crawl.py --semester 2026S

# 2. Generate embeddings (768-dim, nomic-embed-text-v1.5)
python backend/scraper/embed.py --semester 2026S

# 3. Start dev server
docker compose --profile dev up
```

## Database Locations

All databases stored in `data/` (gitignored):
```
data/
├── lectures_FS2026.db
├── embeddings_FS2026.db
├── lectures_HS2026.db
└── embeddings_HS2026.db
```

## Semester Codes

| Code | Display | Description |
|------|---------|-------------|
| 2026S | FS2026 | Frühjahrssemester 2026 |
| 2026W | HS2026 | Herbstsemester 2026 |
| 2025W | HS2025 | Herbstsemester 2025 |
| 2025S | FS2025 | Frühjahrssemester 2025 |
| 2024W | HS2024 | Herbstsemester 2024 |

## Notes

- The crawler respects rate limits (default 0.3s delay between detail requests)
- Each text field embedded separately for fine-grained search
- sqlite-vec requires the `vec0` extension (loaded at runtime)
- SQLite + sqlite-vec is used in all environments (both dev and prod)