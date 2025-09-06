Minecraft Mod Searcher Bot

A powerful and efficient Telegram bot that allows users to quickly find Minecraft mods by name and check their available game versions. The bot fetches real-time data from the Modrinth API, one of the largest mod repositories.

Features

· Mod Search by Name: Simply send the name of a mod (e.g., "Sodium", "Create") to the bot.
· Version Compatibility: Instantly see which Minecraft versions the mod supports.
· Direct Links: Get a direct link to the mod's official page on Modrinth for more details and downloads.
· Real-Time Data: All information is fetched live from the Modrinth API, ensuring accuracy.
· User-Friendly: Simple text-based interaction with no complex commands needed.

How It Works

1. The user starts a chat with the bot on Telegram.
2. The user sends the name of a Minecraft mod.
3. The bot queries the Modrinth API with the search term.
4. The bot parses the response, extracting the mod's name, supported versions, and project page URL.
5. The bot formats this information into a clean, readable message and sends it back to the user.

Technologies Used

· Language: Python 3
· Telegram API Library: python-telegram-bot
· HTTP Requests: requests
· Data Source: Modrinth API
