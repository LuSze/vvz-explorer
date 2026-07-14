"""
Re-embed lectures using nomic-ai/nomic-embed-text-v1.5 (768-dim).
Reads from data/lectures_<SEM>.db, writes to data/embeddings_<SEM>.db.
"""
import json
import os
import sys
from pathlib import Path

from sentence_transformers import SentenceTransformer
import sqlite3
import sqlite_vec

from scraper.embed import TEXT_FIELDS, clean, has_meaningful_content

MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5"
BATCH_SIZE = 16

SEMESTER_DISPLAY = {
    "2026S": "FS2026",
    "2026W": "HS2026",
    "2025W": "HS2025",
    "2025S": "FS2025",
    "2024W": "HS2024",
}

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def reembed(semester_code, lectures_path, embeddings_path):
    display = SEMESTER_DISPLAY.get(semester_code, f"SEM{semester_code}")
    print(f"\n=== {semester_code} ({display}) ===")

    lec_conn = sqlite3.connect(str(lectures_path))
    lec_conn.row_factory = sqlite3.Row

    emb_conn = sqlite3.connect(str(embeddings_path))
    emb_conn.enable_load_extension(True)
    sqlite_vec.load(emb_conn)
    emb_conn.enable_load_extension(False)

    emb_conn.execute("DROP TABLE IF EXISTS vss_embeddings")
    emb_conn.execute("DROP TABLE IF EXISTS embeddings")
    emb_conn.execute("""CREATE TABLE IF NOT EXISTS embeddings (
        id INTEGER PRIMARY KEY,
        lecture_number TEXT,
        embedding BLOB
    )""")
    emb_conn.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS vss_embeddings USING vec0 (
        id INTEGER PRIMARY KEY,
        lecture_number TEXT,
        embedding float[768]
    )""")

    cur = lec_conn.execute(
        "SELECT number, title, abstract, learning_objective, content, "
        "lecture_notes, literature, performance_assessment FROM lectures"
    )
    lectures = list(set(cur.fetchall()))
    print(f"Total unique lectures: {len(lectures)}")

    model = SentenceTransformer(MODEL_NAME, trust_remote_code=True)
    print(f"Model loaded. Max tokens: {model.max_seq_length}")

    for i in range(0, len(lectures), BATCH_SIZE):
        batch = lectures[i : i + BATCH_SIZE]
        texts = []
        lecture_numbers = []

        for lecture in batch:
            number = lecture["number"]
            for field in TEXT_FIELDS:
                value = lecture[field]
                if field == "performance_assessment" and value:
                    try:
                        parsed = json.loads(value)
                        if isinstance(parsed, dict):
                            text = ". ".join(f"{k}: {v}" for k, v in parsed.items())
                        else:
                            text = str(parsed)
                    except (json.JSONDecodeError, TypeError):
                        text = value
                else:
                    text = value
                text = clean(text)
                if has_meaningful_content(text):
                    texts.append(text)
                    lecture_numbers.append(number)

        if not texts:
            continue

        print(f"  Batch {i // BATCH_SIZE + 1}: encoding {len(texts)} texts", flush=True)
        embeddings = model.encode(texts, prompt_name="document", show_progress_bar=False)

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
        print(f"  Batch {i // BATCH_SIZE + 1}/{(len(lectures) + BATCH_SIZE - 1) // BATCH_SIZE} done", flush=True)

    lec_conn.close()
    emb_conn.close()

    print(f"Done. {embeddings_path} written.")


if __name__ == "__main__":
    for sem_code in SEMESTER_DISPLAY.keys():
        display = SEMESTER_DISPLAY[sem_code]
        lec_path = DATA_DIR / f"lectures_{display}.db"
        emb_path = DATA_DIR / f"embeddings_{display}.db"
        if lec_path.exists():
            reembed(sem_code, lec_path, emb_path)
        else:
            print(f"Skipping {sem_code}: {lec_path} not found")