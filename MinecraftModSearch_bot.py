import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, InlineQueryHandler
import requests
import json

# ВСТАВЬТЕ ВАШ ТОКЕН ЗДЕСЬ
BOT_TOKEN = "TOKEN"

# Проверяем, что токен был загружен
if not BOT_TOKEN:
    raise ValueError("ОШИБКА: Токен бота не найден!")

# Включаем логирование
import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Глобальные переменные
user_search_results = {}
search_type = {}

# Функция для настройки меню команд
async def set_commands_menu(application: Application):
    """Устанавливает меню команд в боте"""
    commands = [
        ("start", "Запустить бота"),
        ("help", "Помощь"),
        ("ms", "Найти мод (Mod Search)"),
        ("ps", "Найти плагин (Plugin Search)"),
    ]
    await application.bot.set_my_commands(commands)

# Функция для обработки команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 Найти мод", callback_data="search_mod")],
        [InlineKeyboardButton("🔧 Найти плагин", callback_data="search_plugin")],
        [InlineKeyboardButton("📋 Помощь", callback_data="help_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        '🎮 <b>Minecraft Mod & Plugin Searcher</b>\n\n'
        'Я помогу найти моды и плагины для Minecraft!\n\n'
        '<b>Доступные команды:</b>\n'
        '/ms - поиск модов\n'
        '/ps - поиск плагинов\n'
        '/help - помощь\n\n'
        'Или выберите действие ниже:',
        parse_mode='HTML',
        reply_markup=reply_markup
    )

# Функция для обработки команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '📖 <b>Как пользоваться ботом:</b>\n\n'
        '<b>В личных сообщениях:</b>\n'
        '1. Используйте команду /ms или /ps\n'
        '2. Или нажмите соответствующую кнопку\n'
        '3. Введите название для поиска\n\n'
        '<b>Инлайн-режим (в любом чате):</b>\n'
        'Начните писать @minecraft_mod_searcher_bot [название]\n\n'
        '<b>Примеры запросов:</b>\n'
        '• "OptiFine"\n'
        '• "WorldEdit"\n'
        '• "JourneyMap"\n'
        '• "Create"',
        parse_mode='HTML'
    )

# Команда /ms - поиск модов
async def mod_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    search_type[user_id] = 'mod'
    
    await update.message.reply_text(
        '🔍 <b>Поиск модов</b>\n\n'
        'Введите название мода для поиска:\n'
        '<i>Например: OptiFine, Create, JourneyMap</i>',
        parse_mode='HTML'
    )

# Команда /ps - поиск плагинов
async def plugin_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    search_type[user_id] = 'plugin'
    
    await update.message.reply_text(
        '🔧 <b>Поиск плагинов</b>\n\n'
        'Введите название плагина для поиска:\n'
        '<i>Например: WorldEdit, Essentials, LuckPerms</i>',
        parse_mode='HTML'
    )

# Функция для определения типа установки
def get_installation_type(item_details):
    """Определяет тип установки (client-side, server-side, universal)"""
    client_side = item_details.get('client_side', 'unknown')
    server_side = item_details.get('server_side', 'unknown')
    
    if client_side == 'required' and server_side == 'required':
        return "🔄 universal", "Требует установки на клиенте и сервере"
    elif client_side == 'required' and server_side in ['optional', 'unsupported']:
        return "🎮 client-side", "Только на клиенте"
    elif server_side == 'required' and client_side in ['optional', 'unsupported']:
        return "🖥️ server-side", "Только на сервере"
    elif client_side == 'optional' and server_side == 'optional':
        return "⚡ optional", "Опциональная установка"
    else:
        return "❓ unknown", "Тип установки неизвестен"

