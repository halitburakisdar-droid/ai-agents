"""
Agent: News Scraper — qwen3.5:4b
Bloomberg/Reuters tarzı fake finansal haberler üret
"""
import ollama
from datetime import datetime


class NewsScraperAgent:
    NAME = "News Scraper"
    MODEL = "qwen3.5:4b"

    def _ask(self, prompt: str) -> str:
        r = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.7, "num_predict": 400},
            think=False,
        )
        return r.message.content.strip()

    def run(self) -> dict:
        print(f"  [{self.NAME}] Haberler toplanıyor...")
        prompt = """Bloomberg/Reuters tarzı 3 adet Türkçe finansal haber özeti yaz (demo/sahte veri).
Konular: altın piyasası, FED kararları, küresel ekonomi.

Format:
HABER_1: [başlık] | [tek cümle özet] | [kaynak: Bloomberg/Reuters/FT]
HABER_2: [başlık] | [tek cümle özet] | [kaynak]
HABER_3: [başlık] | [tek cümle özet] | [kaynak]"""

        raw = self._ask(prompt)
        news_items = []
        for line in raw.splitlines():
            if line.startswith("HABER_") and "|" in line:
                parts = line.split("|")
                if len(parts) >= 3:
                    baslik = parts[0].split(":", 1)[-1].strip()
                    ozet   = parts[1].strip()
                    kaynak = parts[2].strip()
                    news_items.append({"baslik": baslik, "ozet": ozet, "kaynak": kaynak})

        if not news_items:
            # Fallback: raw'dan ilk 3 satırı al
            for line in raw.splitlines()[:3]:
                if line.strip():
                    news_items.append({"baslik": line[:80], "ozet": "", "kaynak": "Demo"})

        print(f"    {len(news_items)} haber toplandı")
        return {"agent": self.NAME, "news": news_items, "raw": raw,
                "timestamp": datetime.now().strftime("%H:%M")}
