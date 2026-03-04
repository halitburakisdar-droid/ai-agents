"""
Masterclass System — Haftalık Eğitim + Peer Learning
=====================================================
Her Pazar: qwen3.5:9b öğretmen rolünde → agent'lara ders verir
Her Ay: En başarılı agent → diğerlerine öğretir
"""

import ollama
from datetime import datetime
from memory.learning_db import (
    save_knowledge, get_knowledge, init_learning_tables,
    ALL_AGENTS, ALL_SKILLS, run as db_run, get as db_get
)
from agents.learning.performance_tracker import get_performance_stats

WEEKLY_CURRICULUM = [
    ("Hook Writing Mastery",       "hook_writing"),
    ("Storytelling Architecture",  "storytelling"),
    ("Pain Point Psychology",      "pain_points"),
    ("Conflict Engineering",       "conflict_creation"),
    ("Data Storytelling",          "data_storytelling"),
    ("CTA Optimization",           "cta_writing"),
    ("Emotional Triggers",         "psychology"),
    ("Viral Mechanics",            "hook_writing"),    # tekrar + derinleştirme
]


class MasterclassSystem:
    NAME     = "Masterclass System"
    TEACHER  = "qwen3.5:9b"   # en büyük qwen3.5 modeli
    FAST_MDL = "qwen3.5:9b"    # peer learning için

    def _ask(self, prompt: str, model: str = None, tokens: int = 700) -> str:
        mdl = model or self.FAST_MDL
        r = ollama.chat(
            model=mdl,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.5, "num_predict": tokens},
            think=False,
        )
        return r.message.content.strip()

    # ── Haftalık Masterclass ──────────────────────────────

    def get_week_topic(self, week_number: int) -> tuple:
        idx = (week_number - 1) % len(WEEKLY_CURRICULUM)
        return WEEKLY_CURRICULUM[idx]

    def conduct_masterclass(self, week_number: int,
                            use_32b: bool = False) -> dict:
        """Haftanın masterclass'ını yürüt."""
        init_learning_tables()
        topic_name, topic_key = self.get_week_topic(week_number)
        model = self.TEACHER if use_32b else self.FAST_MDL

        print(f"\n  [{self.NAME}] Hafta #{week_number}: '{topic_name}'")
        print(f"  Öğretmen model: {model}")
        if use_32b:
            print("  ⚠️  2-4 dk sürebilir...")

        # Mevcut bilgiyi al (varsa)
        existing = get_knowledge(topic_key)
        existing_text = existing.get("content", "")[:300] if existing else ""

        curriculum = self._ask(f"""
Sen bir AI içerik sistemi için uzman öğretmensin.
Bu haftanın konusu: {topic_name}

Mevcut bilgi (varsa): {existing_text}

Agent'lara şu formatta ders hazırla:

📚 TEORİ (en iyi örnekler + pattern'ler):
[3-5 madde]

⚡ PRATİK (hazır şablonlar):
[5 kullanıma hazır şablon]

📝 ÖDEV (önümüzdeki hafta):
[3 somut görev]

🎯 KRİTER (başarı nasıl ölçülür):
[ölçülebilir hedef]

Türk finans Instagram kitlesi için özelleştir.""",
            model=model, tokens=700)

        # Kaydet
        db_run("""
            INSERT INTO masterclass_history
            (week_number, topic, teacher, curriculum, agents_trained, conducted_at)
            VALUES (?,?,?,?,?,?)
        """, (week_number, topic_name, model, curriculum,
              str(ALL_AGENTS), datetime.now().isoformat()))

        save_knowledge(f"masterclass_w{week_number}", curriculum,
                       level="advanced", source=f"masterclass_{topic_key}")
        # Ana topic bilgisini de güncelle
        save_knowledge(topic_key, curriculum, level="advanced", source="masterclass")

        print(f"  ✅ Masterclass tamamlandı, {len(ALL_AGENTS)} agent eğitildi")
        return {
            "agent":      self.NAME,
            "week":       week_number,
            "topic":      topic_name,
            "topic_key":  topic_key,
            "curriculum": curriculum,
            "model":      model,
        }

    # ── Peer Learning ─────────────────────────────────────

    def find_mvp(self, last_n: int = 30) -> str:
        """Son N döngüde en yüksek skorlu 'agent' tipini bul."""
        stats = get_performance_stats(last_n=last_n)
        # Basit: yayın oranı yüksekse carousel iyidir
        return "Carousel Agent" if stats.get("publish_rate", 0) > 50 else "Content Creator"

    def peer_learning_session(self, mvp_agent: str = None) -> dict:
        """MVP agent → diğerlerine öğretir."""
        init_learning_tables()
        if not mvp_agent:
            mvp_agent = self.find_mvp()

        print(f"\n  [{self.NAME}] Peer Learning: {mvp_agent} öğretiyor...")

        # MVP'nin başarı sırlarını çıkar
        mvp_raw = self._ask(f"""
Sen "{mvp_agent}" adlı AI agent'sın. Bu ay en yüksek engagement aldın.

Diğer agent'lara şunları öğret:
1. En güçlü 3 başarı taktiğin
2. Kaçındığın 3 hata
3. İlk haftadan öğrendiğin en kritik şey

Türk finans Instagram odaklı, pratik ve somut ol.""", tokens=400)

        # Diğer agent'lara dağıt
        student_responses = {}
        students = [a for a in ALL_AGENTS if a != mvp_agent][:3]  # hız için 3

        for student in students:
            resp = self._ask(f"""
{mvp_agent}'dan şunları öğrendin:
{mvp_raw[:300]}

Sen "{student}" olarak bu bilgiyi kendi görevine nasıl uygularsın?
2-3 madde yaz.""", tokens=200)
            student_responses[student] = resp

        session_content = f"MVP: {mvp_agent}\n{mvp_raw}\n\nÖğrenci tepkileri:\n" + \
                          "\n".join(f"{k}: {v[:100]}" for k, v in student_responses.items())

        db_run("""
            INSERT INTO masterclass_history
            (week_number, topic, teacher, curriculum, agents_trained, conducted_at)
            VALUES (?,?,?,?,?,?)
        """, (-1, "Peer Learning", mvp_agent, session_content,
              str(students), datetime.now().isoformat()))

        save_knowledge("peer_learning_latest", session_content,
                       level="master", source="peer_learning")

        print(f"  ✅ Peer learning tamamlandı")
        return {
            "agent":    self.NAME,
            "mvp":      mvp_agent,
            "students": students,
            "teachings": mvp_raw,
            "responses": student_responses,
        }
