from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from collections import Counter
import os
import json


with open('data/quiz.json', 'r', encoding='utf-8') as file:
    quiz = json.load(file)

with open('data/results.json', 'r', encoding='utf-8') as file:
    results = json.load(file)

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Пройти тест", callback_data="start_quiz"),
            InlineKeyboardButton("Обратиться в поддержку", callback_data="support")
        ]
    ])
    await update.message.reply_text(
        "Привет! Я помогу тебе пройти тест или связаться с поддержкой. Что ты хочешь сделать?",
        reply_markup=keyboard
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if query.data == "start_quiz":
        user_data[user_id] = {"answers": [], "current_q": 0}
        await send_question(update, context)
    elif query.data == "support":
        await query.message.reply_text("Вы можете обратиться в нашу поддержку по почте pcn@culture.mos.ru")
        await start_over(update, context)
    elif query.data == "restart":
        await start_over(update, context)
    else:
        if user_id in user_data:
            user_data[user_id]["answers"].append(query.data)
            user_data[user_id]["current_q"] += 1
            await send_question(update, context)

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_data.get(user_id)
    
    if not state:
        return
    
    q_index = state["current_q"]
    
    if q_index >= len(quiz):
        await show_result(update, context)
        return
    
    q_data = quiz[q_index]
    buttons = [
        [InlineKeyboardButton(text, callback_data=animal)]
        for text, animal in q_data["answers"]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    
    try:
        await update.callback_query.message.edit_text(
            q_data["question"],
            reply_markup=reply_markup
        )
    except Exception as e:
        print(f"Ошибка при редактировании сообщения: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=q_data["question"],
            reply_markup=reply_markup
        )

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from collections import Counter
import os

async def show_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    answers = user_data[user_id]["answers"]

    if not answers:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Вы не ответили ни на один вопрос."
        )
        return

    result = Counter(answers).most_common(1)[0][0]
    result_text = results.get(result, "Ты уникален, как и твой выбор!")
    message = (
        f"{result_text}\n\n"
        "Хочешь заботиться об этом животном? Узнай больше о программе опеки: "
        "https://moscowzoo.ru/my-animal"
    )

    # Кнопки: перезапуск и поделиться
    bot_link = "https://t.me/AnimalQuizBot?start=share"
    share_text = f"Я прошёл викторину и получил результат: {result_text} 👉 {bot_link}"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 Попробовать ещё раз", callback_data="restart")],
        [InlineKeyboardButton("📤 Поделиться в Telegram", url=f"https://t.me/share/url?url={bot_link}&text={share_text}")],
        [InlineKeyboardButton("📲 Поделиться в VK", url=f"https://vk.com/share.php?url={bot_link}")],
        [InlineKeyboardButton("🐦 Поделиться в X (Twitter)", url=f"https://twitter.com/intent/tweet?text={share_text}")]
    ])

    try:
        await update.callback_query.message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение: {e}")

    image_path = os.path.join("media", f"{result.lower()}.jpg")

    if os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=InputFile(image_file),
                caption=message,
                reply_markup=keyboard
            )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message,
            reply_markup=keyboard
        )
async def start_over(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {"answers": [], "current_q": 0}

    try:
        await update.callback_query.message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение: {e}")

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Пройти тест", callback_data="start_quiz"),
            InlineKeyboardButton("Обратиться в поддержку", callback_data="support")
        ]
    ])
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Привет! Я помогу тебе пройти тест или связаться с поддержкой. Что ты хочешь сделать?",
        reply_markup=keyboard
    )

if __name__ == '__main__':
    TOKEN = "7398342794:AAFJe3tfq0vBDJP4dXk49Yd_x3q0C7uh7iM"

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    
    print("Бот запущен...")
    app.run_polling()