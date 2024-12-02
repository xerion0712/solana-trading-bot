from telegram import Update
from telegram.ext import CallbackContext
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode


def support(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id
    message = (
        "<u><b>Which tokens can I trade?</b></u>\n"
        "Any SPL token that is tradeable via Raydium, Jupiter, 1INTRO, Meteora, Pump.fun, Orca, and Fluxbeam.\n\n"

        "<u><b>What are the fees for using Dogbot?</b></u>\n"
        "Transactions made through Dogbot incur a fee of 2%.\n\n"

        "<u><b>Who is the team?</b></u>\n"
        "Dogbot on Solana is developed and overseen by the DumbMoney/GME team.\n"
        "- @VisionMark (CEO)\n"
        "- @RaymondMontreal (Project Manager)\n"
        "- @idioRusty (Developer)\n"
        "- @CRYPTO_PECKERWOOD (Marketing)\n"
        "- @CryptoKrusty (Operations Technician)\n"
        "- @Dumb_Money_Savage (Chart Analysis Expert)\n\n"

        "<u><b>Additional questions or need support?</b></u>\n"
        "You can find the support chat at:\n"
        "https://t.me/DOGBOT911"
    )
    keyboard = [
        [InlineKeyboardButton("☰ MENU", callback_data="EXIT")],
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except:
        context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        context.bot.send_message(chat_id=chat_id, message_id=message_id, text=message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)