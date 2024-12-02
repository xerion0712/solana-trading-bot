import os

from telegram import Bot
from telegram.ext import Updater, CommandHandler

# Import your command handlers
from command_handlers import command_handlers

# Import callback query handlers
from callback_handlers import callback_query_handler

# Import message handlers
from message_handlers import message_handler

# Import postgre SQL db handlers
from postgre_sql import connect_db

# Import BOT token
from state import TOKEN

# DB Connection
connect_db()

# Bot initialization
bot = Bot(token=TOKEN)
updater = Updater(bot.token, use_context=True)
dispatcher = updater.dispatcher

# Add command handler
dispatcher.add_handler(CommandHandler(["start", "pin", "unpin", "reset"], command_handlers))

# Add callback query handlers
dispatcher.add_handler(callback_query_handler())

# Add message handler
dispatcher.add_handler(message_handler())

# Start the bot
print("Starting bot...")
updater.start_polling()
updater.idle()
