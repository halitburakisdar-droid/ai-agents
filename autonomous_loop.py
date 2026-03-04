"""
Otonom Döngü v2 — Token Optimize + Telegram + Code Writer
==========================================================
Her 30 dakikada:
  1. Price Monitor → fiyat kontrol
  2. Alarm VEYA süre doldu → Instagram pipeline çalıştır
  3. JSON özet → Telegram'a gönder (✅/❌ butonlar)
  4. Opus limiti dolunca → agent tavsiyesi otomatik kullan
  5. AGENT_REVIZE kararı → Code Writer tetikle
  6. Her 5 döngü → Learning Engine

Durdurmak: Ctrl+C
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime
from agents.price_monitor        import PriceMonitorAgent
from agents.research_agent       import ResearchAgent
from agents.content_creator      import ContentCreatorAgent
from agents.quality_controller   import QualityControllerAgent
from agents.learning_engine      import LearningEngineAgent
from agents.instagram.news_scraper      import NewsScraperAgent
from agents.instagram.market_data       import MarketDataAgent
from agents.instagram.geopolitical      import GeopoliticalAgent
from agents.instagram.morning_bulletin  import MorningBulletinAgent
from agents.instagram.carousel_agent    import CarouselAgent
from agents.instagram.caption_generator import CaptionGeneratorAgent
from agents.instagram.viral_predictor   import ViralPredictorAgent
from agents.code_writer          import CodeWriterAgent
from memory.database             import init_db, save_content, save_decision, save_metrics, get_stats
from utils.summary_generator     import build_instagram_summary, format_for_opus
from utils.orchestrator_interface import present_to_orchestrator
from utils.decision_logger       import print_token_report
from utils.telegram_bot          import send_summary, send_text, start_bot_listener

# ── Ayarlar ────────────────────────────────────────────
PRICE_INTERVAL    = 60      # saniye: fiyat kontrol aralığı
PIPELINE_INTERVAL = 30 * 60 # 30 dakika: tam pipeline
LEARNING_EVERY    = 5       # her kaç döngüde learning engine
DAILY_OPUS_LIMIT  = 10      # günlük Opus karar limiti


def sep(title="", w=52):
    print(f"\n{'═'*w}")
    if title:
        print(f"  {title}")
        print(f"{'═'*w}")


def run_instagram_mini(market_data: dict) -> dict:
    """Hızlı Instagram paketi: carousel + caption + viral."""
    news    = NewsScraperAgent().run()
    geo     = GeopoliticalAgent().run()
    carousel = CarouselAgent().run(market_data, news, geo)
    titles  = [v for k, v in carousel.get("slides", {}).items() if "BASLIK" in k]
    winner  = market_data.get("winner", {})
    summary_text = f"{winner.get('sembol','?')} {winner.get('degisim',0):+.1f}%"
    caption = CaptionGeneratorAgent().run("carousel", summary_text, market_data)
    ht_n    = len(caption.get("hashtag_tr","").split()) + len(caption.get("hashtag_en","").split())
    viral   = ViralPredictorAgent().run("carousel", titles, caption.get("caption",""), ht_n)
    return {"market": market_data, "news": news, "geo": geo,
            "carousel": carousel, "caption": caption, "viral": viral,
            "trends": {"trends": []}}


def trigger_code_writer(summary: dict, decision_note: str):
    """AGENT_REVIZE kararı gelince Code Writer'ı tetikle."""
    print("\n  🛠  CODE WRITER tetikleniyor (qwen3.5:9b)...")
    send_text("🛠 *Code Writer aktif!* qwen3.5:9b agent promptunu optimize ediyor...")

    weakness = summary.get("qc", {}).get("zayif", "Genel iyileştirme gerekli")
    pattern  = summary.get("qc", {}).get("iyilestirme", "")

    cw = CodeWriterAgent()

    # Research Agent promptunu iyileştir (en sık sorunlu olan)
    from agents.research_agent import ResearchAgent
    import inspect
    src = inspect.getsource(ResearchAgent)
    # Sadece prompt kısmını al
    prompt_start = src.find('prompt = f"""')
    prompt_end   = src.find('"""', prompt_start + 20) + 3
    current_prompt = src[prompt_start:prompt_end][:400] if prompt_start > 0 else "mevcut prompt"

    result = cw.improve_prompt(
        agent_name="Research Agent",
        current_prompt=current_prompt,
        weakness=weakness,
        pattern=pattern,
    )

    report = (
        f"🛠 *Code Writer Raporu*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Agent: Research Agent\n"
        f"Zayıflık: {weakness[:80]}\n"
        f"Süre: {result.get('elapsed','?')}s\n\n"
        f"*Değişiklikler:*\n{result.get('changes','')[:200]}\n\n"
        f"✅ Öneri kaydedildi."
    )
    send_text(report)
    print(f"  ✅ Code Writer tamamlandı ({result.get('elapsed','?')}s)")
    return result


