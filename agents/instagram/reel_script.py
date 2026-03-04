"""
Agent: Reel Script — qwen3.5:9b
60 saniyelik Instagram Reels scripti — Hook + İçerik + CTA
"""
import ollama


class ReelScriptAgent:
    NAME = "Reel Script"
    MODEL = "qwen3.5:9b"

    def _ask(self, prompt: str) -> str:
        r = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.8, "num_predict": 500},
            think=False,
        )
        return r.message.content.strip()

    def run(self, market: dict, geo: dict, trends: list) -> dict:
        print(f"  [{self.NAME}] 60sn Reel scripti yazılıyor...")

        d = market["data"]
        winner = market["winner"]
        top_trend = trends[0]["konu"] if trends else "altın yatırımı"

        prompt = f"""60 saniyelik Instagram Reels için Türkçe konuşma metni yaz.

Günün öne çıkanı: {winner['sembol']} {winner['degisim']:+.1f}% {winner['icon']}
Trend konu: {top_trend}
Jeopolitik risk: {geo['risk_level']}

Yapı:
HOOK (0-5sn): İzleyiciyi durduracak çarpıcı açılış — soru veya şok edici stat
ICERIK (5-45sn): Ana bilgi — 3 madde, kısa cümleler, konuşma dili
CTA (45-60sn): Harekete geçirici kapanış — kaydet, yorum, takip

Format:
HOOK: [tam metin, 1-2 cümle]
ICERIK_1: [madde 1]
ICERIK_2: [madde 2]
ICERIK_3: [madde 3]
CTA: [kapanış metin]
SUSIT_YAZI: [ekrana konacak alt yazı önerisi, 5 kelime]"""

        raw = self._ask(prompt)
        parts = {}
        for line in raw.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                parts[k.strip()] = v.strip()

        return {
            "agent":       self.NAME,
            "hook":        parts.get("HOOK", ""),
            "icerik":      [parts.get(f"ICERIK_{i}", "") for i in range(1, 4)],
            "cta":         parts.get("CTA", ""),
            "susit_yazi":  parts.get("SUSIT_YAZI", ""),
            "sure":        "~60 saniye",
            "raw":         raw,
        }
