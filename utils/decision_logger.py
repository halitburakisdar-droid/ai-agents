"""
Karar & Token Loglayıcı
========================
Orchestrator (Opus) kararlarını ve token kullanımını takip eder.
SQLite'a yazar, günlük/aylık rapor üretir.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "agent_memory.db"


def init_decision_table():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS orchestrator_decisions (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp     TEXT NOT NULL,
        content_type  TEXT,
        title         TEXT,
        summary_json  TEXT,
        summary_tokens INTEGER,
        decision      TEXT,
        decision_note TEXT,
        decision_tokens INTEGER,
        total_tokens  INTEGER,
        elapsed_ms    INTEGER
    )""")
    conn.commit()
    conn.close()


def log_decision(summary: dict, decision: str, note: str,
                 summary_tokens: int, decision_tokens: int, elapsed_ms: int = 0):
    init_decision_table()
    total = summary_tokens + decision_tokens
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO orchestrator_decisions
        (timestamp, content_type, title, summary_json, summary_tokens,
         decision, decision_note, decision_tokens, total_tokens, elapsed_ms)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (
        datetime.now().isoformat(),
        summary.get("type", "?"),
        summary.get("title", "?"),
        json.dumps(summary, ensure_ascii=False),
        summary_tokens,
        decision, note, decision_tokens, total, elapsed_ms,
    ))
    conn.commit()
    conn.close()
    return total


def get_token_report() -> dict:
    init_decision_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")
    month = datetime.now().strftime("%Y-%m")

    daily  = c.execute("SELECT COUNT(*), SUM(total_tokens) FROM orchestrator_decisions WHERE timestamp LIKE ?", (f"{today}%",)).fetchone()
    monthly= c.execute("SELECT COUNT(*), SUM(total_tokens) FROM orchestrator_decisions WHERE timestamp LIKE ?", (f"{month}%",)).fetchone()
    total  = c.execute("SELECT COUNT(*), SUM(total_tokens) FROM orchestrator_decisions").fetchone()
    by_dec = c.execute("SELECT decision, COUNT(*) FROM orchestrator_decisions GROUP BY decision").fetchall()
    last5  = c.execute("SELECT timestamp, content_type, decision, total_tokens FROM orchestrator_decisions ORDER BY id DESC LIMIT 5").fetchall()

    conn.close()
    return {
        "today":   {"count": daily[0] or 0,   "tokens": daily[1] or 0},
        "month":   {"count": monthly[0] or 0,  "tokens": monthly[1] or 0},
        "total":   {"count": total[0] or 0,    "tokens": total[1] or 0},
        "by_decision": dict(by_dec),
        "last5": [{"ts": r[0][:16], "type": r[1], "decision": r[2], "tokens": r[3]} for r in last5],
    }


def print_token_report():
    r = get_token_report()
    print(f"""
  💰 TOKEN KULLANIM RAPORU
  ├─ Bugün    : {r['today']['count']} karar  / {r['today']['tokens']:,} token
  ├─ Bu ay    : {r['month']['count']} karar  / {r['month']['tokens']:,} token
  ├─ Toplam   : {r['total']['count']} karar  / {r['total']['tokens']:,} token
  ├─ Kararlar : {r['by_decision']}
  └─ Son 5:""")
    for d in r["last5"]:
        print(f"     [{d['ts']}] {d['type']:20s} → {d['decision']:12s} ({d['tokens']} tk)")
