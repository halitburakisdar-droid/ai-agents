"""
Token Optimizer Test
--------------------
1. Instagram pipeline'ı çalıştır
2. JSON özet üret
3. Orchestrator kararını simüle et
4. Token raporunu göster
5. Code Writer'ın ne yaptığını göster (yavaş olduğu için sadece tanıt)
"""
import sys, json
sys.path.insert(0, ".")

from utils.summary_generator    import build_instagram_summary, format_for_opus, print_summary_stats
from utils.orchestrator_interface import present_to_orchestrator, manual_orchestrator_decision
from utils.decision_logger      import init_decision_table, print_token_report

# DB hazırla
init_decision_table()

print("\n" + "="*52)
print("  TOKEN OPTIMIZER TEST")
print("="*52)

# ── Test 1: Fake özet ile karar testi ────────────────
print("\n[TEST 1] Fake özet → Orchestrator karar")

fake_summary_high = {
    "ts": "2026-03-03 22:45",
    "type": "carousel",
    "title": "Altın Düşerken Dolar Neden Uçuyor?",
    "quality": 8.5,
    "viral": 8.5,
    "engagement": "yüksek",
    "best_time": "20:00-22:00",
    "market": {"altin": "-4.1%", "btc": "-2.1%", "dolar": "+2.9%", "bist": "+0.5%"},
    "signals": {"winner": "DOLAR +2.9%", "loser": "ALTIN -4.1%", "geo_risk": "orta", "altin_etki": "olumlu"},
    "content": {"slides": 10, "hashtags": 25, "caption_chars": 563, "top_trends": ["Altın düşüşü", "Dolar rekor"]},
    "qc": {"guclu": "Dikkat çekici başlıklar, güncel veri", "zayif": "Risk uyarısı eksik", "iyilestirme": "Son slayda sorumluluk reddi ekle"},
    "agent_rec": "ONAY",
}

fake_summary_low = {
    "ts": "2026-03-03 22:45",
    "type": "carousel",
    "title": "Borsa Haberleri",
    "quality": 4,
    "viral": 4,
    "engagement": "düşük",
    "best_time": "12:00-14:00",
    "market": {"altin": "+0.1%", "btc": "+0.0%", "dolar": "-0.1%", "bist": "-0.2%"},
    "signals": {"winner": "ALTIN +0.1%", "loser": "BIST -0.2%", "geo_risk": "düşük", "altin_etki": "nötr"},
    "content": {"slides": 3, "hashtags": 5, "caption_chars": 120, "top_trends": []},
    "qc": {"guclu": "Sade dil", "zayif": "Başlık zayıf, veri yok, CTA yok", "iyilestirme": "Tüm içerik yeniden yazılmalı"},
    "agent_rec": "RED",
}

# Yüksek kalite → ONAY bekleniyor
print("\nSenaryo A: Kaliteli içerik (skor=8.5)")
j1, t1 = format_for_opus(fake_summary_high)
print(f"  Özet token sayısı: {t1}")
r1 = present_to_orchestrator(fake_summary_high)

# Düşük kalite → RED bekleniyor
print("\nSenaryo B: Düşük kalite içerik (skor=4)")
j2, t2 = format_for_opus(fake_summary_low)
print(f"  Özet token sayısı: {t2}")
r2 = present_to_orchestrator(fake_summary_low)

# ── Test 2: Manuel Orchestrator kararı ───────────────
print("\n[TEST 2] Manuel Orchestrator kararı (REVİZE)")
manual_orchestrator_decision(
    fake_summary_high,
    decision="REVİZE",
    note="Son slayda risk uyarısı eklenince yayınlanabilir"
)

# ── Test 3: Token Raporu ─────────────────────────────
print("\n[TEST 3] Token kullanım raporu")
print_token_report()

# ── Test 4: Code Writer tanıtımı (çalıştırmıyoruz) ──
print("\n[TEST 4] Code Writer (qwen3.5:9b) tanıtımı")
print("  Code Writer şu görevler için kullanılır:")
print("  ├─ orchestrator.manual_decision('AGENT_REVIZE') → Code Writer tetiklenir")
print("  ├─ Learning Engine yeni kalıp öğrenince → prompt güncellenir")
print("  └─ Kullanım: from agents.code_writer import CodeWriterAgent")
print()
print("  Örnek çağrı (1-3dk sürer):")
print("  >>> cw = CodeWriterAgent()")
print("  >>> result = cw.improve_prompt('Research Agent',")
print("  ...     current_prompt='...', weakness='risk uyarısı eksik',")
print("  ...     pattern='yüksek skorlu içeriklerde risk uyarısı var')")
print()

# ── Özet ─────────────────────────────────────────────
print("="*52)
print("  SONUÇ: Token Optimizer Sistemi Aktif!")
print("="*52)
print(f"""
  Mimari:
  ├─ Qwen agent'lar → tam içerik üretir
  ├─ summary_generator → ~80-100 token JSON özet
  ├─ orchestrator_interface → kararı loglar
  ├─ decision_logger → SQLite'a yazar, raporlar
  └─ Code Writer (qwen3.5:9b) → sadece gerektiğinde

  Hedef: Günde max 10 karar × ~100 token = 1,000 token/gün
  Aylık: ~31,000 token (Opus için minimal!)
""")
