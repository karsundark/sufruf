import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

# ===== Настройка бота =====
TOKEN = "8008211499:AAFUuCnNQNR9R76g3fMioo3F2yejZoLnqJk"  # замените на свой токен
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ===== Доступные языки =====
LANGUAGES = ["Казахский (Қазақ тілі)", "Английский (English)", "Турецкий (Türkçe)", "Испанский (Español)", "Французский (Français)", "Корейский (한국어)", 
"Русский (Русский)", "Арабский (العربية)", "Итальянский (Italiano)", "Португальский (Português)", "Китайский (中文 - Mandarin)", "Японский (日本語)", 
"Узбекский (O‘zbek tili)", "Кыргызский (Кыргыз тили)", "Немецкий (Deutsch)"]

# ===== Достижения =====
ACHIEVEMENTS = {
    "5_messages": {"text": "👶 Новичок – 5 сообщений", "goal": 5},
    "20_messages": {"text": "💬 Болтун – 20 сообщений", "goal": 20},
    "50_messages": {"text": "🔥 Говорун – 50 сообщений", "goal": 50},
    "100_messages": {"text": "🏆 Легенда – 100 сообщений", "goal": 100},
    "first_partner": {"text": "🤝 Первый собеседник", "goal": 1}
}

# ===== Хранение данных пользователей =====
# Ключ – user_id, значение – словарь с данными:
# username, known (список выбранных известных языков),
# learning (язык для изучения), partner (ID собеседника),
# blocked (множество заблокированных ID),
# stats (например, количество сообщений и партнеров),
# achievements (список полученных ачивок)
users = {}

# ===== Функция генерации инлайн-клавиатуры для выбора языка =====
def generate_language_keyboard(prefix, selected_languages=[]):
    keyboard = InlineKeyboardMarkup(row_width=2)
    for lang in LANGUAGES:
        status = "✅ " if lang in selected_languages else ""
        keyboard.add(InlineKeyboardButton(text=f"{status}{lang}", callback_data=f"{prefix}_{lang}"))
    if prefix == "known":
        keyboard.add(InlineKeyboardButton("✅ Далее", callback_data="choose_learning"))
    return keyboard

# ===== Команда /start – регистрация пользователя =====
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    users[message.from_user.id] = {
        "username": message.from_user.username,
        "known": [],
        "learning": None,
        "partner": None,
        "blocked": set(),
        "stats": {"messages": 0, "partners": 0},
        "achievements": []
    }
    await message.answer(
        "Выберите языки, которые вы знаете (можно несколько):", 
        reply_markup=generate_language_keyboard("known")
    )

