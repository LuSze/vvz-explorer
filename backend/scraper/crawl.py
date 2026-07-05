"""
VVZ course catalog scraper.

Usage:
    python scraper/crawl.py                         # FS2026
    python scraper/crawl.py --semester 2026W        # HS2026
    python scraper/crawl.py --semester 2025W        # WS2025/26
    python scraper/crawl.py --output-dir /tmp/dbs
"""

import argparse
import json
import re
import sqlite3
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.vvz.ethz.ch"

SEMESTER_DISPLAY = {
    "2026S": "FS2026",
    "2026W": "HS2026",
    "2025W": "HS2025",
    "2025S": "FS2025",
    "2024W": "HS2024",
}


def _clean(text):
    if text is None:
        return None
    return text.replace("\xa0", " ").strip()


def count_arrows(row_html):
    soup = BeautifulSoup(row_html, "html.parser")
    return len(soup.find_all("img", {"src": "images/arrow-level-indicator.png"}))


def extract_info_table(soup):
    result = {}
    h1 = soup.find("h1")
    if not h1:
        return result
    table = h1.find_next("table")
    if not table:
        return result
    for tr in table.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) >= 2:
            label = cells[0].get_text(strip=True)
            value = cells[1].get_text(separator="\n", strip=True)
            result[label] = value
    return result


def extract_performance_assessment(soup):
    h3 = soup.find("h3", string=lambda t: t and "Performance assessment" in t)
    if not h3:
        return None
    table = h3.find_next("table")
    if not table:
        return None
    lines = []
    for tr in table.find_all("tr"):
        line = tr.get_text(separator=" ", strip=True)
        if line:
            lines.append(line)
    return " | ".join(lines) if lines else None


def extract_competencies(soup):
    h3 = soup.find("h3", string=lambda t: t and "Catalogue data" in t)
    if not h3:
        return None
    table = h3.find_next("table")
    if not table:
        return None
    for tr in table.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) >= 2 and "Competencies" in cells[0].get_text():
            inner = cells[1].find("table")
            if not inner:
                return None
            competencies = []
            for row in inner.find_all("tr"):
                competencies.append([c.get_text(strip=True) for c in row.find_all(["td", "th"])])
            return json.dumps(competencies, ensure_ascii=False)
    return None


def extract_catalogue_data(soup):
    h3 = soup.find("h3", string=lambda t: t and "Catalogue data" in t)
    if not h3:
        raise Exception("Could not find the 'Catalogue data' header.")
    table = h3.find_next("table")
    if not table:
        return []
    rows = []
    for tr in table.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) == 2:
            label = cells[0].get_text(strip=True)
            if label == "Competencies":
                continue
            value = cells[1].get_text(separator="\n", strip=True)
            rows.append((label, value))
    return rows


