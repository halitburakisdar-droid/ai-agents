"""
Knowledge Extraction Engine
============================
Her beceriyi moleküler seviyede çöz.
Qwen 2.5:32b → derin araştırma (yavaş ama kaliteli)
Qwen 3.5:9b  → hızlı özet
"""

import ollama
from memory.learning_db import save_knowledge, get_knowledge, init_learning_tables

MASTERY_TOPICS = {
    "hook_writing": {
        "desc": "Viral hook yazma — ilk 3 saniye",
        "model": "qwen3.5:9b",
        "prompt": """Hook writing mastery için derin analiz (Türk finans Instagram'ı):

ARAŞTIR:
- Alex Hormozi hook formülleri
- MrBeast başlık yapısı
- Morning Brew email subject'leri

ÇÖZ:
1. İlk 3 kelime pattern'i (sayı / soru / şok)
2. Merak boşluğu yaratma
3. Paradoks kurma ("neden zenginler fakir kalır?")
4. Loss aversion tetikleme

FORMÜLLER:
- "[SAYI] kişinin bilmediği [ŞOK GERÇEK]"
- "[YIL]'de [OLAY] oldu, [SONUÇ]"
- "Eğer [YAYGIN İNANÇ] ise, neden [ZIT SONUÇ]?"
- "[KİŞİ] bunu [EYLEM] iken [BEKLENMEDIK ŞEY] oldu"

Türk kitleye özel 10 hazır hook şablonu yaz."""
    },
    "storytelling": {
        "desc": "Hikaye anlatımı mimarisi",
        "model": "qwen3.5:9b",
        "prompt": """Finans Instagram için storytelling mastery (Türkçe):

YAPI:
- 3 Act Structure (sorun → çözüm yolculuğu → sonuç)
- Hero's Journey finans versiyonu
- StoryBrand: kahraman MÜŞTERİ, rehber SEN

TÜRK FİNANS BAŞLANGICI:
- "2008'de babam..." (kişisel kriz)
- "İlk Bitcoin alımım..." (macera başlangıcı)
- "Pes ettiğim gün..." (dönüm noktası)

5 hazır hikaye şablonu yaz (her biri 3 cümle özet)."""
    },
    "pain_points": {
        "desc": "Acı noktası psikolojisi",
        "model": "qwen3.5:9b",
        "prompt": """Türk yatırımcı kitlesi için acı noktaları ve tetikleyiciler:

TÜRK KİTLEYE ÖZEL:
- "Maaşın eriyor" → Enflasyon korkusu (TL değer kaybı)
- "Arkadaşların zenginleşiyor" → Sosyal FOMO
- "Emeklilik planın yok" → Gelecek kaygısı
- "Çocuklarına ev alamayacaksın" → Aile baskısı
- "Bankada para tutmak para kaybetmek" → Fırsat maliyeti

Her acı noktası için:
1. Hook cümlesi
2. İçerik formatı önerisi
3. CTA önerisi"""
    },
    "conflict_creation": {
        "desc": "Çatışma mühendisliği",
        "model": "qwen3.5:9b",
        "prompt": """Instagram'da çatışma ile etkileşim artırma:

ÇATIŞMA TİPLERİ:
- Zenginler vs Fakirler (sistem eleştirisi)
- Eski nesil vs Yeni nesil (yatırım anlayışı)
- Gerçek vs Algı (altın gerçekten güvenli mi?)
- Biliyor vs Bilmiyor (içeriden bilgi)

Her tip için:
- Hook cümlesi
- 3 slayt yapısı
- Kapanış sorusu (yorum tetikler)"""
    },
    "data_storytelling": {
        "desc": "Veri ile hikaye anlatma",
        "model": "qwen3.5:9b",
        "prompt": """Finansal veriyi Instagram'da hikayeye çevirme:

PRENSİPLER:
- Karşılaştırma: "Altın 1971: $35 → 2026: $3,150 = %8,900 artış"
- Relatability: "1 Big Mac = X gram altın"
- Zaman serisi: "50 yıl önce yatırsaydın..."
- Görselleştirme talimatı (slayt tasarım rehberi)

5 veri-hikaye şablonu yaz."""
    },
    "cta_writing": {
        "desc": "CTA (harekete geçirme) optimizasyonu",
        "model": "qwen3.5:9b",
        "prompt": """Instagram finans CTA mastery (Türkçe):

AMAÇLARA GÖRE CTA:
- Kaydet (bilgi içeriği için)
- Yorum (tartışma için)
- Takip (seri içerik için)
- DM (satış dönüşümü için)
- Paylaş (sosyal kanıt için)

Her amaç için 3 CTA şablonu.
Türk kültürüne uygun, samimi dil kullan."""
    },
    "psychology": {
        "desc": "Kitle psikolojisi ve duygusal tetikleyiciler",
        "model": "qwen3.5:9b",
        "prompt": """Finans içeriği için psikolojik tetikleyiciler (Türkçe):

TEMEL:
- Sosyal kanıt: "Binlerce kişi bunu yapıyor..."
- Otorite: "Buffett şunu söyledi..."
- Kıtlık: "Bu bilgi az biliniyor..."
- Reciprocity: Ücretsiz değer ver, bağlılık kazan

KOGNİTİF ÖNYARGILAR:
- Anchoring: İlk rakam algıyı şekillendirir
- Confirmation bias: Okuyucunun ne düşündüğünü söyle
- Loss aversion: Kazanç değil, kayıp vurgula

Her biri için Instagram slayt örneği."""
    },
}


