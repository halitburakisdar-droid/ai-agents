"""
Performance Tracker
===================
Her içerik döngüsünden sonra skor + kararları kaydet.
Hangi prompt versiyonu daha iyi? Bunu takip eder.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent.parent / "agent_memory.db"


def init_tables():
    conn = sqlite3.connect(DB)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS prompt_versions (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp    TEXT,
        agent_name   TEXT,
        version      INTEGER,
        prompt_hash  TEXT,
        prompt_text  TEXT,
        source       TEXT  -- 'original' / 'optimized' / 'ab_test'
    );

    CREATE TABLE IF NOT EXISTS content_performance (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp      TEXT,
        prompt_version INTEGER REFERENCES prompt_versions(id),
        quality_score  REAL,
        viral_score    REAL,
        engagement     TEXT,
        decision       TEXT,
        market_context TEXT,
        content_title  TEXT
    );

    CREATE TABLE IF NOT EXISTS competitor_insights (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp   TEXT,
        patterns    TEXT,  -- JSON
        raw_summary TEXT,
        applied     INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS ab_tests (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp   TEXT,
        agent_name  TEXT,
        version_a   INTEGER,
        version_b   INTEGER,
        winner      INTEGER,
        a_avg_score REAL,
        b_avg_score REAL,
        n_samples   INTEGER,
        status      TEXT  -- 'running' / 'completed'
    );
    """)
    conn.commit()
    conn.close()


def record_performance(agent_name: str, quality: float, viral: float,
                       engagement: str, decision: str,
                       market_ctx: str = "", title: str = "",
                       prompt_version_id: int = None):
    init_tables()
    conn = sqlite3.connect(DB)
    conn.execute("""
        INSERT INTO content_performance
        (timestamp, prompt_version, quality_score, viral_score,
         engagement, decision, market_context, content_title)
        VALUES (?,?,?,?,?,?,?,?)
    """, (datetime.now().isoformat(), prompt_version_id, quality, viral,
          engagement, decision, market_ctx[:100], title[:80]))
    conn.commit()
    conn.close()


def save_prompt_version(agent_name: str, prompt_text: str, source: str = "original") -> int:
    init_tables()
    import hashlib
    h = hashlib.md5(prompt_text.encode()).hexdigest()[:8]
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Zaten var mı kontrol et
    existing = c.execute("SELECT id FROM prompt_versions WHERE prompt_hash=?", (h,)).fetchone()
    if existing:
        conn.close()
        return existing[0]

    ver = (c.execute("SELECT MAX(version) FROM prompt_versions WHERE agent_name=?",
                     (agent_name,)).fetchone()[0] or 0) + 1
    c.execute("""
        INSERT INTO prompt_versions (timestamp, agent_name, version, prompt_hash, prompt_text, source)
        VALUES (?,?,?,?,?,?)
    """, (datetime.now().isoformat(), agent_name, ver, h, prompt_text, source))
    row_id = c.lastrowid
    conn.commit()
    conn.close()
    return row_id


def save_competitor_insight(patterns: dict, raw: str):
    init_tables()
    conn = sqlite3.connect(DB)
    conn.execute("""
        INSERT INTO competitor_insights (timestamp, patterns, raw_summary)
        VALUES (?,?,?)
    """, (datetime.now().isoformat(), json.dumps(patterns, ensure_ascii=False), raw))
    conn.commit()
    conn.close()


def get_performance_stats(agent_name: str = None, last_n: int = 20) -> dict:
    init_tables()
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    rows = c.execute("""
        SELECT cp.quality_score, cp.viral_score, cp.decision, cp.engagement
        FROM content_performance cp
        ORDER BY cp.id DESC LIMIT ?
    """, (last_n,)).fetchall()

    if not rows:
        conn.close()
        return {"avg_quality": 0, "avg_viral": 0, "publish_rate": 0, "n": 0}

    avg_q = sum(r[0] or 0 for r in rows) / len(rows)
    avg_v = sum(r[1] or 0 for r in rows) / len(rows)
    publish = sum(1 for r in rows if "ONAY" in (r[2] or ""))
    conn.close()
    return {
        "avg_quality":  round(avg_q, 2),
        "avg_viral":    round(avg_v, 2),
        "publish_rate": round(publish / len(rows) * 100, 1),
        "n":            len(rows),
        "top_decision": max(set(r[2] for r in rows if r[2]), key=[r[2] for r in rows if r[2]].count) if rows else "?",
    }


def get_best_worst(last_n: int = 30) -> dict:
    """En iyi ve en kötü 5 içeriği getir."""
    init_tables()
    conn = sqlite3.connect(DB)
    best  = conn.execute("SELECT content_title, quality_score, decision FROM content_performance ORDER BY quality_score DESC LIMIT 5").fetchall()
    worst = conn.execute("SELECT content_title, quality_score, decision FROM content_performance ORDER BY quality_score ASC  LIMIT 5").fetchall()
    conn.close()
    return {
        "best":  [{"title": r[0], "score": r[1], "decision": r[2]} for r in best],
        "worst": [{"title": r[0], "score": r[1], "decision": r[2]} for r in worst],
    }
