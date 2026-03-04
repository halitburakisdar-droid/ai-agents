"""
Agent 2: Research Agent
Model: qwen3.5:9b (/no_think — hızlı mod)
Görev: Fiyat verisini analiz et, piyasa trendi belirle
"""

import ollama


class ResearchAgent:
    NAME = "Research Agent"
    MODEL = "qwen3.5:9b"

    def _ask(self, prompt: str) -> str:
        response = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.3, "num_predict": 400},
            think=False,
        )
        return response.message.content.strip()

    def run(self, price_data: dict) -> dict:
        print(f"\n{'─'*50}")
        print(f"  Agent 2: {self.NAME}  [{self.MODEL}]")
        print(f"{'─'*50}")
        print("  Analiz yapılıyor...")

        gold_chg   = price_data["changes"]["gold"]
        silver_chg = price_data["changes"]["silver"]
        alarms     = price_data["alarms"]
        gold_price = price_data["prices"]["gold"]
        silver_prc = price_data["prices"]["silver"]

        prompt = f"""Sen bir kıdemli emtia analistisin. Aşağıdaki anlık piyasa verilerini analiz et:

ALTIN: ${gold_price} (değişim: {gold_chg:+.2f}%)
GÜMÜŞ: ${silver_prc} (değişim: {silver_chg:+.2f}%)
Tetiklenen alarm sayısı: {len(alarms)}
{f"Alarm detayı: {', '.join(a['metal'].upper()+' '+a['direction'] for a in alarms)}" if alarms else ""}

Şunları belirle:
1. TREND: tek kelime (YÜKSELİŞ / DÜŞÜŞ / NÖTR)
2. GÜVEN: yüzde olarak (örn: %75)
3. ANALİZ: 2-3 cümle Türkçe piyasa yorumu
4. TAVSİYE: "İZLE", "AL" veya "SAT"

Formatı kesinlikle şu şekilde kullan:
TREND: ...
GÜVEN: ...
ANALİZ: ...
TAVSİYE: ...
"""
        raw = self._ask(prompt)
        print(f"\n  Model yanıtı:\n{raw}\n")

        # Basit parse
        lines = {line.split(":")[0].strip(): ":".join(line.split(":")[1:]).strip()
                 for line in raw.splitlines() if ":" in line}

        trend    = lines.get("TREND", "NÖTR")
        guven    = lines.get("GÜVEN", "%50")
        analiz   = lines.get("ANALİZ", raw[:200])
        tavsiye  = lines.get("TAVSİYE", "İZLE")

        return {
            "agent": self.NAME,
            "trend": trend,
            "guven": guven,
            "analiz": analiz,
            "tavsiye": tavsiye,
            "raw": raw,
        }
