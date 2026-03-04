"""
Agent: Trend Detector — qwen3.5:9b
Haftalık top 7 finansal/sosyal trend (demo)
"""
import ollama
from datetime import datetime


class TrendDetectorAgent:
    NAME = "Trend Detector"
    MODEL = "qwen3.5:9b"

    def _ask(self, prompt: str) -> str:
        r = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.6, "num_predict": 400},
            think=False,
        )
        return r.message.content.strip()

    def run(self, market: dict) -> dict:
        print(f"  [{self.NAME}] Haftanın trendleri tespit ediliyor...")

        d = market["data"]
        btc_dir = "yükselen" if d["BTC"]["degisim"] > 0 else "düşen"
        altin_dir = "güçlü" if d["ALTIN"]["degisim"] > 0 else "zayıf"

        prompt = f"""Türkiye'deki finansal sosyal medya için bu hafta top 7 trend konuyu listele (demo/tahmin).
Bağlam: Altın {altin_dir}, BTC {btc_dir}.

Format:
TREND_1: [konu] | [neden trend] | [içerik önerisi]
TREND_2: [konu] | [neden trend] | [içerik önerisi]
...
TREND_7: [konu] | [neden trend] | [içerik önerisi]"""

        raw = self._ask(prompt)
        trends = []
        for line in raw.splitlines():
            if line.startswith("TREND_") and "|" in line:
                parts = line.split("|")
                konu = parts[0].split(":", 1)[-1].strip()
                neden = parts[1].strip() if len(parts) > 1 else ""
                oneri = parts[2].strip() if len(parts) > 2 else ""
                trends.append({"konu": konu, "neden": neden, "icerik_onerisi": oneri})

        print(f"    {len(trends)} trend belirlendi")
        return {
            "agent":  self.NAME,
            "trends": trends,
            "hafta":  datetime.now().strftime("%Y-W%W"),
            "raw":    raw,
        }
