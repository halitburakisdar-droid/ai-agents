"""
Agent 5: Learning Engine
Model: qwen3.5:9b (think=False)
Görev: DB'deki geçmiş verileri analiz et, kalıp çıkar, sistemi iyileştir
"""

import ollama
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from memory.database import get_recent_for_learning, save_pattern


class LearningEngineAgent:
    NAME = "Learning Engine"
    MODEL = "qwen3.5:9b"

    def _ask(self, prompt: str) -> str:
        r = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.4, "num_predict": 500},
            think=False,
        )
        return r.message.content.strip()

    def run(self, cycle_number: int) -> dict:
        print(f"\n{'─'*50}")
        print(f"  Agent 5: {self.NAME}  [{self.MODEL}]")
        print(f"{'─'*50}")
        print("  Geçmiş veriler analiz ediliyor...")

        records = get_recent_for_learning(limit=20)
        if not records:
            print("  Henüz yeterli veri yok.")
            return {"patterns": [], "suggestions": ""}

        # Özet tablo oluştur
        summary_lines = []
        for r in records:
            summary_lines.append(
                f"Altın:{r.get('gold_change',0):+.1f}% Gümüş:{r.get('silver_change',0):+.1f}% "
                f"Trend:{r.get('trend','?')} Skor:{r.get('quality_score','?')} "
                f"Karar:{r.get('decision','?')}"
            )
        summary = "\n".join(summary_lines)

        prompt = f"""Bir AI sisteminin son {len(records)} döngüsünün verisi:

{summary}

Görev: Bu verilerde ne tür kalıplar var? Sistemi iyileştirmek için ne öğrenebiliriz?

Yanıt formatı (kısa, Türkçe):
KALIP_1: [ne zaman yüksek skor alındığı]
KALIP_2: [hangi piyasa koşulunda içerik daha iyi]
KALIP_3: [kaçınılması gereken durum]
ÖNERİ: [sisteme 1 somut iyileştirme önerisi]"""

        raw = self._ask(prompt)
        print(f"\n  Öğrenilen kalıplar:\n{raw}\n")

        # Kalıpları DB'ye kaydet
        patterns = []
        for line in raw.splitlines():
            if line.startswith("KALIP") and ":" in line:
                desc = line.split(":", 1)[1].strip()
                patterns.append(desc)
                save_pattern(
                    pattern_type="auto_learned",
                    description=desc,
                    confidence=0.7,
                    source=f"cycles_up_to_{cycle_number}"
                )

        return {
            "agent": self.NAME,
            "patterns": patterns,
            "suggestions": raw,
            "records_analyzed": len(records),
        }
