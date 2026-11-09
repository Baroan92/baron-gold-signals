import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, ContextTypes, filters
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
log = logging.getLogger("baron-gold")

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = os.environ.get("CHANNEL_ID", "@baroan92")
ADMIN_ID = int(os.environ["ADMIN_ID"])

SIDE, ENTRY, SL, TP1, TP2, TP3 = range(6)

def is_admin(update: Update) -> bool:
    user = update.effective_user
    return bool(user and user.id == ADMIN_ID)

async def reject_non_admin(update: Update):
    if update.effective_message:
        await update.effective_message.reply_text("عذراً، هذا البوت مخصص للمدير فقط.")

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 صفقة شراء BUY", callback_data="buy"),
         InlineKeyboardButton("🔴 صفقة بيع SELL", callback_data="sell")],
        [InlineKeyboardButton("📊 حالة البوت", callback_data="status")]
    ])


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Safe helper: returns only the caller's own Telegram numeric ID.
    await update.message.reply_text(f"رقم حسابك في تيليجرام (ADMIN_ID): {update.effective_user.id}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await reject_non_admin(update)
        return ConversationHandler.END
    await update.message.reply_text(
        "👑 أهلاً بك في BARON GOLD SIGNALS\\n\\nاختر نوع العملية:",
        reply_markup=menu()
    )
    return ConversationHandler.END

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.from_user.id != ADMIN_ID:
        await q.edit_message_text("غير مصرح لك باستخدام لوحة التحكم.")
        return ConversationHandler.END
    if q.data == "status":
        await q.edit_message_text(f"✅ البوت متصل\\nالقناة: {CHANNEL}")
        return ConversationHandler.END
    context.user_data["side"] = q.data.upper()
    await q.edit_message_text("أرسل سعر الدخول (Entry):")
    return ENTRY

async def ask_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await reject_non_admin(update); return ConversationHandler.END
    context.user_data["entry"] = update.message.text.strip()
    await update.message.reply_text("أرسل وقف الخسارة (SL):")
    return SL

async def ask_sl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await reject_non_admin(update); return ConversationHandler.END
    context.user_data["sl"] = update.message.text.strip()
    await update.message.reply_text("أرسل الهدف الأول TP1:")
    return TP1

async def ask_tp1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await reject_non_admin(update); return ConversationHandler.END
    context.user_data["tp1"] = update.message.text.strip()
    await update.message.reply_text("أرسل الهدف الثاني TP2:")
    return TP2

async def ask_tp2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await reject_non_admin(update); return ConversationHandler.END
    context.user_data["tp2"] = update.message.text.strip()
    await update.message.reply_text("أرسل الهدف الثالث TP3:")
    return TP3

async def ask_tp3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await reject_non_admin(update); return ConversationHandler.END
    context.user_data["tp3"] = update.message.text.strip()
    d = context.user_data
    side = "شراء 🟢" if d["side"] == "BUY" else "بيع 🔴"
    post = (
        "👑 BARON GOLD SIGNALS\\n"
        "━━━━━━━━━━━━━━\\n"
        f"الأداة: XAUUSD | GOLD\\n"
        f"الاتجاه: {side}\\n"
        f"الدخول: {d['entry']}\\n"
        f"وقف الخسارة: {d['sl']}\\n"
        f"الهدف الأول: {d['tp1']}\\n"
        f"الهدف الثاني: {d['tp2']}\\n"
        f"الهدف الثالث: {d['tp3']}\\n"
        "━━━━━━━━━━━━━━\\n"
        "⚠️ إدارة رأس المال مسؤوليتك. هذه إشارة وليست ضماناً للربح."
    )
    try:
        await context.bot.send_message(chat_id=CHANNEL, text=post)
        await update.message.reply_text("✅ تم نشر الصفقة بالقناة.", reply_markup=menu())
    except Exception as e:
        log.exception("Publish failed")
        await update.message.reply_text(
            "تعذر النشر. تحقق من أن البوت مشرف ولديه صلاحية نشر الرسائل، "
            "وأن CHANNEL_ID صحيح."
        )
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await reject_non_admin(update); return ConversationHandler.END
    context.user_data.clear()
    await update.message.reply_text("تم إلغاء تجهيز الصفقة.", reply_markup=menu())
    return ConversationHandler.END

async def post_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await reject_non_admin(update); return
    await context.bot.send_message(
        chat_id=CHANNEL,
        text="👑 BARON GOLD SIGNALS\\n✅ رسالة اختبار ربط البوت بالقناة."
    )
    await update.message.reply_text("تم إرسال رسالة الاختبار إلى القناة.")

def main():
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button)],
        states={
            ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_entry)],
            SL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_sl)],
            TP1: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_tp1)],
            TP2: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_tp2)],
            TP3: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_tp3)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    app.add_handler(CommandHandler("myid", myid))\n    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", post_test))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
