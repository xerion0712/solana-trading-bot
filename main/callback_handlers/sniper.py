import threading
import sqlite3

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext
from web3.basic import get_token_information

from state import user_data, user_states, SNIPE_TOKEN_ADDRESS

STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
STATUS_ERROR = "error"

def active_sniper(chat_id: int, message_id:int, context: CallbackContext):
    try:
        message = "<b>Your current Snipes:</b>\n\n"

        if chat_id in user_data and 'amount' in user_data[chat_id] and 'address' in user_data[chat_id]:
            sol_price_usd = float(get_token_information("So11111111111111111111111111111111111111112")[3])
            message += f"<b>🧾 CA:</b> <code>{user_data[chat_id]['address']}</code>\n<b>💰 Amount:</b> {user_data[chat_id]['amount']:,.5f} SOL\n<b>💰 Amount in USD:</b> {float(user_data[chat_id]['amount']) * float(sol_price_usd):,.5f} USD\n\n"
            button = InlineKeyboardButton("➖ DELETE SNIPE", callback_data="DELETE_SNIPE_TOKEN")

        else:
            message += "No active snipes found at the moment. Please check back later or set up a new snipe to stay ahead!"
            button = InlineKeyboardButton("➕ NEW SNIPE", callback_data="SNIPENOW")

        keyboard = [
            [button],
            [InlineKeyboardButton("🔄 REFRESH", callback_data="ACTIVE_SNIPER")],
            [InlineKeyboardButton("☰ MENU", callback_data="EXIT")],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except sqlite3.Error as e:
        print("An error occurred in active sniper:", e)


def sniper(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    db_portfolio_thread = threading.Thread(
        target=active_sniper, args=(chat_id, context), daemon=True)
    db_portfolio_thread.start()


def create_new_snipe(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id
    snipe_status = STATUS_INACTIVE
    keyboard = [
        [InlineKeyboardButton("☰ MENU", callback_data="ACTIVE_SNIPER")],
    ]
    if snipe_status == STATUS_ACTIVE:
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="<b>Snipe Already Active</b>\nYou already have the (Snipe CA) in your active snipes. Please delete it to open a new one.",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        # message_id = chat_log['message_id']
        # user_logs[chat_id] = message_id
    elif snipe_status == STATUS_INACTIVE:
        user_states[chat_id] = SNIPE_TOKEN_ADDRESS
        user_data[chat_id] = {}
        reply_markup = InlineKeyboardMarkup(keyboard)
        # context.bot.delete_message(chat_id, message_id = user_logs[chat_id])
        context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Enter the token address you want to snipe", reply_markup=reply_markup)
        # message_id = chat_log['message_id']
        # user_logs[chat_id] = message_id
    elif snipe_status == STATUS_ERROR:
        reply_markup = InlineKeyboardMarkup(keyboard)
        chat_log = context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Database Access Error", reply_markup=reply_markup)
