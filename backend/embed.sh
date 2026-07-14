#!/usr/bin/env bash
set -e

# Usage: ./embed.sh [semester]
# Semesters: 2026S (FS2026), 2026W (HS2026), 2025W, 2025S, 2024W
# Default: 2026S (FS2026)

SEMESTER="${1:-2026S}"
SEM_DISPLAY=""

case "$SEMESTER" in
  2026S) SEM_DISPLAY="FS2026" ;;
  2026W) SEM_DISPLAY="HS2026" ;;
  2025W) SEM_DISPLAY="HS2025" ;;
  2025S) SEM_DISPLAY="FS2025" ;;
  2024W) SEM_DISPLAY="HS2024" ;;
  *) echo "Unknown semester: $SEMESTER"; exit 1 ;;
esac

echo "=== Generating embeddings for $SEMESTER ($SEM_DISPLAY) ==="

# Install deps into a temporary venv
python3 -m venv /tmp/embed-nomic
source /tmp/embed-nomic/bin/activate

# CPU-only torch
pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu || \
  pip install --no-cache-dir torch

pip install --no-cache-dir sentence-transformers sqlite-vec einops

# Point to the DB files in the data directory (repo root)
cd "$(dirname "$0")/../.."

LEC_DB="data/lectures_${SEM_DISPLAY}.db"
EMB_DB="data/embeddings_${SEM_DISPLAY}.db"

if [ ! -f "$LEC_DB" ]; then
    echo "Error: $LEC_DB not found. Run crawl.py first."
    exit 1
fi

echo "Using lectures DB: $LEC_DB"
echo "Writing embeddings to: $EMB_DB"

# Remove old embeddings DB
rm -f "$EMB_DB"

python -u app/backend/scraper/embed.py --semester "$SEMESTER" --input-dir data

deactivate
echo "Done! You can now docker compose up as usual."