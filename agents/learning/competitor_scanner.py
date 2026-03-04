"""
Competitor Scanner
==================
Rakip hesapları analiz et, kazanan pattern'leri çıkar.
Model: qwen3.5:9b (think=False)

Hesaplar (simüle edilir — gerçek scraping yerine Qwen örnek üretir):
  @APompliano, @GrahamStephan, @VisualizeValue, @ThinkingPhysics
  + Türk finans hesapları
"""

import ollama
from datetime import datetime


COMPETITORS = [
    {"handle": "@APompliano",     "niche": "crypto/macro finance",    "lang": "EN"},
    {"handle": "@GrahamStephan",  "niche": "personal finance/real estate", "lang": "EN"},
    {"handle": "@VisualizeValue", "niche": "data visualization/wealth",    "lang": "EN"},
    {"handle": "@ThinkingPhysics","niche": "science/curiosity content",    "lang": "EN"},
    {"handle": "@paraborsa",      "niche": "Türk borsa analizi",           "lang": "TR"},
    {"handle": "@finanskafasi",   "niche": "Türk kişisel finans",          "lang": "TR"},
    {"handle": "@altin_analiz",   "niche": "Türk altın/emtia",            "lang": "TR"},
]


class CompetitorScannerAgent:
    NAME  = "Competitor Scanner"
    MODEL = "qwen3.5:9b"

    def _ask(self, prompt: str) -> str:
        r = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.6, "num_predict": 600},
            think=False,
        )
        return r.message.content.strip()

    def scan_account(self, handle: str, niche: str, lang: str) -> dict:
        """Bir hesabın içerik stratejisini simüle et + analiz et."""
        prompt = f"""Sen sosyal medya içerik analistisin.
"{handle}" ({niche}) hesabının tipik {'Türkçe' if lang=='TR' else 'İngilizce'} Instagram içerik stratejisini analiz et.

Bu hesap türünde genellikle ne tür içerikler viral olur?

Format:
HOOK_STILI: [nasıl dikkat çekiyor]
ICERIK_FORMATI: [carousel/reel/story — hangisi dominant]
BASLIK_FORMATI: [başlık yapısı örneği]
HASHTAG_STRATEJISI: [kaç hashtag, hangi türde]
PAYLASIM_SAATI: [en iyi saat]
VIRAL_FORMUL: [tek cümle — neyi farklı yapıyor]
ORNEK_BASLIK: [bu hesap tarzında örnek bir başlık]"""

        raw = self._ask(prompt)
        lines = {}
        for line in raw.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                lines[k.strip()] = v.strip()

        return {
            "handle":          handle,
            "niche":           niche,
            "hook_stili":      lines.get("HOOK_STILI", ""),
            "icerik_formati":  lines.get("ICERIK_FORMATI", "carousel"),
            "baslik_formati":  lines.get("BASLIK_FORMATI", ""),
            "hashtag_str":     lines.get("HASHTAG_STRATEJISI", ""),
            "paylasim_saati":  lines.get("PAYLASIM_SAATI", "20:00"),
            "viral_formul":    lines.get("VIRAL_FORMUL", ""),
            "ornek_baslik":    lines.get("ORNEK_BASLIK", ""),
            "raw":             raw,
        }

    def daily_research_cycle(self, targets: list = None) -> dict:
        """
        Sabah 06:00 çalışır.
        Tüm rakip hesapları tara, pattern'leri birleştir.
        """
        if targets is None:
            targets = COMPETITORS

        print(f"\n  [{self.NAME}] Rakip taraması başladı ({len(targets)} hesap)...")
        insights = []

        for comp in targets:
            print(f"    Taranan: {comp['handle']} ({comp['niche']})")
            insight = self.scan_account(comp["handle"], comp["niche"], comp["lang"])
            insights.append(insight)

        # Birleşik özet çıkar
        viral_formuller = "\n".join(f"- {i['handle']}: {i['viral_formul']}" for i in insights)
        baslik_ornekleri = "\n".join(f"- {i['handle']}: {i['ornek_baslik']}" for i in insights)

        merge_prompt = f"""Aşağıdaki rakip analizlerinden evrensel başarı formüllerini çıkar.
Türk finans Instagram hesapları için uygulanabilir öğrenmeleri listele.

Viral formüller:
{viral_formuller}

Başlık örnekleri:
{baslik_ornekleri}

Format:
KAZANAN_PATTERN_1: [her hesapta ortak olan şey]
KAZANAN_PATTERN_2: [ikinci ortak pattern]
KAZANAN_PATTERN_3: [üçüncü]
TR_UYARLAMA: [Türk kitlesi için özel adaptasyon]
KACIN: [ne yapılmamalı]
YARIN_DENE: [yarın uygulanacak 1 somut taktik]"""

        merged_raw = self._ask(merge_prompt)
        merged = {}
        for line in merged_raw.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                merged[k.strip()] = v.strip()

        print(f"    ✅ {len(insights)} hesap tarandı, pattern'ler birleştirildi")
        return {
            "agent":        self.NAME,
            "date":         datetime.now().strftime("%Y-%m-%d"),
            "scan_time":    datetime.now().strftime("%H:%M"),
            "account_count": len(insights),
            "insights":     insights,
            "patterns": {
                "pattern_1":     merged.get("KAZANAN_PATTERN_1", ""),
                "pattern_2":     merged.get("KAZANAN_PATTERN_2", ""),
                "pattern_3":     merged.get("KAZANAN_PATTERN_3", ""),
                "tr_uyarlama":   merged.get("TR_UYARLAMA", ""),
                "kacin":         merged.get("KACIN", ""),
                "yarin_dene":    merged.get("YARIN_DENE", ""),
            },
            "raw_merge": merged_raw,
        }
