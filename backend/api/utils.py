import sqlite3
import sqlite_vec
import numpy as np
from sentence_transformers import SentenceTransformer
from django.conf import settings

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME, trust_remote_code=True)
    return _model


CROSS_SEMESTER_PARTNER = {
    "2026W": "2026S",
    "2026S": "2025W",
    "2025W": "2025S",
    "2025S": "2024W",
    "2024W": None,
}


def _semester_db_path(semester):
    if semester and semester in settings.SEMESTER_DB_MAP:
        lec, emb = settings.SEMESTER_DB_MAP[semester]
        return settings.DATA_DIR / lec, settings.DATA_DIR / emb
    return settings.LECTURES_DB_PATH, settings.EMBEDDINGS_DB_PATH


def get_lectures_db(semester=None):
    lec_path, _ = _semester_db_path(semester)
    conn = sqlite3.connect(lec_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_embeddings_db(semester=None):
    _, emb_path = _semester_db_path(semester)
    conn = sqlite3.connect(emb_path)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    conn.row_factory = sqlite3.Row
    return conn


def _enrich_lecture(lecture, lec_db, study_track_name=None):
    data = dict(lecture)
    cur = lec_db.execute(
        """
        SELECT l.name, l.url
        FROM lecturers l
        JOIN lecture_lecturer_link ll ON l.id = ll.lecturer_id
        WHERE ll.lecture_id = ?
        """,
        (lecture["id"],),
    )
    data["lecturers"] = [
        {"name": row["name"].replace("\xa0", " "), "url": row["url"]}
        for row in cur.fetchall()
    ]
    for field in ["ects", "hours", "abstract", "learning_objective", "content", "lecture_notes", "literature", "performance_assessment"]:
        if data.get(field):
            data[field] = data[field].replace("\xa0", " ")
    if study_track_name:
        cur = lec_db.execute("""
            SELECT a1.name AS cat1, a2.name AS cat2, a3.name AS cat3
            FROM lecture_category_link lcl
            JOIN study_tracks st ON st.id = lcl.study_tracks_id
            LEFT JOIN arrow_one_categories a1 ON a1.id = lcl.arrow_one_category_id
            LEFT JOIN arrow_two_categories a2 ON a2.id = lcl.arrow_two_category_id
            LEFT JOIN arrow_three_categories a3 ON a3.id = lcl.arrow_three_category_id
            WHERE lcl.lecture_id = ? AND st.name = ?
        """, (lecture["id"], study_track_name))
        cats = []
        for row in cur.fetchall():
            entry = {}
            if row["cat1"]: entry["cat1"] = row["cat1"].replace("\xa0", " ")
            if row["cat2"]: entry["cat2"] = row["cat2"].replace("\xa0", " ")
            if row["cat3"]: entry["cat3"] = row["cat3"].replace("\xa0", " ")
            if entry:
                cats.append(entry)
        data["categories"] = cats
    return data


def search_lectures(query_text, k=20, study_track=None, semester=None, cross_semester=False):
    model = get_model()
    query_embedding = model.encode([query_text], prompt_name="query")

    semesters_to_query = [semester] if semester else [None]
    if cross_semester and semester and semester in CROSS_SEMESTER_PARTNER:
        partner = CROSS_SEMESTER_PARTNER[semester]
        if partner:
            semesters_to_query.append(partner)

    seen = set()
    lectures = []
    default_sem = semester or settings.DEFAULT_SEMESTER

    for sem in semesters_to_query:
        emb_db = get_embeddings_db(semester=sem)
        try:
            results = emb_db.execute(
                """
                SELECT lecture_number, distance
                FROM vss_embeddings
                WHERE embedding MATCH ?
                AND k = ?
                """,
                (query_embedding, k),
            ).fetchall()
        finally:
            emb_db.close()

        lecture_numbers = []
        for row in results:
            num = row["lecture_number"]
            if num not in seen:
                seen.add(num)
                lecture_numbers.append(num)

        if not lecture_numbers:
            continue

        if study_track:
            lec_db = get_lectures_db(semester=sem)
            try:
                placeholders = ",".join("?" for _ in lecture_numbers)
                cur = lec_db.execute(f"""
                    SELECT DISTINCT l.number FROM lectures l
                    JOIN lecture_category_link lcl ON l.id = lcl.lecture_id
                    JOIN study_tracks st ON st.id = lcl.study_tracks_id
                    WHERE st.name = ? AND l.number IN ({placeholders})
                """, [study_track] + lecture_numbers)
                filtered = {row["number"] for row in cur.fetchall()}
                lecture_numbers = [n for n in lecture_numbers if n in filtered]
            finally:
                lec_db.close()

        lec_db = get_lectures_db(semester=sem)
        sem_label = sem or default_sem
        try:
            for num in lecture_numbers:
                cur = lec_db.execute("SELECT * FROM lectures WHERE number = ?", (num,))
                lecture = cur.fetchone()
                if lecture:
                    enriched = _enrich_lecture(lecture, lec_db)
                    enriched["semester"] = sem_label
                    lectures.append(enriched)
        finally:
            lec_db.close()

    return lectures


def similar_lectures(number, k=20, max_results=10, semester=None):
    emb_db = get_embeddings_db(semester=semester)
    try:
        embeddings = emb_db.execute(
            "SELECT embedding FROM embeddings WHERE lecture_number = ?",
            (number,),
        ).fetchall()
    finally:
        emb_db.close()

    if not embeddings:
        return None

    emb_db = get_embeddings_db(semester=semester)
    try:
        similar_numbers = set()
        for row in embeddings:
            emb_array = np.frombuffer(row["embedding"], dtype=np.float32)
            results = emb_db.execute(
                """
                SELECT lecture_number, distance
                FROM vss_embeddings
                WHERE embedding MATCH ?
                AND k = ?
                """,
                (emb_array, k),
            ).fetchall()
            for r in results:
                if r["lecture_number"] != number:
                    similar_numbers.add(r["lecture_number"])
    finally:
        emb_db.close()

    lec_db = get_lectures_db(semester=semester)
    try:
        lectures = []
        for num in list(similar_numbers)[:max_results]:
            cur = lec_db.execute("SELECT * FROM lectures WHERE number = ?", (num,))
            lecture = cur.fetchone()
            if lecture:
                lectures.append(_enrich_lecture(lecture, lec_db))
    finally:
        lec_db.close()

    return lectures


def get_lecture_by_number(number, semester=None):
    lec_db = get_lectures_db(semester=semester)
    try:
        cur = lec_db.execute("SELECT * FROM lectures WHERE number = ?", (number,))
        lecture = cur.fetchone()
        if not lecture:
            return None
        return _enrich_lecture(lecture, lec_db)
    finally:
        lec_db.close()


FIELD_MAP = {
    "title": "l.title",
    "number": "l.number",
    "lecturer": "lec.name",
    "abstract": "l.abstract",
    "content": "l.content",
    "learning_objective": "l.learning_objective",
    "lecture_notes": "l.lecture_notes",
    "literature": "l.literature",
    "performance_assessment": "l.performance_assessment",
}

def list_lectures(search=None, study_track=None, fields=None, page=1, page_size=50, semester=None, level1_id=None, level2_id=None, level3_id=None):
    lec_db = get_lectures_db(semester=semester)
    try:
        joins = "FROM lectures l"
        conditions = []
        params = []
        count_params = []

        needs_lecturer = False
        if fields:
            selected = [f.strip() for f in fields.split(",") if f.strip() in FIELD_MAP]
            needs_lecturer = "lecturer" in selected
        else:
            needs_lecturer = True

        needs_category_join = bool(study_track or level1_id is not None or level2_id is not None or level3_id is not None)

        if needs_lecturer or search:
            joins += " LEFT JOIN lecture_lecturer_link ll ON l.id = ll.lecture_id"
            joins += " LEFT JOIN lecturers lec ON lec.id = ll.lecturer_id"

        if search:
            if fields:
                cols = [FIELD_MAP[f] for f in selected if f != "lecturer"]
                if needs_lecturer:
                    cols.append("lec.name")
                if not cols:
                    cols = ["l.title", "lec.name"]
            else:
                cols = [
                    "l.title", "l.number", "l.abstract", "l.content",
                    "l.learning_objective", "l.lecture_notes", "l.literature",
                    "l.performance_assessment",
                    "lec.name",
                ]
            words = [w for w in search.split() if len(w) > 2]
            if not words:
                words = [search]
            for word in words:
                clause = " OR ".join(f"{c} LIKE ?" for c in cols)
                conditions.append(f"({clause})")
                p = f"%{word}%"
                params.extend([p] * len(cols))
                count_params.extend([p] * len(cols))

        if needs_category_join:
            joins += " LEFT JOIN lecture_category_link lcl ON l.id = lcl.lecture_id"
            joins += " LEFT JOIN study_tracks st ON st.id = lcl.study_tracks_id"

        if study_track:
            conditions.append("st.name = ?")
            params.append(study_track)
            count_params.append(study_track)

        if level1_id is not None:
            conditions.append("lcl.arrow_one_category_id = ?")
            params.append(level1_id)
            count_params.append(level1_id)

        if level2_id is not None:
            conditions.append("lcl.arrow_two_category_id = ?")
            params.append(level2_id)
            count_params.append(level2_id)

        if level3_id is not None:
            conditions.append("lcl.arrow_three_category_id = ?")
            params.append(level3_id)
            count_params.append(level3_id)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        count_row = lec_db.execute(f"SELECT COUNT(DISTINCT l.id) as total {joins} {where}", count_params).fetchone()
        total = count_row["total"] if count_row else 0

        offset = (page - 1) * page_size
        query = f"SELECT DISTINCT l.* {joins} {where} LIMIT ? OFFSET ?"
        params.extend([page_size, offset])
        cur = lec_db.execute(query, params)
        return [_enrich_lecture(row, lec_db, study_track) for row in cur.fetchall()], total
    finally:
        lec_db.close()


def list_study_tracks(semester=None):
    lec_db = get_lectures_db(semester=semester)
    try:
        cur = lec_db.execute(
            "SELECT DISTINCT st.name FROM study_tracks st "
            "JOIN lecture_category_link lcl ON st.id = lcl.study_tracks_id "
            "WHERE st.name NOT LIKE '%\n%' AND st.name NOT LIKE '»%' "
            "ORDER BY st.name"
        )
        return [row["name"] for row in cur.fetchall()]
    finally:
        lec_db.close()


def _clean(s):
    return s.replace("\xa0", " ") if s else s


def list_level1_categories(study_track, semester=None):
    lec_db = get_lectures_db(semester=semester)
    try:
        cur = lec_db.execute("""
            SELECT DISTINCT a1.id, a1.name
            FROM arrow_one_categories a1
            JOIN lecture_category_link lcl ON a1.id = lcl.arrow_one_category_id
            JOIN study_tracks st ON st.id = lcl.study_tracks_id
            WHERE st.name = ?
            ORDER BY a1.name
        """, (study_track,))
        return [{"id": row["id"], "name": _clean(row["name"])} for row in cur.fetchall()]
    finally:
        lec_db.close()


def list_level2_categories(study_track, level1_id, semester=None):
    lec_db = get_lectures_db(semester=semester)
    try:
        cur = lec_db.execute("""
            SELECT DISTINCT a2.id, a2.name
            FROM arrow_two_categories a2
            JOIN lecture_category_link lcl ON a2.id = lcl.arrow_two_category_id
            JOIN study_tracks st ON st.id = lcl.study_tracks_id
            WHERE st.name = ? AND lcl.arrow_one_category_id = ?
            ORDER BY a2.name
        """, (study_track, level1_id))
        return [{"id": row["id"], "name": _clean(row["name"])} for row in cur.fetchall()]
    finally:
        lec_db.close()


def list_level3_categories(study_track, level1_id, level2_id, semester=None):
    lec_db = get_lectures_db(semester=semester)
    try:
        cur = lec_db.execute("""
            SELECT DISTINCT a3.id, a3.name
            FROM arrow_three_categories a3
            JOIN lecture_category_link lcl ON a3.id = lcl.arrow_three_category_id
            JOIN study_tracks st ON st.id = lcl.study_tracks_id
            WHERE st.name = ? AND lcl.arrow_one_category_id = ? AND lcl.arrow_two_category_id = ?
            ORDER BY a3.name
        """, (study_track, level1_id, level2_id))
        return [{"id": row["id"], "name": _clean(row["name"])} for row in cur.fetchall()]
    finally:
        lec_db.close()


def get_category_tree(study_track, semester=None):
    lec_db = get_lectures_db(semester=semester)
    try:
        cur = lec_db.execute("""
            SELECT DISTINCT a1.id AS l1_id, a1.name AS l1_name,
                            a2.id AS l2_id, a2.name AS l2_name,
                            a3.id AS l3_id, a3.name AS l3_name
            FROM lecture_category_link lcl
            JOIN study_tracks st ON st.id = lcl.study_tracks_id
            LEFT JOIN arrow_one_categories a1 ON a1.id = lcl.arrow_one_category_id
            LEFT JOIN arrow_two_categories a2 ON a2.id = lcl.arrow_two_category_id
            LEFT JOIN arrow_three_categories a3 ON a3.id = lcl.arrow_three_category_id
            WHERE st.name = ?
            ORDER BY a1.name, a2.name, a3.name
        """, (study_track,))

        tree = []
        seen_l1 = {}

        for row in cur.fetchall():
            l1_id = row["l1_id"]
            if not l1_id:
                continue
            l1_name = _clean(row["l1_name"])
            l2_id = row["l2_id"]
            l2_name = _clean(row["l2_name"]) if row["l2_name"] else ""
            l3_id = row["l3_id"]
            l3_name = _clean(row["l3_name"]) if row["l3_name"] else ""

            if l1_id not in seen_l1:
                seen_l1[l1_id] = {"id": l1_id, "name": l1_name, "children": []}
                tree.append(seen_l1[l1_id])

            if l2_id:
                l1_node = seen_l1[l1_id]
                l2_node = next((c for c in l1_node["children"] if c["id"] == l2_id), None)
                if not l2_node:
                    l2_node = {"id": l2_id, "name": l2_name, "children": []}
                    l1_node["children"].append(l2_node)

                if l3_id:
                    if not any(c["id"] == l3_id for c in l2_node["children"]):
                        l2_node["children"].append({"id": l3_id, "name": l3_name})

        return tree
    finally:
        lec_db.close()


def smart_suggest(query, limit=8, semester=None):
    lec_db = get_lectures_db(semester=semester)
    try:
        results = []
        q = f"%{query}%"

        cur = lec_db.execute(
            "SELECT DISTINCT name FROM study_tracks WHERE name LIKE ? AND name NOT LIKE '%\n%' AND name NOT LIKE '»%' LIMIT ?",
            (q, limit),
        )
        for row in cur.fetchall():
            results.append({"type": "study_track", "value": _clean(row["name"])})

        if len(results) >= limit * 3:
            return results[: limit * 3]

        cur = lec_db.execute(
            """SELECT DISTINCT a1.id, a1.name, st.name AS study_track
               FROM arrow_one_categories a1
               JOIN lecture_category_link lcl ON a1.id = lcl.arrow_one_category_id
               JOIN study_tracks st ON st.id = lcl.study_tracks_id
               WHERE a1.name LIKE ? AND st.name NOT LIKE '%\n%' AND st.name NOT LIKE '»%'
               LIMIT ?""",
            (q, limit),
        )
        for row in cur.fetchall():
            name = _clean(row["name"])
            track = _clean(row["study_track"])
            results.append({
                "type": "category_l1",
                "id": row["id"],
                "value": name,
                "study_track": track,
                "breadcrumb": [track, name],
            })

        cur = lec_db.execute(
            """SELECT DISTINCT a2.id, a2.name, st.name AS study_track,
                      a1.id AS l1_id, a1.name AS l1_name
               FROM arrow_two_categories a2
               JOIN lecture_category_link lcl ON a2.id = lcl.arrow_two_category_id
               JOIN study_tracks st ON st.id = lcl.study_tracks_id
               JOIN arrow_one_categories a1 ON a1.id = lcl.arrow_one_category_id
               WHERE a2.name LIKE ? AND st.name NOT LIKE '%\n%' AND st.name NOT LIKE '»%'
               LIMIT ?""",
            (q, limit),
        )
        for row in cur.fetchall():
            name = _clean(row["name"])
            track = _clean(row["study_track"])
            l1_name = _clean(row["l1_name"])
            results.append({
                "type": "category_l2",
                "id": row["id"],
                "value": name,
                "study_track": track,
                "breadcrumb": [track, l1_name, name],
                "level1_id": row["l1_id"],
                "level1_name": l1_name,
            })

        cur = lec_db.execute(
            """SELECT DISTINCT a3.id, a3.name, st.name AS study_track,
                      a1.id AS l1_id, a1.name AS l1_name,
                      a2.id AS l2_id, a2.name AS l2_name
               FROM arrow_three_categories a3
               JOIN lecture_category_link lcl ON a3.id = lcl.arrow_three_category_id
               JOIN study_tracks st ON st.id = lcl.study_tracks_id
               JOIN arrow_one_categories a1 ON a1.id = lcl.arrow_one_category_id
               JOIN arrow_two_categories a2 ON a2.id = lcl.arrow_two_category_id
               WHERE a3.name LIKE ? AND st.name NOT LIKE '%\n%' AND st.name NOT LIKE '»%'
               LIMIT ?""",
            (q, limit),
        )
        for row in cur.fetchall():
            name = _clean(row["name"])
            track = _clean(row["study_track"])
            l1_name = _clean(row["l1_name"])
            l2_name = _clean(row["l2_name"])
            results.append({
                "type": "category_l3",
                "id": row["id"],
                "value": name,
                "study_track": track,
                "breadcrumb": [track, l1_name, l2_name, name],
                "level1_id": row["l1_id"],
                "level1_name": l1_name,
                "level2_id": row["l2_id"],
                "level2_name": l2_name,
            })

        cur = lec_db.execute(
            "SELECT DISTINCT name FROM lecturers WHERE name LIKE ? LIMIT ?",
            (q, limit),
        )
        for row in cur.fetchall():
            results.append({"type": "lecturer", "value": _clean(row["name"])})

        cur = lec_db.execute(
            "SELECT DISTINCT number FROM lectures WHERE number LIKE ? LIMIT ?",
            (q, limit),
        )
        for row in cur.fetchall():
            results.append({"type": "course_number", "value": row["number"]})

        cur = lec_db.execute(
            "SELECT DISTINCT title FROM lectures WHERE title LIKE ? LIMIT ?",
            (q, limit),
        )
        for row in cur.fetchall():
            results.append({"type": "course_title", "value": _clean(row["title"])})

        return results[: limit * 3]
    finally:
        lec_db.close()


def resolve_category_path(study_track, level, category_id, semester=None):
    """Resolve the ancestor chain for a category at any level.
    level=1 → just the category itself
    level=2 → its level-1 parent + itself
    level=3 → its level-1 and level-2 parents + itself
    """
    lec_db = get_lectures_db(semester=semester)
    try:
        if level == 1:
            cur = lec_db.execute(
                "SELECT id, name FROM arrow_one_categories WHERE id = ?", (category_id,)
            )
            row = cur.fetchone()
            if not row:
                return None
            return {"level1": {"id": row["id"], "name": _clean(row["name"])}}

        if level == 2:
            cur = lec_db.execute("""
                SELECT DISTINCT a1.id AS l1_id, a1.name AS l1_name,
                                a2.id AS l2_id, a2.name AS l2_name
                FROM lecture_category_link lcl
                JOIN study_tracks st ON st.id = lcl.study_tracks_id
                JOIN arrow_one_categories a1 ON a1.id = lcl.arrow_one_category_id
                JOIN arrow_two_categories a2 ON a2.id = lcl.arrow_two_category_id
                WHERE st.name = ? AND a2.id = ?
                LIMIT 1
            """, (study_track, category_id))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "level1": {"id": row["l1_id"], "name": _clean(row["l1_name"])},
                "level2": {"id": row["l2_id"], "name": _clean(row["l2_name"])},
            }

        if level == 3:
            cur = lec_db.execute("""
                SELECT DISTINCT a1.id AS l1_id, a1.name AS l1_name,
                                a2.id AS l2_id, a2.name AS l2_name,
                                a3.id AS l3_id, a3.name AS l3_name
                FROM lecture_category_link lcl
                JOIN study_tracks st ON st.id = lcl.study_tracks_id
                JOIN arrow_one_categories a1 ON a1.id = lcl.arrow_one_category_id
                JOIN arrow_two_categories a2 ON a2.id = lcl.arrow_two_category_id
                JOIN arrow_three_categories a3 ON a3.id = lcl.arrow_three_category_id
                WHERE st.name = ? AND a3.id = ?
                LIMIT 1
            """, (study_track, category_id))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "level1": {"id": row["l1_id"], "name": _clean(row["l1_name"])},
                "level2": {"id": row["l2_id"], "name": _clean(row["l2_name"])},
                "level3": {"id": row["l3_id"], "name": _clean(row["l3_name"])},
            }

        return None
    finally:
        lec_db.close()


