"""
Agent: Viral Predictor — qwen3.5:9b
İçerik için engagement tahmini (1-10) ve viral potansiyeli
"""
import ollama


class ViralPredictorAgent:
    NAME = "Viral Predictor"
    MODEL = "qwen3.5:9b"

    def _ask(self, prompt: str) -> str:
        r = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.3, "num_predict": 300},
            think=False,
        )
        return r.message.content.strip()

    def run(self, content_type: str, basliklar: list, caption: str, hashtag_count: int) -> dict:
        print(f"  [{self.NAME}] Viral potansiyel tahmin ediliyor...")

        baslik_str = "\n".join(f"- {b}" for b in basliklar[:5]) if basliklar else "- İçerik yok"

        prompt = f"""Türk Instagram finans içeriğinin viral potansiyelini değerlendir.

İçerik türü: {content_type}
Başlıklar:
{baslik_str}
Caption uzunluğu: {len(caption)} karakter
Hashtag sayısı: {hashtag_count}

Kriterler: başlık gücü, zamanlama, hedef kitle uyumu, paylaşılabilirlik, etkileşim potansiyeli.

Format:
SKOR: [1-10]
ENGAGEMENT_TAHMINI: [düşük/orta/yüksek/viral]
GUCLU: [tek cümle]
ZAYIF: [tek cümle]
IYILESTİRME: [tek somut öneri]
EN_IYI_SAAT: [paylaşım için en iyi saat aralığı, Türkiye saati]"""

        raw = self._ask(prompt)
        lines = {}
        for line in raw.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                lines[k.strip()] = v.strip()

        try:
            skor = int(''.join(filter(str.isdigit, lines.get("SKOR", "5")))[:2])
            skor = max(1, min(10, skor))
        except Exception:
            skor = 5

        eng = lines.get("ENGAGEMENT_TAHMINI", "orta")
        emoji = {"düşük": "🔴", "orta": "🟡", "yüksek": "🟢", "viral": "🚀"}.get(eng.lower(), "🟡")

        print(f"    Viral Skor: {skor}/10 {emoji} {eng}")
        return {
            "agent":       self.NAME,
            "skor":        skor,
            "engagement":  eng,
            "emoji":       emoji,
            "guclu":       lines.get("GUCLU", ""),
            "zayif":       lines.get("ZAYIF", ""),
            "iyilestirme": lines.get("IYILESTİRME", ""),
            "en_iyi_saat": lines.get("EN_IYI_SAAT", "20:00-22:00"),
            "raw":         raw,
        }
