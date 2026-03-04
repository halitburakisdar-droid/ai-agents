#!/usr/bin/env python3
"""
Level 1 Content Loop — Her 2 saatte çalışır
=============================================
- Instagram carousel + caption üretir
- Kalite < 6.5 ise "issue" olarak Level 2'ye raporlar
- Performans DB'ye kaydeder
"""

import sys, random, json
sys.path.insert(0, "/Users/burak/ai-agents")

from datetime import datetime
from agents.instagram.carousel_agent    import CarouselAgent
from agents.instagram.caption_generator import CaptionGeneratorAgent
from agents.instagram.viral_predictor   import ViralPredictorAgent
from agents.instagram.market_data       import MarketDataAgent
from agents.learning.performance_tracker import record_performance
from memory.learning_db import (
    init_learning_tables, save_level1_report
)
from utils.telegram_bot import send_text, send_content_for_feedback, send_report

QUALITY_THRESHOLD = 6.5   # Bu altı → Level 2'ye issue raporla
VIRAL_THRESHOLD   = 5.0

def run_cycle():
    init_learning_tables()
    cycle_num = int(datetime.now().timestamp())

    print(f"\n{'═'*52}")
    print(f"  LEVEL 1 CONTENT LOOP — {datetime.now().strftime('%H:%M')}")
    print(f"{'═'*52}")

    errors  = []
    issues  = []

    # 1. Piyasa verisi
    try:
        market = MarketDataAgent().run()
        print(f"  Piyasa: ALTIN={market['prices']['ALTIN']}, BTC={market['prices']['BTC']}")
    except Exception as e:
        errors.append(f"MarketData: {e}")
        market = {"prices": {"ALTIN": 3150, "BTC": 85000}, "alarms": [], "changes": {}}

    # 2. Carousel oluştur
    try:
        carousel = CarouselAgent().run(market)
        print(f"  Carousel: {len(carousel.get('slides', []))} slayt")
    except Exception as e:
        errors.append(f"Carousel: {e}")
        carousel = {"slides": [], "hook": ""}

    # 3. Caption
    try:
        caption_data = CaptionGeneratorAgent().run(carousel)
        caption = caption_data.get("caption", "")
    except Exception as e:
        errors.append(f"Caption: {e}")
        caption = ""

    # 4. Viral tahmin
    try:
        viral = ViralPredictorAgent().run(carousel, caption)
        quality_score = float(viral.get("viral_score", 6.0))
        engagement    = viral.get("engagement_prediction", "orta")
        best_time     = viral.get("best_time", "18:00")
    except Exception as e:
        errors.append(f"ViralPredictor: {e}")
        quality_score = random.uniform(5.5, 7.5)
        engagement    = "orta"
        best_time     = "18:00"

    print(f"  Kalite skoru: {quality_score:.1f}/10 | Engagement: {engagement}")

    # 5. Performans kaydet
    decision = "ONAY" if quality_score >= QUALITY_THRESHOLD else "REVİZE"
    hook = (carousel.get("slides") or [{}])[0].get("baslik", "")[:60] if carousel.get("slides") else ""
    record_performance("carousel", round(quality_score, 1),
                       round(quality_score * 0.9, 1), engagement, decision,
                       title=hook or f"Cycle {cycle_num}")

    # 6. Issue tespiti
    if quality_score < QUALITY_THRESHOLD:
        issues.append({
            "type":        "low_quality",
            "description": f"Carousel kalite skoru düştü: {quality_score:.1f}/10",
            "agent":       "Carousel Agent",
            "impact":      f"{QUALITY_THRESHOLD - quality_score:.1f} puan altında",
            "priority":    "high" if quality_score < 5.0 else "medium",
        })

    if errors:
        issues.append({
            "type":        "agent_errors",
            "description": f"{len(errors)} ajan hatası: {'; '.join(errors[:3])}",
            "agent":       "multiple",
            "impact":      "pipeline stability",
            "priority":    "critical" if len(errors) > 2 else "high",
        })

    # 7. Level 1 raporunu kaydet
    report_id = save_level1_report(
        cycle_num    = cycle_num,
        avg_score    = round(quality_score, 2),
        engagement   = engagement,
        errors       = errors,
        issues       = issues,
        raw_output   = json.dumps({
            "hook":     hook,
            "decision": decision,
            "best_time": best_time,
        }, ensure_ascii=False),
    )

    print(f"  Level 1 raporu kaydedildi (id={report_id})")
    if issues:
        print(f"  ⚠️  {len(issues)} issue tespit edildi — Level 2 analiz edecek")

    # 8. Telegram — her çevrimde içerik bildirimi
    send_content_for_feedback(
        title      = hook or f"Cycle {cycle_num}",
        score      = round(quality_score, 1),
        engagement = engagement,
        hook       = hook,
        best_time  = best_time,
        decision   = decision,
    )
    if issues:
        issue_lines = "\n".join(f"• {i['type']}: {i['description'][:60]}" for i in issues)
        send_report(1, f"⚠️ {len(issues)} Issue Tespit Edildi",
                    f"{issue_lines}\n\nLevel 2 analiz edecek.", success=False)

    return {"cycle": cycle_num, "score": quality_score,
            "issues": issues, "errors": errors}


if __name__ == "__main__":
    result = run_cycle()
    print(f"\n  Tamamlandı: score={result['score']:.1f}, "
          f"issues={len(result['issues'])}, errors={len(result['errors'])}")
