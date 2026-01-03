import time
import logging
import json
import os
import asyncio
import sys
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode

# ---------- Настройки ----------
BOT_TOKEN = "8291804416:AAHqlpSYJGJc3PhxpuY2ySgvwdpKng048c0"  # ← ЗАМЕНИТЕ НА СВОЙ ТОКЕН
BLACKLIST_FILE = "blocked_sticker_packs.json"


# ---------- Работа с чёрным списком ----------
def load_blacklist():
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_blacklist(blacklist):
    with open(BLACKLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(list(blacklist), f, ensure_ascii=False, indent=2)

blocked_packs = load_blacklist()


# ---------- Обработчики команд ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡️ Бот для блокировки стикерпаков.\n\n"
        "Отправьте мне стикер из пака, который нужно заблокировать.\n"
        "Используйте /list — чтобы посмотреть список запрещённых паков.\n"
        "Нажмите на пак в списке, чтобы разблокировать."
    )

async def add_pack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.sticker:
        return

    pack_name = update.message.sticker.set_name
    if not pack_name:
        await update.message.reply_text("❌ Этот стикер не принадлежит ни к одному паку.")
        return

    blocked_packs.add(pack_name)
    save_blacklist(blocked_packs)
    await update.message.reply_text(f"✅ Пак `{pack_name}` добавлен в чёрный список.")

async def list_packs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not blocked_packs:
        await update.message.reply_text("🗑️ Чёрный список пуст.")
        return

    keyboard = [
        [InlineKeyboardButton(f"❌ {pack}", callback_data=f"unban_{pack}")]
        for pack in blocked_packs
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Заблокированные стикерпаки:", reply_markup=reply_markup)

async def handle_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("unban_"):
        pack_name = data[6:]
        if pack_name in blocked_packs:
            blocked_packs.remove(pack_name)
            save_blacklist(blocked_packs)
            await query.edit_message_text(f"🔓 Пак `{pack_name}` разблокирован.")
        else:
            await query.edit_message_text("❗ Пак уже разблокирован.")


# ---------- Модерация в группах с мутом ----------
async def moderate_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.sticker:
        return

    pack_name = update.message.sticker.set_name
    if pack_name and pack_name in blocked_packs:
        user = update.message.from_user
        chat = update.message.chat

        try:
            # Мут на 1 час = текущее время + 3600 секунд
            until_timestamp = int(time.time() + 3600)

            permissions = {
                "can_send_messages": False,
                "can_send_media_messages": False,
                "can_send_polls": False,
                "can_send_other_messages": False,
                "can_add_web_page_previews": False,
                "can_change_info": False,
                "can_invite_users": False,
                "can_pin_messages": False,
            }

            await chat.restrict_member(
                user_id=user.id,
                permissions=permissions,
                until_date=until_timestamp,  # ← теперь это число секунд
            )

            await chat.send_message(
                text=(
                    f"🔇 <b>{user.first_name}</b> отправил(а) стикер из запрещённого пака "
                    f"<code>{pack_name}</code>.\n"
                    "⏳ За это наложен <b>мут на 1 час</b>."
                ),
                parse_mode=ParseMode.HTML
            )

            await update.message.delete()

        except Exception as e:
            logging.warning(f"Не удалось замутить или удалить стикер: {e}")
            try:
                await update.message.delete()
            except Exception:
                pass


# ---------- Основная функция ----------
async def main():
    logging.basicConfig(level=logging.INFO)

    app = Application.builder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_packs))
    app.add_handler(MessageHandler(filters.Sticker.ALL & filters.ChatType.PRIVATE, add_pack))
    app.add_handler(MessageHandler(filters.Sticker.ALL & ~filters.ChatType.PRIVATE, moderate_sticker))
    app.add_handler(CallbackQueryHandler(handle_unban))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    logging.info("✅ Бот запущен и готов к работе!")

    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


# ---------- Точка входа ----------
if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())