def run():
    sep("OTONOM DÖNGÜ v2 — BAŞLADI")
    print(f"  Pipeline aralığı : 30 dakika")
    print(f"  Fiyat kontrolü   : {PRICE_INTERVAL}sn")
    print(f"  Telegram         : aktif")
    print(f"  Code Writer      : AGENT_REVIZE'de tetiklenecek")
    print(f"  Durdurmak        : Ctrl+C")

    init_db()
    start_bot_listener()          # Buton dinleyici arka planda başla
    send_text("🚀 *AI Agent Sistemi başladı!*\nHer 30 dakikada içerik üretip sana göndereceğim.")

    market_agent  = MarketDataAgent()
    price_agent   = PriceMonitorAgent()
    research_agent = ResearchAgent()
    content_agent  = ContentCreatorAgent()
    quality_agent  = QualityControllerAgent()
    learning_agent = LearningEngineAgent()

    full_cycle = 0
    last_pipeline_t = 0
    learned_patterns = []

    try:
        while True:
            now = time.time()
            ts  = datetime.now().strftime("%H:%M:%S")

            # ── Fiyat Kontrolü ───────────────────────────────
            print(f"\n[{ts}] Fiyat kontrol...")
            price_data = price_agent.run()
            market_data = market_agent.run()

            has_alarm = price_data["alarm_count"] > 0
            time_since = now - last_pipeline_t
            run_full = has_alarm or (time_since >= PIPELINE_INTERVAL)

            if not run_full:
                mins = int((PIPELINE_INTERVAL - time_since) / 60)
                print(f"  ⏳ Pipeline'a {mins}dk kaldı | Alarm: {'VAR 🚨' if has_alarm else 'YOK'}")
                time.sleep(PRICE_INTERVAL)
                continue

            # ── Tam Pipeline ─────────────────────────────────
            full_cycle += 1
            sep(f"DÖNGÜ #{full_cycle} — {'🚨 ALARM' if has_alarm else '⏰ ZAMANLANDI'}")
            t0 = time.time()

            # Gold/Silver pipeline
            research = research_agent.run(price_data)
            content  = content_agent.run(price_data, research)
            quality  = quality_agent.run(content, research, learned_patterns)

            gold_results = {"price": price_data, "research": research,
                           "content": content, "quality": quality}
            cid = save_content(gold_results)

            # Instagram mini paketi
            ig = run_instagram_mini(market_data)

            total_t = round(time.time() - t0, 1)
            save_metrics({"cycle": full_cycle, "price_time": 0, "research_time": 0,
                          "content_time": 0, "quality_time": 0, "total_time": total_t,
                          "quality_score": quality.get("skor", 0), "had_alarm": has_alarm})

            # ── JSON Özet → Orchestrator ──────────────────────
            summary      = build_instagram_summary(ig)
            _, tok       = format_for_opus(summary)
            decision_res = present_to_orchestrator(summary)
            decision     = decision_res["decision"]

            save_decision(cid, decision, decision_res.get("note", ""), full_cycle)

            # ── Telegram Gönder ───────────────────────────────
            print(f"\n  📨 Telegram'a gönderiliyor...")
            send_summary(summary)

            # ── Code Writer (AGENT_REVIZE) ────────────────────
            if decision == "AGENT_REVIZE":
                trigger_code_writer(summary, decision_res.get("note", ""))

            # ── Learning Engine ───────────────────────────────
            if full_cycle % LEARNING_EVERY == 0:
                sep("LEARNING ENGINE")
                ld = learning_agent.run(full_cycle)
                learned_patterns = ld.get("patterns", [])
                send_text(f"🧠 *Learning Engine*\n{len(learned_patterns)} yeni kalıp öğrenildi.")

            # ── Döngü Özeti ───────────────────────────────────
            stats = get_stats()
            sep(f"Döngü #{full_cycle} Bitti — {total_t}s")
            print(f"  Karar    : {decision}")
            print(f"  QC Skor  : {quality.get('skor','?')}/10")
            print(f"  Ort.Kalite: {stats['avg_quality']}/10 ({stats['total_cycles']} döngü)")
            print_token_report()

            last_pipeline_t = time.time()
            print(f"\n  Sonraki pipeline: 30 dakika sonra\n")
            time.sleep(PRICE_INTERVAL)

    except KeyboardInterrupt:
        sep("SİSTEM DURDURULDU")
        send_text("⛔ *AI Agent sistemi durduruldu.* Görüşmek üzere!")
        stats = get_stats()
        print(f"  Toplam döngü : {full_cycle}")
        print(f"  Ort. kalite  : {stats['avg_quality']}/10")
        print_token_report()


if __name__ == "__main__":
    run()
