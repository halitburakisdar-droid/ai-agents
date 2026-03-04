"""
Pattern Analyzer
================
Geçmiş performans + rakip analizinden kazanan pattern'leri bulur.
Model: qwen3.5:9b (think=False)
"""

import ollama
import sqlite3
import json
from pathlib import Path
from agents.learning.performance_tracker import get_best_worst, get_performance_stats, DB

class PatternAnalyzerAgent:
    NAME  = "Pattern Analyzer"
    MODEL = "qwen3.5:9b"

    def _ask(self, prompt: str) -> str:
        r = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.4, "num_predict": 500},
            think=False,
        )
        return r.message.content.strip()

    def analyze(self, competitor_patterns: dict = None) -> dict:
        print(f"\n  [{self.NAME}] Pattern analizi başladı...")

        # DB'den performans verisi al
        stats    = get_performance_stats(last_n=30)
        bw       = get_best_worst(last_n=30)
        best_str = "\n".join(f"  {r['title'][:50]} → {r['score']}/10 ({r['decision']})"
                             for r in bw["best"] if r["title"])
        worst_str = "\n".join(f"  {r['title'][:50]} → {r['score']}/10 ({r['decision']})"
                              for r in bw["worst"] if r["title"])

        comp_patterns = ""
        if competitor_patterns:
            comp_patterns = f"""
Rakip analizinden öğrenilenler:
- {competitor_patterns.get('pattern_1', '')}
- {competitor_patterns.get('pattern_2', '')}
- {competitor_patterns.get('pattern_3', '')}
- Türkiye uyarlaması: {competitor_patterns.get('tr_uyarlama', '')}
- Kaçınılacak: {competitor_patterns.get('kacin', '')}"""

        prompt = f"""AI içerik sisteminin performans verisini analiz et.

GENEL İSTATİSTİK (son {stats['n']} döngü):
- Ortalama kalite skoru: {stats['avg_quality']}/10
- Ortalama viral skor: {stats['avg_viral']}/10
- Yayınlama oranı: %{stats['publish_rate']}

EN İYİ İÇERİKLER:
{best_str or '(henüz veri yok)'}

EN KÖTÜ İÇERİKLER:
{worst_str or '(henüz veri yok)'}
{comp_patterns}

Görev: Sistemi iyileştirmek için ne yapılmalı?

Format:
SORUN_1: [ana sorun]
SORUN_2: [ikinci sorun]
COZUM_1: [somut çözüm — prompt değişikliği]
COZUM_2: [somut çözüm]
ONCELIKLI_AGENT: [hangisi iyileştirilmeli: Research/Content/Quality]
BEKLENEN_ARTIS: [skor artışı tahmini, örn: +1.5 puan]
ACIKLAMA: [2 cümle genel yorum]"""

        raw = self._ask(prompt)
        lines = {}
        for line in raw.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                lines[k.strip()] = v.strip()

        result = {
            "agent":             self.NAME,
            "stats":             stats,
            "sorun_1":           lines.get("SORUN_1", ""),
            "sorun_2":           lines.get("SORUN_2", ""),
            "cozum_1":           lines.get("COZUM_1", ""),
            "cozum_2":           lines.get("COZUM_2", ""),
            "oncelikli_agent":   lines.get("ONCELIKLI_AGENT", "Content"),
            "beklenen_artis":    lines.get("BEKLENEN_ARTIS", ""),
            "aciklama":          lines.get("ACIKLAMA", ""),
            "raw":               raw,
        }

        print(f"    Öncelikli agent: {result['oncelikli_agent']}")
        print(f"    Beklenen artış : {result['beklenen_artis']}")
        return result
