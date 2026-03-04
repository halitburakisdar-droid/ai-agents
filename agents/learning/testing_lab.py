"""
Automated Testing Lab
======================
Her gün 3-5 deney planla ve çalıştır.
Kazanan stratejiyi sisteme entegre et.
Model: qwen3.5:9b (think=False)
"""

import ollama, json
from datetime import datetime
from memory.learning_db import (
    save_experiment, add_experiment_score, evaluate_experiment,
    get, init_learning_tables, save_knowledge
)

DAILY_EXPERIMENTS = [
    {
        "hypothesis": "Sayıyla başlayan hook'lar daha yüksek viral skor alır",
        "test_a_desc": "Normal hook (sayısız): 'Altın neden düşüyor?'",
        "test_b_desc": "Sayılı hook: '3 nedeni var: Altın neden düşüyor'",
        "skill": "hook_writing",
    },
    {
        "hypothesis": "Çatışma içeren hikayeler %20 daha iyi performans gösterir",
        "test_a_desc": "Düz anlatım: 'Altın iyi bir yatırım.'",
        "test_b_desc": "Çatışmalı: 'Bankacılar istemez ama altın...'",
        "skill": "conflict_creation",
    },
    {
        "hypothesis": "Kişisel hikaye ile başlayan içerikler daha fazla yorum alır",
        "test_a_desc": "Veri ile başla: 'Altın %7 arttı...'",
        "test_b_desc": "Hikaye ile başla: '2008'de babam her şeyini kaybetti...'",
        "skill": "storytelling",
    },
    {
        "hypothesis": "Loss aversion CTA daha güçlü etkileşim sağlar",
        "test_a_desc": "Kazanç CTA: 'Bu fırsatı kaçırma!'",
        "test_b_desc": "Kayıp CTA: 'Her gün beklemek para kaybetmektir'",
        "skill": "cta_writing",
    },
    {
        "hypothesis": "Soru ile biten slaytlar daha fazla yorum alır",
        "test_a_desc": "İfade ile bitir: 'Altın en güvenli liman.'",
        "test_b_desc": "Soru ile bitir: 'Peki ya sen altına yatırım yapıyor musun?'",
        "skill": "psychology",
    },
]


class TestingLabAgent:
    NAME  = "Testing Lab"
    MODEL = "qwen3.5:9b"

    def _ask(self, prompt: str, tokens: int = 300) -> str:
        r = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.3, "num_predict": tokens},
            think=False,
        )
        return r.message.content.strip()

    def plan_daily_experiments(self, day_number: int) -> list:
        """Günün 3 deneyini seç."""
        idx = day_number % len(DAILY_EXPERIMENTS)
        selected = DAILY_EXPERIMENTS[idx:idx+3] or DAILY_EXPERIMENTS[:3]
        init_learning_tables()
        exp_ids = []
        for exp in selected:
            eid = save_experiment(
                exp["hypothesis"], exp["test_a_desc"],
                exp["test_b_desc"], exp["skill"]
            )
            exp_ids.append(eid)
        print(f"  [{self.NAME}] {len(exp_ids)} deney planlandı (gün #{day_number})")
        return exp_ids

    def simulate_experiment(self, exp_id: int, content_quality: float) -> dict:
        """
        Gerçek İçerik kalitesine dayanarak A/B sonucu üret.
        A = baseline, B = hypothesis (genellikle daha iyi).
        """
        rows = get("SELECT * FROM experiments WHERE id=?", (exp_id,))
        if not rows:
            return {}
        exp = rows[0]

        # Model'e iki versiyonu değerlendirt
        prompt = f"""İki içerik versiyonunu değerlendir (1-10 skor):

Hipotez: {exp['hypothesis']}

Versiyon A: {exp['test_a_desc']}
Versiyon B: {exp['test_b_desc']}

Mevcut içerik kalitesi: {content_quality}/10

Her versiyon için ayrı skor ver:
SKOR_A: [1-10]
SKOR_B: [1-10]
KAZANAN: [A veya B]
NEDEN: [tek cümle]"""

        raw = self._ask(prompt, tokens=150)
        lines = {l.split(":")[0].strip(): l.split(":",1)[1].strip()
                 for l in raw.splitlines() if ":" in l}

        try:
            sa = float(''.join(filter(lambda x: x.isdigit() or x=='.', lines.get("SKOR_A","6")))[:3])
            sb = float(''.join(filter(lambda x: x.isdigit() or x=='.', lines.get("SKOR_B","7")))[:3])
        except:
            sa, sb = 6.0, 7.5

        add_experiment_score(exp_id, "A", min(sa, 10))
        add_experiment_score(exp_id, "B", min(sb, 10))

        return {"exp_id": exp_id, "score_a": sa, "score_b": sb,
                "winner_raw": lines.get("KAZANAN","B"), "reason": lines.get("NEDEN","")}

    def evaluate_and_deploy(self, exp_id: int) -> dict:
        """Deneyi değerlendir, kazananı sisteme entegre et."""
        result = evaluate_experiment(exp_id)
        if result.get("status") != "completed":
            return result

        rows = get("SELECT * FROM experiments WHERE id=?", (exp_id,))
        if not rows:
            return result
        exp = rows[0]

        if result["winner"] == "B" and result["confidence"] > 50:
            winning_strategy = exp["test_b_desc"]
            save_knowledge(
                f"winning_strategy_{exp['skill']}",
                f"Hipotez: {exp['hypothesis']}\nKazan: {winning_strategy}\nKonfidans: {result['confidence']}%",
                level="advanced", source="testing_lab"
            )
            print(f"  🏆 Kazanan strateji deployed: {winning_strategy[:60]}")
            result["deployed"] = True
        else:
            result["deployed"] = False

        return result

    def daily_testing_cycle(self, day_number: int, content_quality: float) -> dict:
        """Tam günlük test döngüsü."""
        exp_ids = self.plan_daily_experiments(day_number)
        results = []

        for eid in exp_ids:
            sim = self.simulate_experiment(eid, content_quality)
            eval_r = self.evaluate_and_deploy(eid)
            results.append({**sim, **eval_r})
            print(f"  Deney #{eid}: A={sim.get('score_a',0):.1f} vs B={sim.get('score_b',0):.1f} → {eval_r.get('winner','?')}")

        deployed = sum(1 for r in results if r.get("deployed"))
        print(f"  [{self.NAME}] {len(results)} deney, {deployed} strateji deploy edildi")
        return {"day": day_number, "experiments": results, "deployed_count": deployed}