def init_db(db_path):
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = OFF")
    for table in [
        "lectures", "lecturers", "lecture_lecturer_link",
        "study_tracks", "arrow_one_categories", "arrow_two_categories",
        "arrow_three_categories", "lecture_category_link",
    ]:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS lectures (
            id INTEGER PRIMARY KEY,
            number TEXT,
            title TEXT,
            url TEXT,
            type TEXT,
            ects TEXT,
            hours TEXT,
            abstract TEXT,
            learning_objective TEXT,
            content TEXT,
            lecture_notes TEXT,
            literature TEXT,
            language TEXT,
            periodicity TEXT,
            competencies TEXT,
            performance_assessment TEXT
        );
        CREATE TABLE IF NOT EXISTS lecturers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            url TEXT
        );
        CREATE TABLE IF NOT EXISTS lecture_lecturer_link (
            lecture_id INTEGER,
            lecturer_id INTEGER,
            FOREIGN KEY (lecture_id) REFERENCES lectures(id),
            FOREIGN KEY (lecturer_id) REFERENCES lecturers(id)
        );
        CREATE TABLE IF NOT EXISTS study_tracks (
            id INTEGER PRIMARY KEY,
            name TEXT
        );
        CREATE TABLE IF NOT EXISTS arrow_one_categories (
            id INTEGER PRIMARY KEY,
            name TEXT
        );
        CREATE TABLE IF NOT EXISTS arrow_two_categories (
            id INTEGER PRIMARY KEY,
            name TEXT
        );
        CREATE TABLE IF NOT EXISTS arrow_three_categories (
            id INTEGER PRIMARY KEY,
            name TEXT
        );
        CREATE TABLE IF NOT EXISTS lecture_category_link (
            lecture_id INTEGER,
            study_tracks_id INTEGER,
            arrow_one_category_id INTEGER,
            arrow_two_category_id INTEGER,
            arrow_three_category_id INTEGER,
            FOREIGN KEY (lecture_id) REFERENCES lectures(id),
            FOREIGN KEY (study_tracks_id) REFERENCES study_tracks(id),
            FOREIGN KEY (arrow_one_category_id) REFERENCES arrow_one_categories(id),
            FOREIGN KEY (arrow_two_category_id) REFERENCES arrow_two_categories(id),
            FOREIGN KEY (arrow_three_category_id) REFERENCES arrow_three_categories(id)
        );
    """)
    conn.commit()
    return conn


def lecture_data_to_database(conn, number, title, url, type_, credits, hours,
                              abstract, learning_objective, content,
                              lecture_notes, literature, language=None,
                              periodicity=None, competencies=None,
                              performance_assessment=None):
    existing = conn.execute(
        "SELECT 1 FROM lectures WHERE number = ?", (number,)
    ).fetchone()
    if existing:
        return
    conn.execute("""
        INSERT INTO lectures (number, title, url, type, ects, hours,
                              abstract, learning_objective, content,
                              lecture_notes, literature, language,
                              periodicity, competencies, performance_assessment)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (number, title, url, type_, credits, hours,
          abstract, learning_objective, content,
          lecture_notes, literature, language,
          periodicity, competencies, performance_assessment))
    conn.commit()


def lecturer_to_database(conn, lecturer_names, lecturer_urls):
    for name, url in zip(lecturer_names, lecturer_urls):
        existing = conn.execute(
            "SELECT 1 FROM lecturers WHERE name = ? AND url = ?", (name, url)
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO lecturers (name, url) VALUES (?, ?)", (name, url)
            )
    conn.commit()


def categories_to_database(conn, study_track, arrow_level_one, arrow_level_two,
                           arrow_level_three):
    mapping = {
        "study_tracks": study_track,
        "arrow_one_categories": arrow_level_one,
        "arrow_two_categories": arrow_level_two,
        "arrow_three_categories": arrow_level_three,
    }
    for table, name in mapping.items():
        if name is None:
            continue
        existing = conn.execute(
            f"SELECT 1 FROM {table} WHERE name = ?", (name,)
        ).fetchone()
        if not existing:
            conn.execute(f"INSERT INTO {table} (name) VALUES (?)", (name,))
    conn.commit()


def _get_or_create_id(conn, table, name):
    if name is None:
        return None
    row = conn.execute(
        f"SELECT id FROM {table} WHERE name = ?", (name,)
    ).fetchone()
    return row["id"] if row else None


def link_lecture_lecturer(conn, number, lecturer_names, lecturer_urls):
    lecture = conn.execute(
        "SELECT id FROM lectures WHERE number = ?", (number,)
    ).fetchone()
    if not lecture:
        return
    lecture_id = lecture["id"]
    conn.row_factory = sqlite3.Row
    for name, url in zip(lecturer_names, lecturer_urls):
        lecturer = conn.execute(
            "SELECT id FROM lecturers WHERE name = ? AND url = ?", (name, url)
        ).fetchone()
        if not lecturer:
            continue
        lecturer_id = lecturer["id"]
        existing = conn.execute(
            "SELECT 1 FROM lecture_lecturer_link WHERE lecture_id = ? AND lecturer_id = ?",
            (lecture_id, lecturer_id),
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO lecture_lecturer_link (lecture_id, lecturer_id) VALUES (?, ?)",
                (lecture_id, lecturer_id),
            )
    conn.commit()


