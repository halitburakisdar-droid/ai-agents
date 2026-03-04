"""
Learning Database — Genişletilmiş Şema
=======================================
Tablolar:
  competitor_best_practices  — rakip pattern'leri
  knowledge_base             — mastery bilgi deposu
  skill_tree                 — her agent'ın skill seviyesi
  masterclass_history        — haftalık eğitim kayıtları
  experiments                — A/B deney planları
  quarterly_reports          — 3 aylık evrim raporları
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "agent_memory.db"


def get(sql: str, params=()) -> list:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def run(sql: str, params=()):
    conn = sqlite3.connect(DB)
    c = conn.execute(sql, params)
    conn.commit()
    last_id = c.lastrowid
    conn.close()
    return last_id


def init_learning_tables():
    conn = sqlite3.connect(DB)
    conn.executescript("""
    -- ── Rakip Pattern Deposu ──────────────────────────────
    CREATE TABLE IF NOT EXISTS competitor_best_practices (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        competitor_name  TEXT,
        content_type     TEXT,   -- carousel / reel / story
        pattern_type     TEXT,   -- hook / storytelling / cta / data_viz
        pattern_data     TEXT,   -- JSON
        hook_power       REAL DEFAULT 0,
        discovered_at    TEXT,
        success_score    REAL DEFAULT 0,
        times_tested     INTEGER DEFAULT 0,
        our_success_rate REAL DEFAULT 0
    );

    -- ── Master Bilgi Deposu ───────────────────────────────
    CREATE TABLE IF NOT EXISTS knowledge_base (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        topic        TEXT UNIQUE,    -- hook_writing / storytelling / pain_points etc
        level        TEXT,           -- beginner / intermediate / advanced / master
        content      TEXT,           -- tam bilgi metni
        source       TEXT,           -- hangi agent / scan üretdi
        updated_at   TEXT,
        usage_count  INTEGER DEFAULT 0
    );

    -- ── Skill Tree ────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS skill_tree (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_name     TEXT,
        skill          TEXT,          -- hook_writing / storytelling / pain_points / data_viz / cta
        level          TEXT DEFAULT 'beginner',  -- beginner→intermediate→advanced→master
        mastery_score  REAL DEFAULT 0.0,
        samples_tested INTEGER DEFAULT 0,
        level_ups      INTEGER DEFAULT 0,
        updated_at     TEXT,
        UNIQUE(agent_name, skill)
    );

    -- ── Masterclass Geçmişi ───────────────────────────────
    CREATE TABLE IF NOT EXISTS masterclass_history (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        week_number  INTEGER,
        topic        TEXT,
        teacher      TEXT,   -- 'qwen3.5:9b' veya agent adı (peer learning)
        curriculum   TEXT,   -- tam ders içeriği
        agents_trained TEXT, -- JSON listesi
        conducted_at TEXT
    );

    -- ── Deney Planları ────────────────────────────────────
    CREATE TABLE IF NOT EXISTS experiments (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at   TEXT,
        hypothesis   TEXT,
        test_a_desc  TEXT,
        test_b_desc  TEXT,
        skill        TEXT,
        sample_size  INTEGER DEFAULT 10,
        a_scores     TEXT DEFAULT '[]',   -- JSON float listesi
        b_scores     TEXT DEFAULT '[]',
        status       TEXT DEFAULT 'planned',  -- planned/running/completed
        winner       TEXT,
        confidence   REAL DEFAULT 0,
        conclusion   TEXT
    );

    -- ── Üç Aylık Evrim ───────────────────────────────────
    CREATE TABLE IF NOT EXISTS quarterly_reports (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        quarter          TEXT,         -- '2026-Q1'
        total_content    INTEGER,
        avg_engagement   REAL,
        best_practices   TEXT,         -- JSON
        worst_practices  TEXT,         -- JSON
        evolution_plan   TEXT,         -- Opus kararı
        created_at       TEXT
    );

    -- ── Level 1 Raporları (Qwen 9b üretir) ───────────────
    CREATE TABLE IF NOT EXISTS level1_reports (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at   TEXT,
        cycle_num    INTEGER,
        avg_score    REAL,
        engagement   TEXT,
        errors       TEXT DEFAULT '[]',  -- JSON hata listesi
        issues       TEXT DEFAULT '[]',  -- JSON sorun listesi
        raw_output   TEXT
    );

    -- ── Escalation'lar (Level 3'e iletilen sorunlar) ─────
    CREATE TABLE IF NOT EXISTS escalations (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at   TEXT,
        issue_type   TEXT,
        description  TEXT,
        attempted_fix TEXT,
        error        TEXT,
        resolved     INTEGER DEFAULT 0,
        resolution   TEXT
    );

    -- ── Otomatik Kod Değişiklikleri ───────────────────────
    CREATE TABLE IF NOT EXISTS code_changes (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at   TEXT,
        file_changed TEXT,
        reason       TEXT,
        commit_hash  TEXT,
        success      INTEGER DEFAULT 1,
        rolled_back  INTEGER DEFAULT 0
    );
    """)
    conn.commit()
    conn.close()


# ── Skill Tree ─────────────────────────────────────────

SKILL_LEVELS   = ["beginner", "intermediate", "advanced", "master"]
LEVEL_THRESHOLD = 0.80  # mastery_score bu eşiği geçince level up

ALL_SKILLS = [
    "hook_writing", "storytelling", "pain_points",
    "data_viz", "cta_writing", "conflict_creation", "psychology"
]

ALL_AGENTS = [
    "Research Agent", "Content Creator", "Quality Controller",
    "Carousel Agent", "Morning Bulletin", "Caption Generator"
]


def init_skill_tree():
    """Tüm agent'lar için başlangıç skill tree oluştur."""
    init_learning_tables()
    conn = sqlite3.connect(DB)
    for agent in ALL_AGENTS:
        for skill in ALL_SKILLS:
            conn.execute("""
                INSERT OR IGNORE INTO skill_tree (agent_name, skill, level, updated_at)
                VALUES (?,?,'beginner',?)
            """, (agent, skill, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def update_skill_score(agent_name: str, skill: str, score: float) -> dict:
    """Yeni skor ekle, gerekirse level up yap."""
    init_learning_tables()
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    row = c.execute("SELECT * FROM skill_tree WHERE agent_name=? AND skill=?",
                    (agent_name, skill)).fetchone()
    if not row:
        c.execute("INSERT INTO skill_tree (agent_name, skill, level, mastery_score, samples_tested, updated_at) VALUES (?,?,'beginner',?,1,?)",
                  (agent_name, skill, score / 10, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return {"leveled_up": False, "new_level": "beginner"}

    row = dict(row)
    n   = row["samples_tested"] + 1
    new_mastery = (row["mastery_score"] * row["samples_tested"] + score / 10) / n
    cur_level   = row["level"]
    new_level   = cur_level
    leveled_up  = False

    if new_mastery >= LEVEL_THRESHOLD and SKILL_LEVELS.index(cur_level) < len(SKILL_LEVELS) - 1:
        new_level  = SKILL_LEVELS[SKILL_LEVELS.index(cur_level) + 1]
        leveled_up = True

    c.execute("""
        UPDATE skill_tree SET mastery_score=?, samples_tested=?, level=?,
        level_ups=level_ups+?, updated_at=? WHERE agent_name=? AND skill=?
    """, (round(new_mastery, 3), n, new_level,
          1 if leveled_up else 0, datetime.now().isoformat(), agent_name, skill))
    conn.commit()
    conn.close()
    return {"leveled_up": leveled_up, "old_level": cur_level,
            "new_level": new_level, "mastery": round(new_mastery, 3)}


def get_skill_tree(agent_name: str = None) -> list:
    init_learning_tables()
    if agent_name:
        return get("SELECT * FROM skill_tree WHERE agent_name=? ORDER BY skill", (agent_name,))
    return get("SELECT * FROM skill_tree ORDER BY agent_name, skill")


def save_competitor_pattern(competitor: str, content_type: str,
                            pattern_type: str, pattern_data: dict,
                            hook_power: float = 0, success_score: float = 0):
    init_learning_tables()
    run("""
        INSERT INTO competitor_best_practices
        (competitor_name, content_type, pattern_type, pattern_data,
         hook_power, discovered_at, success_score)
        VALUES (?,?,?,?,?,?,?)
    """, (competitor, content_type, pattern_type,
          json.dumps(pattern_data, ensure_ascii=False),
          hook_power, datetime.now().isoformat(), success_score))


def save_knowledge(topic: str, content: str, level: str = "intermediate", source: str = "system"):
    init_learning_tables()
    conn = sqlite3.connect(DB)
    conn.execute("""
        INSERT INTO knowledge_base (topic, level, content, source, updated_at)
        VALUES (?,?,?,?,?)
        ON CONFLICT(topic) DO UPDATE SET
          content=excluded.content, level=excluded.level,
          source=excluded.source, updated_at=excluded.updated_at
    """, (topic, level, content, source, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_knowledge(topic: str) -> dict:
    rows = get("SELECT * FROM knowledge_base WHERE topic=?", (topic,))
    return rows[0] if rows else {}


def save_experiment(hypothesis: str, test_a: str, test_b: str,
                    skill: str, sample_size: int = 10) -> int:
    init_learning_tables()
    return run("""
        INSERT INTO experiments (created_at, hypothesis, test_a_desc, test_b_desc, skill, sample_size)
        VALUES (?,?,?,?,?,?)
    """, (datetime.now().isoformat(), hypothesis, test_a, test_b, skill, sample_size))


def add_experiment_score(exp_id: int, variant: str, score: float):
    conn = sqlite3.connect(DB)
    row = conn.execute("SELECT a_scores, b_scores FROM experiments WHERE id=?", (exp_id,)).fetchone()
    if not row:
        conn.close()
        return
    key  = "a_scores" if variant == "A" else "b_scores"
    vals = json.loads(row[0] if variant == "A" else row[1])
    vals.append(score)
    conn.execute(f"UPDATE experiments SET {key}=?, status='running' WHERE id=?",
                 (json.dumps(vals), exp_id))
    conn.commit()
    conn.close()


def evaluate_experiment(exp_id: int) -> dict:
    rows = get("SELECT * FROM experiments WHERE id=?", (exp_id,))
    if not rows:
        return {}
    exp     = rows[0]
    a_scores = json.loads(exp["a_scores"] or "[]")
    b_scores = json.loads(exp["b_scores"] or "[]")
    if len(a_scores) < 3 or len(b_scores) < 3:
        return {"status": "running", "a_n": len(a_scores), "b_n": len(b_scores)}
    avg_a = sum(a_scores) / len(a_scores)
    avg_b = sum(b_scores) / len(b_scores)
    winner = "B" if avg_b > avg_a else "A"
    conf   = min(abs(avg_b - avg_a) / max(avg_a, 1) * 100, 99)
    run("""UPDATE experiments SET status='completed', winner=?, confidence=?,
           conclusion=? WHERE id=?""",
        (winner, round(conf, 1),
         f"{'B' if winner=='B' else 'A'} kazandı: {max(avg_a,avg_b):.1f} vs {min(avg_a,avg_b):.1f}",
         exp_id))
    return {"status": "completed", "winner": winner, "avg_a": round(avg_a,2),
            "avg_b": round(avg_b,2), "confidence": round(conf,1)}


# ── Self-Coding System Helpers ──────────────────────────

def save_level1_report(cycle_num: int, avg_score: float,
                       engagement: str, errors: list, issues: list,
                       raw_output: str = "") -> int:
    init_learning_tables()
    return run("""
        INSERT INTO level1_reports (created_at, cycle_num, avg_score, engagement, errors, issues, raw_output)
        VALUES (?,?,?,?,?,?,?)
    """, (datetime.now().isoformat(), cycle_num, avg_score, engagement,
          json.dumps(errors, ensure_ascii=False),
          json.dumps(issues, ensure_ascii=False), raw_output))


def get_level1_reports(hours: int = 6) -> list:
    from datetime import timedelta
    since = (datetime.now() - timedelta(hours=hours)).isoformat()
    rows = get("SELECT * FROM level1_reports WHERE created_at > ? ORDER BY id DESC", (since,))
    for r in rows:
        r["errors"] = json.loads(r.get("errors") or "[]")
        r["issues"] = json.loads(r.get("issues") or "[]")
    return rows


def save_escalation(issue_type: str, description: str,
                    attempted_fix: str, error: str) -> int:
    init_learning_tables()
    return run("""
        INSERT INTO escalations (created_at, issue_type, description, attempted_fix, error)
        VALUES (?,?,?,?,?)
    """, (datetime.now().isoformat(), issue_type, description, attempted_fix, error))


def resolve_escalation(esc_id: int, resolution: str):
    run("UPDATE escalations SET resolved=1, resolution=? WHERE id=?", (resolution, esc_id))


def get_open_escalations() -> list:
    return get("SELECT * FROM escalations WHERE resolved=0 ORDER BY id DESC")


def save_code_change(file_changed: str, reason: str,
                     commit_hash: str = "", success: bool = True) -> int:
    init_learning_tables()
    return run("""
        INSERT INTO code_changes (created_at, file_changed, reason, commit_hash, success)
        VALUES (?,?,?,?,?)
    """, (datetime.now().isoformat(), file_changed, reason, commit_hash, 1 if success else 0))


def mark_code_change_rolled_back(change_id: int):
    run("UPDATE code_changes SET rolled_back=1 WHERE id=?", (change_id,))
