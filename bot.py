import os
import logging
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "8537953320:AAHg9tebajVFYkWs-hiWwaPGYQEzP0D9c1I")
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "612230948"))
CHANNEL_LINK = os.environ.get("CHANNEL_LINK", "https://t.me/KAZ_METALSBOT")

# Состояния пользователей (в памяти)
users = {}

# ─────────────────────────────────────────
# /start
# ─────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Зарегистрироваться", callback_data="reg_start"),
            InlineKeyboardButton("❓ О платформе", callback_data="about")
        ]
    ])
    await update.message.reply_text(
        "🏅 *Добро пожаловать в KAZMETALS!*\n\n"
        "Мы — закрытая платформа аукционов и продаж драгоценных металлов в Казахстане.\n\n"
        "📦 *Категории:*\n"
        "• 🪙 Монеты\n"
        "• 🥇 Слитки\n"
        "• 💍 Ювелирные изделия\n"
        "• 💎 Камни\n"
        "• ⌚ Часы\n"
        "• 📈 Инвестиции\n"
        "• 💬 Обсуждения\n\n"
        "Для доступа к каналу нужно пройти регистрацию 👇",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# ─────────────────────────────────────────
# Обработка кнопок
# ─────────────────────────────────────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    chat_id = query.message.chat_id
    data = query.data

    # О платформе
    if data == "about":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Зарегистрироваться", callback_data="reg_start")]
        ])
        await context.bot.send_message(
            chat_id=chat_id,
            text="ℹ️ *О платформе KAZMETALS*\n\n"
                 "🔨 *Аукцион* — участники делают ставки и борются за лот в реальном времени\n\n"
                 "🤝 *Прямые продажи* — продавец указывает цену, покупатель и продавец связываются напрямую\n\n"
                 "Мы выступаем посредником и соединяем людей мира драгоценных металлов Казахстана.\n\n"
                 "Готовы начать?",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        return

    # Начало регистрации
    if data == "reg_start":
        # Проверяем не зарегистрирован ли уже
        if user_id in users and users[user_id].get("step") == "approved":
            await context.bot.send_message(
                chat_id=chat_id,
                text="✅ Вы уже зарегистрированы в KAZMETALS!\n\n"
                     f"Перейдите в канал: {CHANNEL_LINK}"
            )
            return

        users[user_id] = {"step": "awaiting_first_name"}
        await context.bot.send_message(
            chat_id=chat_id,
            text="📝 *Регистрация — Шаг 1 из 3*\n\n"
                 "Введите ваше *имя*:",
            parse_mode="Markdown"
        )
        return

    # Принял правила
    if data == "accept_rules":
        if user_id not in users:
            await context.bot.send_message(chat_id=chat_id, text="Пожалуйста, начните регистрацию заново: /start")
            return
        users[user_id]["step"] = "awaiting_phone"
        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("📲 Поделиться номером телефона", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text="📞 *Шаг 3 из 3 — Номер телефона*\n\n"
                 "Нажмите кнопку ниже чтобы поделиться номером через Telegram 👇",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        return

    # Отказался от правил
    if data == "decline_rules":
        users.pop(user_id, None)
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Вы отказались от регистрации.\n\n"
                 "Если передумаете — напишите /start 🙂",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # Админ одобрил
    if data.startswith("approve_"):
        target_id = data.replace("approve_", "")
        if target_id in users:
            users[target_id]["step"] = "approved"
        await context.bot.send_message(
            chat_id=int(target_id),
            text="🎉 *Поздравляем! Регистрация завершена!*\n\n"
                 "Вы успешно верифицированы в KAZMETALS!\n\n"
                 "Теперь вам доступны:\n"
                 "🔨 Аукционы — делайте ставки на лоты\n"
                 "🤝 Продажи — покупайте и продавайте напрямую\n\n"
                 f"Перейдите в канал:\n👉 {CHANNEL_LINK}\n\n"
                 "Удачных торгов! 🏅",
            parse_mode="Markdown"
        )
        await query.edit_message_text(
            text=query.message.text + "\n\n✅ *Одобрено. Пользователь уведомлён.*",
            parse_mode="Markdown"
        )
        return

    # Админ отклонил
    if data.startswith("reject_"):
        target_id = data.replace("reject_", "")
        if target_id in users:
            users[target_id]["step"] = "rejected"
        await context.bot.send_message(
            chat_id=int(target_id),
            text="😔 *Ваша заявка отклонена.*\n\n"
                 "Администратор KAZMETALS отклонил вашу регистрацию.\n\n"
                 "Если считаете что это ошибка — свяжитесь с администратором.\n\n"
                 "Для повторной попытки: /start",
            parse_mode="Markdown"
        )
        await query.edit_message_text(
            text=query.message.text + "\n\n❌ *Отклонено. Пользователь уведомлён.*",
            parse_mode="Markdown"
        )
        return

# ─────────────────────────────────────────
# Обработка текстовых сообщений
# ─────────────────────────────────────────
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    chat_id = update.message.chat_id
    text = update.message.text.strip()
    username = update.message.from_user.username or "нет"

    if user_id not in users:
        await update.message.reply_text(
            "Напишите /start чтобы начать регистрацию."
        )
        return

    step = users[user_id].get("step")

    # Шаг 1 — имя
    if step == "awaiting_first_name":
        users[user_id]["first_name"] = text
        users[user_id]["step"] = "awaiting_last_name"
        await update.message.reply_text(
            f"👍 Имя *{text}* сохранено!\n\n"
            "📝 *Шаг 2 из 3 — Фамилия*\n\n"
            "Введите вашу фамилию:",
            parse_mode="Markdown"
        )
        return

    # Шаг 2 — фамилия
    if step == "awaiting_last_name":
        users[user_id]["last_name"] = text
        users[user_id]["username"] = username
        users[user_id]["step"] = "awaiting_rules"
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Принимаю правила", callback_data="accept_rules"),
                InlineKeyboardButton("❌ Отказаться", callback_data="decline_rules")
            ]
        ])
        await update.message.reply_text(
            "📋 *Правила платформы KAZMETALS*\n\n"
            "1️⃣ Все участники проходят верификацию администратором\n"
            "2️⃣ Запрещено размещать поддельные лоты\n"
            "3️⃣ Продавец несёт ответственность за достоверность описания товара\n"
            "4️⃣ Сделки совершаются между участниками напрямую — KAZMETALS информационный посредник\n"
            "5️⃣ При нарушении правил аккаунт блокируется без предупреждения\n"
            "6️⃣ Ваши данные хранятся конфиденциально\n\n"
            "Принимаете правила платформы?",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        return

# ─────────────────────────────────────────
# Обработка номера телефона
# ─────────────────────────────────────────
async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    chat_id = update.message.chat_id
    phone = update.message.contact.phone_number
    username = update.message.from_user.username or "нет"

    if user_id not in users:
        await update.message.reply_text("Пожалуйста, начните регистрацию заново: /start")
        return

    users[user_id]["phone"] = phone
    users[user_id]["step"] = "awaiting_approval"

    u = users[user_id]
    admin_text = (
        f"🆕 *Новая заявка — KAZMETALS*\n\n"
        f"👤 *Имя:* {u.get('first_name','')} {u.get('last_name','')}\n"
        f"📞 *Телефон:* {phone}\n"
        f"🔗 *Username:* @{u.get('username', username)}\n"
        f"🆔 *Telegram ID:* {user_id}"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user_id}")
        ]
    ])

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=admin_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

    await update.message.reply_text(
        "✅ *Заявка отправлена!*\n\n"
        "Спасибо! Ваша заявка передана администратору.\n"
        "Обычно проверка занимает до 24 часов.\n\n"
        "Как только вас одобрят — придёт уведомление со ссылкой в канал. ⏳",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )

# ─────────────────────────────────────────
# Запуск
# ─────────────────────────────────────────
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    logger.info("KAZMETALS Bot запущен!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