def link_lecture_category(conn, number, study_track, arrow_level_one,
                           arrow_level_two, arrow_level_three):
    lecture = conn.execute(
        "SELECT id FROM lectures WHERE number = ?", (number,)
    ).fetchone()
    if not lecture:
        return
    lecture_id = lecture["id"]
    study_tracks_id = _get_or_create_id(conn, "study_tracks", study_track)
    a1_id = _get_or_create_id(conn, "arrow_one_categories", arrow_level_one)
    a2_id = _get_or_create_id(conn, "arrow_two_categories", arrow_level_two)
    a3_id = _get_or_create_id(conn, "arrow_three_categories", arrow_level_three)

    existing = conn.execute(
        """SELECT 1 FROM lecture_category_link
           WHERE lecture_id = ? AND study_tracks_id = ?
             AND (arrow_one_category_id IS ? OR arrow_one_category_id IS NULL)
             AND (arrow_two_category_id IS ? OR arrow_two_category_id IS NULL)
             AND (arrow_three_category_id IS ? OR arrow_three_category_id IS NULL)""",
        (lecture_id, study_tracks_id, a1_id, a2_id, a3_id),
    ).fetchone()
    if not existing:
        conn.execute(
            """INSERT INTO lecture_category_link
               (lecture_id, study_tracks_id, arrow_one_category_id,
                arrow_two_category_id, arrow_three_category_id)
               VALUES (?, ?, ?, ?, ?)""",
            (lecture_id, study_tracks_id, a1_id, a2_id, a3_id),
        )
    conn.commit()


