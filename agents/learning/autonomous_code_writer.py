"""
Autonomous Code Writer — Level 2 Agent
========================================
Qwen 2.5:32b kullanır.
Sorunları analiz eder, kod yazar, test eder, git'e commit eder.
"""

import ollama
import subprocess
import json
import os
import re
from datetime import datetime
from pathlib import Path

from memory.learning_db import (
    save_escalation, save_code_change, mark_code_change_rolled_back,
    init_learning_tables
)
from utils.telegram_bot import send_text

REPO = Path("/Users/burak/ai-agents")
VENV_PYTHON = str(REPO / "venv" / "bin" / "python")


class AutonomousCodeWriter:
    MODEL = "qwen3.5:9b"
    NAME  = "Autonomous Code Writer"

    def _ask(self, prompt: str, tokens: int = 1200) -> str:
        r = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.2, "num_predict": tokens},
            think=False,
        )
        return r.message.content.strip()

    def _parse_json(self, text: str) -> dict:
        """JSON bloğu veya düz JSON yakala."""
        # Kod bloğu içinde mi?
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            text = m.group(1)
        else:
            # İlk { ... } bloğu
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                text = m.group(0)
        try:
            return json.loads(text)
        except Exception:
            return {}

    # ── 1. Derin Analiz ──────────────────────────────────

    def deep_analysis(self, issue: dict) -> dict:
        """Qwen 2.5-32B ile kök neden analizi."""
        relevant = self._read_relevant_files(issue)

        prompt = f"""Sen bir Python developer agent'sın. Sistemi OTONOM olarak geliştiriyorsun.

SORUN:
Type: {issue.get('type','unknown')}
Description: {issue.get('description','')}
Agent: {issue.get('agent','unknown')}
Impact: {issue.get('impact','unknown')}

İLGİLİ KOD:
{relevant}

JSON olarak cevap ver (başka hiçbir şey yazma):
{{
  "root_cause": "...",
  "solution_approach": "...",
  "files_to_change": ["relative/path.py"],
  "risk_level": "low",
  "estimated_impact": "+X%"
}}"""

        raw = self._ask(prompt, tokens=400)
        result = self._parse_json(raw)
        if not result:
            result = {
                "root_cause": issue.get("description", ""),
                "solution_approach": "Prompt optimizasyonu",
                "files_to_change": [],
                "risk_level": "low",
                "estimated_impact": "+5%",
            }
        return result

    # ── 2. Kod Üret ──────────────────────────────────────

    def generate_code(self, analysis: dict) -> dict:
        """Her değiştirilecek dosya için yeni kodu üret."""
        files_to_change = analysis.get("files_to_change", [])
        if not files_to_change:
            return {"changes": [], "tests": ""}

        existing_codes = []
        for rel_path in files_to_change:
            full = REPO / rel_path
            if full.exists():
                content = full.read_text(encoding="utf-8")[:1500]
                existing_codes.append(f"# {rel_path}\n{content}")

        prompt = f"""Sen bir Python code writer agent'sın. Aşağıdaki sorunu çözen GERÇEK KOD yaz.

ANALİZ:
{json.dumps(analysis, ensure_ascii=False, indent=2)}

MEVCUT KOD:
{chr(10).join(existing_codes) or '(dosya bulunamadı)'}

JSON olarak cevap ver (başka hiçbir şey yazma):
{{
  "changes": [
    {{
      "file": "relative/path.py",
      "patch_lines": ["satır1", "satır2"],
      "reason": "Neden bu değişiklik"
    }}
  ],
  "tests": "# minimal test kodu"
}}

KURAL: patch_lines yerine sadece değişen fonksiyonu yaz (tüm dosyayı değil)."""

        raw = self._ask(prompt, tokens=2000)
        result = self._parse_json(raw)
        if not result or not result.get("changes"):
            return {"changes": [], "tests": ""}
        return result

    # ── 3. Değişiklikleri Uygula ─────────────────────────

    def apply_changes(self, solution: dict) -> list:
        """Dosyaları güncelle, backup al. Uygulanan dosya listesini döndür."""
        applied = []
        backup_dir = REPO / ".backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)

        for change in solution.get("changes", []):
            rel = change.get("file", "")
            if not rel:
                continue
            full = REPO / rel
            if not full.exists():
                continue

            # Backup
            (backup_dir / Path(rel).name).write_text(
                full.read_text(encoding="utf-8"), encoding="utf-8"
            )

            # Yama: patch_lines'ı dosyanın sonuna append etme,
            # bunun yerine fonksiyonu bul-değiştir mantığı yok,
            # sadece dosyaya yorum+patch ekle (güvenli mod)
            patch = "\n".join(change.get("patch_lines", []))
            if patch:
                original = full.read_text(encoding="utf-8")
                # Güvenli: mevcut dosyanın en sonuna değişikliği ekle (yorum ile)
                # Gerçek bir patch sistemi için diff/patch kullanılır
                full.write_text(
                    original + f"\n\n# [AUTO-PATCH {datetime.now().isoformat()}]\n# Reason: {change.get('reason','')}\n{patch}\n",
                    encoding="utf-8"
                )
                applied.append(rel)
                print(f"  [CodeWriter] Patched: {rel}")

        # Test dosyası
        tests = solution.get("tests", "")
        if tests:
            test_file = REPO / "tests" / "auto_generated_test.py"
            test_file.write_text(tests, encoding="utf-8")

        return applied

    # ── 4. Testleri Çalıştır ─────────────────────────────

    def run_tests(self) -> dict:
        """pytest çalıştır ve integration test yap."""
        try:
            r = subprocess.run(
                [VENV_PYTHON, "-m", "pytest", "tests/", "-v", "--tb=short", "-q"],
                cwd=REPO, capture_output=True, timeout=120,
                text=True
            )
            if r.returncode == 0:
                return {"success": True, "details": r.stdout[-500:]}
            else:
                return {"success": False, "error": (r.stdout + r.stderr)[-500:]}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Tests timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_integration_test(self) -> bool:
        """Hızlı integration: price_monitor'ü import et."""
        try:
            r = subprocess.run(
                [VENV_PYTHON, "-c",
                 "import sys; sys.path.insert(0,'.');"
                 "from agents.price_monitor import PriceMonitorAgent;"
                 "p=PriceMonitorAgent(); d=p.run();"
                 "assert 'gold' in d; print('OK')"],
                cwd=REPO, capture_output=True, timeout=30, text=True
            )
            return r.returncode == 0
        except Exception:
            return False

    # ── 5. Git ──────────────────────────────────────────

    def git_commit(self, applied_files: list, reason: str) -> str:
        """Değişiklikleri commit et, hash döndür."""
        try:
            subprocess.run(["git", "add"] + applied_files, cwd=REPO, check=True)
            msg = (
                f"🤖 Auto-fix: {reason[:60]}\n\n"
                f"Files: {', '.join(applied_files)}\n"
                f"Agent: {self.NAME} ({self.MODEL})\n"
                f"Time: {datetime.now().isoformat()}"
            )
            subprocess.run(["git", "commit", "-m", msg], cwd=REPO, check=True)
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=REPO, capture_output=True, text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return ""

    def git_rollback(self, files: list):
        """Son değişiklikleri geri al."""
        try:
            subprocess.run(["git", "checkout", "--"] + files, cwd=REPO, check=True)
            print(f"  [CodeWriter] Rolled back: {files}")
        except Exception as e:
            print(f"  [CodeWriter] Rollback failed: {e}")

    # ── 6. Ana Döngü ─────────────────────────────────────

    def analyze_and_fix(self, issue: dict) -> dict:
        """
        Tam döngü: analiz → kod → uygula → test → commit veya rollback.
        """
        print(f"\n  [{self.NAME}] Analiz ediliyor: {issue.get('type','?')}")

        # 1. Analiz
        analysis = self.deep_analysis(issue)
        if analysis.get("risk_level") == "high":
            print("  Risk yüksek — escalate to Level 3")
            eid = save_escalation(
                issue.get("type", ""), issue.get("description", ""),
                "Risk too high for auto-fix", "High risk level detected"
            )
            send_text(
                f"⚠️ *Level 3 ESCALATION*\n"
                f"Issue: {issue.get('type','')}\n"
                f"Risk: high — otomatik düzeltme yapılmadı"
            )
            return {"success": False, "escalated": True, "esc_id": eid}

        # 2. Kod üret
        solution = self.generate_code(analysis)
        if not solution.get("changes"):
            print("  Kod değişikliği üretilemedi — atlıyorum")
            return {"success": False, "reason": "no_changes_generated"}

        # 3. Uygula
        applied = self.apply_changes(solution)
        if not applied:
            return {"success": False, "reason": "no_files_applied"}

        # 4. Test
        test_result = self.run_tests()
        integration_ok = self.run_integration_test()

        if test_result["success"] and integration_ok:
            # 5. Commit
            commit_hash = self.git_commit(applied, analysis.get("solution_approach", "improvement"))
            for f in applied:
                save_code_change(f, analysis.get("solution_approach", ""), commit_hash, True)
            send_text(
                f"✅ *Auto-fix başarılı!*\n"
                f"Issue: {issue.get('type','')}\n"
                f"Files: {', '.join(applied)}\n"
                f"Commit: `{commit_hash}`"
            )
            return {"success": True, "commit": commit_hash, "files": applied}
        else:
            # 6. Rollback
            self.git_rollback(applied)
            err = test_result.get("error", "integration test failed")
            eid = save_escalation(
                issue.get("type", ""), issue.get("description", ""),
                f"Auto-fix attempted: {', '.join(applied)}", err
            )
            send_text(
                f"⚠️ *Auto-fix BAŞARISIZ → Opus'a escalate*\n"
                f"Issue: {issue.get('type','')}\n"
                f"Error: {err[:200]}"
            )
            return {"success": False, "escalated": True, "esc_id": eid, "error": err}

    # ── Yardımcı ─────────────────────────────────────────

    def _read_relevant_files(self, issue: dict) -> str:
        """Issue'ya göre ilgili dosyaları kısaca oku."""
        agent = issue.get("agent", "").lower().replace(" ", "_")
        candidates = []
        if agent:
            for suffix in [".py"]:
                for d in ["agents", "agents/learning", "agents/instagram"]:
                    p = REPO / d / (agent + suffix)
                    if p.exists():
                        candidates.append(p)
        if not candidates:
            # En son değiştirilen agents/*.py
            candidates = sorted(
                (REPO / "agents").glob("*.py"),
                key=lambda x: x.stat().st_mtime, reverse=True
            )[:2]

        out = []
        for p in candidates[:2]:
            content = p.read_text(encoding="utf-8")[:800]
            out.append(f"# {p.relative_to(REPO)}\n{content}")
        return "\n\n".join(out) or "(dosya bulunamadı)"
