"""
1 Aylık Simülasyon
==================
30 günlük sistemi hızla simüle eder.
Gerçek LLM çağrısı: sadece kritik agent'lar (research + masterclass).
Diğerleri: fake skor + DB yazma → hız önceliği.

Çıktı:
  - Skill progression tablosu
  - Engagement artış grafiği
  - Kazanan deneyler
  - Quarterly evolution raporu
  - Telegram özet mesajı
"""

import sys, random, time
sys.path.insert(0, ".")

from datetime import datetime, timedelta
from memory.learning_db import (
    init_learning_tables, init_skill_tree, update_skill_score,
    get_skill_tree, save_experiment, add_experiment_score,
    evaluate_experiment, ALL_AGENTS, ALL_SKILLS
)
from agents.learning.performance_tracker import (
    init_tables, record_performance, get_performance_stats, get_best_worst
)
from agents.learning.competitor_scanner  import CompetitorScannerAgent
from agents.learning.knowledge_engine    import KnowledgeExtractionEngine
from agents.learning.masterclass_system  import MasterclassSystem
from agents.learning.testing_lab         import TestingLabAgent
from agents.learning.quarterly_evolution import QuarterlyEvolutionAgent
from utils.telegram_bot import send_text

# ── Simülasyon Ayarları ────────────────────────────────
DAYS        = 30
CYCLES_PER_DAY = 4    # günde 4 içerik döngüsü
MASTERCLASS_DAY = 7   # her 7 günde bir masterclass
LEARNING_RATE   = 0.015  # her döngüde skill puanı artışı

SEP = "═" * 56

print(f"\n{SEP}")
print("  1 AYLIK SİMÜLASYON BAŞLADI")
print(f"  {DAYS} gün × {CYCLES_PER_DAY} döngü = {DAYS*CYCLES_PER_DAY} toplam içerik")
print(SEP)

# DB Başlat
init_learning_tables()
init_skill_tree()
init_tables()

# ── HAFTA 1: Başlangıç Araştırması ────────────────────
print(f"\n{'─'*56}")
print("  HAFTA 1: Temel araştırma + İlk masterclass")
print(f"{'─'*56}")

# Gerçek: Competitor Scanner (2 hesap, hızlı)
scanner = CompetitorScannerAgent()
scan = scanner.daily_research_cycle(targets=[
    {"handle": "@APompliano",    "niche": "crypto/macro",      "lang": "EN"},
    {"handle": "@GrahamStephan", "niche": "personal finance",  "lang": "EN"},
])
print(f"  Rakip tarama: {scan['account_count']} hesap | Pattern: {scan['patterns'].get('pattern_1','')[:50]}")

# Gerçek: Knowledge Engine (hızlı konular)
ke = KnowledgeExtractionEngine()
print("\n  Knowledge Engine — hook_writing ve pain_points öğreniliyor...")
ke.extract_topic("hook_writing")
ke.extract_topic("pain_points")

# Gerçek: Hafta 1 Masterclass
print("\n  Hafta 1 Masterclass: Hook Writing...")
mc = MasterclassSystem()
mc_result = mc.conduct_masterclass(week_number=1, use_32b=False)
print(f"  Masterclass tamamlandı: {mc_result['topic']}")

# ── 30 GÜNLÜK SİMÜLASYON ─────────────────────────────
print(f"\n{'─'*56}")
print("  30 GÜNLÜK SİMÜLASYON (hızlı mod)")
print(f"{'─'*56}")

lab       = TestingLabAgent()
base_q    = 5.5   # başlangıç kalite skoru
day_scores = []
level_ups  = []
sim_start  = time.time()

for day in range(1, DAYS + 1):
    day_base_q = base_q + (day - 1) * 0.08 + random.uniform(-0.3, 0.3)
    day_base_q = min(9.5, max(3.5, day_base_q))

    day_scores_list = []
    for cycle in range(CYCLES_PER_DAY):
        q = day_base_q + random.uniform(-0.5, 0.5)
        q = min(10, max(1, q))
        v = q + random.uniform(-1, 1)
        v = min(10, max(1, v))
        eng = "viral" if q > 8.5 else "yüksek" if q > 7 else "orta" if q > 5 else "düşük"
        dec = "ONAY" if q >= 7 else "REVİZE" if q >= 5 else "RED"

        titles = [f"Gün {day} Döngü {cycle+1} — {['Altın','BTC','Dolar','BIST'][cycle%4]}"]
        record_performance("carousel", round(q,1), round(v,1), eng, dec,
                           title=titles[0])
        day_scores_list.append(q)

        # Skill puanları güncelle (random skill, random agent)
        agent = random.choice(ALL_AGENTS)
        skill = random.choice(ALL_SKILLS)
        result = update_skill_score(agent, skill, q)
        if result.get("leveled_up"):
            level_ups.append({
                "day": day, "agent": agent, "skill": skill,
                "old": result["old_level"], "new": result["new_level"]
            })

    day_avg = sum(day_scores_list) / len(day_scores_list)
    day_scores.append(round(day_avg, 2))

    # Günlük Testing Lab
    lab.daily_testing_cycle(day, day_avg)

    # Haftalık masterclass
    if day % MASTERCLASS_DAY == 0:
        week_n = day // MASTERCLASS_DAY + 1
        mc.conduct_masterclass(week_number=week_n, use_32b=False)

    if day % 5 == 0:
        print(f"  Gün {day:2d}/30 tamamlandı | Ort. skor: {day_avg:.1f}/10")