# Функция для показа одного элемента (мода или плагина)
async def show_single_item(update: Update, context: ContextTypes.DEFAULT_TYPE, item_index: int = 0):
    query = update.callback_query
    user_id = query.from_user.id if query else update.effective_user.id
    
    if user_id not in user_search_results:
        if query:
            await query.answer("Результаты поиска устарели. Начните новый поиск.")
        return
    
    search_data = user_search_results[user_id]
    hits = search_data['hits']
    total_hits = search_data['total_hits']
    search_query = search_data['query']
    current_type = search_data['type']
    
    if item_index >= len(hits):
        if query:
            await query.answer("Это последний элемент в результатах.")
        return
    
    item = hits[item_index]
    item_title = item['title']
    item_slug = item['slug']
    item_versions = item['versions']
    item_description = item.get('description', 'Описание отсутствует')
    
    # Получаем детальную информацию для определения типа установки
    try:
        details_url = f"https://api.modrinth.com/v2/project/{item_slug}"
        details_response = requests.get(details_url, timeout=5)
        if details_response.status_code == 200:
            item_details = details_response.json()
            install_type, install_desc = get_installation_type(item_details)
        else:
            install_type, install_desc = "❓ unknown", "Не удалось определить тип"
    except:
        install_type, install_desc = "❓ unknown", "Не удалось определить тип"
    
    # Форматируем версии
    if item_versions:
        versions_str = ", ".join(item_versions[:5])
        if len(item_versions) > 5:
            versions_str += f" ... (всего {len(item_versions)})"
    else:
        versions_str = "информация о версиях отсутствует"
    
    # Определяем тип контента для отображения
    if current_type == 'mod':
        content_type = "мод"
        content_icon = "🔍"
        page_url = f"https://modrinth.com/mod/{item_slug}"
    else:
        content_type = "плагин"
        content_icon = "🔧"
        page_url = f"https://modrinth.com/plugin/{item_slug}"
    
    # Создаем сообщение для одного элемента
    message = (
        f"{content_icon} <b>{item_title}</b>\n"
        f"📁 <b>Тип:</b> {content_type}\n"
        f"⚙️ <b>Установка:</b> {install_type} - {install_desc}\n\n"
        f"📝 <b>Описание:</b>\n{item_description[:300]}...\n\n"
        f"🎮 <b>Версии Minecraft:</b>\n{versions_str}\n\n"
        f"📊 <b>Результат:</b> {item_index + 1} из {total_hits}\n"
        f"🔗 <a href='{page_url}'>Страница на Modrinth</a>"
    )
    
    # Создаем клавиатуру для навигации
    keyboard = []
    row_buttons = []
    
    if item_index > 0:
        row_buttons.append(InlineKeyboardButton("⬅️ Предыдущий", callback_data=f"item_{item_index - 1}"))
    
    if item_index < len(hits) - 1:
        row_buttons.append(InlineKeyboardButton("Следующий ➡️", callback_data=f"item_{item_index + 1}"))
    
    if row_buttons:
        keyboard.append(row_buttons)
    
    # Кнопки переключения типа поиска
    if current_type == 'mod':
        keyboard.append([InlineKeyboardButton("🔧 Искать плагины", callback_data="switch_to_plugin")])
    else:
        keyboard.append([InlineKeyboardButton("🔍 Искать моды", callback_data="switch_to_mod")])
    
    keyboard.append([InlineKeyboardButton("🔄 Новый поиск", callback_data="new_search")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(
            message,
            parse_mode='HTML',
            disable_web_page_preview=False,
            reply_markup=reply_markup
        )
        await query.answer()
    else:
        await update.message.reply_text(
            message,
            parse_mode='HTML',
            disable_web_page_preview=False,
            reply_markup=reply_markup
        )

# ПРОСТОЙ обработчик инлайн-запросов (упрощенная версия)
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Упрощенный обработчик инлайн-запросов"""
    query = update.inline_query.query.strip()
    
    # Если запрос пустой или слишком короткий
    if not query or len(query) < 2:
        # Простой ответ с инструкцией
        results = [
            InlineQueryResultArticle(
                id="help",
                title="Как использовать?",
                description="Введите название мода или плагина",
                input_message_content=InputTextMessageContent(
                    "🔍 Введите название мода или плагина для поиска.\n"
                    "Например: OptiFine, WorldEdit, JourneyMap"
                )
            )
        ]
        await update.inline_query.answer(results, cache_time=3600)
        return
    
    try:
        # Простой запрос к API без сложных параметров
        api_url = f"https://api.modrinth.com/v2/search?query={query}&limit=5"
        
        response = requests.get(api_url, timeout=3)
        
        # Если ответ не 200 OK
        if response.status_code != 200:
            # Возвращаем простое сообщение об ошибке
            results = [
                InlineQueryResultArticle(
                    id="error",
                    title="Сервер временно недоступен",
                    description="Попробуйте позже",
                    input_message_content=InputTextMessageContent(
                        "⚠️ Сервер поиска временно недоступен. Попробуйте позже."
                    )
                )
            ]
            await update.inline_query.answer(results, cache_time=60)
            return
        
        data = response.json()
        
        # Проверяем наличие результатов
        if 'hits' not in data:
            results = [
                InlineQueryResultArticle(
                    id="no_results",
                    title="Ничего не найдено",
                    description=f"По запросу '{query}'",
                    input_message_content=InputTextMessageContent(
                        f"🔍 По запросу '{query}' ничего не найдено."
                    )
                )
            ]
            await update.inline_query.answer(results, cache_time=60)
            return
        
        hits = data['hits']
        
        if not hits:
            results = [
                InlineQueryResultArticle(
                    id="empty",
                    title="Ничего не найдено",
                    description="Попробуйте другой запрос",
                    input_message_content=InputTextMessageContent(
                        f"😕 По запросу '{query}' ничего не найдено."
                    )
                )
            ]
            await update.inline_query.answer(results, cache_time=60)
            return
        
        # Создаем простые результаты
        results = []
        for i, item in enumerate(hits[:5]):  # Ограничиваем 5 результатами
            title = item.get('title', 'Без названия')
            slug = item.get('slug', '')
            versions = item.get('versions', [])
            
            # Формируем описание
            if versions:
                version_text = f"Версии: {', '.join(versions[:2])}"
                if len(versions) > 2:
                    version_text += f" и ещё {len(versions)-2}"
            else:
                version_text = "Версии не указаны"
            
            # Определяем тип проекта
            project_type = item.get('project_type', 'mod')
            page_url = f"https://modrinth.com/{project_type}/{slug}"
            
            # Простое сообщение
            message_text = f"🔍 <b>{title}</b>\n{version_text}\n🔗 {page_url}"
            
            result = InlineQueryResultArticle(
                id=str(i),
                title=title,
                description=version_text[:50],
                input_message_content=InputTextMessageContent(
                    message_text,
                    parse_mode='HTML'
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📄 Открыть", url=page_url)]
                ])
            )
            results.append(result)
        
        # Отправляем результаты
        await update.inline_query.answer(results, cache_time=60)
        
    except Exception as e:
        logging.error(f"Inline query error: {str(e)[:100]}")
        # При любой ошибке возвращаем простое сообщение
        results = [
            InlineQueryResultArticle(
                id="general_error",
                title="Ошибка поиска",
                description="Попробуйте другой запрос",
                input_message_content=InputTextMessageContent(
                    "🔍 Используйте бота в личных сообщениях для поиска модов и плагинов."
                )
            )
        ]
        await update.inline_query.answer(results, cache_time=60)

# Обработчик кнопок навигации
async def handle_navigation_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if query.data == "new_search":
        if user_id in user_search_results:
            del user_search_results[user_id]
        
        keyboard = [
            [InlineKeyboardButton("🔍 Найти мод", callback_data="search_mod")],
            [InlineKeyboardButton("🔧 Найти плагин", callback_data="search_plugin")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "Выберите тип поиска:",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        return
    
    elif query.data == "switch_to_mod":
        search_type[user_id] = 'mod'
        await query.edit_message_text(
            '🔍 <b>Поиск модов</b>\n\n'
            'Введите название мода для поиска:\n'
            '<i>Например: OptiFine, Create, JourneyMap</i>',
            parse_mode='HTML'
        )
        return
    
    elif query.data == "switch_to_plugin":
        search_type[user_id] = 'plugin'
        await query.edit_message_text(
            '🔧 <b>Поиск плагинов</b>\n\n'
            'Введите название плагина для поиска:\n'
            '<i>Например: WorldEdit, Essentials, LuckPerms</i>',
            parse_mode='HTML'
        )
        return
    
    elif query.data.startswith("item_"):
        item_index = int(query.data.split("_")[1])
        await show_single_item(update, context, item_index)
        return

# Обработчик кнопок меню
async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if query.data == "search_mod":
        search_type[user_id] = 'mod'
        await query.edit_message_text(
            '🔍 <b>Поиск модов</b>\n\n'
            'Введите название мода для поиска:\n'
            '<i>Например: OptiFine, Create, JourneyMap</i>',
            parse_mode='HTML'
        )
    
    elif query.data == "search_plugin":
        search_type[user_id] = 'plugin'
        await query.edit_message_text(
            '🔧 <b>Поиск плагинов</b>\n\n'
            'Введите название плагина для поиска:\n'
            '<i>Например: WorldEdit, Essentials, LuckPerms</i>',
            parse_mode='HTML'
        )
    
    elif query.data == "help_menu":
        await query.edit_message_text(
            '📖 <b>Как пользоваться ботом:</b>\n\n'
            '<b>В личных сообщениях:</b>\n'
            '1. Используйте команду /ms или /ps\n'
            '2. Или нажмите соответствующую кнопку\n'
            '3. Введите название для поиска\n\n'
            '<b>Примеры запросов:</b>\n'
            '• "OptiFine"\n'
            '• "WorldEdit"\n'
            '• "JourneyMap"',
            parse_mode='HTML'
        )

# Основная функция для поиска (работает в личных сообщениях)
async def search_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_query = update.message.text
    
    # Определяем тип поиска
    current_search_type = search_type.get(user_id, 'mod')
    
    logging.info(f"User {update.effective_user.username} searched for {current_search_type}: {user_query}")
    
    await update.message.chat.send_action(action="typing")
    
    try:
        # Простой запрос к API
        api_url = f"https://api.modrinth.com/v2/search?query={user_query}&limit=15"
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        hits = data['hits']
        total_hits = data['total_hits']
        
        if not hits:
            await update.message.reply_text(
                f"😕 По вашему запросу ничего не найдено.\n"
                f"Попробуйте уточнить название."
            )
            return
        
        # Сохраняем результаты поиска
        user_search_results[user_id] = {
            'hits': hits,
            'total_hits': total_hits,
            'query': user_query,
            'type': current_search_type
        }
        
        # Показываем первый элемент
        await show_single_item(update, context, 0)
        
    except requests.exceptions.RequestException as e:
        logging.error(f"API Error: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка при обращении к API. Попробуйте позже.")
    
    except Exception as e:
        logging.error(f"Unexpected Error: {e}")
        await update.message.reply_text("⚠️ Произошла непредвиденная ошибка.")

# Главная функция для запуска бота
def main():
    # Создаем Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ms", mod_search))
    application.add_handler(CommandHandler("ps", plugin_search))
    
    # Обработчик кнопок меню
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^(search_mod|search_plugin|help_menu)$"))
    
    # Обработчик кнопок навигации
    application.add_handler(CallbackQueryHandler(handle_navigation_buttons, pattern="^(new_search|switch_to_mod|switch_to_plugin|item_)"))
    
    # Упрощенный обработчик инлайн-запросов
    application.add_handler(InlineQueryHandler(inline_query))
    
    # Обработчик сообщений (поиск)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_item))
    
    # Функция для настройки при запуске
    async def post_init(application: Application):
        await set_commands_menu(application)
        print("Бот запущен! Инлайн-режим активирован.")
    
    application.post_init = post_init
    
    # Запускаем бота
    print("Бот запускается...")
    application.run_polling()

if __name__ == '__main__':
    main()
