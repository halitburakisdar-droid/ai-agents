"""
Agent 3: Content Creator
Model: qwen3.5:9b (/no_think — hızlı mod)
Görev: Research verisinden 3 slaytlı Instagram carousel yaz
"""

import ollama


class ContentCreatorAgent:
    NAME = "Content Creator"
    MODEL = "qwen3.5:9b"

    def _ask(self, prompt: str) -> str:
        response = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.6, "num_predict": 600},
            think=False,
        )
        return response.message.content.strip()

    def run(self, price_data: dict, research_data: dict) -> dict:
        print(f"\n{'─'*50}")
        print(f"  Agent 3: {self.NAME}  [{self.MODEL}]")
        print(f"{'─'*50}")
        print("  İçerik oluşturuluyor...")

        gold_chg   = price_data["changes"]["gold"]
        silver_chg = price_data["changes"]["silver"]
        gold_price = price_data["prices"]["gold"]
        trend      = research_data["trend"]
        analiz     = research_data["analiz"]
        tavsiye    = research_data["tavsiye"]

        prompt = f"""Sen bir finansal içerik uzmanısın. Aşağıdaki piyasa verileri için Instagram carousel (3 slayt) hazırla.

Veriler:
- Altın: ${gold_price} ({gold_chg:+.2f}%)
- Gümüş değişim: {silver_chg:+.2f}%
- Piyasa trendi: {trend}
- Uzman tavsiyesi: {tavsiye}
- Analiz özeti: {analiz}

Her slayt için çekici, kısa ve net Türkçe metin yaz.
Emoji kullan. Finansal jargonu sadeleştir. Hedef kitle: yatırımı düşünen genç Türkler.

Formatı TAM OLARAK şu şekilde kullan:

SLAYT 1 BAŞLIK: [çarpıcı başlık, maks 10 kelime]
SLAYT 1 METIN: [1-2 etkileyici cümle + istatistik]

SLAYT 2 BAŞLIK: [trend analizi başlığı]
SLAYT 2 METIN: [2-3 cümle trend açıklaması]

SLAYT 3 BAŞLIK: [eylem çağrısı başlığı]
SLAYT 3 METIN: [harekete geçirici CTA + soru]
"""
        raw = self._ask(prompt)
        print(f"\n  Model yanıtı:\n{raw}\n")

        # Parse slaytlar
        slides = {}
        for i in range(1, 4):
            baslik_key = f"SLAYT {i} BAŞLIK"
            metin_key  = f"SLAYT {i} METIN"
            lines = {line.split(":")[0].strip(): ":".join(line.split(":")[1:]).strip()
                     for line in raw.splitlines() if ":" in line}
            slides[f"slide_{i}"] = {
                "baslik": lines.get(baslik_key, f"Slayt {i}"),
                "metin":  lines.get(metin_key, ""),
            }

        return {
            "agent": self.NAME,
            "slides": slides,
            "raw": raw,
        }
