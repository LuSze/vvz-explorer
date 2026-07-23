"""
Add the database indexes to existing scraped DB files.

New crawls already create these indexes. This script adds them to older
databases that were made before the indexes existed. Running it again does
no harm. Same indexes as crawl.py and embed.py.

Usage:
    python scraper/add_indexes.py --lectures lectures_HS2026.db --embeddings embeddings_HS2026.db
    python scraper/add_indexes.py --lectures lectures_*.db      # one or more paths
"""

import argparse
import sqlite3

LECTURE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_lectures_number ON lectures(number)",
    "CREATE INDEX IF NOT EXISTS idx_lll_lecture_id ON lecture_lecturer_link(lecture_id)",
    "CREATE INDEX IF NOT EXISTS idx_lcl_lecture_id ON lecture_category_link(lecture_id)",
    "CREATE INDEX IF NOT EXISTS idx_lcl_study_tracks_id ON lecture_category_link(study_tracks_id)",
    "CREATE INDEX IF NOT EXISTS idx_lcl_arrow_categories ON lecture_category_link"
    "(arrow_one_category_id, arrow_two_category_id, arrow_three_category_id)",
]

EMBEDDING_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_embeddings_lecture_number ON embeddings(lecture_number)",
]


def apply(db_path, statements):
    conn = sqlite3.connect(db_path)
    for stmt in statements:
        conn.execute(stmt)
    conn.commit()
    conn.close()
    print(f"Indexed {db_path}")


def main():
    parser = argparse.ArgumentParser(description="Add query indexes to existing VVZ databases")
    parser.add_argument("--lectures", nargs="*", default=[], help="lectures_*.db path(s)")
    parser.add_argument("--embeddings", nargs="*", default=[], help="embeddings_*.db path(s)")
    args = parser.parse_args()

    for path in args.lectures:
        apply(path, LECTURE_INDEXES)
    for path in args.embeddings:
        apply(path, EMBEDDING_INDEXES)


if __name__ == "__main__":
    main()
