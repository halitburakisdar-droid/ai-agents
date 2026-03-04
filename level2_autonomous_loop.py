#!/usr/bin/env python3
"""
Level 2 Autonomous Loop — Günde 4x (06:00 / 12:00 / 18:00 / 00:00)
=====================================================================
- Level 1 raporlarını okur
- Sorunları tespit eder
- Qwen 2.5-32B ile kod yazar + test eder + commit eder
- Kritik sorunları Level 3'e escalate eder
"""

import sys, json
sys.path.insert(0, "/Users/burak/ai-agents")

from datetime import datetime
from memory.learning_db import (
    get_level1_reports, init_learning_tables, get_open_escalations
)
from agents.learning.autonomous_code_writer import AutonomousCodeWriter
from utils.telegram_bot import send_text

MAX_FIXES_PER_CYCLE = 3   # Tek çevrimde maksimum otomatik düzeltme


def analyze_reports(reports: list) -> list:
    """Raporlardan öncelikli sorun listesi çıkar."""
    if not reports:
        return []

    issues = []
    scores  = [r["avg_score"] for r in reports]
    avg_score = sum(scores) / len(scores)

    # Performans düşüşü
    if avg_score < 6.0:
        issues.append({
            "type":        "low_avg_quality",
            "description": f"Son 6h ort. skor: {avg_score:.1f}/10 — eşik 6.0",
            "agent":       "Carousel Agent",
            "impact":      f"{6.0 - avg_score:.1f} puan altında",
            "priority":    "high",
        })

    # Hata birikimi
    total_errors = sum(len(r.get("errors", [])) for r in reports)
    if total_errors >= 5:
        issues.append({
            "type":        "error_accumulation",
            "description": f"Son 6h'de {total_errors} agent hatası",
            "agent":       "multiple",
            "impact":      "pipeline stability",
            "priority":    "critical" if total_errors > 10 else "high",
        })

    # Tekrarlayan bireysel sorunlar
    issue_counts: dict = {}
    for r in reports:
        for iss in r.get("issues", []):
            k = iss.get("type", "unknown")
            issue_counts[k] = issue_counts.get(k, 0) + 1

    for issue_type, cnt in issue_counts.items():
        if cnt >= 3:
            issues.append({
                "type":        issue_type,
                "description": f"'{issue_type}' sorunu {cnt} raporda tekrarlandı",
                "agent":       "recurring",
                "impact":      "persistent problem",
                "priority":    "high",
            })

    # Önceliğe göre sırala
    priority_map = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    issues.sort(key=lambda x: priority_map.get(x.get("priority", "low"), 3))
    return issues


def build_status_report(reports: list, results: list) -> str:
    """Telegram için durum raporu yaz."""
    n        = len(reports)
    scores   = [r["avg_score"] for r in reports] if reports else [0]
    avg      = sum(scores) / len(scores)
    fixed    = sum(1 for r in results if r.get("success"))
    escalated = sum(1 for r in results if r.get("escalated"))
    failed   = len(results) - fixed - escalated

    lines = [
        f"🤖 *Level 2 Raporu* — {datetime.now().strftime('%d/%m %H:%M')}",
        f"📊 Son 6h: {n} rapor | Ort. {avg:.1f}/10",
        f"🔧 Düzeltme: ✅{fixed}  ⚠️{escalated}(escalated)  ❌{failed}",
    ]
    open_esc = get_open_escalations()
    if open_esc:
        lines.append(f"📌 Açık escalation: {len(open_esc)} adet")
    return "\n".join(lines)


def main():
    init_learning_tables()
    print(f"\n{'═'*52}")
    print(f"  LEVEL 2 AUTONOMOUS LOOP — {datetime.now().strftime('%H:%M')}")
    print(f"{'═'*52}")

    # 1. Son 6 saatin raporlarını al
    reports = get_level1_reports(hours=6)
    print(f"  {len(reports)} Level 1 raporu okundu")

    if not reports:
        print("  Rapor yok — sistem sağlıklı.")
        send_text(f"🤖 *Level 2*: Rapor yok, sistem sağlıklı — {datetime.now().strftime('%H:%M')}")
        return

    # 2. Sorunları analiz et
    issues = analyze_reports(reports)
    print(f"  {len(issues)} sorun tespit edildi")

    if not issues:
        print("  Sorun yok — performans yeterli.")
        send_text(build_status_report(reports, []))
        return

    # 3. Sorunları çöz
    code_writer = AutonomousCodeWriter()
    results     = []

    for issue in issues[:MAX_FIXES_PER_CYCLE]:
        print(f"\n  {'─'*48}")
        print(f"  [{issue['priority'].upper()}] {issue['type']}: {issue['description'][:60]}")

        result = code_writer.analyze_and_fix(issue)
        results.append(result)

        if result.get("success"):
            print(f"  ✅ Düzeltme başarılı — commit: {result.get('commit','?')}")
        elif result.get("escalated"):
            print(f"  ⚠️  Escalated to Level 3 (esc_id={result.get('esc_id','?')})")
        else:
            print(f"  ❌ Düzeltme başarısız: {result.get('reason','?')}")

    # 4. Rapor gönder
    send_text(build_status_report(reports, results))
    print(f"\n  Level 2 tamamlandı.")


if __name__ == "__main__":
    main()
