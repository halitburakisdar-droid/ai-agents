"""
Hafıza Sistemi — SQLite Database
4 tablo: content_archive, decisions, metrics, learned_patterns
"""

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "agent_memory.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS content_archive (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp       TEXT NOT NULL,
        gold_price      REAL,
        silver_price    REAL,
        gold_change     REAL,
        silver_change   REAL,
        alarm_count     INTEGER DEFAULT 0,
        trend           TEXT,
        confidence      TEXT,
        recommendation  TEXT,
        analysis        TEXT,
        slide1_title    TEXT,
        slide1_text     TEXT,
        slide2_title    TEXT,
        slide2_text     TEXT,
        slide3_title    TEXT,
        slide3_text     TEXT,
        quality_score   INTEGER DEFAULT 0,
        qc_decision     TEXT,
        qc_feedback     TEXT
    );

    CREATE TABLE IF NOT EXISTS decisions (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp       TEXT NOT NULL,
        content_id      INTEGER REFERENCES content_archive(id),
        orchestrator    TEXT DEFAULT 'Claude Opus 4.6',
        decision        TEXT,
        reasoning       TEXT,
        cycle_number    INTEGER
    );

    CREATE TABLE IF NOT EXISTS metrics (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp       TEXT NOT NULL,
        cycle_number    INTEGER,
        price_time      REAL,
        research_time   REAL,
        content_time    REAL,
        quality_time    REAL,
        total_time      REAL,
        quality_score   INTEGER,
        had_alarm       INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS learned_patterns (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp       TEXT NOT NULL,
        pattern_type    TEXT,
        description     TEXT,
        confidence      REAL,
        source_cycles   TEXT,
        applied_count   INTEGER DEFAULT 0
    );
    """)

    conn.commit()
    conn.close()
    print(f"  DB hazır: {DB_PATH}")


def save_content(data: dict) -> int:
    conn = get_conn()
    c = conn.cursor()
    p = data.get("price", {})
    r = data.get("research", {})
    cont = data.get("content", {})
    q = data.get("quality", {})
    slides = cont.get("slides", {})

    c.execute("""
        INSERT INTO content_archive (
            timestamp, gold_price, silver_price, gold_change, silver_change,
            alarm_count, trend, confidence, recommendation, analysis,
            slide1_title, slide1_text, slide2_title, slide2_text,
            slide3_title, slide3_text, quality_score, qc_decision, qc_feedback
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        datetime.now().isoformat(),
        p.get("prices", {}).get("gold"),
        p.get("prices", {}).get("silver"),
        p.get("changes", {}).get("gold"),
        p.get("changes", {}).get("silver"),
        p.get("alarm_count", 0),
        r.get("trend"), r.get("guven"), r.get("tavsiye"), r.get("analiz"),
        slides.get("slide_1", {}).get("baslik"), slides.get("slide_1", {}).get("metin"),
        slides.get("slide_2", {}).get("baslik"), slides.get("slide_2", {}).get("metin"),
        slides.get("slide_3", {}).get("baslik"), slides.get("slide_3", {}).get("metin"),
        q.get("skor", 0), q.get("karar"), q.get("guclu"),
    ))
    row_id = c.lastrowid
    conn.commit()
    conn.close()
    return row_id


def save_decision(content_id: int, decision: str, reasoning: str, cycle: int):
    conn = get_conn()
    conn.execute("""
        INSERT INTO decisions (timestamp, content_id, decision, reasoning, cycle_number)
        VALUES (?,?,?,?,?)
    """, (datetime.now().isoformat(), content_id, decision, reasoning, cycle))
    conn.commit()
    conn.close()


def save_metrics(data: dict):
    conn = get_conn()
    conn.execute("""
        INSERT INTO metrics (
            timestamp, cycle_number, price_time, research_time,
            content_time, quality_time, total_time, quality_score, had_alarm
        ) VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        datetime.now().isoformat(),
        data.get("cycle"), data.get("price_time", 0),
        data.get("research_time", 0), data.get("content_time", 0),
        data.get("quality_time", 0), data.get("total_time", 0),
        data.get("quality_score", 0), int(data.get("had_alarm", False)),
    ))
    conn.commit()
    conn.close()


def save_pattern(pattern_type: str, description: str, confidence: float, source: str):
    conn = get_conn()
    conn.execute("""
        INSERT INTO learned_patterns (timestamp, pattern_type, description, confidence, source_cycles)
        VALUES (?,?,?,?,?)
    """, (datetime.now().isoformat(), pattern_type, description, confidence, source))
    conn.commit()
    conn.close()


def get_stats() -> dict:
    conn = get_conn()
    c = conn.cursor()

    total   = c.execute("SELECT COUNT(*) FROM content_archive").fetchone()[0]
    avg_q   = c.execute("SELECT AVG(quality_score) FROM content_archive WHERE quality_score > 0").fetchone()[0]
    publish = c.execute("SELECT COUNT(*) FROM decisions WHERE decision LIKE '%YAYINLA%'").fetchone()[0]
    revise  = c.execute("SELECT COUNT(*) FROM decisions WHERE decision LIKE '%REVİZE%'").fetchone()[0]
    patterns= c.execute("SELECT COUNT(*) FROM learned_patterns").fetchone()[0]
    last5   = c.execute("""
        SELECT trend, quality_score, gold_change, silver_change
        FROM content_archive ORDER BY id DESC LIMIT 5
    """).fetchall()

    conn.close()
    return {
        "total_cycles": total,
        "avg_quality":  round(avg_q, 1) if avg_q else 0,
        "publish_count": publish,
        "revise_count":  revise,
        "pattern_count": patterns,
        "last5": [dict(r) for r in last5],
    }


def get_recent_for_learning(limit: int = 20) -> list:
    conn = get_conn()
    rows = conn.execute("""
        SELECT ca.*, d.decision
        FROM content_archive ca
        LEFT JOIN decisions d ON d.content_id = ca.id
        ORDER BY ca.id DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
