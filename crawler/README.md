# Archived Crawler Notebooks

These Jupyter notebooks contain the original crawlers and embedding pipelines. They are **archived for reference only** and not used in production.

## Active Pipeline

The crawler and embedding pipeline is now simple Python scripts in `../backend/scraper/`:

```bash
# Crawl VVZ
python ../backend/scraper/crawl.py --semester 2026S

# Generate embeddings
python ../backend/scraper/embed.py --semester 2026S

# Re-embed with Nomic (768-dim)
python ../backend/reembed.py
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