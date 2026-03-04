"""
Instagram İçerik Pipeline
==========================
10 Agent → Tam Instagram içerik paketi üret

Çıktı:
  - Sabah Story (5 slayt)
  - Carousel (10 slayt)
  - Reel Script (60sn)
  - Caption + Hashtag
  - Viral Score
  - Haftalık Rapor (opsiyonel)

Kullanım:
  python instagram_pipeline.py            # tam paket
  python instagram_pipeline.py --weekly   # + haftalık rapor
"""

import sys
import time
import argparse
sys.path.insert(0, ".")

from utils.summary_generator    import build_instagram_summary, format_for_opus, print_summary_stats
from utils.orchestrator_interface import present_to_orchestrator

from agents.instagram.news_scraper      import NewsScraperAgent
from agents.instagram.market_data       import MarketDataAgent
from agents.instagram.geopolitical      import GeopoliticalAgent
from agents.instagram.morning_bulletin  import MorningBulletinAgent
from agents.instagram.carousel_agent    import CarouselAgent
from agents.instagram.trend_detector    import TrendDetectorAgent
from agents.instagram.reel_script       import ReelScriptAgent
from agents.instagram.weekly_report     import WeeklyReportAgent
from agents.instagram.caption_generator import CaptionGeneratorAgent
from agents.instagram.viral_predictor   import ViralPredictorAgent


def section(title: str):
    print(f"\n{'═'*52}")
    print(f"  {title}")
    print(f"{'═'*52}")


def show_result(label: str, content: str, indent: int = 4):
    prefix = " " * indent
    print(f"{prefix}▸ {label}:")
    for line in content.strip().splitlines()[:6]:
        print(f"{prefix}  {line}")


def run(weekly: bool = False):
    t_start = time.time()
    section("INSTAGRAM PIPELINE — BAŞLADI")
    print("  10 agent devrede | Ctrl+C ile durdur\n")

    # ── FAZA 1: Veri Toplama ─────────────────────────────
    section("FAZA 1: VERİ TOPLAMA")

    market  = MarketDataAgent().run()
    news    = NewsScraperAgent().run()
    geo     = GeopoliticalAgent().run()
    trends_data = TrendDetectorAgent().run(market)
    trends_list = trends_data.get("trends", [])

    print(f"\n  Toplanan veri özeti:")
    print(f"  ├─ Haber     : {len(news['news'])} adet")
    print(f"  ├─ Trend     : {len(trends_list)} adet")
    print(f"  └─ Jeopolitik: risk={geo['risk_level']} | altın_etki={geo['altin_etki']}")

    # ── FAZA 2: İçerik Üretimi ───────────────────────────
    section("FAZA 2: İÇERİK ÜRETİMİ")

    bulletin = MorningBulletinAgent().run(market, news, geo)
    carousel = CarouselAgent().run(market, news, geo)
    reel     = ReelScriptAgent().run(market, geo, trends_list)

    if weekly:
        weekly_rep = WeeklyReportAgent().run(market, news, geo, trends_list)
    else:
        weekly_rep = None

    # ── FAZA 3: Caption + Viral ──────────────────────────
    section("FAZA 3: CAPTION & VİRAL ANALİZ")

    # Carousel başlıklarını topla
    carousel_titles = [v for k, v in carousel["slides"].items() if "BASLIK" in k]
    content_summary = f"Piyasa {'yükseliyor' if market['winner']['degisim']>0 else 'karışık'}, {market['winner']['sembol']} {market['winner']['degisim']:+.1f}%"

    caption   = CaptionGeneratorAgent().run("carousel", content_summary, market)
    hashtag_n = len(caption["hashtag_tr"].split()) + len(caption["hashtag_en"].split())
    viral     = ViralPredictorAgent().run("carousel", carousel_titles, caption["caption"], hashtag_n)

    # ── SONUÇ RAPORU ─────────────────────────────────────
    section("ORCHESTRATOR (Claude Opus 4.6) — SONUÇ PAKETİ")

    d = market["data"]
    print(f"""
  📊 PİYASA DURUMU  [{market['timestamp']}]
  ├─ {d['ALTIN']['icon']}  Altın  : ${d['ALTIN']['fiyat']:>9.2f}  ({d['ALTIN']['degisim']:+.2f}%)
  ├─ {d['GUMUS']['icon']}  Gümüş  : ${d['GUMUS']['fiyat']:>9.2f}  ({d['GUMUS']['degisim']:+.2f}%)
  ├─ {d['BTC']['icon']}  BTC    : ${d['BTC']['fiyat']:>9,.0f}  ({d['BTC']['degisim']:+.2f}%)
  ├─ {d['BIST100']['icon']}  BIST100: {d['BIST100']['fiyat']:>9,.0f}  ({d['BIST100']['degisim']:+.2f}%)
  └─ {d['DOLAR']['icon']}  Dolar  : {d['DOLAR']['fiyat']:>9.2f} TL  ({d['DOLAR']['degisim']:+.2f}%)

  🌍 JEOPOLİTİK: Risk={geo['risk_level'].upper()} | Altın Etkisi={geo['altin_etki']}
  {geo.get('fed','')}

  📰 HABERLER:""")
    for n in news["news"]:
        print(f"  ├─ [{n['kaynak']}] {n['baslik']}")

    print(f"""
  📱 SABAH STORY ({len(bulletin['stories'])} slayt):""")
    for k, v in list(bulletin["stories"].items())[:3]:
        print(f"  ├─ {k}: {v[:70]}")

    print(f"""
  🎠 CAROUSEL ({len(carousel_titles)} başlık):""")
    for t in carousel_titles[:5]:
        print(f"  ├─ {t[:65]}")

    print(f"""
  🎬 REEL SCRIPT (60sn):
  ├─ Hook  : {reel['hook'][:80]}
  ├─ CTA   : {reel['cta'][:70]}
  └─ Alt Yazı: {reel['susit_yazi']}

  📝 CAPTION ({len(caption['caption'])} karakter):
  {caption['caption'][:200]}...

  #️⃣  HASHTAG: {caption['hashtag_tr'][:100]}

  🚀 VİRAL SKORU: {viral['skor']}/10  {viral['emoji']}  [{viral['engagement']}]
  ├─ En iyi paylaşım saati: {viral['en_iyi_saat']}
  └─ İyileştirme: {viral['iyilestirme']}
""")

    if weekly_rep:
        print(f"  📆 HAFTALIK RAPOR: {weekly_rep['slide_count']} slayt hazır")

    print(f"""  🔥 TREND'LER:""")
    for i, t in enumerate(trends_list[:5], 1):
        print(f"  {i}. {t['konu']} — {t['icerik_onerisi'][:50]}")

    total = round(time.time() - t_start, 1)
    section(f"TAMAMLANDI — {total}sn")

    # ── JSON Özet → Orchestrator Kararı ─────────────────
    all_results = {
        "market": market, "news": news, "geo": geo,
        "bulletin": bulletin, "carousel": carousel,
        "reel": reel, "caption": caption,
        "viral": viral, "trends": trends_data,
        "weekly": weekly_rep,
    }
    section("ORCHESTRATOR KARAR SİSTEMİ (Token-Optimized)")
    summary              = build_instagram_summary(all_results)
    summary_json, tokens = format_for_opus(summary)
    print_summary_stats(summary, tokens)
    decision_result      = present_to_orchestrator(summary)

    from utils.decision_logger import print_token_report
    print_token_report()

    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--weekly", action="store_true", help="Haftalık rapor da üret")
    args = parser.parse_args()
    run(weekly=args.weekly)
