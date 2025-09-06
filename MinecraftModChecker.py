import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests

# Вставьте сюда токен, который вы получили от @BotFather
BOT_TOKEN = "8364754669:AAGa_SoRZ3zd0KCuS-q2ALUppSu0owcxBUk"

# Включаем логирование, чтобы видеть ошибки
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Функция для обработки команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Привет! Я бот для поиска модов Minecraft. '
        'Просто напиши мне название мода (например, "Iron Chests"), '
        'и я найду, на каких версиях игры он доступен.'
    )

# Функция для обработки команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Просто напиши название мода!')

# Основная функция для поиска мода
async def search_mod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text
    logging.info(f"User {update.effective_user.username} searched for: {user_query}")

    # Показываем статус "печатает..."
    await update.message.chat.send_action(action="typing")

    try:
        # Делаем запрос к Modrinth API
        api_url = f"https://api.modrinth.com/v2/search?query={user_query}&limit=5"
        response = requests.get(api_url)
        response.raise_for_status()  # Проверяем, не была ли ошибка HTTP
        data = response.json()

        hits = data['hits']

        if not hits:
            await update.message.reply_text("😕 По вашему запросу ничего не найдено. Попробуйте уточнить название.")
            return

        # Обрабатываем результаты
        for mod in hits:
            mod_title = mod['title']
            mod_slug = mod['slug']
            mod_versions = mod['versions']

            # Формируем красивый список версий (берем последние 10 для краткости)
            if mod_versions:
                # Версии приходят в виде списка, например: ['1.19.2', '1.19.1', ...]
                # Обрезаем список до последних 10 версий
                recent_versions = mod_versions[:10]
                versions_str = ", ".join(recent_versions)
                if len(mod_versions) > 10:
                    versions_str += f" ... (и еще {len(mod_versions) - 10})"
            else:
                versions_str = "информация о версиях отсутствует"

            # Создаем сообщение
            message = (
                f"🔍 <b>{mod_title}</b>\n"
                f"🌐 <b>Версии:</b> {versions_str}\n"
                f"🔗 <a href='https://modrinth.com/mod/{mod_slug}'>Страница на Modrinth</a>\n"
                f"----------------------------------------\n"
            )

            # Отправляем сообщение пользователю
            await update.message.reply_text(message, parse_mode='HTML', disable_web_page_preview=True)

    except requests.exceptions.RequestException as e:
        logging.error(f"API Error: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка при обращении к API. Попробуйте позже.")

    except Exception as e:
        logging.error(f"Unexpected Error: {e}")
        await update.message.reply_text("⚠️ Произошла непредвиденная ошибка.")

# Главная функция для запуска бота
def main():
    # Создаем Application и передаем ему токен бота
    application = Application.builder().token(BOT_TOKEN).build()

    # Добавляем обработчики команд и сообщений
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_mod))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
