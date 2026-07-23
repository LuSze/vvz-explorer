"""
Measurement harness for the database index change.

Measures the three core read paths from backend/api/utils.py before and after
the indexes are applied to the *same* file:

  list_lectures(study_track=...)   the four way LEFT JOIN + count
  get_lecture_by_number(number)    WHERE number = ?  (plus lecturer enrich)
  _enrich_lecture(..., track)      lecturer subquery + category subquery

Reports: EXPLAIN QUERY PLAN before and after, median wall time, file size
growth. Does not touch application code.

Two modes:
  python docs/bench_indexes.py                       # synthetic full semester DB
  python docs/bench_indexes.py --db lectures_HS2026.db   # your real DB

--db is nondestructive: it copies the DB to a temp file, drops the indexes
on the copy to measure "before", then adds them back. The original is never
modified.
"""

import argparse
import os
import random
import shutil
import tempfile
import sqlite3
import statistics
import time

random.seed(1234)

DB = os.path.join(tempfile.gettempdir(), "vvz_bench_indexes.db")
RUNS = 50

# sizes: representative of one full ETH VVZ semester listing
N_LECTURES = 8000
N_LECTURERS = 3000
N_TRACKS = 300
N_ARROW1 = 60
N_ARROW2 = 200
N_ARROW3 = 400

# Schema copied verbatim from crawl.py init_db(), WITHOUT the new indexes,
# so "before" is a true database from before the change.
SCHEMA = """
CREATE TABLE lectures (
    id INTEGER PRIMARY KEY, number TEXT, title TEXT, url TEXT, type TEXT,
    ects TEXT, hours TEXT, abstract TEXT, learning_objective TEXT, content TEXT,
    lecture_notes TEXT, literature TEXT, language TEXT, periodicity TEXT,
    competencies TEXT, performance_assessment TEXT
);
CREATE TABLE lecturers (id INTEGER PRIMARY KEY, name TEXT, url TEXT);
CREATE TABLE lecture_lecturer_link (
    lecture_id INTEGER, lecturer_id INTEGER,
    FOREIGN KEY (lecture_id) REFERENCES lectures(id),
    FOREIGN KEY (lecturer_id) REFERENCES lecturers(id)
);
CREATE TABLE study_tracks (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE arrow_one_categories (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE arrow_two_categories (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE arrow_three_categories (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE lecture_category_link (
    lecture_id INTEGER, study_tracks_id INTEGER,
    arrow_one_category_id INTEGER, arrow_two_category_id INTEGER,
    arrow_three_category_id INTEGER,
    FOREIGN KEY (lecture_id) REFERENCES lectures(id),
    FOREIGN KEY (study_tracks_id) REFERENCES study_tracks(id),
    FOREIGN KEY (arrow_one_category_id) REFERENCES arrow_one_categories(id),
    FOREIGN KEY (arrow_two_category_id) REFERENCES arrow_two_categories(id),
    FOREIGN KEY (arrow_three_category_id) REFERENCES arrow_three_categories(id)
);
"""

# Index set applied for "after", identical to crawl.py + add_indexes.py.
INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_lectures_number ON lectures(number)",
    "CREATE INDEX IF NOT EXISTS idx_lll_lecture_id ON lecture_lecturer_link(lecture_id)",
    "CREATE INDEX IF NOT EXISTS idx_lcl_lecture_id ON lecture_category_link(lecture_id)",
    "CREATE INDEX IF NOT EXISTS idx_lcl_study_tracks_id ON lecture_category_link(study_tracks_id)",
    "CREATE INDEX IF NOT EXISTS idx_lcl_arrow_categories ON lecture_category_link"
    "(arrow_one_category_id, arrow_two_category_id, arrow_three_category_id)",
]

# Names only, for stripping the indexes off a real DB copy to measure "before".
INDEX_NAMES = [
    "idx_lectures_number", "idx_lll_lecture_id", "idx_lcl_lecture_id",
    "idx_lcl_study_tracks_id", "idx_lcl_arrow_categories",
]

BLURB = ("Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do "
         "eiusmod tempor incididunt ut labore et dolore magna aliqua. ") * 3


