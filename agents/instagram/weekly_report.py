"""
Agent: Weekly Report — qwen3.5:9b
Pazar günü yayınlanacak 15-20 slaytlık haftalık kapsamlı rapor
"""
import ollama


class WeeklyReportAgent:
    NAME = "Weekly Report"
    MODEL = "qwen3.5:9b"

    def _ask(self, prompt: str) -> str:
        r = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.5, "num_predict": 1000},
            think=False,
        )
        return r.message.content.strip()

    def run(self, market: dict, news: dict, geo: dict, trends: list) -> dict:
        print(f"  [{self.NAME}] Haftalık rapor hazırlanıyor (uzun sürebilir)...")

        d = market["data"]
        trend_list = ", ".join(t["konu"] for t in trends[:5]) if trends else "genel piyasa"
        news_list  = " | ".join(n["baslik"] for n in news["news"]) if news["news"] else ""

        prompt = f"""Pazar günü paylaşılacak 15 slaytlık haftalık Instagram carousel raporu yaz.

Hedef: 25-55 yaş, haftanın özetini sindirgemek isteyen Türk yatırımcı.
Ton: Profesyonel ama anlaşılır, veriye dayalı.

Veriler:
- Altın: {d['ALTIN']['fiyat']}$ ({d['ALTIN']['degisim']:+.1f}%)
- Gümüş: {d['GUMUS']['fiyat']}$ ({d['GUMUS']['degisim']:+.1f}%)
- BTC: {d['BTC']['fiyat']:,.0f}$ ({d['BTC']['degisim']:+.1f}%)
- BIST100: {d['BIST100']['fiyat']:,.0f} ({d['BIST100']['degisim']:+.1f}%)
- Dolar/TL: {d['DOLAR']['fiyat']} ({d['DOLAR']['degisim']:+.1f}%)
- Haftanın trendleri: {trend_list}
- Önemli haberler: {news_list}
- Jeopolitik: {geo.get('ozet','')}

Yapı önerisi:
Slayt 1: Kapak + haftanın özet başlığı
Slayt 2-4: Piyasa performansı (altın, BTC, borsa ayrı ayrı)
Slayt 5-7: Haber analizi
Slayt 8-10: Jeopolitik etki
Slayt 11-13: Fırsat ve riskler
Slayt 14: Gelecek haftaya bakış
Slayt 15: CTA

Format:
WR_01_BASLIK: [...]
WR_01_METIN: [kısa metin]
... (15 slayta kadar)"""

        raw = self._ask(prompt)
        slides = {}
        for line in raw.splitlines():
            if "WR_" in line and ":" in line:
                k, v = line.split(":", 1)
                slides[k.strip()] = v.strip()

        count = len([k for k in slides if "BASLIK" in k])
        print(f"    {count} haftalık rapor slaydı hazır")
        return {"agent": self.NAME, "slides": slides, "raw": raw, "slide_count": count}
