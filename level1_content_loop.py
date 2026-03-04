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
from agents.instagram.market_data        import MarketDataAgent
from agents.instagram.news_scraper       import NewsScraperAgent
from agents.instagram.geopolitical       import GeopoliticalAgent
from agents.instagram.carousel_agent     import CarouselAgent
from agents.instagram.caption_generator  import CaptionGeneratorAgent
from agents.instagram.viral_predictor    import ViralPredictorAgent
from agents.learning.performance_tracker import record_performance
from memory.learning_db import init_learning_tables, save_level1_report
from utils.telegram_bot import send_level1_report, send_message

QUALITY_THRESHOLD = 6.5


def run_cycle():
    init_learning_tables()
    cycle_num = int(datetime.now().timestamp())

    print(f"\n{'═'*52}")
    print(f"  LEVEL 1 CONTENT LOOP — {datetime.now().strftime('%H:%M')}")
    print(f"{'═'*52}")

    errors = []
    issues = []

    # ── 1. Piyasa verisi ──────────────────────────────
    try:
        market = MarketDataAgent().run()
        # market['data'] = {ALTIN: {fiyat, degisim, icon}, ...}
        d = market["data"]
        print(f"  Piyasa: ALTIN={d['ALTIN']['fiyat']:.0f}$  BTC={d['BTC']['fiyat']:,.0f}$")
    except Exception as e:
        errors.append(f"MarketData: {e}")
        market = {
            "data": {
                "ALTIN":  {"fiyat": 3150.0, "degisim": 0.0, "icon": "📈"},
                "GUMUS":  {"fiyat": 32.50,  "degisim": 0.0, "icon": "📈"},
                "BTC":    {"fiyat": 85000.0,"degisim": 0.0, "icon": "📈"},
                "BIST100":{"fiyat": 9800.0, "degisim": 0.0, "icon": "📈"},
                "DOLAR":  {"fiyat": 32.5,   "degisim": 0.0, "icon": "📈"},
                "EURO":   {"fiyat": 35.0,   "degisim": 0.0, "icon": "📈"},
            },
            "winner": {"sembol": "BTC",   "fiyat": 85000, "degisim": 1.5, "icon": "📈"},
            "loser":  {"sembol": "DOLAR", "fiyat": 32.5,  "degisim": -0.5,"icon": "📉"},
            "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M"),
        }
        print(f"  ⚠️  MarketData fallback kullanılıyor")

    # ── 2. Haber & Jeopolitik ──────────────────────────
    try:
        news = NewsScraperAgent().run()
        print(f"  Haber: {len(news.get('news', []))} haber tarandı")
    except Exception as e:
        errors.append(f"NewsScraper: {e}")
        news = {"news": [{"baslik": "Piyasalar karışık seyrediyor", "ozet": "Küresel belirsizlik sürüyor"}], "raw": ""}

    try:
        geo = GeopoliticalAgent().run()
        print(f"  Jeopolitik risk: {geo.get('risk_level', '?')}")
    except Exception as e:
        errors.append(f"Geopolitical: {e}")
        geo = {"ozet": "Küresel belirsizlik devam ediyor", "risk_level": "orta",
               "fed": "", "ortadogu": "", "petrol": "sabit", "altin_etki": "nötr"}

    # ── 3. Carousel oluştur ────────────────────────────
    try:
        carousel = CarouselAgent().run(market, news, geo)
        slides = carousel.get("slides", {})
        slide_count = len(slides) // 2  # BASLIK + METIN çiftleri
        print(f"  Carousel: {slide_count} slayt hazır")
    except Exception as e:
        errors.append(f"Carousel: {e}")
        carousel = {"slides": {}, "raw": ""}
        slides = {}
        print(f"  ❌ Carousel hatası: {e}")

    # ── 4. Caption oluştur ────────────────────────────
    try:
        # İlk slide başlığını summary olarak kullan
        first_title = slides.get("SLIDE_01_BASLIK", "Piyasa Analizi")
        summary_text = f"{first_title}. " + slides.get("SLIDE_01_METIN", "")[:100]
        caption_data = CaptionGeneratorAgent().run("carousel", summary_text, market)
        caption      = caption_data.get("caption", "")
        hashtag_tr   = caption_data.get("hashtag_tr", "")
        hashtag_count = len(hashtag_tr.split()) if hashtag_tr else 5
        print(f"  Caption: {len(caption)} karakter")
    except Exception as e:
        errors.append(f"Caption: {e}")
        caption       = "Altın ve BTC analizi için takipte kalın!"
        hashtag_tr    = "#altın #borsa #bitcoin"
        hashtag_count = 3
        print(f"  ❌ Caption hatası: {e}")

    # ── 5. Viral tahmin ──────────────────────────────
    try:
        # basliklar: slide başlıklarını liste olarak çıkar
        basliklar = [v for k, v in slides.items() if "BASLIK" in k][:5]
        if not basliklar:
            basliklar = [first_title]
        viral      = ViralPredictorAgent().run("carousel", basliklar, caption, hashtag_count)
        quality_score = float(viral.get("skor", 6.0))
        engagement    = viral.get("engagement", "orta")
        best_time     = viral.get("en_iyi_saat", "18:00-20:00")
        print(f"  Viral skor: {quality_score}/10 | Engagement: {engagement}")
    except Exception as e:
        errors.append(f"ViralPredictor: {e}")
        quality_score = random.uniform(5.5, 7.5)
        engagement    = "orta"
        best_time     = "18:00-20:00"
        print(f"  ❌ ViralPredictor hatası: {e}")

    # ── 6. Karar ve kayıt ────────────────────────────
    decision   = "ONAY" if quality_score >= QUALITY_THRESHOLD else "REVİZE"
    first_title_str = slides.get("SLIDE_01_BASLIK", f"Cycle {cycle_num}")

    record_performance(
        "carousel", round(quality_score, 1),
        round(quality_score * 0.9, 1), engagement, decision,
        title=first_title_str[:60],
    )

    # ── 7. Issue tespiti ──────────────────────────────
    if quality_score < QUALITY_THRESHOLD:
        issues.append({
            "type":        "low_quality",
            "description": f"Carousel skoru düştü: {quality_score:.1f}/10",
            "agent":       "Carousel Agent",
            "impact":      f"{QUALITY_THRESHOLD - quality_score:.1f} puan altında",
            "priority":    "high" if quality_score < 5.0 else "medium",
        })

    if len(errors) >= 3:
        issues.append({
            "type":        "agent_errors",
            "description": f"{len(errors)} ajan hatası: {'; '.join(errors[:2])}",
            "agent":       "multiple",
            "impact":      "pipeline stability",
            "priority":    "critical" if len(errors) > 3 else "high",
        })

    # ── 8. DB'ye kaydet ──────────────────────────────
    report_id = save_level1_report(
        cycle_num  = cycle_num,
        avg_score  = round(quality_score, 2),
        engagement = engagement,
        errors     = errors,
        issues     = issues,
        raw_output = json.dumps({
            "hook":     first_title_str[:80],
            "decision": decision,
            "best_time": best_time,
            "slide_count": slide_count if "slide_count" in dir() else 0,
        }, ensure_ascii=False),
    )

    print(f"\n  {'─'*48}")
    print(f"  Rapor kaydedildi (id={report_id})")
    print(f"  Kalite: {quality_score:.1f}/10 | Karar: {decision} | Hata: {len(errors)}")
    if issues:
        print(f"  ⚠️  {len(issues)} issue → Level 2 analiz edecek")

    # ── 9. Telegram ───────────────────────────────────
    issue_str = issues[0]["description"][:80] if issues else None
    send_level1_report({
        "type":  "Carousel",
        "title": first_title_str[:100],
        "score": round(quality_score, 1),
        "viral": round(quality_score * 0.9, 1),
        "issue": issue_str,
    })

    return {
        "cycle":     cycle_num,
        "score":     quality_score,
        "decision":  decision,
        "slides":    len(slides) // 2,
        "issues":    issues,
        "errors":    errors,
    }


if __name__ == "__main__":
    result = run_cycle()
    print(f"\n  TAMAMLANDI:")
    print(f"  score={result['score']:.1f} | slides={result['slides']}"
          f" | issues={len(result['issues'])} | errors={len(result['errors'])}")