def build():
    if os.path.exists(DB):
        os.remove(DB)
    c = sqlite3.connect(DB)
    c.executescript(SCHEMA)

    lectures = []
    for i in range(1, N_LECTURES + 1):
        num = f"{random.randint(100, 999)}-{i:04d}-{random.randint(0,99):02d}L"
        lectures.append((i, num, f"Lecture {i}", f"https://vvz/{i}", "V",
                         "4", "2G", BLURB, BLURB, BLURB, BLURB, BLURB, "en",
                         "yearly", None, None))
    c.executemany("INSERT INTO lectures VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", lectures)

    c.executemany("INSERT INTO lecturers VALUES (?,?,?)",
                  [(i, f"Prof {i}", f"https://p/{i}") for i in range(1, N_LECTURERS + 1)])
    c.executemany("INSERT INTO study_tracks VALUES (?,?)",
                  [(i, f"Track {i}") for i in range(1, N_TRACKS + 1)])
    c.executemany("INSERT INTO arrow_one_categories VALUES (?,?)",
                  [(i, f"A1 {i}") for i in range(1, N_ARROW1 + 1)])
    c.executemany("INSERT INTO arrow_two_categories VALUES (?,?)",
                  [(i, f"A2 {i}") for i in range(1, N_ARROW2 + 1)])
    c.executemany("INSERT INTO arrow_three_categories VALUES (?,?)",
                  [(i, f"A3 {i}") for i in range(1, N_ARROW3 + 1)])

    ll = []
    for lec in range(1, N_LECTURES + 1):
        for _ in range(random.randint(1, 3)):
            ll.append((lec, random.randint(1, N_LECTURERS)))
    c.executemany("INSERT INTO lecture_lecturer_link VALUES (?,?)", ll)

    lcl = []
    for lec in range(1, N_LECTURES + 1):
        for _ in range(random.randint(1, 5)):
            lcl.append((lec, random.randint(1, N_TRACKS),
                        random.randint(1, N_ARROW1),
                        random.randint(1, N_ARROW2),
                        random.randint(1, N_ARROW3)))
    c.executemany("INSERT INTO lecture_category_link VALUES (?,?,?,?,?)", lcl)

    c.commit()
    c.close()


# the three core paths, replicated verbatim from utils.py

LIST_JOINS = ("FROM lectures l "
              "LEFT JOIN lecture_lecturer_link ll ON l.id = ll.lecture_id "
              "LEFT JOIN lecturers lec ON lec.id = ll.lecturer_id "
              "LEFT JOIN lecture_category_link lcl ON l.id = lcl.lecture_id "
              "LEFT JOIN study_tracks st ON st.id = lcl.study_tracks_id")
LIST_COUNT = f"SELECT COUNT(DISTINCT l.id) as total {LIST_JOINS} WHERE st.name = ?"
LIST_MAIN = f"SELECT DISTINCT l.* {LIST_JOINS} WHERE st.name = ? LIMIT ? OFFSET ?"
ENRICH_LECT = ("SELECT l.name, l.url FROM lecturers l "
               "JOIN lecture_lecturer_link ll ON l.id = ll.lecturer_id "
               "WHERE ll.lecture_id = ?")
ENRICH_CAT = ("SELECT a1.name AS cat1, a2.name AS cat2, a3.name AS cat3 "
              "FROM lecture_category_link lcl "
              "JOIN study_tracks st ON st.id = lcl.study_tracks_id "
              "LEFT JOIN arrow_one_categories a1 ON a1.id = lcl.arrow_one_category_id "
              "LEFT JOIN arrow_two_categories a2 ON a2.id = lcl.arrow_two_category_id "
              "LEFT JOIN arrow_three_categories a3 ON a3.id = lcl.arrow_three_category_id "
              "WHERE lcl.lecture_id = ? AND st.name = ?")
GET_BY_NUMBER = "SELECT * FROM lectures WHERE number = ?"


def op_list(conn, track):
    conn.execute(LIST_COUNT, (track,)).fetchone()
    rows = conn.execute(LIST_MAIN, (track, 50, 0)).fetchall()
    for r in rows:                       # list_lectures enriches every row
        conn.execute(ENRICH_LECT, (r["id"],)).fetchall()
        conn.execute(ENRICH_CAT, (r["id"], track)).fetchall()


def op_get(conn, number):
    row = conn.execute(GET_BY_NUMBER, (number,)).fetchone()
    if row:                              # get_lecture_by_number then enrich (no track)
        conn.execute(ENRICH_LECT, (row["id"],)).fetchall()


def op_enrich(conn, lid, track):
    conn.execute(ENRICH_LECT, (lid,)).fetchall()
    conn.execute(ENRICH_CAT, (lid, track)).fetchall()


