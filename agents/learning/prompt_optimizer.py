"""
Prompt Optimizer
================
Pattern Analyzer sonuçlarına göre agent promptlarını otomatik günceller.
Code Writer (qwen3.5:9b) kullanır — yavaş ama kaliteli.
Prompt versiyonlarını DB'ye kaydeder.
"""

import re
import os
from pathlib import Path
from agents.code_writer import CodeWriterAgent
from agents.learning.performance_tracker import save_prompt_version

AGENT_FILES = {
    "Research":        "agents/research_agent.py",
    "Research Agent":  "agents/research_agent.py",
    "Content":         "agents/content_creator.py",
    "Content Creator": "agents/content_creator.py",
    "Quality":         "agents/quality_controller.py",
    "Quality Controller": "agents/quality_controller.py",
    "Carousel":        "agents/instagram/carousel_agent.py",
    "Morning Bulletin": "agents/instagram/morning_bulletin.py",
}

BASE_DIR = Path(__file__).parent.parent.parent


class PromptOptimizerAgent:
    NAME = "Prompt Optimizer"

    def _extract_prompt(self, file_path: str) -> str:
        """Dosyadan prompt metnini çıkar."""
        try:
            src = (BASE_DIR / file_path).read_text(encoding="utf-8")
            # f-string prompt bloğunu bul
            match = re.search(r'prompt\s*=\s*f?"""(.*?)"""', src, re.DOTALL)
            if match:
                return match.group(1)[:600]
        except Exception:
            pass
        return ""

    def _apply_improved_prompt(self, file_path: str, old_prompt: str, new_prompt: str) -> bool:
        """Geliştirilmiş promptu dosyaya yaz."""
        try:
            full_path = BASE_DIR / file_path
            src = full_path.read_text(encoding="utf-8")

            # Eski promptu bul ve değiştir (ilk occurrence)
            old_block = f'"""{old_prompt}'
            if old_block in src:
                new_src = src.replace(old_block, f'"""{new_prompt}', 1)
                full_path.write_text(new_src, encoding="utf-8")
                return True
        except Exception as e:
            print(f"    ⚠️  Prompt yazma hatası: {e}")
        return False

    def optimize(self, analysis: dict) -> dict:
        """
        Pattern Analyzer sonucuna göre en sorunlu agent'ı iyileştir.
        Code Writer ile yeni prompt üret, DB'ye kaydet.
        """
        target_key   = analysis.get("oncelikli_agent", "Content")
        file_path    = AGENT_FILES.get(target_key, AGENT_FILES.get("Content"))
        weakness     = analysis.get("sorun_1", "Genel iyileştirme")
        solution     = analysis.get("cozum_1", "")
        comp_pattern = analysis.get("comp_pattern", "")

        print(f"\n  [{self.NAME}] '{target_key}' optimize ediliyor...")
        print(f"  Sorun   : {weakness[:70]}")
        print(f"  Çözüm   : {solution[:70]}")

        current_prompt = self._extract_prompt(file_path)
        if not current_prompt:
            current_prompt = "# Prompt bulunamadı"

        # Mevcut promptu kaydet (v1)
        v_old = save_prompt_version(target_key, current_prompt, source="original")

        # Code Writer'a iyileştirt
        cw     = CodeWriterAgent()
        result = cw.improve_prompt(
            agent_name    = target_key,
            current_prompt= current_prompt,
            weakness      = weakness,
            pattern       = f"{solution} | Rakip pattern: {comp_pattern}"[:200],
        )

        improved = result.get("improved", "")
        changes  = result.get("changes", "")

        if improved and len(improved) > 50:
            # Yeni versiyonu kaydet
            v_new = save_prompt_version(target_key, improved, source="optimized")
            # Dosyaya uygula
            applied = self._apply_improved_prompt(file_path, current_prompt, improved)
            status  = "✅ Uygulandı" if applied else "📋 Kaydedildi (manuel uygulama gerek)"
        else:
            v_new   = v_old
            applied = False
            status  = "⚠️  Yeterli iyileştirme üretilemedi"

        print(f"  {status} (v{v_old} → v{v_new})")

        return {
            "agent":         self.NAME,
            "target":        target_key,
            "file":          file_path,
            "old_version":   v_old,
            "new_version":   v_new,
            "changes":       changes,
            "applied":       applied,
            "status":        status,
            "elapsed":       result.get("elapsed", 0),
        }
