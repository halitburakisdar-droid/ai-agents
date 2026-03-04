"""
Telegram Bot Modülü
===================
- İçerik özeti gönderir
- ✅ ONAYLA / ❌ REDDET butonları
- Manuel override
- SQLite'a karar loglar
"""

import os
import json
import asyncio
import threading
from datetime import datetime
from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

# Bekleyen kararlar: message_id → {summary, event, decision}
_pending: dict = {}


# ── Mesaj Gönderme ──────────────────────────────────

def _build_message(summary: dict) -> str:
    """JSON özetinden okunabilir Telegram mesajı oluştur."""
    m   = summary.get("market", {})
    sig = summary.get("signals", {})
    cnt = summary.get("content", {})
    qc  = summary.get("qc", {})

    altin_icon = "📈" if "+" in m.get("altin","") else "📉"
    btc_icon   = "📈" if "+" in m.get("btc","")   else "📉"
    dolar_icon = "📈" if "+" in m.get("dolar","") else "📉"

    score = summary.get("quality", 0)
    score_bar = "🟢" if score >= 8 else "🟡" if score >= 6 else "🔴"

    return (
        f"🤖 *AI Agent — Yeni İçerik Hazır*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 *{summary.get('title', 'İçerik')[:55]}*\n\n"
        f"📊 *Piyasa*\n"
        f"{altin_icon} Altın: `{m.get('altin','?')}`   "
        f"{btc_icon} BTC: `{m.get('btc','?')}`\n"
        f"{dolar_icon} Dolar: `{m.get('dolar','?')}`   "
        f"📈 BIST: `{m.get('bist','?')}`\n\n"
        f"🌍 Jeopolitik risk: *{sig.get('geo_risk','?').upper()}*\n"
        f"🏆 Kazanan: `{sig.get('winner','?')}` | Kaybeden: `{sig.get('loser','?')}`\n\n"
        f"📱 *İçerik*\n"
        f"Slayt: {cnt.get('slides','?')} | Hashtag: {cnt.get('hashtags','?')} | Caption: {cnt.get('caption_chars','?')} kr\n"
        f"Trendler: {', '.join(cnt.get('top_trends',[])[:3]) or '-'}\n\n"
        f"{score_bar} *Kalite Skoru: {score}/10* | Engagement: {summary.get('engagement','?')}\n"
        f"⏰ En iyi saat: `{summary.get('best_time','?')}`\n\n"
        f"💡 *QC Notu:*\n"
        f"✔️ {qc.get('guclu','')[:60]}\n"
        f"⚠️ {qc.get('zayif','')[:60]}\n"
        f"🔧 {qc.get('iyilestirme','')[:70]}\n\n"
        f"🤖 Agent tavsiyesi: *{summary.get('agent_rec','?')}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"_Karar ver:_"
    )


def _build_keyboard(summary_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ ONAYLA",      callback_data=f"ONAY|{summary_key}"),
            InlineKeyboardButton("❌ REDDET",      callback_data=f"RED|{summary_key}"),
        ],
        [
            InlineKeyboardButton("🔄 REVİZE ET",  callback_data=f"REVIZE|{summary_key}"),
            InlineKeyboardButton("🛠 AGENT FİX",  callback_data=f"AGENT_REVIZE|{summary_key}"),
        ],
    ])


async def _send_async(summary: dict) -> dict:
    bot = Bot(token=TOKEN)
    text    = _build_message(summary)
    summary_key = datetime.now().strftime("%H%M%S")

    msg = await bot.send_message(
        chat_id    = CHAT_ID,
        text       = text,
        parse_mode = "Markdown",
        reply_markup = _build_keyboard(summary_key),
    )

    # Kararı beklemek için event koy
    event = asyncio.Event()
    _pending[summary_key] = {
        "summary":  summary,
        "event":    event,
        "decision": None,
        "note":     "",
        "msg_id":   msg.message_id,
    }
    return {"msg_id": msg.message_id, "summary_key": summary_key}


def send_summary(summary: dict) -> dict:
    """Özeti Telegram'a gönder (sync wrapper)."""
    if not TOKEN or not CHAT_ID:
        print("  ⚠️  Telegram credentials eksik, atlanıyor.")
        return {"error": "no_credentials"}
    try:
        result = asyncio.run(_send_async(summary))
        print(f"  📨 Telegram'a gönderildi (msg_id={result['msg_id']})")
        return result
    except Exception as e:
        print(f"  ⚠️  Telegram gönderme hatası: {e}")
        return {"error": str(e)}


async def _send_simple_async(text: str):
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")


def send_text(text: str):
    """Düz metin mesaj gönder."""
    if not TOKEN or not CHAT_ID:
        return
    try:
        asyncio.run(_send_simple_async(text))
    except Exception as e:
        print(f"  ⚠️  Telegram metin hatası: {e}")


# ── Buton Callback Handler ──────────────────────────

async def _button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    if "|" not in data:
        return

    decision, key = data.split("|", 1)
    decision_map = {
        "ONAY": "ONAY", "RED": "RED",
        "REVIZE": "REVİZE", "AGENT_REVIZE": "AGENT_REVIZE",
    }
    decision = decision_map.get(decision, decision)

    emoji = {"ONAY": "✅", "RED": "❌", "REVİZE": "🔄", "AGENT_REVIZE": "🛠"}.get(decision, "📌")

    # Log + kullanıcıya geri bildirim
    from utils.decision_logger import log_decision, init_decision_table
    init_decision_table()
    pending = _pending.get(key)
    if pending:
        summary = pending["summary"]
        summary_json = json.dumps(summary, ensure_ascii=False, separators=(",", ":"))
        tokens_s = int(len(summary_json.split()) * 1.3)
        tokens_d = 5
        log_decision(summary, decision, f"Telegram buton: {decision}", tokens_s, tokens_d)
        pending["decision"] = decision
        if pending.get("event"):
            pending["event"].set()

    await query.edit_message_text(
        text=f"{emoji} *{decision}* kararı verildi!\n\n"
             f"_{query.message.text[:200] if query.message else ''}_",
        parse_mode="Markdown",
    )
    print(f"\n  📲 Telegram kararı: {decision} [key={key}]")


def start_bot_listener():
    """
    Arka planda buton dinleyici başlat.
    Bağımsız thread'de çalışır, ana loop'u bloklamaz.
    """
    if not TOKEN:
        return

    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CallbackQueryHandler(_button_handler))
        print("  🤖 Telegram bot dinliyor (buton callback'ler aktif)")
        app.run_polling(stop_signals=None)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t
