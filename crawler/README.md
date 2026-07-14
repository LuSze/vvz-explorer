# Archived Crawler Notebooks

These Jupyter notebooks contain the original crawlers and embedding pipelines. They are **archived for reference only** and not used in production.

## Active Pipeline

The crawler and embedding pipeline has been extracted to Django management commands in `../app/backend/scraper/management/commands/`:

```bash
# Crawl VVZ
python manage.py crawl_vvz --semester 2026S

# Import lectures to PostgreSQL
python manage.py import_lectures --sqlite-path /path/to/lectures.db

# Generate embeddings
python manage.py generate_embeddings --semester 2026S
```

## Notebooks (Read-Only)

| Notebook | Purpose |
|----------|---------|
| `VVZ_crawler.ipynb` | Scrapes ETH VVZ tables via BeautifulSoup → SQLite |
| `getting_embedding_from_db.ipynb` | Generates embeddings (sentence-transformers) → sqlite-vec |
| `database_explorer.ipynb` | Ad-hoc DB exploration queries |

## Notes

- Notebooks reference paths relative to the old project structure
- They use `sqlite-vec` (vec0 extension) for vector search
- Production uses PostgreSQL + pgvector instead
- See `../docs/crawler-pipeline.md` for detailed documentation