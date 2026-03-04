"""
Agent: Morning Bulletin — qwen3.5:9b
3-5 slaytlık sabah Instagram Story scripti, basit dil
"""
import ollama


class MorningBulletinAgent:
    NAME = "Morning Bulletin"
    MODEL = "qwen3.5:9b"

    def _ask(self, prompt: str) -> str:
        r = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.6, "num_predict": 500},
            think=False,
        )
        return r.message.content.strip()

    def run(self, market: dict, news: dict, geo: dict) -> dict:
        print(f"  [{self.NAME}] Sabah bülteni hazırlanıyor...")

        d = market["data"]
        top_news = news["news"][:2] if news["news"] else []
        news_text = " | ".join(n["baslik"] for n in top_news) if top_news else "Piyasalar hareketli"

        prompt = f"""Sabah Instagram Story scripti yaz (3-5 slayt). Hedef kitle: sıradan Türk yatırımcı.
BASIT dil kullan, finans jargonu KULLANMA. Emoji olsun.

Piyasa verileri:
- Altın: {d['ALTIN']['fiyat']} $ ({d['ALTIN']['degisim']:+.1f}%)
- BTC: {d['BTC']['fiyat']:,.0f} $ ({d['BTC']['degisim']:+.1f}%)
- BIST: {d['BIST100']['fiyat']:,.0f} ({d['BIST100']['degisim']:+.1f}%)
- Dolar: {d['DOLAR']['fiyat']} TL

Önemli gelişme: {news_text}
Jeopolitik risk: {geo['risk_level']}

Format (her slayt ayrı):
STORY_1: [kısa başlık + emoji]
STORY_2: [altın/dolar haberi, 1-2 cümle]
STORY_3: [BTC/borsa, 1-2 cümle]
STORY_4: [günün özeti, tavsiye]
STORY_5: [soru/etkileşim davet]"""

        raw = self._ask(prompt)
        stories = {}
        for line in raw.splitlines():
            if line.startswith("STORY_") and ":" in line:
                k, v = line.split(":", 1)
                stories[k.strip()] = v.strip()

        print(f"    {len(stories)} story slaydı hazır")
        return {"agent": self.NAME, "stories": stories, "raw": raw}
