from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext

from command_handlers import show_main_panel
from web3.basic import get_wallet_pubkey, get_solfare_wallet_pubkey
from postgre_sql import store_priv_key

from state import user_states, user_logs

def handle_private_key(update: Update, context: CallbackContext, pubkey, chat_id, new=True):
    if (pubkey != ''):
        if new:
            context.bot.delete_message(chat_id, message_id=update.message.message_id)
        else:
            context.bot.delete_message(chat_id, message_id=update.callback_query.message.message_id)

        # context.bot.send_message(chat_id, f"You Have Successfully Imported The Account: {pubkey}")
        show_main_panel(context, pubkey, chat_id)
        user_states[chat_id] = ''
    else:
        keyboard = [
            [InlineKeyboardButton("⬅️ BACK", callback_data="WALLET_CONNECTION")],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        text = f"Incorrect Private Key"
        # if chat_id in user_logs:
        #     context.bot.delete_message(chat_id, user_logs[chat_id])
        context.bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


def handle_private_key_handler_phantom(update: Update, context: CallbackContext) -> None:
    try:
        chat_id = update.effective_chat.id
        user_input = update.message.text
        pubkey = get_wallet_pubkey(user_input)
        context.bot.delete_message(chat_id, user_logs[chat_id])

        if (pubkey != ''):
            store_priv_key(chat_id, user_input)
            handle_private_key(update, context, pubkey, chat_id)
        else:
            keyboard = [
                [InlineKeyboardButton("⬅️ BACK", callback_data="WALLET_CONNECTION")],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            text = f"Incorrect Private Key, Please try again"
            chat_log = context.bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            user_states[chat_id] = 'IMPORT_NEW_ACCOUNT'
            user_logs[chat_id] = chat_log.message_id
    except Exception as e:
        print(e)


def handle_private_key_handler_solfare(update: Update, context: CallbackContext) -> None:
    try:
        chat_id = update.effective_chat.id
        user_input = update.message.text
        info = get_solfare_wallet_pubkey(user_input)
        context.bot.delete_message(chat_id, user_logs[chat_id])
        
        if (info!= ''):
            pubkey, privkey = info
            store_priv_key(chat_id, privkey)
            handle_private_key(update, context, pubkey, chat_id)
        else:
            keyboard = [
                [InlineKeyboardButton("⬅️ BACK", callback_data="WALLET_CONNECTION")],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            text = f"Incorrect Private Key, Please try again"
            chat_log = context.bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            user_states[chat_id] = 'IMPORT_NEW_ACCOUNT_SOLFARE'
            user_logs[chat_id] = chat_log.message_id
            
    except Exception as e:
        print(e)