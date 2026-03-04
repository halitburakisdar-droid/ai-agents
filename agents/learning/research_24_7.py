"""
ContinuousResearchAgent — 7/24 Rakip Araştırma
===============================================
Günde 4 tarama: 06:00 / 12:00 / 18:00 / 00:00
Her tarama farklı odak → bulgular birleştirilir
Model: qwen3.5:9b (think=False)
"""

import ollama
from datetime import datetime
from memory.learning_db import save_competitor_pattern, save_knowledge, init_learning_tables

COMPETITORS = [
    {"handle": "@APompliano",     "niche": "crypto/macro",            "lang": "EN"},
    {"handle": "@GrahamStephan",  "niche": "personal finance",        "lang": "EN"},
    {"handle": "@VisualizeValue", "niche": "data storytelling",       "lang": "EN"},
    {"handle": "@ThinkingPhysics","niche": "curiosity/science",       "lang": "EN"},
    {"handle": "@paraborsa",      "niche": "Türk borsa",              "lang": "TR"},
    {"handle": "@finanskafasi",   "niche": "Türk kişisel finans",     "lang": "TR"},
]


class ContinuousResearchAgent:
    NAME  = "Research 24/7"
    MODEL = "qwen3.5:9b"

    def _ask(self, prompt: str, tokens: int = 400) -> str:
        r = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.6, "num_predict": tokens},
            think=False,
        )
        return r.message.content.strip()

    # ── 4 Günlük Tarama ───────────────────────────────────

    def scan_competitors(self, targets: list) -> dict:
        """Sabah 06:00 — Rakip hook ve içerik formatları."""
        print(f"  [{self.NAME}] 06:00 Sabah taraması...")
        results = []
        for t in targets[:4]:   # hız için 4 ile sınırla
            raw = self._ask(f"""
"{t['handle']}" ({t['niche']}) hesabının viral hook stratejisini analiz et.
Türk finans kitlesi için uyarlanabilir pattern'leri bul.

HOOK_FORMULA: [kullandığı hook yapısı]
BASLIK_YAPISI: [başlık şablonu]
HOOK_GUCU: [1-10 puan]
TR_UYARLAMA: [Türk versiyonu örnek]""", tokens=250)

            lines = {l.split(":")[0].strip(): l.split(":",1)[1].strip()
                     for l in raw.splitlines() if ":" in l}
            pattern = {
                "hook_formula":  lines.get("HOOK_FORMULA", ""),
                "baslik_yapisi": lines.get("BASLIK_YAPISI", ""),
                "tr_uyarlama":   lines.get("TR_UYARLAMA", ""),
            }
            try:
                power = float(''.join(filter(lambda x: x.isdigit() or x=='.', lines.get("HOOK_GUCU","5")))[:3])
            except:
                power = 5.0
            save_competitor_pattern(t["handle"], "carousel", "hook", pattern,
                                    hook_power=power, success_score=power)
            results.append({"handle": t["handle"], "pattern": pattern, "power": power})

        return {"scan": "morning", "results": results, "count": len(results)}

    def scan_trending_content(self) -> dict:
        """Öğle 12:00 — Trend içerik formülleri."""
        print(f"  [{self.NAME}] 12:00 Trend taraması...")
        raw = self._ask("""
Türk Instagram finans içeriklerinde bu hafta trending olan içerik yapılarını analiz et.

FORMAT_1: [en çok paylaşılan içerik tipi + örnek başlık]
FORMAT_2: [ikinci format]
FORMAT_3: [üçüncü format]
KACIN: [düşük performanslı format]
ALTIN_KURAL: [trend içeriğin tek bir altın kuralı]""", tokens=300)

        lines = {l.split(":")[0].strip(): l.split(":",1)[1].strip()
                 for l in raw.splitlines() if ":" in l}
        trends = {k: v for k, v in lines.items() if k.startswith("FORMAT") or k in ("KACIN","ALTIN_KURAL")}
        save_knowledge("trending_formats", raw, level="intermediate", source="noon_scan")
        return {"scan": "noon", "trends": trends}

    def scan_viral_patterns(self) -> dict:
        """Akşam 18:00 — Viral mekanikler."""
        print(f"  [{self.NAME}] 18:00 Viral pattern taraması...")
        raw = self._ask("""
Finansal Instagram içeriklerinde viral olan psikolojik tetikleyicileri listele.
Türk kitlesi için özelleştir.

TETIKLEYICI_1: [isim] | [nasıl kullanılır] | [örnek]
TETIKLEYICI_2: [isim] | [nasıl kullanılır] | [örnek]
TETIKLEYICI_3: [isim] | [nasıl kullanılır] | [örnek]
FOMO_FORMULU: [en güçlü FOMO oluşturma yöntemi]
KAYIP_KORKU: [loss aversion nasıl kullanılır]""", tokens=350)

        triggers = []
        for line in raw.splitlines():
            if line.startswith("TETIKLEYICI_") and "|" in line:
                parts = line.split("|")
                name  = parts[0].split(":",1)[-1].strip()
                how   = parts[1].strip() if len(parts)>1 else ""
                ex    = parts[2].strip() if len(parts)>2 else ""
                triggers.append({"name": name, "how": how, "example": ex})
                save_competitor_pattern("viral_pattern", "any", "psychology",
                                        {"name": name, "how": how, "example": ex},
                                        hook_power=8.0, success_score=8.0)
        save_knowledge("viral_triggers", raw, level="advanced", source="evening_scan")
        return {"scan": "evening", "triggers": triggers}

    def deep_analysis(self) -> dict:
        """Gece 00:00 — Derin trend analizi."""
        print(f"  [{self.NAME}] 00:00 Derin analiz...")
        raw = self._ask("""
Finansal içerik yaratıcılığı üzerine derin analiz yap.

MEGA_TREND: [önümüzdeki ayın en büyük fırsatı]
OLUM_CERCEVESI: [death-frame içeriklerin şablonu - "neden X öldü?"]
KAHRAMAN_HIKAYESI: [hero's journey finans versiyonu şablonu]
PARADOKS_HOOK: [beklenmedik çatışma yaratan hook şablonu]
DATA_HIKAYE: [veriyi hikayeye çevirme formülü]
YARIN_DENE: [yarın hemen denenebilecek somut taktik]""", tokens=400)

        lines = {l.split(":")[0].strip(): l.split(":",1)[1].strip()
                 for l in raw.splitlines() if ":" in l}
        save_knowledge("deep_patterns", raw, level="advanced", source="midnight_scan")
        return {"scan": "midnight", "insights": lines}

    def synthesize_findings(self, morning: dict, noon: dict,
                             evening: dict, midnight: dict) -> dict:
        """Tüm bulguları birleştir."""
        print(f"  [{self.NAME}] Bulgular sentezleniyor...")
        all_text = (
            f"Sabah: {str(morning)[:200]}\n"
            f"Öğle: {str(noon)[:200]}\n"
            f"Akşam: {str(evening)[:200]}\n"
            f"Gece: {str(midnight)[:200]}"
        )
        synthesis = self._ask(f"""
Aşağıdaki 4 taramanın bulgularını sentezle.
Yarın tüm agent'lara dağıtılacak 3 altın kural belirle:

{all_text}

ALTIN_KURAL_1: [en önemli öğrenme]
ALTIN_KURAL_2: [ikinci öğrenme]
ALTIN_KURAL_3: [üçüncü öğrenme]
YARIN_UYGULA: [yarın ilk denenecek şey]""", tokens=300)

        lines = {l.split(":")[0].strip(): l.split(":",1)[1].strip()
                 for l in synthesis.splitlines() if ":" in l}
        save_knowledge("daily_synthesis", synthesis, level="master", source="synthesizer")
        return {
            "golden_rules": [
                lines.get("ALTIN_KURAL_1",""),
                lines.get("ALTIN_KURAL_2",""),
                lines.get("ALTIN_KURAL_3",""),
            ],
            "tomorrow_action": lines.get("YARIN_UYGULA",""),
        }

    def distribute_learnings(self, discoveries: dict) -> str:
        """Agent'lara eğitim materyali olarak gönder."""
        rules = "\n".join(f"  {i+1}. {r}" for i, r in enumerate(discoveries.get("golden_rules",[])))
        msg = (
            f"📡 GÜNLÜK ARAŞTIRMA TAMAMLANDI\n"
            f"Altın Kurallar:\n{rules}\n"
            f"Yarın Dene: {discoveries.get('tomorrow_action','')}"
        )
        save_knowledge("latest_distribution", msg, level="master", source="distributor")
        return msg

    def daily_research_cycle(self) -> dict:
        """Tam günlük araştırma döngüsü."""
        init_learning_tables()
        morning  = self.scan_competitors(COMPETITORS)
        noon     = self.scan_trending_content()
        evening  = self.scan_viral_patterns()
        midnight = self.deep_analysis()
        findings = self.synthesize_findings(morning, noon, evening, midnight)
        msg      = self.distribute_learnings(findings)
        print(f"\n  ✅ Günlük araştırma tamamlandı")
        print(f"  Altın Kural 1: {findings['golden_rules'][0][:70]}")
        return {
            "agent":    self.NAME,
            "date":     datetime.now().strftime("%Y-%m-%d"),
            "morning":  morning,
            "noon":     noon,
            "evening":  evening,
            "midnight": midnight,
            "findings": findings,
            "broadcast": msg,
        }
