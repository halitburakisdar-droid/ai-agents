"""
Continuous Learning sistemi hızlı testi.
Pipeline yerine fake skor enjekte ederek tüm modülleri doğrular.
"""
import sys, time
sys.path.insert(0, ".")

from agents.learning.competitor_scanner  import CompetitorScannerAgent
from agents.learning.performance_tracker import init_tables, record_performance, get_performance_stats, get_best_worst
from agents.learning.pattern_analyzer   import PatternAnalyzerAgent
from agents.learning.ab_tester          import ABTesterAgent
from utils.telegram_bot                 import send_text

init_tables()

SEP = "=" * 54

# ── ADIM 1: Fake performans verisi ekle ──────────────
print(f"\n{SEP}\n  ADIM 1: Performans verisi ekleniyor\n{SEP}")
test_data = [
    ("ALTIN DÜŞÜYOR", 8.5, 8.0, "yüksek", "ONAY"),
    ("DOLAR REKOR", 7.0, 6.5, "orta",   "REVİZE"),
    ("BTC ÇÖKÜYOR", 9.0, 9.5, "viral",  "ONAY"),
    ("BORSA HABERLERI", 4.0, 3.5, "düşük", "RED"),
    ("ALTIN REKOR", 8.0, 7.5, "yüksek", "ONAY"),
    ("GÜMÜŞ FIRSATI", 6.5, 6.0, "orta",  "REVİZE"),
]
for title, q, v, eng, dec in test_data:
    record_performance("carousel", q, v, eng, dec, title=title)
    print(f"  Eklendi: {title:20s} → {q}/10 [{dec}]")

stats = get_performance_stats(last_n=20)
print(f"\n  Ort. kalite: {stats['avg_quality']}/10 | Yayın: %{stats['publish_rate']}")

# ── ADIM 2: Competitor Scanner (2 hesap, hızlı) ──────
print(f"\n{SEP}\n  ADIM 2: Competitor Scanner (2 hesap)\n{SEP}")
scanner = CompetitorScannerAgent()
scan = scanner.daily_research_cycle(targets=[
    {"handle": "@GrahamStephan", "niche": "personal finance", "lang": "EN"},
    {"handle": "@paraborsa",     "niche": "Türk borsa",       "lang": "TR"},
])
comp_pats = scan["patterns"]
print(f"\n  Pattern 1 : {comp_pats.get('pattern_1','')[:70]}")
print(f"  TR Adapt  : {comp_pats.get('tr_uyarlama','')[:70]}")
print(f"  Yarın Dene: {comp_pats.get('yarin_dene','')[:70]}")

# Telegram'a gönder
send_text(
    f"📡 *Rakip Tarama Sonucu*\n"
    f"━━━━━━━━━━━━━━━━━━━━\n"
    f"Taranan: {scan['account_count']} hesap\n"
    f"Pattern: {comp_pats.get('pattern_1','')[:60]}\n"
    f"Yarın dene: {comp_pats.get('yarin_dene','')[:60]}"
)

# ── ADIM 3: Pattern Analyzer ──────────────────────────
print(f"\n{SEP}\n  ADIM 3: Pattern Analyzer\n{SEP}")
analyzer = PatternAnalyzerAgent()
analysis = analyzer.analyze(competitor_patterns=comp_pats)
print(f"\n  Sorun 1  : {analysis['sorun_1'][:70]}")
print(f"  Çözüm 1  : {analysis['cozum_1'][:70]}")
print(f"  Öncelik  : {analysis['oncelikli_agent']}")
print(f"  Beklenti : {analysis['beklenen_artis']}")

# ── ADIM 4: A/B Tester ───────────────────────────────
print(f"\n{SEP}\n  ADIM 4: A/B Tester\n{SEP}")
ab = ABTesterAgent()
ab.MIN_SAMPLES = 3  # test için düşür

test_id = ab.start_test("carousel", v_a=1, v_b=2)
# Fake örnekler
for score in [7.0, 8.0, 7.5]:
    ab.record_sample(test_id, 1, score)  # A versiyonu
for score in [8.5, 9.0, 8.0]:
    ab.record_sample(test_id, 2, score)  # B versiyonu (daha iyi)

result = ab.evaluate(test_id)
print(f"\n  Durum    : {result.get('status')}")
print(f"  Kazanan  : Versiyon {result.get('winner_label')} ({'v'+str(result.get('winner'))})")
print(f"  A skoru  : {result.get('avg_a')}/10  B skoru: {result.get('avg_b')}/10")
print(f"  Fark     : +{result.get('improvement')} puan")

# ── Özet Rapor ────────────────────────────────────────
print(f"\n{SEP}\n  ÖZET RAPOR\n{SEP}")
bw = get_best_worst()
print("\n  En iyi içerikler:")
for r in bw["best"]:
    if r["title"]:
        print(f"    {r['score']}/10  {r['title']}")
print("\n  En kötü içerikler:")
for r in bw["worst"]:
    if r["title"]:
        print(f"    {r['score']}/10  {r['title']}")

send_text(
    f"✅ *Continuous Learning Testi Tamamlandı!*\n"
    f"━━━━━━━━━━━━━━━━━━━━\n"
    f"📊 Ort. skor: {stats['avg_quality']}/10\n"
    f"🔍 Sorun: {analysis['sorun_1'][:60]}\n"
    f"🏆 A/B Kazanan: Versiyon {result.get('winner_label')} (+{result.get('improvement')} puan)\n"
    f"🎯 Öncelikli agent: {analysis['oncelikli_agent']}\n"
    f"📈 Beklenen artış: {analysis['beklenen_artis']}\n\n"
    f"Sistem hazır! `continuous_loop.py` ile başlatabilirsin. 🚀"
)

print(f"\n{SEP}")
print("  TÜM MODÜLLER ÇALIŞIYOR!")
print("  Telegram'ı kontrol et.")
print(SEP)
print("\n  Sistemi başlatmak için:")
print("  python continuous_loop.py")
