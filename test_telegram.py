"""Telegram entegrasyon testi — pipeline çalıştır ve mesaj gönder"""
import sys, time
sys.path.insert(0, ".")

from agents.instagram.market_data    import MarketDataAgent
from agents.instagram.news_scraper   import NewsScraperAgent
from agents.instagram.geopolitical   import GeopoliticalAgent
from agents.instagram.carousel_agent import CarouselAgent
from agents.instagram.caption_generator import CaptionGeneratorAgent
from agents.instagram.viral_predictor   import ViralPredictorAgent
from utils.summary_generator  import build_instagram_summary, format_for_opus, print_summary_stats
from utils.orchestrator_interface import present_to_orchestrator
from utils.decision_logger    import init_decision_table, print_token_report
from utils.telegram_bot       import send_summary, send_text, start_bot_listener

init_decision_table()

print("\n" + "="*52)
print("  TELEGRAM ENTEGRASYON TESTİ")
print("="*52)

# Adım 1: Hoş geldin mesajı
print("\n[1] Test mesajı gönderiliyor...")
send_text(
    "🧪 *Test Başladı!*\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "Pipeline çalışıyor, birazdan içerik özeti gelecek...\n"
    "✅ Onayla veya ❌ Reddet butonlarını test edebilirsin."
)
print("  ✅ Hoş geldin mesajı gönderildi")
time.sleep(2)

# Adım 2: Gerçek pipeline çalıştır
print("\n[2] Instagram pipeline çalıştırılıyor...")
t0 = time.time()

market   = MarketDataAgent().run()
news     = NewsScraperAgent().run()
geo      = GeopoliticalAgent().run()
carousel = CarouselAgent().run(market, news, geo)
titles   = [v for k, v in carousel.get("slides", {}).items() if "BASLIK" in k]
winner   = market.get("winner", {})
caption  = CaptionGeneratorAgent().run("carousel", f"{winner.get('sembol','?')} {winner.get('degisim',0):+.1f}%", market)
ht_n     = len(caption.get("hashtag_tr","").split()) + len(caption.get("hashtag_en","").split())
viral    = ViralPredictorAgent().run("carousel", titles, caption.get("caption",""), ht_n)

elapsed = round(time.time() - t0, 1)
print(f"  ✅ Pipeline tamamlandı ({elapsed}s)")

# Adım 3: JSON özet
print("\n[3] JSON özet üretiliyor...")
results = {"market": market, "news": news, "geo": geo,
           "carousel": carousel, "caption": caption,
           "viral": viral, "trends": {"trends": []}}
summary      = build_instagram_summary(results)
json_str, tokens = format_for_opus(summary)
print_summary_stats(summary, tokens)

# Adım 4: Orchestrator karar
print("\n[4] Orchestrator kararı...")
decision = present_to_orchestrator(summary)
print(f"  Karar: {decision['decision']} ({decision['total_tokens']} token)")

# Adım 5: Telegram'a gönder
print("\n[5] Telegram'a özet gönderiliyor (butonlarla)...")
result = send_summary(summary)

# Adım 6: Buton dinleyici başlat (30sn bekle)
if "error" not in result:
    print("\n[6] Buton dinleyici başlatılıyor (30sn bekle, butona bas)...")
    start_bot_listener()
    time.sleep(30)
    print("  (30sn geçti, test tamamlandı)")

# Token raporu
print("\n[7] Token raporu:")
print_token_report()

print("\n" + "="*52)
print("  TEST TAMAMLANDI!")
print("  Telefona bak — Telegram'da mesaj var!")
print("="*52)
