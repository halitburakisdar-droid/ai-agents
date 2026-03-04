"""
Continuous Learning Loop
========================
7/24 çalışan, kendini sürekli geliştiren AI Agent sistemi.

Zamanlama:
  06:00       → Competitor Scanner (günlük rakip taraması)
  Her 30 dak  → Instagram pipeline + Telegram karar
  Her 5 döngü → Pattern Analyzer
  AGENT_REVIZE kararı → Prompt Optimizer (Code Writer)
  Her 10 döngü → A/B test değerlendirme

Durdurmak: Ctrl+C
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, time as dtime
from agents.instagram.market_data       import MarketDataAgent
from agents.instagram.news_scraper      import NewsScraperAgent
from agents.instagram.geopolitical      import GeopoliticalAgent
from agents.instagram.carousel_agent    import CarouselAgent
from agents.instagram.caption_generator import CaptionGeneratorAgent
from agents.instagram.viral_predictor   import ViralPredictorAgent
from agents.learning.competitor_scanner  import CompetitorScannerAgent
from agents.learning.performance_tracker import (
    init_tables, record_performance, save_competitor_insight, get_performance_stats
)
from agents.learning.pattern_analyzer   import PatternAnalyzerAgent
from agents.learning.prompt_optimizer   import PromptOptimizerAgent
from agents.learning.ab_tester          import ABTesterAgent
from memory.database                    import init_db
from utils.summary_generator            import build_instagram_summary, format_for_opus
from utils.orchestrator_interface       import present_to_orchestrator
from utils.decision_logger              import print_token_report
from utils.telegram_bot                 import send_summary, send_text, start_bot_listener

# ── Ayarlar ────────────────────────────────────────────
PIPELINE_INTERVAL = 30 * 60    # 30 dakika
PRICE_CHECK       = 60         # 1 dakika
ANALYZE_EVERY     = 5          # her 5 döngüde pattern analizi
AB_EVAL_EVERY     = 10         # her 10 döngüde A/B değerlendirme
MORNING_SCAN_HOUR = 6          # rakip tarama saati


def sep(msg="", w=54):
    print(f"\n{'═'*w}")
    if msg:
        print(f"  {msg}")
        print(f"{'═'*w}")


def is_morning_scan_time() -> bool:
    now = datetime.now()
    return now.hour == MORNING_SCAN_HOUR and now.minute < 5


def run_pipeline_cycle(market: dict, news: dict, geo: dict,
                       learned_patterns: list, cycle: int) -> dict:
    """Tek bir Instagram içerik döngüsü çalıştır."""
    sep(f"DÖNGÜ #{cycle} — {datetime.now().strftime('%H:%M')}")

    carousel = CarouselAgent().run(market, news, geo)
    titles   = [v for k, v in carousel.get("slides", {}).items() if "BASLIK" in k]
    winner   = market.get("winner", {})
    caption  = CaptionGeneratorAgent().run(
        "carousel", f"{winner.get('sembol','?')} {winner.get('degisim',0):+.1f}%", market)
    ht_n     = (len(caption.get("hashtag_tr","").split()) +
                len(caption.get("hashtag_en","").split()))
    viral    = ViralPredictorAgent().run("carousel", titles, caption.get("caption",""), ht_n)

    return {"market": market, "news": news, "geo": geo,
            "carousel": carousel, "caption": caption,
            "viral": viral, "trends": {"trends": []}}


def notify_learning_update(analysis: dict, opt_result: dict = None):
    """Telegram'a öğrenme güncellemesi gönder."""
    msg = (
        f"🧠 *Learning Engine Raporu*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Ort. skor: {analysis['stats']['avg_quality']}/10 "
        f"({analysis['stats']['n']} döngü)\n"
        f"📈 Yayın oranı: %{analysis['stats']['publish_rate']}\n\n"
        f"🔴 Sorun: {analysis['sorun_1'][:80]}\n"
        f"✅ Çözüm: {analysis['cozum_1'][:80]}\n"
        f"🎯 Öncelik: {analysis['oncelikli_agent']}\n"
        f"📈 Beklenen artış: {analysis['beklenen_artis']}"
    )
    if opt_result:
        msg += (
            f"\n\n🛠 *Prompt Optimize Edildi!*\n"
            f"Agent: {opt_result['target']}\n"
            f"Durum: {opt_result['status']}\n"
            f"Süre: {opt_result.get('elapsed','?')}s"
        )
    send_text(msg)


def notify_ab_result(ab_result: dict):
    """A/B test sonucunu Telegram'a gönder."""
    if ab_result.get("status") != "completed":
        return
    send_text(
        f"🔬 *A/B Test Sonucu #{ab_result['test_id']}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Versiyon A: {ab_result['avg_a']}/10 ({ab_result['n_a']} örnek)\n"
        f"Versiyon B: {ab_result['avg_b']}/10 ({ab_result['n_b']} örnek)\n"
        f"🏆 Kazanan: *Versiyon {ab_result['winner_label']}*\n"
        f"📈 Fark: +{ab_result['improvement']} puan"
    )


