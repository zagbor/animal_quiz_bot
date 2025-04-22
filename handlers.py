from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from quiz_data import QUESTIONS, ANIMAL_RESULTS
from config import ADMIN_CHAT_ID

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id] = {
        "answers": [],
        "current_q": 0
    }
    await update.message.reply_text("Привет! 🐾 Готов пройти викторину, чтобы узнать, какое ты животное?")
    await ask_question(update, context)

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = user_data.get(user.id)

    if data["current_q"] >= len(QUESTIONS):
        await show_result(update, context)
        return

    q = QUESTIONS[data["current_q"]]
    buttons = [
        [InlineKeyboardButton(option, callback_data=option)]
        for option in q["options"]
    ]
    await context.bot.send_message(
        chat_id=user.id,
        text=q["question"],
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    answer = query.data
    data = user_data[user_id]

    question = QUESTIONS[data["current_q"]]
    data["answers"].append(question["weights"][answer])
    data["current_q"] += 1

    await ask_question(update, context)

async def show_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = user_data[user_id]
    result_animal = max(set(data["answers"]), key=data["answers"].count)
    result_info = ANIMAL_RESULTS[result_animal]

    await context.bot.send_message(
        chat_id=user_id,
        text=result_info["description"]
    )

    # Отправка сотруднику зоопарка
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"Пользователь @{update.effective_user.username} получил результат: {result_animal}"
    )

    await context.bot.send_message(
        chat_id=user_id,
        text="Хочешь пройти ещё раз?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Попробовать ещё раз", callback_data="restart")]
        ])
    )

async def handle_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data[user_id] = {"answers": [], "current_q": 0}
    await ask_question(update, context)

def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_answer, pattern="^(?!restart).*"))
    app.add_handler(CallbackQueryHandler(handle_restart, pattern="^restart$"))