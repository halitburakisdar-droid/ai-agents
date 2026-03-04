"""
Quarterly Evolution — 3 Aylık Köklü Değişim
=============================================
Opus 4.6 (Orchestrator) stratejik karar verir.
qwen3.5:9b analiz hazırlar, Opus son kararı verir.
"""

import ollama, json
from datetime import datetime
from memory.learning_db import (
    init_learning_tables, save_knowledge, get as db_get, run as db_run, ALL_AGENTS
)
from agents.learning.performance_tracker import get_performance_stats, get_best_worst


class QuarterlyEvolutionAgent:
    NAME  = "Quarterly Evolution"
    MODEL = "qwen3.5:9b"

    def _ask(self, prompt: str, tokens: int = 600) -> str:
        r = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.4, "num_predict": tokens},
            think=False,
        )
        return r.message.content.strip()

    def compile_quarter_report(self, quarter: str) -> dict:
        """Son 3 ayın verisini derle."""
        init_learning_tables()
        stats = get_performance_stats(last_n=200)
        bw    = get_best_worst(last_n=200)

        # Masterclass geçmişi
        masterclasses = db_get(
            "SELECT topic, conducted_at FROM masterclass_history ORDER BY id DESC LIMIT 10")
        # Deney kazananları
        winning_exp = db_get(
            "SELECT hypothesis, winner, confidence FROM experiments WHERE status='completed' AND winner='B' LIMIT 5")
        # Skill seviyeleri
        skills = db_get("SELECT agent_name, skill, level, mastery_score FROM skill_tree ORDER BY mastery_score DESC LIMIT 10")

        report = {
            "quarter":         quarter,
            "total_content":   stats["n"],
            "avg_quality":     stats["avg_quality"],
            "avg_viral":       stats["avg_viral"],
            "publish_rate":    stats["publish_rate"],
            "best_content":    bw["best"][:3],
            "worst_content":   bw["worst"][:3],
            "masterclasses":   len(masterclasses),
            "winning_experiments": len(winning_exp),
            "top_skills":      skills[:5],
        }
        return report

    def generate_evolution_plan(self, q_report: dict) -> str:
        """Qwen analizi ile evrim planı taslağı üret."""
        best_str  = "\n".join(f"  - {c['title']} ({c['score']}/10)"
                              for c in q_report["best_content"] if c.get("title"))
        worst_str = "\n".join(f"  - {c['title']} ({c['score']}/10)"
                              for c in q_report["worst_content"] if c.get("title"))
        top_skill = q_report["top_skills"][0] if q_report["top_skills"] else {}

        analysis = self._ask(f"""
{q_report['quarter']} çeyreği analizi:

İstatistikler:
- Toplam içerik: {q_report['total_content']}
- Ort. kalite: {q_report['avg_quality']}/10
- Yayın oranı: %{q_report['publish_rate']}
- Masterclass: {q_report['masterclasses']}
- Kazanan deney: {q_report['winning_experiments']}

En iyi içerikler:
{best_str or '  (veri yok)'}

En kötü içerikler:
{worst_str or '  (veri yok)'}

En güçlü skill: {top_skill.get('agent_name','?')} → {top_skill.get('skill','?')} [{top_skill.get('level','?')}]

Sonraki çeyrek için öneriler:
1. HANGİ_AGENT_YENİDEN_EĞİTİLMELİ: [agent adı + neden]
2. YENİ_BECERİ_EKLENMELİ: [skill + açıklama]
3. TERKEDILECEK_STRATEJİ: [ne kaldırılmalı]
4. YENİ_BENCHMARK: [hangi hesap örnek alınmalı]
5. Q2_HEDEFİ: [ölçülebilir hedef]""", tokens=600)

        return analysis

    def orchestrator_decision_prompt(self, q_report: dict, analysis: str) -> str:
        """Opus'a gönderilecek minimal JSON özet."""
        return json.dumps({
            "type": "quarterly_evolution",
            "quarter": q_report["quarter"],
            "avg_quality": q_report["avg_quality"],
            "publish_rate": q_report["publish_rate"],
            "total_cycles": q_report["total_content"],
            "masterclasses_done": q_report["masterclasses"],
            "qwen_recommendation": analysis[:400],
            "decision_needed": "Sonraki çeyrek strateji onayı"
        }, ensure_ascii=False)

    def run(self, quarter: str = None) -> dict:
        """Tam çeyrek evrim döngüsü."""
        if not quarter:
            now = datetime.now()
            q   = (now.month - 1) // 3 + 1
            quarter = f"{now.year}-Q{q}"

        print(f"\n  [{self.NAME}] {quarter} evrim analizi başladı...")
        q_report = self.compile_quarter_report(quarter)
        analysis = self.generate_evolution_plan(q_report)
        opus_json = self.orchestrator_decision_prompt(q_report, analysis)

        # Kaydet
        db_run("""
            INSERT INTO quarterly_reports
            (quarter, total_content, avg_engagement, best_practices,
             worst_practices, evolution_plan, created_at)
            VALUES (?,?,?,?,?,?,?)
        """, (quarter, q_report["total_content"], q_report["avg_quality"],
              json.dumps(q_report["best_content"], ensure_ascii=False),
              json.dumps(q_report["worst_content"], ensure_ascii=False),
              analysis, datetime.now().isoformat()))

        save_knowledge(f"quarterly_{quarter}", analysis,
                       level="master", source="quarterly_evolution")

        print(f"  ✅ {quarter} raporu hazır")
        print(f"  Ort. kalite: {q_report['avg_quality']}/10 | Yayın: %{q_report['publish_rate']}")
        return {
            "agent":      self.NAME,
            "quarter":    quarter,
            "report":     q_report,
            "analysis":   analysis,
            "opus_json":  opus_json,
        }