# ===== Выбор известных языков =====
@dp.callback_query_handler(lambda c: c.data.startswith("known_"))
async def select_known_language(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    lang = callback_query.data.split("_")[1]
    if lang in users[user_id]["known"]:
        users[user_id]["known"].remove(lang)
    else:
        users[user_id]["known"].append(lang)
    await callback_query.message.edit_text(
        "Выберите языки, которые вы знаете (можно несколько):\n"
        f"Ваш выбор: {', '.join(users[user_id]['known'])}",
        reply_markup=generate_language_keyboard("known", users[user_id]["known"])
    )

# ===== Переход к выбору изучаемого языка =====
@dp.callback_query_handler(lambda c: c.data == "choose_learning")
async def ask_learning_language(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text(
        "Выберите язык, который хотите учить:",
        reply_markup=generate_language_keyboard("learning")
    )

@dp.callback_query_handler(lambda c: c.data.startswith("learning_"))
async def select_learning_language(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    lang = callback_query.data.split("_")[1]
    users[user_id]["learning"] = lang
    await callback_query.answer(f"Вы выбрали изучаемый язык: {lang}")
    # После выбора изучаемого языка отправляем сообщение с меню
    menu = ReplyKeyboardMarkup(resize_keyboard=True)
    menu.add(KeyboardButton("Найти собеседника"))
    menu.add(KeyboardButton("❌ Остановить разговор"),
             KeyboardButton("🔄 Сбросить языки"),
             KeyboardButton("🚫 Заблокировать собеседника"))
    admin_id = 666324876
    await bot.send_message(admin_id, users[user_id])
    await bot.send_message(user_id, "Теперь вы можете найти собеседника!", reply_markup=menu)

# ===== Команда /reset – сброс языковых настроек =====
@dp.message_handler(lambda message: message.text == "🔄 Сбросить языки")
async def reset_languages(message: types.Message):
    user_id = message.from_user.id
    users[user_id] = {
        "username": users[user_id]["username"],
        "known": [],
        "learning": None,
        "partner": None,
        "blocked": set(),
        "stats": {"messages": 0, "partners": 0},
        "achievements": []
    }
    await message.answer("Вы сбросили настройки. Выберите языки заново!", reply_markup=generate_language_keyboard("known"))

# ===== Команда /block – блокировка собеседника =====
@dp.message_handler(lambda message: message.text == "🚫 Заблокировать собеседника")
async def block_user(message: types.Message):
    user_id = message.from_user.id
    partner_id = users[user_id]["partner"]
    if partner_id:
        users[user_id]["blocked"].add(partner_id)
        users[partner_id]["blocked"].add(user_id)
        users[user_id]["partner"] = None
        users[partner_id]["partner"] = None
        await message.answer("🚫 Вы заблокировали этого собеседника.")
        await bot.send_message(partner_id, "🚫 Ваш собеседник завершил разговор и заблокировал вас.")
    else:
        await message.answer("Нет собеседника для блокировки.")

# ===== Команда для остановки разговора =====
@dp.message_handler(lambda message: message.text == "❌ Остановить разговор")
async def stop_conversation(message: types.Message):
    user_id = message.from_user.id
    partner_id = users[user_id]["partner"]
    if partner_id:
        users[user_id]["partner"] = None
        users[partner_id]["partner"] = None
        await message.answer("🚫 Вы остановили разговор. Найдите нового собеседника, нажав 'Найти собеседника'.")
        await bot.send_message(partner_id, "🚫 Ваш собеседник завершил разговор.")
    else:
        await message.answer("Нет активного разговора для остановки.")

# ===== Поиск собеседника =====
@dp.message_handler(lambda message: message.text == "Найти собеседника")
async def find_partner(message: types.Message):
    user_id = message.from_user.id
    known_languages = users[user_id]["known"]
    learning_language = users[user_id]["learning"]
    for partner_id, partner_data in users.items():
        if partner_id != user_id and partner_data["learning"] in known_languages and learning_language in partner_data["known"]:
            # Проверяем, что ни один из пользователей не заблокирован
            if user_id in partner_data["blocked"] or partner_id in users[user_id]["blocked"]:
                continue
            users[user_id]["partner"] = partner_id
            users[partner_id]["partner"] = user_id
            # Обновляем статистику
            users[user_id]["stats"]["partners"] += 1
            users[partner_id]["stats"]["partners"] += 1

            user_known = ", ".join(users[user_id]["known"])
            partner_known = ", ".join(partner_data["known"])
            await bot.send_message(partner_id, f"Мы нашли вам собеседника: @{users[user_id]['username']}!\n"
                                               f"Языки, которые он знает: {user_known}\n"
                                               f"Он хочет изучать: {learning_language}\n\nНачните чат!")
            await message.answer(f"Мы нашли вам собеседника: @{partner_data['username']}!\n"
                                 f"Языки, которые он знает: {partner_known}\n"
                                 f"Он хочет изучать: {partner_data['learning']}\n\nНачните чат!")
            return
    await message.answer("Пока нет подходящих собеседников. Попробуйте позже.")

# ===== Чат между пользователями =====
@dp.message_handler(lambda message: message.from_user.id in users and users[message.from_user.id]["partner"])
async def chat(message: types.Message):
    sender_id = message.from_user.id
    partner_id = users[sender_id]["partner"]
    if partner_id:
        # Обновляем статистику сообщений
        users[sender_id]["stats"]["messages"] += 1
        # Проверяем достижения
        new_achievements = check_achievements(sender_id)
        if new_achievements:
            await message.answer(f"🏆 Поздравляем! Вы получили достижения: {', '.join(new_achievements)}")
        await bot.send_message(partner_id, f"💬 @{users[sender_id]['username']}: {message.text}")

# ===== Функция проверки достижений =====
def check_achievements(user_id):
    user = users[user_id]
    new_ach = []
    # Достижение за 5 сообщений
    if user["stats"]["messages"] >= 5 and "5_messages" not in user["achievements"]:
        user["achievements"].append("5_messages")
        new_ach.append(ACHIEVEMENTS["5_messages"]["text"])
    # Достижение за 20 сообщений
    if user["stats"]["messages"] >= 20 and "20_messages" not in user["achievements"]:
        user["achievements"].append("20_messages")
        new_ach.append(ACHIEVEMENTS["20_messages"]["text"])
    # Достижение за 50 сообщений
    if user["stats"]["messages"] >= 50 and "50_messages" not in user["achievements"]:
        user["achievements"].append("50_messages")
        new_ach.append(ACHIEVEMENTS["50_messages"]["text"])
    # Достижение за 100 сообщений
    if user["stats"]["messages"] >= 100 and "100_messages" not in user["achievements"]:
        user["achievements"].append("100_messages")
        new_ach.append(ACHIEVEMENTS["100_messages"]["text"])
    # Достижение за первого собеседника
    if user["stats"]["partners"] >= 1 and "first_partner" not in user["achievements"]:
        user["achievements"].append("first_partner")
        new_ach.append(ACHIEVEMENTS["first_partner"]["text"])
    return new_ach

# ===== Команда /achievements для просмотра достижений =====
@dp.message_handler(commands=["achievements"])
async def show_achievements(message: types.Message):
    user_id = message.from_user.id
    ach_list = [ACHIEVEMENTS[ach_id]["text"] for ach_id in users[user_id]["achievements"]]
    text = "\n".join(ach_list) if ach_list else "❌ У вас пока нет достижений."
    await message.answer(f"🏅 Ваши достижения:\n{text}")

# ===== Команда /help для справки =====
@dp.message_handler(commands=["help"])
async def help_command(message: types.Message):
    await message.answer("Доступные команды:\n/start - начать\n/achievements - ваши достижения\n/reset - сбросить языковые настройки\n/block - заблокировать собеседника")

# ===== Команда /reset уже реализована через кнопку, но можно добавить и команду =====
@dp.message_handler(commands=["reset"])
async def reset_cmd(message: types.Message):
    user_id = message.from_user.id
    users[user_id] = {
        "username": users[user_id]["username"],
        "known": [],
        "learning": None,
        "partner": None,
        "blocked": set(),
        "stats": {"messages": 0, "partners": 0},
        "achievements": []
    }
    await message.answer("Вы сбросили настройки. Выберите языки заново!", reply_markup=generate_language_keyboard("known"))

# ===== Команда /block для блокировки собеседника =====
@dp.message_handler(commands=["block"])
async def block_cmd(message: types.Message):
    user_id = message.from_user.id
    partner_id = users[user_id]["partner"]
    if partner_id:
        users[user_id]["blocked"].add(partner_id)
        users[partner_id]["blocked"].add(user_id)
        users[user_id]["partner"] = None
        users[partner_id]["partner"] = None
        await message.answer("Вы заблокировали собеседника.")
        await bot.send_message(partner_id, "Ваш собеседник заблокировал вас.")
    else:
        await message.answer("Нет собеседника для блокировки.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
