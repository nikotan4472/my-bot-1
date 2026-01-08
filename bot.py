import logging
import json
import os
import asyncio
import sys
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# ---------- Настройки ----------
BOT_TOKEN = "8447551685:AAGaXMpEnJ8O1H5gx4ysaKBjp_DTn78mnBw"        # ← ЗАМЕНИТЕ
OWNER_ID = 6591792069                        # ← ВАШ Telegram ID (число!)
BLACKLIST_FILE = "blocked_media.json"
CACHE_FILE = "sticker_titles_cache.json"

# 🔥 Ключевые слова (проверяются и в set_name, и в title)
BAD_KEYWORDS = {
    "nsfw", "xxx", "porn", "adult", "sex", "fuck", "bitch", "nude", "hentai", "NSFW",
    "erotic", "lewd", "r18", "18+", "kinky", "sexy", "xхх", "ххх", "порно", "секс", "эротика",
    "hot", "horny", "boobs", "ass", "cum", "fuck", "anal", "gay", "lesbian", "yaoi", "yuri"
}


# ---------- Загрузка/сохранение ----------
def load_blacklist():
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "packs": set(data.get("packs", [])),
                "stickers": set(data.get("stickers", [])),
                "gifs": set(data.get("gifs", [])),
            }
    return {"packs": set(), "stickers": set(), "gifs": set()}

def save_blacklist(blacklist):
    with open(BLACKLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "packs": list(blacklist["packs"]),
                "stickers": list(blacklist["stickers"]),
                "gifs": list(blacklist["gifs"]),
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

def load_title_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_title_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

blocked = load_blacklist()
title_cache = load_title_cache()


# ---------- Вспомогательная проверка ----------
def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

def contains_nsfw(text: str) -> bool:
    if not text:
        return False
    lower_text = text.lower()
    return any(word in lower_text for word in BAD_KEYWORDS)


# ---------- Команды (только для владельца) ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(
        "🛡️ Бот блокирует стикеры:\n"
        "• По имени пака (из ссылки)\n"
        "• По названию пака (видимому имени)\n"
        "• По ID (ручная блокировка)\n\n"
        "Используйте /list — управление чёрным списком."
    )

async def list_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return

    if not blocked["packs"] and not blocked["stickers"] and not blocked["gifs"]:
        await update.message.reply_text("🗑️ Чёрный список пуст.")
        return

    keyboard = []

    for pack in sorted(blocked["packs"]):
        title = title_cache.get(pack, "—")
        keyboard.append([InlineKeyboardButton(f"📦 {pack}\n«{title[:20]}»", callback_data=f"del_pack_{pack}")])

    for fid in sorted(blocked["stickers"])[:5]:
        keyboard.append([InlineKeyboardButton(f"🖼️ Стикер {fid[:8]}...", callback_data=f"del_sticker_{fid}")])
    for fid in sorted(blocked["gifs"])[:5]:
        keyboard.append([InlineKeyboardButton(f"🎬 GIF {fid[:8]}...", callback_data=f"del_gif_{fid}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите элемент для удаления:", reply_markup=reply_markup)


#Удаление 
async def handle_delete_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("del_pack_"):
        pack_name = data[9:]
        title = title_cache.get(pack_name, pack_name)
        await query.message.reply_text(
            f"❓ Удалить пак?\nИмя: `{pack_name}`\nНазвание: «{title}»",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Да", callback_data=f"confirm_del_pack_{pack_name}")],
                [InlineKeyboardButton("❌ Нет", callback_data="cancel")]
            ])
        )

    elif data.startswith("del_sticker_"):
        fid = data[12:]
        await query.message.reply_text(
            f"❓ Удалить стикер?\nID: `{fid}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Да", callback_data=f"confirm_del_sticker_{fid}")],
                [InlineKeyboardButton("❌ Нет", callback_data="cancel")]
            ])
        )

    elif data.startswith("del_gif_"):
        fid = data[8:]
        await query.message.reply_text(
            f"❓ Удалить GIF?\nID: `{fid}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Да", callback_data=f"confirm_del_gif_{fid}")],
                [InlineKeyboardButton("❌ Нет", callback_data="cancel")]
            ])
        )

async def confirm_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("confirm_del_pack_"):
        pack_name = data[17:]
        if pack_name in blocked["packs"]:
            blocked["packs"].remove(pack_name)
            save_blacklist(blocked)
            await query.edit_message_text(f"✅ Пак `{pack_name}` удалён из чёрного списка.")
        else:
            await query.edit_message_text("❌ Пак уже удалён.")

    elif data.startswith("confirm_del_sticker_"):
        fid = data[20:]
        if fid in blocked["stickers"]:
            blocked["stickers"].remove(fid)
            save_blacklist(blocked)
            await query.edit_message_text(f"✅ Стикер `{fid}` удалён.")
        else:
            await query.edit_message_text("❌ Стикер уже удалён.")

    elif data.startswith("confirm_del_gif_"):
        fid = data[16:]
        if fid in blocked["gifs"]:
            blocked["gifs"].remove(fid)
            save_blacklist(blocked)
            await query.edit_message_text(f"✅ GIF `{fid}` удалена.")
        else:
            await query.edit_message_text("❌ GIF уже удалена.")

    elif data == "cancel":
        await query.edit_message_text("❌ Удаление отменено.")

