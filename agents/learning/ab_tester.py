"""
A/B Tester
==========
İki prompt versiyonunu karşılaştırır, kazananı seçer.
N örnek sonra istatistiksel kazananı bildirir.
"""

import sqlite3
import random
from datetime import datetime
from pathlib import Path
from agents.learning.performance_tracker import DB, init_tables


class ABTesterAgent:
    NAME = "A/B Tester"
    MIN_SAMPLES = 6  # her versiyon için minimum örnek sayısı

    def start_test(self, agent_name: str, v_a: int, v_b: int) -> int:
        """Yeni A/B testi başlat, test ID döndür."""
        init_tables()
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("""
            INSERT INTO ab_tests (timestamp, agent_name, version_a, version_b, status)
            VALUES (?,?,?,?,?)
        """, (datetime.now().isoformat(), agent_name, v_a, v_b, "running"))
        test_id = c.lastrowid
        conn.commit()
        conn.close()
        print(f"  [{self.NAME}] A/B Test #{test_id} başlatıldı: v{v_a} vs v{v_b}")
        return test_id

    def record_sample(self, test_id: int, version: int, score: float):
        """Test sonucu kaydet."""
        init_tables()
        conn = sqlite3.connect(DB)
        conn.execute("""
            INSERT INTO content_performance (timestamp, prompt_version, quality_score, viral_score, decision)
            VALUES (?,?,?,0,'AB_TEST')
        """, (datetime.now().isoformat(), version, score))
        conn.commit()
        conn.close()

    def evaluate(self, test_id: int) -> dict:
        """Yeterli örnek varsa kazananı belirle."""
        init_tables()
        conn = sqlite3.connect(DB)
        c = conn.cursor()

        test = c.execute("SELECT agent_name, version_a, version_b FROM ab_tests WHERE id=?",
                         (test_id,)).fetchone()
        if not test:
            conn.close()
            return {"status": "not_found"}

        agent_name, v_a, v_b = test

        scores_a = c.execute("SELECT quality_score FROM content_performance WHERE prompt_version=?",
                             (v_a,)).fetchall()
        scores_b = c.execute("SELECT quality_score FROM content_performance WHERE prompt_version=?",
                             (v_b,)).fetchall()

        n_a = len(scores_a)
        n_b = len(scores_b)

        if n_a < self.MIN_SAMPLES or n_b < self.MIN_SAMPLES:
            conn.close()
            return {
                "status":   "running",
                "test_id":  test_id,
                "n_a":      n_a,
                "n_b":      n_b,
                "needed":   self.MIN_SAMPLES,
                "message":  f"Henüz yeterli veri yok: A={n_a}/{self.MIN_SAMPLES}, B={n_b}/{self.MIN_SAMPLES}",
            }

        avg_a = sum(r[0] for r in scores_a) / n_a
        avg_b = sum(r[0] for r in scores_b) / n_b
        winner = v_a if avg_a >= avg_b else v_b
        winner_label = "A" if winner == v_a else "B"

        c.execute("""
            UPDATE ab_tests
            SET winner=?, a_avg_score=?, b_avg_score=?, n_samples=?, status='completed'
            WHERE id=?
        """, (winner, round(avg_a, 2), round(avg_b, 2), n_a + n_b, test_id))
        conn.commit()
        conn.close()

        print(f"\n  [{self.NAME}] Test #{test_id} sonucu:")
        print(f"    v{v_a} (A): {avg_a:.2f}/10 ({n_a} örnek)")
        print(f"    v{v_b} (B): {avg_b:.2f}/10 ({n_b} örnek)")
        print(f"    🏆 KAZANAN: Versiyon {winner_label} (v{winner})")

        return {
            "status":       "completed",
            "test_id":      test_id,
            "winner":       winner,
            "winner_label": winner_label,
            "avg_a":        round(avg_a, 2),
            "avg_b":        round(avg_b, 2),
            "n_a":          n_a,
            "n_b":          n_b,
            "improvement":  round(abs(avg_a - avg_b), 2),
        }

    def should_use_b(self, test_id: int) -> bool:
        """Aktif test sırasında rastgele A veya B seç (%50/%50)."""
        return random.random() > 0.5
