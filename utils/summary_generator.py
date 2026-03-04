"""
JSON Özet Üretici
=================
Pipeline çıktısını Opus'a gönderilecek minimal JSON'a sıkıştırır.
Hedef: 80-120 token (Opus mümkün olduğu kadar az token okusun)
"""

import json
from datetime import datetime


def _token_estimate(text: str) -> int:
    """Kabaca token tahmini: kelime sayısı * 1.3"""
    return int(len(text.split()) * 1.3)


def build_instagram_summary(results: dict) -> dict:
    """Instagram pipeline sonucunu minimal JSON'a sıkıştır."""
    market  = results.get("market", {})
    viral   = results.get("viral", {})
    carousel = results.get("carousel", {})
    caption = results.get("caption", {})
    geo     = results.get("geo", {})
    trends  = results.get("trends", {})

    d = market.get("data", {})

    # Carousel başlıklarından ilkini al
    titles = [v for k, v in carousel.get("slides", {}).items() if "BASLIK" in k]
    main_title = titles[0].replace("**", "").strip() if titles else "İçerik"

    # En yüksek değişim gösteren varlık
    winner = market.get("winner", {})
    loser  = market.get("loser", {})

    # Hashtag sayısı
    ht_tr = len(caption.get("hashtag_tr", "").split())
    ht_en = len(caption.get("hashtag_en", "").split())

    summary = {
        "ts":           datetime.now().strftime("%Y-%m-%d %H:%M"),
        "type":         "carousel",
        "title":        main_title[:60],
        "quality":      viral.get("skor", 0),
        "viral":        viral.get("skor", 0),
        "engagement":   viral.get("engagement", "?"),
        "best_time":    viral.get("en_iyi_saat", "20:00"),
        "market": {
            "altin":  f"{d.get('ALTIN',{}).get('degisim',0):+.1f}%",
            "btc":    f"{d.get('BTC',{}).get('degisim',0):+.1f}%",
            "dolar":  f"{d.get('DOLAR',{}).get('degisim',0):+.1f}%",
            "bist":   f"{d.get('BIST100',{}).get('degisim',0):+.1f}%",
        },
        "signals": {
            "winner":    f"{winner.get('sembol','?')} {winner.get('degisim',0):+.1f}%",
            "loser":     f"{loser.get('sembol','?')} {loser.get('degisim',0):+.1f}%",
            "geo_risk":  geo.get("risk_level", "?"),
            "altin_etki": geo.get("altin_etki", "?")[:30],
        },
        "content": {
            "slides":    len(titles),
            "hashtags":  ht_tr + ht_en,
            "caption_chars": len(caption.get("caption", "")),
            "top_trends": [t["konu"] for t in trends.get("trends", [])[:3]],
        },
        "qc": {
            "guclu": viral.get("guclu", "")[:60],
            "zayif": viral.get("zayif", "")[:60],
            "iyilestirme": viral.get("iyilestirme", "")[:80],
        },
        "agent_rec": viral.get("engagement", "yüksek"),
    }

    return summary


def build_pipeline_summary(results: dict) -> dict:
    """Ana altın/gümüş pipeline sonucunu özetle."""
    p = results.get("price", {})
    r = results.get("research", {})
    q = results.get("quality", {})
    c = results.get("content", {})
    slides = c.get("slides", {})
    title  = slides.get("slide_1", {}).get("baslik", "İçerik")

    summary = {
        "ts":      datetime.now().strftime("%Y-%m-%d %H:%M"),
        "type":    "gold_silver_carousel",
        "title":   title[:60],
        "market": {
            "altin":  f"{p.get('changes',{}).get('gold',0):+.1f}%",
            "gumus":  f"{p.get('changes',{}).get('silver',0):+.1f}%",
            "alarm":  p.get("alarm_count", 0),
        },
        "analysis": {
            "trend":    r.get("trend", "?"),
            "guven":    r.get("guven", "?"),
            "tavsiye":  r.get("tavsiye", "?"),
        },
        "quality": {
            "score":  q.get("skor", 0),
            "karar":  q.get("karar", "?"),
            "guclu":  q.get("guclu", "")[:50],
            "zayif":  q.get("zayif", "")[:50],
        },
        "agent_rec": q.get("karar", "REVİZE ET"),
    }
    return summary


def format_for_opus(summary: dict) -> str:
    """JSON'ı Opus'a gönderilecek kısa metne dönüştür."""
    j = json.dumps(summary, ensure_ascii=False, separators=(",", ":"))
    tokens = _token_estimate(j)
    return j, tokens


def print_summary_stats(summary: dict, tokens: int):
    print(f"\n  📦 OPUS'A GÖNDERİLEN ÖZET ({tokens} token tahmini):")
    print(f"  {json.dumps(summary, ensure_ascii=False, indent=2)[:600]}...")
