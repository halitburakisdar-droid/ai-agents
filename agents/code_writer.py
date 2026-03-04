"""
Agent: Code Writer — qwen3.5:9b
=================================
Görevler:
  - Yeni Python agent kodu yazar
  - Mevcut agent'ları geliştirir
  - Bug fix yapar
  - Prompt optimizasyonu yapar

NOT: qwen3.5:9b büyük model — her çağrı 1-3 dakika sürebilir.
Yalnızca şu durumda çağrılır:
  1. Orchestrator "AGENT_REVIZE" kararı verdiğinde
  2. Learning Engine yeni kalıp öğrendiğinde
  3. Manuel tetikleme
"""

import ollama
import time
from pathlib import Path


class CodeWriterAgent:
    NAME  = "Code Writer"
    MODEL = "qwen3.5:9b"

    def _ask(self, prompt: str) -> str:
        r = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.2, "num_predict": 800},
        )
        return r.message.content.strip()

    def improve_prompt(self, agent_name: str, current_prompt: str,
                       weakness: str, pattern: str) -> dict:
        """Mevcut bir agent'ın promptunu iyileştir."""
        print(f"\n  [{self.NAME}] '{agent_name}' promptu iyileştiriliyor...")
        print(f"  ⚠️  qwen3.5:9b — 1-3dk sürebilir")
        t0 = time.time()

        prompt = f"""Sen deneyimli bir AI prompt mühendisisin. Aşağıdaki agent promptunu iyileştir.

Agent: {agent_name}
Tespit edilen zayıflık: {weakness}
Öğrenilen kalıp: {pattern}

Mevcut prompt:
---
{current_prompt[:500]}
---

Görev:
1. Zayıflığı gider
2. Kalıbı uygula
3. İyileştirilmiş prompt yaz (aynı format, Türkçe)
4. Değişiklikleri kısaca açıkla

Format:
IMPROVED_PROMPT:
[yeni prompt buraya]

DEGISIKLIKLER: [1-2 cümle açıklama]"""

        raw = self._ask(prompt)
        elapsed = round(time.time() - t0, 1)

        # Parse
        improved = ""
        changes  = ""
        if "IMPROVED_PROMPT:" in raw:
            parts = raw.split("IMPROVED_PROMPT:", 1)
            rest  = parts[1].strip()
            if "DEGISIKLIKLER:" in rest:
                improved = rest.split("DEGISIKLIKLER:")[0].strip()
                changes  = rest.split("DEGISIKLIKLER:")[1].strip()
            else:
                improved = rest

        print(f"    Tamamlandı ({elapsed}s)")
        return {
            "agent":    self.NAME,
            "target":   agent_name,
            "improved": improved or raw,
            "changes":  changes,
            "elapsed":  elapsed,
        }

    def write_new_agent(self, description: str, model: str = "qwen3.5:9b") -> dict:
        """Sıfırdan yeni bir agent yaz."""
        print(f"\n  [{self.NAME}] Yeni agent yazılıyor: {description[:50]}...")
        print(f"  ⚠️  qwen3.5:9b — 2-4dk sürebilir")
        t0 = time.time()

        prompt = f"""Python'da yeni bir Instagram içerik agent'ı yaz.

Açıklama: {description}
Kullanılacak model: {model}

Gereksinimler:
- Ollama ile {model} kullan, think=False
- run() metodu dict döndürsün
- Türkçe print mesajları
- Şu template'i takip et:

```python
import ollama

class YeniAgent:
    NAME = "..."
    MODEL = "{model}"

    def _ask(self, prompt: str) -> str:
        r = ollama.chat(
            model=self.MODEL,
            messages=[{{"role": "user", "content": prompt}}],
            options={{"temperature": 0.5, "num_predict": 300}},
            think=False,
        )
        return r.message.content.strip()

    def run(self, ...data...) -> dict:
        ...
```

Tam çalışan Python kodu yaz."""

        raw = self._ask(prompt)
        elapsed = round(time.time() - t0, 1)
        print(f"    Tamamlandı ({elapsed}s)")

        return {
            "agent":   self.NAME,
            "code":    raw,
            "elapsed": elapsed,
        }

    def fix_bug(self, file_path: str, error: str, code_snippet: str) -> dict:
        """Bir dosyadaki bug'ı tespit et ve düzelt."""
        print(f"\n  [{self.NAME}] Bug düzeltiliyor: {file_path}")
        t0 = time.time()

        prompt = f"""Python bug düzeltme görevi.

Dosya: {file_path}
Hata: {error}

İlgili kod:
```python
{code_snippet[:600]}
```

Düzeltilmiş kodu yaz. Sadece değişen kısmı göster.
Format:
SORUN: [ne yanlış]
COZUM:
```python
[düzeltilmiş kod]
```"""

        raw = self._ask(prompt)
        elapsed = round(time.time() - t0, 1)

        return {
            "agent":   self.NAME,
            "file":    file_path,
            "fix":     raw,
            "elapsed": elapsed,
        }
