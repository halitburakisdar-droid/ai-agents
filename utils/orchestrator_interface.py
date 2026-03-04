"""
Orchestrator Interface
======================
Opus 4.6'nın karar verdiği yer.

Bu modül:
  1. JSON özeti formatlar (minimal, ~80 token)
  2. Kararı bekler (ONAY / RED / REVİZE / AGENT_REVIZE)
  3. Kararı loglar
  4. Günlük 10 karar limitini korur

Orchestrator (Claude Code) bu modülden gelen özeti okur
ve sadece kararını yazar — kod veya içerik okumaz.
"""

import json
import time
from datetime import datetime
from utils.decision_logger import log_decision, get_token_report, print_token_report, init_decision_table

# Günlük limit
DAILY_DECISION_LIMIT = 10

VALID_DECISIONS = {"ONAY", "RED", "REVİZE", "AGENT_REVIZE"}


def _token_count(text: str) -> int:
    return int(len(text.split()) * 1.3)


def _check_daily_limit() -> tuple[int, bool]:
    """Bugün kaç karar verildi? Limite ulaşıldı mı?"""
    r = get_token_report()
    count = r["today"]["count"]
    return count, count >= DAILY_DECISION_LIMIT


def present_to_orchestrator(summary: dict, context: str = "") -> dict:
    """
    Özeti ekrana basar → Orchestrator (biz/Opus) kararını okur.
    Otomasyon modunda agent_rec'i kullan.
    """
    init_decision_table()

    used, limit_hit = _check_daily_limit()

    summary_json = json.dumps(summary, ensure_ascii=False, separators=(",", ":"))
    summary_tokens = _token_count(summary_json)

    print(f"\n{'★'*52}")
    print(f"  ORCHESTRATOR KARAR NOKTASI  [{datetime.now().strftime('%H:%M')}]")
    print(f"  Bugün: {used}/{DAILY_DECISION_LIMIT} karar kullanıldı")
    print(f"{'★'*52}")

    if limit_hit:
        print(f"\n  ⚠️  Günlük limit doldu ({DAILY_DECISION_LIMIT} karar)!")
        print(f"  Otomatik karar: agent tavsiyesi kullanılıyor")
        decision = summary.get("agent_rec", "REVİZE").upper()
        if decision not in VALID_DECISIONS:
            decision = "REVİZE"
        note = f"[OTO-LİMİT] Agent tavsiyesi: {summary.get('agent_rec','?')}"
        dec_tokens = 5
        total = log_decision(summary, decision, note, summary_tokens, dec_tokens)
        print(f"  Karar: {decision} | Toplam: {total} token")
        return {"decision": decision, "note": note, "tokens": total, "auto": True}

    # Özeti göster (Opus okur)
    print(f"\n  📋 ÖZET ({summary_tokens} token):")
    print(f"  {summary_json}\n")

    if context:
        print(f"  🔍 Bağlam: {context}\n")

    print(f"  ┌─ KARAR SEÇENEKLERİ:")
    print(f"  │  ONAY         → Yayınla, sistem devam etsin")
    print(f"  │  RED          → Yayınlama, atla")
    print(f"  │  REVİZE       → Küçük düzeltme yap, sonra yayınla")
    print(f"  │  AGENT_REVIZE → Agent promptunu Code Writer'a düzelt")
    print(f"  └─ [Orchestrator kararını bu konuşmada veriyor...]\n")

    # Otomatik mod: agent tavsiyesini kullan (pipeline çalışırken)
    auto_decision = summary.get("agent_rec", "REVİZE").upper()
    if auto_decision not in VALID_DECISIONS:
        auto_decision = "ONAY" if summary.get("quality", 0) >= 7 else "REVİZE"

    note = f"[OTO] quality={summary.get('quality',0)} engagement={summary.get('engagement','?')}"
    dec_tokens = 8
    elapsed_ms = 0

    total = log_decision(summary, auto_decision, note, summary_tokens, dec_tokens, elapsed_ms)

    print(f"  ✅ Otomatik karar (Orchestrator onayı bekleniyor): {auto_decision}")
    print(f"  📊 Token kullanımı: {summary_tokens} + {dec_tokens} = {total} token\n")

    return {
        "decision":       auto_decision,
        "note":           note,
        "summary_tokens": summary_tokens,
        "dec_tokens":     dec_tokens,
        "total_tokens":   total,
        "auto":           True,
    }


def manual_orchestrator_decision(summary: dict, decision: str, note: str = "") -> dict:
    """
    Orchestrator'ın bu konuşmada verdiği manuel kararı logla.
    instagram_pipeline.py veya autonomous_loop.py'den çağrılır.
    """
    init_decision_table()
    decision = decision.upper().strip()
    if decision not in VALID_DECISIONS:
        raise ValueError(f"Geçersiz karar: {decision}. Geçerli: {VALID_DECISIONS}")

    summary_json   = json.dumps(summary, ensure_ascii=False, separators=(",", ":"))
    summary_tokens = _token_count(summary_json)
    dec_tokens     = _token_count(f"{decision} {note}")
    total = log_decision(summary, decision, note, summary_tokens, dec_tokens)

    print(f"\n  ✅ ORCHESTRATOR KARARI KAYDEDILDI")
    print(f"  Karar   : {decision}")
    print(f"  Not     : {note}")
    print(f"  Tokenler: {summary_tokens} (özet) + {dec_tokens} (karar) = {total} toplam")

    return {"decision": decision, "note": note, "total_tokens": total}
