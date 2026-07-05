"""
Generate embeddings for all lectures in a scraped VVZ database.

Reads lectures_FS2026.db (or --semester variant), embeds each non-trivial
text field with all-MiniLM-L6-v2, and writes results into
embeddings_FS2026.db (sqlite-vec virtual table + BLOB backup).

Usage:
    python scraper/embed.py                         # FS2026
    python scraper/embed.py --semester 2026W        # HS2026
    python scraper/embed.py --input-dir /tmp/dbs    # custom location
"""

import argparse
import sqlite3
import time
from pathlib import Path

import numpy as np
import sqlite_vec
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

TEXT_FIELDS = [
    "title",
    "abstract",
    "learning_objective",
    "content",
    "lecture_notes",
    "literature",
    "performance_assessment",
]

SEMESTER_DISPLAY = {
    "2026S": "FS2026",
    "2026W": "HS2026",
    "2025W": "HS2025",
    "2025S": "FS2025",
    "2024W": "HS2024",
}


def has_meaningful_content(text):
    if not text:
        return False
    cleaned = text.replace("\xa0", " ").strip()
    return len(cleaned) >= 20


def clean(text):
    if text is None:
        return None
    return text.replace("\xa0", " ").strip()


def main():
    parser = argparse.ArgumentParser(description="Generate embeddings for VVZ lectures")
    parser.add_argument(
        "--semester", default="2026S",
        help="Semester code (e.g. 2026S, 2026W). Default: 2026S",
    )
    parser.add_argument(
        "--input-dir", default=".",
        help="Directory containing lectures_*.db. Default: current directory",
    )
    parser.add_argument(
        "--batch-size", type=int, default=16,
        help="Lecture batch size for encoding. Default: 16",
    )
    args = parser.parse_args()

    semester_code = args.semester
    display = SEMESTER_DISPLAY.get(semester_code, f"SEM{semester_code}")
    data_dir = Path(args.input_dir).resolve()

    lec_path = data_dir / f"lectures_{display}.db"
    emb_path = data_dir / f"embeddings_{display}.db"

    print(f"Semester: {semester_code} ({display})")
    print(f"Lectures DB: {lec_path}")
    print(f"Embeddings DB: {emb_path}")

    if not lec_path.exists():
        print(f"Error: {lec_path} not found. Run crawl.py first.")
        return

    print(f"Loading model {EMBEDDING_MODEL}...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("Model loaded.")

    lec_conn = sqlite3.connect(str(lec_path))
    lec_conn.row_factory = sqlite3.Row

    emb_conn = sqlite3.connect(str(emb_path))
    emb_conn.enable_load_extension(True)
    sqlite_vec.load(emb_conn)
    emb_conn.enable_load_extension(False)

    emb_conn.execute("DROP TABLE IF EXISTS vss_embeddings")
    emb_conn.execute("DROP TABLE IF EXISTS embeddings")

    emb_conn.execute("""
        CREATE TABLE IF NOT EXISTS embeddings (
            id INTEGER PRIMARY KEY,
            lecture_number TEXT,
            embedding BLOB
        )
    """)
    emb_conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS vss_embeddings USING vec0 (
            id INTEGER PRIMARY KEY,
            lecture_number TEXT,
            embedding float[384]
        )
    """)
    emb_conn.commit()

    cur = lec_conn.execute(
        "SELECT number, title, abstract, learning_objective, content, "
        "lecture_notes, literature, performance_assessment FROM lectures"
    )
    lectures = list(cur.fetchall())
    lectures = list(set(lectures))
    print(f"Loaded {len(lectures)} lectures.")

    batch_size = args.batch_size
    total_embeddings = 0
    start_time = time.time()

    for i in range(0, len(lectures), batch_size):
        batch = lectures[i : i + batch_size]

        texts = []
        lecture_numbers = []

        for row in batch:
            number = row["number"]
            for field in TEXT_FIELDS:
                text = clean(row[field])
                if has_meaningful_content(text):
                    texts.append(text)
                    lecture_numbers.append(number)

        if not texts:
            print(f"  Batch {i // batch_size + 1}: 0 embeddings (no meaningful text)")
            continue

        embeddings = model.encode(texts)

        for lecture_number, embedding in zip(lecture_numbers, embeddings):
            emb_conn.execute(
                "INSERT INTO embeddings (lecture_number, embedding) VALUES (?, ?)",
                (lecture_number, embedding.tobytes()),
            )
            emb_conn.execute(
                "INSERT INTO vss_embeddings (lecture_number, embedding) VALUES (?, ?)",
                (lecture_number, embedding),
            )

        emb_conn.commit()
        total_embeddings += len(texts)

        elapsed = time.time() - start_time
        print(
            f"  Batch {i // batch_size + 1}: {len(texts)} embeddings "
            f"({total_embeddings} total, {elapsed:.0f}s elapsed)"
        )

    lec_conn.close()
    emb_conn.close()

    elapsed = time.time() - start_time
    print(f"\nDone! {total_embeddings} embeddings for {len(lectures)} lectures "
          f"in {elapsed:.0f}s.")
    print(f"Output: {emb_path}")


if __name__ == "__main__":
    main()