def fetch_detail(session, lerneinheit_id, semester_code):
    url = (f"{BASE_URL}/Vorlesungsverzeichnis/lerneinheit.view"
           f"?semkez={semester_code}&ansicht=ALLE&lerneinheitId={lerneinheit_id}&lang=en")
    resp = session.get(url, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def extract_lectures(session, soup, semester_code, conn, delay):
    study_track = None
    arrow_level_one = None
    arrow_level_two = None
    arrow_level_three = None
    rows = soup.find_all("tr")
    total = 0

    for row in rows:
        html = str(row)
        classes = row.get("class", [])
        cells = row.find_all("td")

        if "td-separator" in classes:
            continue

        if cells and "td-level" in cells[0].get("class", []):
            n_arrows = count_arrows(html)
            text = _clean(cells[0].get_text(strip=True))
            if n_arrows == 0:
                study_track = text
                arrow_level_one = None
                arrow_level_two = None
                arrow_level_three = None
            elif n_arrows == 1:
                arrow_level_one = text
                arrow_level_two = None
                arrow_level_three = None
            elif n_arrows == 2:
                arrow_level_two = text
                arrow_level_three = None
            elif n_arrows == 3:
                arrow_level_three = text
            continue

        if len(cells) < 6:
            continue

        number = _clean(cells[0].get_text(strip=True))
        title_elem = cells[1].find("a")
        if not title_elem:
            continue
        title = _clean(title_elem.get_text(strip=True))
        type_ = _clean(cells[2].get_text(strip=True))
        credits = _clean(cells[3].get_text(strip=True))
        hours = _clean(cells[4].get_text(strip=True))

        lecturer_links = cells[5].find_all("a")
        lecturer_names = [_clean(a.get_text(strip=True)) for a in lecturer_links]
        lecturer_urls = [
            BASE_URL + a["href"] if a.get("href") else "" for a in lecturer_links
        ]

        lerneinheit_match = re.search(r"lerneinheitId=(\d+)", str(cells[1]))
        detail_url = None
        if lerneinheit_match:
            lerneinheit_id = lerneinheit_match.group(1)
            detail_url = (f"{BASE_URL}/Vorlesungsverzeichnis/lerneinheit.view"
                          f"?semkez={semester_code}&ansicht=ALLE&lerneinheitId={lerneinheit_id}&lang=en")

        abstract = learning_objective = content = None
        lecture_notes = literature = None
        language = periodicity = competencies = performance_assessment = None

        if detail_url:
            try:
                time.sleep(delay)
                detail_soup = fetch_detail(session, lerneinheit_id, semester_code)
                cat_data = extract_catalogue_data(detail_soup)
                for label, value in cat_data:
                    label = label.strip()
                    if label == "Abstract":
                        abstract = _clean(value)
                    elif label == "Learning objective":
                        learning_objective = _clean(value)
                    elif label == "Content":
                        content = _clean(value)
                    elif "Lecture notes" in label:
                        lecture_notes = _clean(value)
                    elif label == "Literature":
                        literature = _clean(value)

                info = extract_info_table(detail_soup)
                for label, value in info.items():
                    if "Periodicity" in label:
                        periodicity = _clean(value)
                    elif "Language" in label or "language" in label:
                        language = _clean(value)

                competencies = extract_competencies(detail_soup)
                performance_assessment = extract_performance_assessment(detail_soup)
            except Exception as e:
                print(f"  Warning: failed to fetch details for {number}: {e}")

        lecture_data_to_database(
            conn, number, title, detail_url, type_, credits, hours,
            abstract, learning_objective, content, lecture_notes, literature,
            language, periodicity, competencies, performance_assessment,
        )
        lecturer_to_database(conn, lecturer_names, lecturer_urls)
        categories_to_database(conn, study_track, arrow_level_one,
                                arrow_level_two, arrow_level_three)
        link_lecture_lecturer(conn, number, lecturer_names, lecturer_urls)
        link_lecture_category(conn, number, study_track, arrow_level_one,
                               arrow_level_two, arrow_level_three)

        print(f"  [{number}] {title} ({type_}, {credits}, {hours})")
        total += 1

    return total


def main():
    parser = argparse.ArgumentParser(description="VVZ course catalog scraper")
    parser.add_argument(
        "--semester", default="2026S",
        help="Semester code (e.g. 2026S, 2026W). Default: 2026S",
    )
    parser.add_argument(
        "--output-dir", default=".",
        help="Directory for output database. Default: current directory",
    )
    parser.add_argument(
        "--delay", type=float, default=0.3,
        help="Seconds between detail page requests. Default: 0.3",
    )
    args = parser.parse_args()

    semester_code = args.semester
    display = SEMESTER_DISPLAY.get(semester_code, f"SEM{semester_code}")
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / f"lectures_{display}.db"

    print(f"Semester: {semester_code} ({display})")
    print(f"Database: {db_path}")

    conn = init_db(db_path)

    first_url = (
        f"{BASE_URL}/Vorlesungsverzeichnis/sucheLehrangebot.view"
        f"?lang=en&search=on&semkez={semester_code}"
        f"&studiengangTyp=&deptId=&studiengangAbschnittId="
        f"&lerneinheititel=&lerneinheitscode=&famname=&rufname="
        f"&wahlinfo=&lehrsprache=&periodizitaet=&kpRange=0%2C999"
        f"&katalogdaten=&_strukturAus=on&search=Search"
    )

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:130.0) Gecko/20100101 Firefox/130.0",
    })

    page_urls = [first_url]
    total_lectures = 0
    page_num = 0

    for url in page_urls:
        page_num += 1
        print(f"\n--- Page {page_num}: {url}")
        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            print(f"  Error fetching page: {e}")
            continue

        count = extract_lectures(session, soup, semester_code, conn, args.delay)
        total_lectures += count
        print(f"  -> {count} lectures on this page")

        next_img = soup.find("img", class_="nextPage")
        if next_img:
            parent_a = next_img.find_parent("a")
            if parent_a and parent_a.get("href"):
                next_url = BASE_URL + parent_a["href"]
                page_urls.append(next_url)
                print(f"  -> next page found")
            else:
                print("  -> No more pages.")
        else:
            print("  -> No more pages.")

    conn.close()
    print(f"\nDone! {total_lectures} total lectures saved to {db_path}")


if __name__ == "__main__":
    main()
