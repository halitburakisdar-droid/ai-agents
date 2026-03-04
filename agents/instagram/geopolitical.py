"""
Agent: Geopolitical — qwen3.5:9b
Orta Doğu gelişmeleri, FED haberleri, jeopolitik risk analizi
"""
import ollama


class GeopoliticalAgent:
    NAME = "Geopolitical"
    MODEL = "qwen3.5:9b"

    def _ask(self, prompt: str) -> str:
        r = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.5, "num_predict": 350},
            think=False,
        )
        return r.message.content.strip()

    def run(self) -> dict:
        print(f"  [{self.NAME}] Jeopolitik analiz...")
        prompt = """Türk Instagram takipçileri için güncel (demo) jeopolitik özeti hazırla.
Konular: Orta Doğu gerilimi, FED faiz kararı beklentisi, petrol fiyatları.

Format:
RISKO: [yüksek/orta/düşük]
FED: [tek cümle FED beklentisi]
ORTADOGU: [tek cümle gelişme özeti]
PETROL: [fiyat tahmini yönü: artacak/düşecek/sabit]
ALTIN_ETKİ: [bu gelişmelerin altına etkisi: olumlu/olumsuz/nötr]
OZET: [2 cümle genel değerlendirme]"""

        raw = self._ask(prompt)
        lines = {}
        for line in raw.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                lines[k.strip()] = v.strip()

        return {
            "agent":      self.NAME,
            "risk_level": lines.get("RISKO", "orta"),
            "fed":        lines.get("FED", ""),
            "ortadogu":   lines.get("ORTADOGU", ""),
            "petrol":     lines.get("PETROL", "sabit"),
            "altin_etki": lines.get("ALTIN_ETKİ", "nötr"),
            "ozet":       lines.get("OZET", raw[:200]),
            "raw":        raw,
        }