def median_ms(fn, args_list):
    # one warmup pass, then RUNS timed iterations rotating through args
    fn(*args_list[0])
    samples = []
    for i in range(RUNS):
        a = args_list[i % len(args_list)]
        t = time.perf_counter()
        fn(*a)
        samples.append((time.perf_counter() - t) * 1000)
    return statistics.median(samples)


def qplan(conn, sql, params):
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
    return [r[3] for r in rows]


def sample_args(conn):
    tracks = [r[0] for r in conn.execute(
        "SELECT name FROM study_tracks ORDER BY id LIMIT 50").fetchall()]
    numbers = [r[0] for r in conn.execute(
        "SELECT number FROM lectures ORDER BY RANDOM() LIMIT 50").fetchall()]
    lids = [r[0] for r in conn.execute(
        "SELECT id FROM lectures ORDER BY RANDOM() LIMIT 50").fetchall()]
    return tracks, numbers, lids


def measure(tag):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    tracks, numbers, lids = sample_args(conn)

    plans = {
        "list_lectures (main join)": qplan(conn, LIST_MAIN, (tracks[0], 50, 0)),
        "get_lecture_by_number": qplan(conn, GET_BY_NUMBER, (numbers[0],)),
        "_enrich_lecture (lecturers)": qplan(conn, ENRICH_LECT, (lids[0],)),
        "_enrich_lecture (categories)": qplan(conn, ENRICH_CAT, (lids[0], tracks[0])),
    }
    times = {
        "list_lectures (study_track)": median_ms(op_list, [(conn, t) for t in tracks]),
        "get_lecture_by_number": median_ms(op_get, [(conn, n) for n in numbers]),
        "_enrich_lecture": median_ms(op_enrich, [(conn, l, tracks[0]) for l in lids]),
    }
    conn.close()
    return plans, times


def prepare_real_db(src):
    # Copy the real DB and strip the indexes so "before" has no indexes.
    # The original file at `src` is never touched.
    shutil.copyfile(src, DB)
    conn = sqlite3.connect(DB)
    for name in INDEX_NAMES:
        conn.execute(f"DROP INDEX IF EXISTS {name}")
    conn.commit()
    conn.close()


def row_counts():
    conn = sqlite3.connect(DB)
    n = lambda t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    out = (n("lectures"), n("lecture_lecturer_link"), n("lecture_category_link"))
    conn.close()
    return out


def main():
    global DB, RUNS
    parser = argparse.ArgumentParser(description="Benchmark the database index change")
    parser.add_argument("--db", help="Path to a real lectures_*.db (nondestructive). "
                                     "Omit to use a synthetic full semester DB.")
    parser.add_argument("--runs", type=int, default=RUNS, help="Timed runs per query (default 50)")
    args = parser.parse_args()
    RUNS = args.runs

    if args.db:
        DB = os.path.join(tempfile.gettempdir(), "vvz_bench_real.db")
        prepare_real_db(args.db)
        source = f"real DB: {args.db} (nondestructive copy)"
    else:
        build()
        source = "synthetic full semester DB"

    size_before = os.path.getsize(DB)
    plans_b, times_b = measure("before")

    conn = sqlite3.connect(DB)
    for stmt in INDEXES:
        conn.execute(stmt)
    conn.commit()
    conn.close()

    size_after = os.path.getsize(DB)
    plans_a, times_a = measure("after")

    lec, ll, lcl = row_counts()
    print("### DB size\n")
    print(f"* source: {source}")
    print(f"* rows: {lec} lectures, {ll} lecturer links, {lcl} category links")
    print(f"* before: {size_before/1024:.0f} KiB")
    print(f"* after:  {size_after/1024:.0f} KiB")
    print(f"* growth: +{(size_after-size_before)/1024:.0f} KiB "
          f"(+{(size_after-size_before)/size_before*100:.1f}%)\n")

    print(f"### Wall time (median of {RUNS} runs)\n")
    print("| Query path | before | after | speedup |")
    print("|:--|--:|--:|--:|")
    for k in times_b:
        b, a = times_b[k], times_a[k]
        print(f"| {k} | {b:.3f} ms | {a:.3f} ms | **{b/a:.1f}×** |")

    print("\n### EXPLAIN QUERY PLAN\n")
    for k in plans_b:
        print(f"**{k}**\n")
        print("_before:_")
        for line in plans_b[k]:
            print(f"    {line}")
        print("\n_after:_")
        for line in plans_a[k]:
            print(f"    {line}")
        print()


if __name__ == "__main__":
    main()