async def handle_delete_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("del_pack_"):
        pack_name = data[9:]
        title = title_cache.get(pack_name, pack_name)
        await query.message.reply_text(
            f"❓ Удалить пак?\nИмя: `{pack_name}`\nНазвание: «{title}»",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Да", callback_data=f"confirm_del_pack_{pack_name}")],
                [InlineKeyboardButton("❌ Нет", callback_data="cancel")]
            ])
        )

    elif data.startswith("del_sticker_"):
        fid = data[12:]
        await query.message.reply_text(
            f"❓ Удалить стикер?\nID: `{fid}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Да", callback_data=f"confirm_del_sticker_{fid}")],
                [InlineKeyboardButton("❌ Нет", callback_data="cancel")]
            ])
        )

    elif data.startswith("del_gif_"):
        fid = data[8:]
        await query.message.reply_text(
            f"❓ Удалить GIF?\nID: `{fid}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Да", callback_data=f"confirm_del_gif_{fid}")],
                [InlineKeyboardButton("❌ Нет", callback_data="cancel")]
            ])
        )

async def confirm_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("confirm_del_pack_"):
        pack_name = data[17:]
        if pack_name in blocked["packs"]:
            blocked["packs"].remove(pack_name)
            save_blacklist(blocked)
            await query.edit_message_text(f"✅ Пак `{pack_name}` удалён из чёрного списка.")
        else:
            await query.edit_message_text("❌ Пак уже удалён.")

    elif data.startswith("confirm_del_sticker_"):
        fid = data[20:]
        if fid in blocked["stickers"]:
            blocked["stickers"].remove(fid)
            save_blacklist(blocked)
            await query.edit_message_text(f"✅ Стикер `{fid}` удалён.")
        else:
            await query.edit_message_text("❌ Стикер уже удалён.")

    elif data.startswith("confirm_del_gif_"):
        fid = data[16:]
        if fid in blocked["gifs"]:
            blocked["gifs"].remove(fid)
            save_blacklist(blocked)
            await query.edit_message_text(f"✅ GIF `{fid}` удалена.")
        else:
            await query.edit_message_text("❌ GIF уже удалена.")

    elif data == "cancel":
        await query.edit_message_text("❌ Удаление отменено.")

# ---------- Добавление медиа (только от владельца) ----------
async def add_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    if not is_owner(user_id) or chat_type != "private":
        return

    if update.message.sticker:
        pack_name = update.message.sticker.set_name
        if not pack_name:
            await update.message.reply_text("❌ Стикер вне пака.")
            return
        blocked["packs"].add(pack_name)
        save_blacklist(blocked)

        # Также обновим кэш заголовка
        try:
            sticker_set = await context.bot.get_sticker_set(pack_name)
            title_cache[pack_name] = sticker_set.title
            save_title_cache(title_cache)
        except:
            pass

        await update.message.reply_text(f"✅ Пак `{pack_name}` добавлен.")
        return

    # GIF — как раньше
    fid = None
    if update.message.document and update.message.document.mime_type == "image/gif":
        fid = update.message.document.file_unique_id
    elif update.message.animation:
        fid = update.message.animation.file_unique_id
    if fid:
        blocked["gifs"].add(fid)
        save_blacklist(blocked)
        await update.message.reply_text("✅ GIF добавлена.")


# ---------- Модерация в группах ----------
async def moderate_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.sticker:
        pack_name = update.message.sticker.set_name

        # 🔹 1. Быстрая проверка по set_name
        if pack_name and contains_nsfw(pack_name):
            if pack_name not in blocked["packs"]:
                blocked["packs"].add(pack_name)
                save_blacklist(blocked)
                logging.info(f"[set_name] Авто-блок: {pack_name}")
            try:
                await update.message.delete()
            except:
                pass
            return

        # 🔹 2. Проверка по заголовку (с кэшированием)
        if pack_name:
            # Загружаем заголовок, если не в кэше
            if pack_name not in title_cache:
                try:
                    sticker_set = await context.bot.get_sticker_set(pack_name)
                    title_cache[pack_name] = sticker_set.title
                    save_title_cache(title_cache)
                    logging.info(f"Кэш заголовка: {pack_name} → {sticker_set.title}")
                except Exception as e:
                    title_cache[pack_name] = ""
                    logging.warning(f"Не удалось загрузить пак {pack_name}: {e}")

            # Проверяем заголовок
            title = title_cache.get(pack_name, "")
            if contains_nsfw(title):
                if pack_name not in blocked["packs"]:
                    blocked["packs"].add(pack_name)
                    save_blacklist(blocked)
                    logging.info(f"[title] Авто-блок: {pack_name} («{title}»)")
                try:
                    await update.message.delete()
                except:
                    pass
                return

        # 🔹 3. Ручная блокировка
        if pack_name and pack_name in blocked["packs"]:
            try:
                await update.message.delete()
            except:
                pass
            return

        # 🔹 4. По ID
        fid = update.message.sticker.file_unique_id
        if fid in blocked["stickers"]:
            try:
                await update.message.delete()
            except:
                pass
            return

    # GIF — без изменений
    fid = None
    if update.message.document and update.message.document.mime_type == "image/gif":
        fid = update.message.document.file_unique_id
    elif update.message.animation:
        fid = update.message.animation.file_unique_id
    if fid and fid in blocked["gifs"]:
        try:
            await update.message.delete()
        except:
            pass


# ---------- Основная функция ----------
async def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_items))
    app.add_handler(CallbackQueryHandler(handle_delete_request, pattern=r"^del_"))
    app.add_handler(CallbackQueryHandler(confirm_deletion, pattern=r"^confirm_del_|^cancel"))
    app.add_handler(MessageHandler(
        (filters.Sticker.ALL | filters.Document.GIF | filters.ANIMATION) & filters.ChatType.PRIVATE,
        add_media
    ))
    app.add_handler(MessageHandler(
        (filters.Sticker.ALL | filters.Document.GIF | filters.ANIMATION) & ~filters.ChatType.PRIVATE,
        moderate_media
    ))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    logging.info(f"✅ Бот запущен! Владелец: {OWNER_ID}")

    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
