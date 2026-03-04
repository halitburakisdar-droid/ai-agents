"""
Agent 4: Quality Controller
Model: qwen3.5:9b (think=False)
Görev: İçeriği puanla, yayın kararı ver
"""

import ollama


class QualityControllerAgent:
    NAME = "Quality Controller"
    MODEL = "qwen3.5:9b"

    def _ask(self, prompt: str) -> str:
        r = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.2, "num_predict": 300},
            think=False,
        )
        return r.message.content.strip()

    def run(self, content_data: dict, research_data: dict, learned_patterns: list = None) -> dict:
        print(f"\n{'─'*50}")
        print(f"  Agent 4: {self.NAME}  [{self.MODEL}]")
        print(f"{'─'*50}")
        print("  İçerik değerlendiriliyor...")

        slides = content_data.get("slides", {})
        s1 = slides.get("slide_1", {})
        s2 = slides.get("slide_2", {})
        s3 = slides.get("slide_3", {})

        pattern_hint = ""
        if learned_patterns:
            pattern_hint = f"\nÖğrenilmiş kalıplar (bunlara dikkat et): {'; '.join(learned_patterns[:3])}\n"

        prompt = f"""Instagram carousel'i hızlıca değerlendir (Türkçe, kısa cevaplar):
{pattern_hint}
Slayt 1: {s1.get('baslik','')} — {s1.get('metin','')}
Slayt 2: {s2.get('baslik','')} — {s2.get('metin','')}
Slayt 3: {s3.get('baslik','')} — {s3.get('metin','')}

Değerlendirme: dil kalitesi, finansal doğruluk, etkileyicilik, risk uyarısı var mı?

Formatı kullan:
SKOR: [1-10]
GÜÇLÜ: [tek cümle]
ZAYIF: [tek cümle]
KARAR: [YAYINLA / REVİZE ET / REDDET]"""

        raw = self._ask(prompt)
        print(f"\n  {raw}\n")

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

        return {
            "agent": self.NAME,
            "skor":  skor,
            "guclu": lines.get("GÜÇLÜ", ""),
            "zayif": lines.get("ZAYIF", ""),
            "karar": lines.get("KARAR", "REVİZE ET"),
            "raw":   raw,
        }