class KnowledgeExtractionEngine:
    NAME = "Knowledge Engine"

    def _ask(self, prompt: str, model: str = "qwen3.5:9b", tokens: int = 500) -> str:
        r = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.4, "num_predict": tokens},
            think=False,
        )
        return r.message.content.strip()

    def extract_topic(self, topic: str) -> dict:
        """Tek bir konuyu derinlemesine araştır."""
        if topic not in MASTERY_TOPICS:
            return {"error": f"Bilinmeyen konu: {topic}"}

        cfg   = MASTERY_TOPICS[topic]
        model = cfg["model"]
        print(f"  [{self.NAME}] '{topic}' araştırılıyor [{model}]...")
        if "32b" in model:
            print(f"  ⚠️  qwen3.5:9b — 1-2 dk sürebilir")

        knowledge = self._ask(cfg["prompt"], model=model, tokens=600)
        level = "advanced" if "32b" in model else "intermediate"
        save_knowledge(topic, knowledge, level=level, source=self.NAME)

        print(f"  ✅ '{topic}' bilgisi kaydedildi ({len(knowledge)} karakter)")
        return {"topic": topic, "level": level, "content": knowledge, "model": model}

    def extract_all(self, use_32b: bool = False) -> dict:
        """Tüm konuları araştır."""
        init_learning_tables()
        results = {}
        for topic, cfg in MASTERY_TOPICS.items():
            # 32b'yi atla (çok yavaş) ya da kullan
            model = cfg["model"] if use_32b else "qwen3.5:9b"
            r = ollama.chat(
                model=model,
                messages=[{"role": "user", "content": cfg["prompt"]}],
                options={"temperature": 0.4, "num_predict": 500},
                think=False,
            )
            content = r.message.content.strip()
            save_knowledge(topic, content, level="intermediate", source=self.NAME)
            results[topic] = {"saved": True, "chars": len(content)}
            print(f"  ✅ {topic}: {len(content)} karakter kaydedildi")
        return results

    def get_topic_knowledge(self, topic: str) -> str:
        """Kaydedilmiş bilgiyi getir."""
        row = get_knowledge(topic)
        return row.get("content", "") if row else ""

    def inject_into_prompt(self, base_prompt: str, topic: str) -> str:
        """Mevcut prompt'a bilgi enjekte et."""
        knowledge = self.get_topic_knowledge(topic)
        if not knowledge:
            return base_prompt
        return f"{base_prompt}\n\n[ÖĞRENILEN BİLGİ — {topic}]:\n{knowledge[:300]}\n"
