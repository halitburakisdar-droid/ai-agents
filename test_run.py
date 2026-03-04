"""2 döngü test scripti"""
import sys, time
sys.path.insert(0, '.')

from memory.database import init_db, save_content, save_decision, save_metrics, get_stats
from agents.price_monitor      import PriceMonitorAgent
from agents.research_agent     import ResearchAgent
from agents.content_creator    import ContentCreatorAgent
from agents.quality_controller import QualityControllerAgent
from agents.learning_engine    import LearningEngineAgent

init_db()

agents = {
    "price":    PriceMonitorAgent(),
    "research": ResearchAgent(),
    "content":  ContentCreatorAgent(),
    "quality":  QualityControllerAgent(),
    "learning": LearningEngineAgent(),
}
learned = []

for cycle in range(1, 3):
    SEP = "=" * 52
    print(f"\n{SEP}")
    print(f"  TEST DONGUSU #{cycle}")
    print(SEP)
    results = {}
    t0 = time.time()

    results["price"]    = agents["price"].run()
    results["research"] = agents["research"].run(results["price"])
    results["content"]  = agents["content"].run(results["price"], results["research"])
    results["quality"]  = agents["quality"].run(results["content"], results["research"], learned)

    total = round(time.time() - t0, 1)
    cid = save_content(results)
    save_metrics({
        "cycle": cycle, "price_time": 0, "research_time": 0,
        "content_time": 0, "quality_time": 0, "total_time": total,
        "quality_score": results["quality"].get("skor", 0),
        "had_alarm": bool(results["price"]["alarms"]),
    })
    save_decision(cid, results["quality"].get("karar", "?"), "test", cycle)
    print(f"\n  Skor: {results['quality'].get('skor','?')}/10  Sure: {total}s")

    if cycle % 2 == 0:
        ld = agents["learning"].run(cycle)
        learned = ld.get("patterns", [])

# Özet
stats = get_stats()
SEP = "=" * 52
print(f"\n{SEP}")
print("  VERITABANI OZETI")
print(SEP)
print(f"  Toplam kayit  : {stats['total_cycles']}")
print(f"  Ort. kalite   : {stats['avg_quality']}/10")
print(f"  Yayin karari  : {stats['publish_count']}")
print(f"  Kalip sayisi  : {stats['pattern_count']}")
print("  Son kayitlar  :")
for r in stats["last5"]:
    print(f"    Trend:{r['trend']}  Skor:{r['quality_score']}  Altin:{r['gold_change']:+.2f}%")
