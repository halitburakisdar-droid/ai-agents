#!/usr/bin/env python3
"""
Level 3 Strategic Loop — Günde 1x (08:00)
===========================================
- Opus 4.6 (Claude) için JSON paket hazırlar
- Açık escalation'ları derler
- Stratejik özet Telegram'a gönderilir
- Kullanıcı (Burak) kararları Telegram'dan verebilir
"""

import sys, json
sys.path.insert(0, "/Users/burak/ai-agents")

from datetime import datetime, timedelta
from memory.learning_db import (
    get_open_escalations, get_level1_reports,
    get as db_get, init_learning_tables, resolve_escalation
)
from agents.learning.performance_tracker import get_performance_stats, get_best_worst
from utils.telegram_bot import send_text

def build_opus_packet() -> dict:
    """Claude/Opus için stratejik özet JSON paketi oluştur."""
    init_learning_tables()

    # Son 24 saat performansı
    stats = get_performance_stats(last_n=48)
    best  = get_best_worst(last_n=48)

    # Açık escalation'lar
    escalations = get_open_escalations()

    # Son 24h Level 1 raporları
    reports_24h = get_level1_reports(hours=24)
    scores_24h  = [r["avg_score"] for r in reports_24h] if reports_24h else [0]
    avg_24h     = sum(scores_24h) / len(scores_24h) if scores_24h else 0

    # Trend: dün vs bugün
    reports_48h = get_level1_reports(hours=48)
    scores_48h  = [r["avg_score"] for r in reports_48h[len(reports_24h):]] if len(reports_48h) > len(reports_24h) else []
    avg_48h     = sum(scores_48h) / len(scores_48h) if scores_48h else avg_24h
    trend       = round(avg_24h - avg_48h, 2)

    # Son kod değişiklikleri
    code_changes = db_get(
        "SELECT file_changed, reason, commit_hash, success, rolled_back "
        "FROM code_changes ORDER BY id DESC LIMIT 5"
    )

    # Son kazanan deneyler
    winning_exp = db_get(
        "SELECT hypothesis, winner, confidence FROM experiments "
        "WHERE status='completed' AND winner='B' ORDER BY id DESC LIMIT 3"
    )

    packet = {
        "type":            "level3_daily_brief",
        "date":            datetime.now().strftime("%Y-%m-%d"),
        "performance": {
            "avg_quality_24h":  round(avg_24h, 2),
            "trend_vs_yesterday": trend,
            "publish_rate":     stats.get("publish_rate", 0),
            "total_cycles_24h": len(reports_24h),
        },
        "escalations": [
            {
                "id":   e["id"],
                "type": e["issue_type"],
                "desc": e["description"][:100],
                "error": e["error"][:80] if e.get("error") else "",
            }
            for e in escalations
        ],
        "recent_code_changes": [
            {
                "file":    c["file_changed"],
                "reason":  c["reason"][:60],
                "commit":  c["commit_hash"],
                "ok":      bool(c["success"]),
                "rolled":  bool(c["rolled_back"]),
            }
            for c in code_changes
        ],
        "winning_experiments": [
            {"hyp": e["hypothesis"][:60], "conf": e["confidence"]}
            for e in winning_exp
        ],
        "best_content": [
            {"title": c["title"][:40], "score": c["score"]}
            for c in (best.get("best") or [])[:2] if c.get("title")
        ],
        "decision_needed": len(escalations) > 0,
        "token_estimate":  120,
    }
    return packet


def format_telegram_brief(packet: dict) -> str:
    """Okunabilir Telegram mesajı."""
    perf  = packet["performance"]
    trend = perf["trend_vs_yesterday"]
    trend_icon = "📈" if trend >= 0 else "📉"

    lines = [
        f"🎯 *Level 3 Günlük Brief* — {packet['date']}",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"📊 *24h Performans*",
        f"Ort. kalite: {perf['avg_quality_24h']}/10 {trend_icon} ({trend:+.2f})",
        f"Yayın oranı: %{perf['publish_rate']} | Döngü: {perf['total_cycles_24h']}",
    ]

    esc = packet["escalations"]
    if esc:
        lines += [
            f"",
            f"⚠️ *Açık Escalation'lar ({len(esc)} adet)*",
        ]
        for e in esc[:3]:
            lines.append(f"  • [{e['id']}] {e['type']}: {e['desc'][:50]}")
        lines.append(f"_Karar için yanıt ver: `/resolve <id> <çözüm>`_")
    else:
        lines.append(f"✅ Açık escalation yok")

    cc = packet["recent_code_changes"]
    if cc:
        lines += [f"", f"🔧 *Son Kod Değişiklikleri*"]
        for c in cc[:3]:
            status = "✅" if c["ok"] and not c["rolled"] else "⏪" if c["rolled"] else "❌"
            lines.append(f"  {status} {c['file']} — {c['reason'][:40]}")

    we = packet["winning_experiments"]
    if we:
        lines += [f"", f"🏆 *Kazanan Deneyler*"]
        for e in we:
            lines.append(f"  • {e['hyp'][:50]} (%{e['conf']:.0f})")

    lines += [
        f"",
        f"_Bu brief Claude/Opus'a da iletildi._",
        f"_Sistem: `level3_strategic.py`_",
    ]
    return "\n".join(lines)


def main():
    print(f"\n{'═'*52}")
    print(f"  LEVEL 3 STRATEGIC BRIEF — {datetime.now().strftime('%H:%M')}")
    print(f"{'═'*52}")

    packet = build_opus_packet()

    # JSON dosyaya kaydet (Opus okuyabilsin diye)
    out_path = "/Users/burak/ai-agents/logs/level3_packet.json"
    import os; os.makedirs("/Users/burak/ai-agents/logs", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(packet, f, ensure_ascii=False, indent=2)
    print(f"  Paket kaydedildi: {out_path}")

    # Telegram
    brief = format_telegram_brief(packet)
    send_text(brief)
    print(f"  Telegram'a gönderildi.")

    # Özet ekrana
    perf = packet["performance"]
    print(f"\n  24h ort: {perf['avg_quality_24h']}/10 (trend {perf['trend_vs_yesterday']:+.2f})")
    print(f"  Escalation: {len(packet['escalations'])} açık")
    print(f"  Kod değişikliği: {len(packet['recent_code_changes'])} kayıt")

    return packet


if __name__ == "__main__":
    main()