sim_elapsed = round(time.time() - sim_start, 1)

# ── SONUÇLAR ─────────────────────────────────────────
print(f"\n{SEP}")
print("  SİMÜLASYON SONUÇLARI")
print(SEP)

stats = get_performance_stats(last_n=DAYS * CYCLES_PER_DAY)

# Skill Progression
skill_data = get_skill_tree()
skill_levels = {"beginner": 0, "intermediate": 0, "advanced": 0, "master": 0}
for s in skill_data:
    skill_levels[s.get("level", "beginner")] = skill_levels.get(s.get("level","beginner"), 0) + 1

print(f"""
  📊 PERFORMANS GELİŞİMİ
  ├─ Başlangıç skoru : {day_scores[0]:.1f}/10
  ├─ Bitiş skoru     : {day_scores[-1]:.1f}/10
  ├─ Toplam artış    : {day_scores[-1]-day_scores[0]:+.1f} puan
  ├─ Ort. skor       : {stats['avg_quality']}/10
  └─ Yayın oranı     : %{stats['publish_rate']}

  🎓 SKILL TREE DURUMU
  ├─ Beginner        : {skill_levels['beginner']} skill
  ├─ Intermediate    : {skill_levels['intermediate']} skill
  ├─ Advanced        : {skill_levels['advanced']} skill
  └─ Master          : {skill_levels['master']} skill

  ⬆️  LEVEL UP'LAR ({len(level_ups)} toplam)""")

for lu in level_ups[:5]:
    print(f"  │  Gün {lu['day']:2d}: {lu['agent']:20s} | {lu['skill']:15s} → {lu['old']} → {lu['new']}")
if len(level_ups) > 5:
    print(f"  │  ... ve {len(level_ups)-5} tane daha")

# Haftadan haftaya ilerleme
print(f"\n  📈 HAFTALIK ORTALAMALAR")
for w in range(4):
    start = w * 7 * CYCLES_PER_DAY
    end   = min(start + 7 * CYCLES_PER_DAY, len(day_scores) * CYCLES_PER_DAY)
    week_days = day_scores[w*7 : (w+1)*7]
    if week_days:
        avg = sum(week_days) / len(week_days)
        bar = "█" * int(avg) + "░" * (10 - int(avg))
        trend = "📈" if (w > 0 and avg > sum(day_scores[(w-1)*7:w*7])/max(len(day_scores[(w-1)*7:w*7]),1)) else "📉"
        print(f"  Hafta {w+1}: {bar} {avg:.1f}/10 {trend}")

# ── Quarterly Evolution ───────────────────────────────
print(f"\n{'─'*56}")
print("  QUARTERLY EVOLUTION RAPORU")
print(f"{'─'*56}")
qe = QuarterlyEvolutionAgent()
q_result = qe.run(quarter="2026-Q1")
print(f"\n  Çeyrek Analizi (ilk 400 karakter):")
print(f"  {q_result['analysis'][:400]}")

# ── Peer Learning ─────────────────────────────────────
print(f"\n{'─'*56}")
print("  PEER LEARNING — MVP Öğretiyor")
print(f"{'─'*56}")
peer = mc.peer_learning_session()
print(f"  MVP: {peer['mvp']}")
print(f"  Öğrenciler: {', '.join(peer['students'])}")

# ── Telegram Raporu ───────────────────────────────────
best = get_best_worst(last_n=DAYS*CYCLES_PER_DAY)
top_skill_rows = sorted(skill_data, key=lambda x: x.get("mastery_score",0), reverse=True)
top_skill = top_skill_rows[0] if top_skill_rows else {}

telegram_msg = (
    f"🎓 *1 AYLIK ÖĞRENME RAPORU*\n"
    f"━━━━━━━━━━━━━━━━━━━━\n"
    f"📊 *Performans*\n"
    f"Başlangıç: {day_scores[0]:.1f}/10 → Bitiş: {day_scores[-1]:.1f}/10\n"
    f"Toplam artış: *{day_scores[-1]-day_scores[0]:+.1f} puan*\n"
    f"Yayın oranı: %{stats['publish_rate']}\n\n"
    f"🎓 *Skill Progression*\n"
    f"Level up: {len(level_ups)} kez\n"
    f"En güçlü: {top_skill.get('agent_name','?')} | {top_skill.get('skill','?')} [{top_skill.get('level','?')}]\n"
    f"Master skill: {skill_levels['master']}\n\n"
    f"🏆 *En İyi İçerik*\n"
    + "\n".join(f"  • {c['title'][:40]} ({c['score']}/10)"
                for c in best['best'][:3] if c.get('title')) +
    f"\n\n⚙️ Simülasyon süresi: {sim_elapsed}s\n"
    f"Sistem hazır! `continuous_loop.py` ile başlat. 🚀"
)
send_text(telegram_msg)

print(f"\n{SEP}")
print(f"  TAMAMLANDI — {sim_elapsed}s")
print(f"  Telegram'ı kontrol et!")
print(SEP)
