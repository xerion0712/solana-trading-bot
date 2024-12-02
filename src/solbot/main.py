import logging

from telegram import Bot
from telegram.error import (
    BadRequest,
    ChatMigrated,
    NetworkError,
    TelegramError,
    TimedOut,
    Unauthorized,
)
from telegram.ext import CommandHandler, Updater

from solbot.callback_handlers import callback_query_handler
from solbot.command_handlers import command_handlers
from solbot.database import connect_db
from solbot.message_handlers import message_handler
from solbot.state import TELEGRAM_BOT_TOKEN

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG,
)

logger = logging.getLogger(__name__)


def error_callback(update, context):
    try:
        raise context.error
    except Unauthorized:
        # remove update.message.chat_id from conversation list
        logger.exception("Telegram Unauthorized")
    except BadRequest:
        # handle malformed requests - read more below!
        logger.exception("Telegram BadRequest")
    except TimedOut:
        # handle slow connection problems
        logger.exception("Telegram TimedOut error")
    except NetworkError:
        # handle other connection problems
        logger.exception("Telegram NetworkError")
    except ChatMigrated:
        # the chat_id of a group has changed, use e.new_chat_id instead
        logger.exception("Telegram ChatMigrated")
    except TelegramError:
        # handle all other telegram related errors
        logger.exception("TelegramError")


def main() -> None:
    # Establish database connection
    connect_db()

    # Bot initialization
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    updater = Updater(bot.token, use_context=True)
    dispatcher = updater.dispatcher

    # Add command handler
    dispatcher.add_handler(
        CommandHandler(["start", "pin", "unpin", "reset", "help"], command_handlers)
    )

    # Add callback query handlers
    dispatcher.add_handler(callback_query_handler())

    # Add message handler
    dispatcher.add_handler(message_handler())

    dispatcher.add_error_handler(error_callback)

    # Start the bot
    logger.info("Starting bot...")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