def get_offered_in(lecture_id, semester=None):
    lec_db = get_lectures_db(semester=semester)
    try:
        cur = lec_db.execute("""
            SELECT st.name AS programme,
                   a1.id AS section_id, a1.name AS section,
                   a2.id AS sub_section_id, a2.name AS sub_section
            FROM lecture_category_link lcl
            JOIN study_tracks st ON st.id = lcl.study_tracks_id
            LEFT JOIN arrow_one_categories a1 ON a1.id = lcl.arrow_one_category_id
            LEFT JOIN arrow_two_categories a2 ON a2.id = lcl.arrow_two_category_id
            WHERE lcl.lecture_id = ?
            ORDER BY st.name, a1.name, a2.name
        """, (lecture_id,))

        offered_in = []
        seen = set()
        for row in cur.fetchall():
            key = (row["programme"], row["section"] or "", row["sub_section"] or "")
            if key in seen:
                continue
            seen.add(key)
            entry = {"programme": _clean(row["programme"])}
            if row["section"]:
                entry["section_id"] = row["section_id"]
                entry["section"] = _clean(row["section"])
            if row["sub_section"]:
                entry["sub_section_id"] = row["sub_section_id"]
                entry["sub_section"] = _clean(row["sub_section"])
            offered_in.append(entry)
        return offered_in
    finally:
        lec_db.close()
