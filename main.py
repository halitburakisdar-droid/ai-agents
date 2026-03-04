"""
AI Agent Sistemi
================
[1] Price Monitor   — qwen3.5:0.8b (Python logic)
[2] Research Agent  — qwen3.5:9b
[3] Content Creator — qwen3.5:9b
[4] Orchestrator    — Claude Code (Opus 4.6) ← bu konuşmada karar verir
"""

import time, sys, os
sys.path.insert(0, os.path.dirname(__file__))

from agents.price_monitor   import PriceMonitorAgent
from agents.research_agent  import ResearchAgent
from agents.content_creator import ContentCreatorAgent


def run_pipeline():
    print("\n" + "═"*52)
    print("  AI AGENT SİSTEMİ")
    print("  Price Monitor → Research → Content → Orchestrator")
    print("═"*52)

    results = {}
    timings = {}

    # ── Agent 1 ──────────────────────────────────────────
    t = time.time()
    results["price"] = PriceMonitorAgent().run()
    timings["price"] = round(time.time() - t, 1)

    # ── Agent 2 ──────────────────────────────────────────
    t = time.time()
    results["research"] = ResearchAgent().run(results["price"])
    timings["research"] = round(time.time() - t, 1)

    # ── Agent 3 ──────────────────────────────────────────
    t = time.time()
    results["content"] = ContentCreatorAgent().run(results["price"], results["research"])
    timings["content"] = round(time.time() - t, 1)

    # ── Özet ─────────────────────────────────────────────
    p, r, c = results["price"], results["research"], results["content"]

    print("\n" + "═"*52)
    print("  ORCHESTRATOR (Claude Opus 4.6) İÇİN VERİ PAKETİ")
    print("═"*52)

    print(f"""
  📊 FİYATLAR
  ├─ Altın : ${p['prices']['gold']:>8.2f}  ({p['changes']['gold']:+.2f}%)
  └─ Gümüş : ${p['prices']['silver']:>8.2f}  ({p['changes']['silver']:+.2f}%)
  {'  🚨 ALARM: ' + ', '.join(a['metal'].upper()+' '+a['direction'] for a in p['alarms']) if p['alarms'] else '  ✅ Alarm yok'}

  📈 ANALİZ  [{r['trend']} | {r['guven']} güven | TAVSİYE: {r['tavsiye']}]
  {r['analiz']}

  📱 İÇERİK (3 slayt)
  ├─ {c['slides']['slide_1']['baslik']}
  │    {c['slides']['slide_1']['metin']}
  ├─ {c['slides']['slide_2']['baslik']}
  │    {c['slides']['slide_2']['metin']}
  └─ {c['slides']['slide_3']['baslik']}
       {c['slides']['slide_3']['metin']}

  ⏱  Süreler: Price={timings['price']}s | Research={timings['research']}s | Content={timings['content']}s
     Toplam: {sum(timings.values())}s
""")

    print("═"*52)
    print("  Pipeline tamamlandı. Claude Code final kararını veriyor...")
    print("═"*52 + "\n")

    return results


if __name__ == "__main__":
    run_pipeline()
