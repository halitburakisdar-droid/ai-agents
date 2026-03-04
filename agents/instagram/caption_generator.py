"""
Agent: Caption Generator — qwen3.5:9b
Instagram caption + hashtag paketi
"""
import ollama


class CaptionGeneratorAgent:
    NAME = "Caption Generator"
    MODEL = "qwen3.5:9b"

    def _ask(self, prompt: str) -> str:
        r = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.7, "num_predict": 400},
            think=False,
        )
        return r.message.content.strip()

    def run(self, content_type: str, content_summary: str, market: dict) -> dict:
        print(f"  [{self.NAME}] Caption + hashtag üretiliyor...")

        d = market["data"]
        prompt = f"""Türkçe Instagram caption yaz.

İçerik türü: {content_type}
İçerik özeti: {content_summary}
Altın bugün: {d['ALTIN']['degisim']:+.1f}% | BTC: {d['BTC']['degisim']:+.1f}%

Caption kuralları:
- İlk satır dikkat çekici (hook)
- 3-4 kısa paragraf
- Soru ile bitir
- Emoji kullan ama abartma

Format:
CAPTION: [tam caption metni]
HASHTAG_TR: [15 Türkçe hashtag, başında # ile]
HASHTAG_EN: [10 İngilizce hashtag]
MENTION: [önerilecek 3 hesap türü, örn: @finans hesabı]"""

        raw = self._ask(prompt)
        parts = {}
        current_key = None
        current_val = []
        for line in raw.splitlines():
            if any(line.startswith(k + ":") for k in ["CAPTION", "HASHTAG_TR", "HASHTAG_EN", "MENTION"]):
                if current_key:
                    parts[current_key] = "\n".join(current_val).strip()
                current_key = line.split(":", 1)[0].strip()
                current_val = [line.split(":", 1)[1].strip()]
            elif current_key:
                current_val.append(line)
        if current_key:
            parts[current_key] = "\n".join(current_val).strip()

        return {
            "agent":       self.NAME,
            "caption":     parts.get("CAPTION", raw[:300]),
            "hashtag_tr":  parts.get("HASHTAG_TR", ""),
            "hashtag_en":  parts.get("HASHTAG_EN", ""),
            "mention":     parts.get("MENTION", ""),
            "raw":         raw,
        }
