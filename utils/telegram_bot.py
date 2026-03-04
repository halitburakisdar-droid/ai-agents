"""
Telegram Bot Modülü — requests tabanlı
=======================================
python-telegram-bot yerine saf requests kullanır.
Daha basit, daha hızlı, async yok.
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


# ── Temel gönderici ──────────────────────────────────

def send_message(text: str) -> bool:
    """Basit Markdown mesaj gönder."""
    if not BOT_TOKEN or not CHAT_ID:
        print("  ⚠️  Telegram credentials eksik (.env kontrol et)")
        return False
    try:
        r = requests.post(
            f"{_API}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"},
            timeout=10,
        )
        return r.ok
    except Exception as e:
        print(f"  ⚠️  Telegram hatası: {e}")
        return False


# send_text alias (eski kodlarla uyumluluk)
def send_text(text: str) -> bool:
    return send_message(text)


# ── Level Raporları ──────────────────────────────────

def send_level1_report(content: dict) -> bool:
    """Level 1 içerik bildirimi."""
    issue_line = f"⚠️ Issue: {content['issue']}" if content.get("issue") else "✅ Healthy"
    msg = (
        f"🎨 *LEVEL 1 — YENİ İÇERİK*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏰ {datetime.now().strftime('%H:%M')}\n"
        f"📝 {content.get('type', 'Carousel')}\n"
        f"⭐ Kalite: *{content.get('score', 0)}/10*\n"
        f"🔥 Viral: {content.get('viral', 0)}/10\n\n"
        f"*BAŞLIK:*\n"
        f"{str(content.get('title', ''))[:100]}\n\n"
        f"{issue_line}"
    )
    return send_message(msg)


def send_level2_report(report: dict) -> bool:
    """Level 2 kod yazma bildirimi."""
    fixed    = report.get("fixes_successful", 0)
    status   = "✅" if fixed > 0 else "🔄"
    msg = (
        f"{status} *LEVEL 2 — AUTONOMOUS CODE*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏰ {datetime.now().strftime('%H:%M')}\n\n"
        f"*YAPILAN:*\n"
        f"• {report.get('issues_found', 0)} sorun tespit\n"
        f"• {report.get('fixes_attempted', 0)} düzeltme denendi\n"
        f"• {report.get('fixes_successful', 0)} başarılı ✅\n"
        f"• {report.get('escalations', 0)} Opus'a gönderildi ⚠️\n"
    )
    if report.get("message"):
        msg += f"\n_{report['message']}_"
    return send_message(msg)


def send_level3_brief(packet: dict = None) -> bool:
    """Level 3 stratejik özet."""
    if packet:
        perf  = packet.get("performance", {})
        n_esc = len(packet.get("escalations", []))
        avg   = perf.get("avg_quality_24h", 0)
        trend = perf.get("trend_vs_yesterday", 0)
        msg = (
            f"🎯 *LEVEL 3 — STRATEGIC BRIEF*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ {datetime.now().strftime('%d/%m %H:%M')} — Sabah Briefingi\n\n"
            f"📊 24h ort: *{avg}/10* ({'📈' if trend >= 0 else '📉'} {trend:+.2f})\n"
            f"⚠️ Açık escalation: {n_esc}\n"
            f"📦 `logs/level3_packet.json` hazır\n\n"
            f"_Opus karar vermesi için paket oluşturuldu._"
        )
    else:
        msg = (
            f"🎯 *LEVEL 3 — STRATEGIC BRIEF*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ {datetime.now().strftime('%d/%m %H:%M')} — Sabah Briefingi\n"
            f"📊 `logs/level3_packet.json` hazır\n\n"
            f"_Opus karar vermesi için paket oluşturuldu._"
        )
    return send_message(msg)


# ── Eski API uyumluluk fonksiyonları ─────────────────

def send_content_for_feedback(title: str, score: float, engagement: str,
                               hook: str = "", best_time: str = "18:00",
                               decision: str = "ONAY") -> bool:
    icon  = "🟢" if score >= 8 else "🟡" if score >= 6 else "🔴"
    emoji = "✅" if decision == "ONAY" else "🔄" if decision == "REVİZE" else "❌"
    text  = (
        f"{emoji} *Yeni İçerik* — {datetime.now().strftime('%H:%M')}\n"
        f"{icon} Kalite: *{score}/10* | {engagement}\n"
        f"⏰ {best_time}\n"
    )
    if hook:
        text += f"🎣 _{hook[:80]}_\n"
    text += f"Karar: *{decision}*"
    return send_message(text)


def send_report(level: int, title: str, body: str, success: bool = True) -> bool:
    icons  = {1: "📊", 2: "🔧", 3: "🎯"}
    status = "✅" if success else "⚠️"
    text   = (
        f"{status} *Level {level} — {title}*\n"
        f"{icons.get(level,'📌')} {datetime.now().strftime('%d/%m %H:%M')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{body[:800]}"
    )
    return send_message(text)


# ── Placeholder (bot listener kaldırıldı) ────────────

def send_summary(summary: dict) -> dict:
    """Eski send_summary uyumluluk wrapper."""
    from utils.summary_generator import build_instagram_summary
    text = f"🤖 *AI Agent — Yeni İçerik*\nKalite: {summary.get('quality',0)}/10"
    send_message(text)
    return {"ok": True}


def start_bot_listener():
    """Placeholder — requests tabanlı versiyon aktif bot listener gerektirmiyor."""
    print("  ℹ️  Telegram bot listener devre dışı (requests modu)")
