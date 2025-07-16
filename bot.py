import logging
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)
from datetime import datetime, timedelta

# Этапы диалога
(
    STEP_DATE, STEP_NAMES, STEP_PLACES, STEP_TIME,
    STEP_PERFORMANCE_SELECT, STEP_REVIEW_TEXT, STEP_SOURCE, STEP_ASSOCIATIONS, STEP_USER_NAME
) = range(9)

# Логирование
logging.basicConfig(level=logging.INFO)

import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Сегодня", callback_data="today")],
        [InlineKeyboardButton("Вчера", callback_data="yesterday")]
    ]
    await update.message.reply_text("📅 Выберите дату визита:", reply_markup=InlineKeyboardMarkup(keyboard))
    return STEP_DATE

async def date_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["date"] = (
        datetime.now().strftime("%d.%m.%Y") if query.data == "today"
        else (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")
    )
    await query.edit_message_text("👥 Введите имена гостей (через запятую и не забудьте указать Пэрринги, если они были):")
    return STEP_NAMES

async def names_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["names"] = update.message.text.strip()
    places_keyboard = [
        [InlineKeyboardButton(p, callback_data=p)] for p in
        ["1/2", "3/4", "5/6", "7/8", "9/10", "11/12", "13/14", "15/16", "17/18", "19/20"]
    ]
    await update.message.reply_text("📍 Выберите, где гости сидели:", reply_markup=InlineKeyboardMarkup(places_keyboard))
    return STEP_PLACES

async def places_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["places"] = query.data

    time_keyboard = [
        [InlineKeyboardButton("13:30", callback_data="13:30")],
        [InlineKeyboardButton("17:00", callback_data="17:00")],
        [InlineKeyboardButton("20:30", callback_data="20:30")]
    ]
    await query.edit_message_text("⏰ Выберите время сервиса:", reply_markup=InlineKeyboardMarkup(time_keyboard))
    return STEP_TIME

async def time_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["time"] = query.data

    show_keyboard = [
        [InlineKeyboardButton("IF", callback_data="IF")],
        [InlineKeyboardButton("IA", callback_data="IA")],
        [InlineKeyboardButton("IR", callback_data="IR")]
    ]
    await query.edit_message_text("🎭 Выберите спектакль:", reply_markup=InlineKeyboardMarkup(show_keyboard))
    return STEP_PERFORMANCE_SELECT

async def performance_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["performance"] = query.data
    await query.edit_message_text("📝 Теперь напишите текст отзыва о спектакле:")
    return STEP_REVIEW_TEXT

async def review_text_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["review_text"] = update.message.text.strip()

    source_keyboard = [
        [InlineKeyboardButton("Уже были у нас ранее", callback_data="Уже были у нас ранее")],
        [InlineKeyboardButton("Порекомендовали знакомые", callback_data="Порекомендовали знакомые")],
        [InlineKeyboardButton("Социальные сети", callback_data="Социальные сети")],
        [InlineKeyboardButton("Подарили сертификат", callback_data="Подарили сертификат")],
        [InlineKeyboardButton("Пришли в компании", callback_data="Пришли в компании")]
    ]
    await update.message.reply_text("📢 Откуда гости узнали о нас?", reply_markup=InlineKeyboardMarkup(source_keyboard))
    return STEP_SOURCE

async def source_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["source"] = query.data

    await query.edit_message_text("✍️ Введите ассоциации гостей:")
    return STEP_ASSOCIATIONS

async def associations_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["associations"] = update.message.text
    await update.message.reply_text("✍️ Введите ваше имя:")
    return STEP_USER_NAME
async def username_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["user_name"] = update.message.text.strip()
    data = context.user_data

    # Финальный отзыв
    response = (
        f"📋 Отзыв сформирован:\n\n"
        f"1.  Дата: {data['date']}\n"
        f"2.  Имена гостей: {data['names']}\n"
        f"3.  Места: {data['places']}\n"
        f"4.  Время сервиса: {data['time']}\n"
        f"5.  Спектакль: {data['performance']}\n"
        f"    Отзыв: {data['review_text']}\n"
        f"6.  Откуда узнали: {data['source']}\n"
        f"7.  Ассоциации: {data['associations']}\n"
        f"8.  {data['user_name']}"
    )

    keyboard = [
        [InlineKeyboardButton("🔁 Новый отзыв", callback_data="new_review")]
    ]
    await update.message.reply_text(response, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END


async def new_review_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Удалим старое сообщение (с отзывом и кнопкой)
    await query.message.delete()

    # Подменим update.message, чтобы start() сработал корректно
    fake_update = Update(
        update.update_id,
        message=query.message  # передаём message из callback в виде "message"
    )

    return await start(fake_update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Операция отменена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()



    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STEP_DATE: [CallbackQueryHandler(date_chosen)],
            STEP_NAMES: [MessageHandler(filters.TEXT & ~filters.COMMAND, names_entered)],
            STEP_PLACES: [CallbackQueryHandler(places_chosen)],
            STEP_TIME: [CallbackQueryHandler(time_chosen)],
            STEP_PERFORMANCE_SELECT: [CallbackQueryHandler(performance_chosen)],
            STEP_REVIEW_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, review_text_entered)],
            STEP_SOURCE: [CallbackQueryHandler(source_chosen)],
            STEP_ASSOCIATIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, associations_entered)],
            STEP_USER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, username_entered)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    app.add_handler(CallbackQueryHandler(new_review_callback, pattern="^new_review$"))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
