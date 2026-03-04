"""
Agent: Carousel Agent — qwen3.5:9b
10 slaytlık derinlemesine carousel, 25-55 yaş, data + gerçekler karışımı
"""
import ollama


class CarouselAgent:
    NAME = "Carousel Agent"
    MODEL = "qwen3.5:9b"

    def _ask(self, prompt: str) -> str:
        r = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.7, "num_predict": 800},
            think=False,
        )
        return r.message.content.strip()

    def run(self, market: dict, news: dict, geo: dict) -> dict:
        print(f"  [{self.NAME}] 10 slayt carousel hazırlanıyor...")

        d = market["data"]
        winner = market["winner"]
        loser  = market["loser"]
        geo_ozet = geo.get("ozet", "")
        top_news = news["news"][0] if news["news"] else {"baslik": "Piyasalar karışık", "ozet": ""}

        prompt = f"""10 slaytlık Instagram carousel yaz. Hedef: 25-55 yaş Türk yatırımcı.

Stil: Merak uyandıran sorular + çarpıcı veri + analiz + harekete geçirici son.
Ton: Bilgilendirici ama akıcı, "biliyor muydun?" etkisi yarat.

Veriler:
- En çok yükselen: {winner['sembol']} ({winner['degisim']:+.1f}%)
- En çok düşen: {loser['sembol']} ({loser['degisim']:+.1f}%)
- Altın: {d['ALTIN']['fiyat']}$ | BTC: {d['BTC']['fiyat']:,.0f}$ | BIST: {d['BIST100']['fiyat']:,.0f}
- Jeopolitik: {geo_ozet[:100]}
- Öne çıkan haber: {top_news['baslik']}

Format (10 slayt):
SLIDE_01_BASLIK: [çarpıcı soru veya stat]
SLIDE_01_METIN: [1-2 cümle]
SLIDE_02_BASLIK: [...]
SLIDE_02_METIN: [...]
... (10 slayta kadar devam)
SLIDE_10_BASLIK: [CTA]
SLIDE_10_METIN: [kaydet + takip et mesajı]"""

        raw = self._ask(prompt)
        slides = {}
        for line in raw.splitlines():
            if ("SLIDE_" in line or "SLİDE_" in line) and ":" in line:
                k, v = line.split(":", 1)
                key = k.strip().replace("SLİDE", "SLIDE")
                slides[key] = v.strip()

        print(f"    {len(slides)//2} tam slayt hazır")
        return {"agent": self.NAME, "slides": slides, "raw": raw}