def run():
    sep("CONTINUOUS LEARNING LOOP — BAŞLADI")
    print(f"  Pipeline   : her 30 dakika")
    print(f"  Rakip tarama: her gün 06:00")
    print(f"  Pattern analiz: her {ANALYZE_EVERY} döngü")
    print(f"  A/B test   : her {AB_EVAL_EVERY} döngü")
    print(f"  Durdurmak  : Ctrl+C\n")

    init_db()
    init_tables()
    start_bot_listener()
    send_text(
        "🤖 *Continuous Learning Loop Başladı!*\n"
        "Sistem kendini sürekli geliştiriyor.\n"
        "Her 30 dakikada içerik + öğrenme raporu gelecek. 🧠"
    )

    cycle           = 0
    last_pipeline   = 0
    last_scan_date  = None
    competitor_pats = {}
    active_ab_test  = None
    ab_tester       = ABTesterAgent()

    try:
        while True:
            now      = time.time()
            now_dt   = datetime.now()

            # ── Rakip Taraması (günlük 06:00) ───────────────
            today = now_dt.strftime("%Y-%m-%d")
            if is_morning_scan_time() and last_scan_date != today:
                sep("SABAH RAKIP TARAMASI — 06:00")
                scanner = CompetitorScannerAgent()
                scan    = scanner.daily_research_cycle()
                competitor_pats = scan["patterns"]
                save_competitor_insight(competitor_pats, scan["raw_merge"])
                last_scan_date = today
                send_text(
                    f"🌅 *Sabah Rakip Taraması Tamamlandı*\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"Taranan hesap: {scan['account_count']}\n"
                    f"Pattern 1: {competitor_pats.get('pattern_1','')[:70]}\n"
                    f"Yarın dene: {competitor_pats.get('yarin_dene','')[:70]}"
                )

            # ── Pipeline Zamanı Geldi Mi? ────────────────────
            if (now - last_pipeline) < PIPELINE_INTERVAL:
                mins = int((PIPELINE_INTERVAL - (now - last_pipeline)) / 60)
                print(f"  [{now_dt.strftime('%H:%M:%S')}] Pipeline'a {mins}dk kaldı...")
                time.sleep(PRICE_CHECK)
                continue

            # ── Veri Toplama ─────────────────────────────────
            market = MarketDataAgent().run()
            news   = NewsScraperAgent().run()
            geo    = GeopoliticalAgent().run()

            # ── Pipeline ─────────────────────────────────────
            cycle += 1
            t0     = time.time()
            result = run_pipeline_cycle(market, news, geo, [], cycle)
            elapsed = round(time.time() - t0, 1)

            # Performans kaydet
            viral  = result.get("viral", {})
            titles = [v for k, v in result.get("carousel", {}).get("slides", {}).items()
                      if "BASLIK" in k]
            record_performance(
                agent_name="carousel",
                quality    = viral.get("skor", 0),
                viral      = viral.get("skor", 0),
                engagement = viral.get("engagement", "?"),
                decision   = "PENDING",
                title      = titles[0][:80] if titles else "",
            )

            # ── JSON Özet → Orchestrator ──────────────────────
            summary = build_instagram_summary(result)
            _, tok  = format_for_opus(summary)
            dec_res = present_to_orchestrator(summary)
            decision = dec_res["decision"]

            # A/B test için örnek kaydet
            if active_ab_test:
                ab_tester.record_sample(active_ab_test, 1, viral.get("skor", 0))

            # ── Telegram ─────────────────────────────────────
            send_summary(summary)

            # ── Pattern Analizi (her N döngü) ────────────────
            if cycle % ANALYZE_EVERY == 0:
                sep(f"PATTERN ANALİZİ — Döngü #{cycle}")
                analyzer = PatternAnalyzerAgent()
                analysis = analyzer.analyze(competitor_pats)

                opt_result = None

                if decision == "AGENT_REVIZE" or analysis["stats"]["avg_quality"] < 6:
                    sep("PROMPT OPTİMİZASYON BAŞLADI")
                    send_text("🛠 *Prompt optimizasyonu başladı...* (2-4 dk sürebilir)")
                    optimizer = PromptOptimizerAgent()
                    analysis["comp_pattern"] = competitor_pats.get("pattern_1", "")
                    opt_result = optimizer.optimize(analysis)

                    # Yeni A/B testi başlat
                    if opt_result.get("new_version") != opt_result.get("old_version"):
                        active_ab_test = ab_tester.start_test(
                            opt_result["target"],
                            opt_result["old_version"],
                            opt_result["new_version"],
                        )

                notify_learning_update(analysis, opt_result)

            # ── A/B Test Değerlendirme ────────────────────────
            if cycle % AB_EVAL_EVERY == 0 and active_ab_test:
                sep(f"A/B TEST DEĞERLENDİRME — Test #{active_ab_test}")
                ab_result = ab_tester.evaluate(active_ab_test)
                notify_ab_result(ab_result)
                if ab_result.get("status") == "completed":
                    active_ab_test = None  # Testi kapat

            # ── Döngü Özeti ───────────────────────────────────
            stats = get_performance_stats(last_n=20)
            sep(f"Döngü #{cycle} Bitti — {elapsed}s")
            print(f"  Karar        : {decision} ({tok} token)")
            print(f"  Viral Skor   : {viral.get('skor','?')}/10")
            print(f"  Ort. Skor    : {stats['avg_quality']}/10 (son {stats['n']})")
            print(f"  Yayın Oranı  : %{stats['publish_rate']}")
            if active_ab_test:
                print(f"  A/B Test     : #{active_ab_test} devam ediyor")
            print_token_report()

            last_pipeline = time.time()
            print(f"\n  Sonraki: 30 dakika sonra\n")
            time.sleep(PRICE_CHECK)

    except KeyboardInterrupt:
        sep("SİSTEM DURDURULDU")
        stats = get_performance_stats(last_n=100)
        send_text(
            f"⛔ *Continuous Learning Loop Durduruldu*\n"
            f"Toplam döngü: {cycle}\n"
            f"Ort. skor: {stats['avg_quality']}/10\n"
            f"Yayın oranı: %{stats['publish_rate']}"
        )
        print(f"  Toplam döngü : {cycle}")
        print(f"  Ort. skor    : {stats['avg_quality']}/10")
        print_token_report()


if __name__ == "__main__":
    run()
