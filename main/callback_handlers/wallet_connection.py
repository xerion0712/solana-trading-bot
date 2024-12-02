from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext
from solders.keypair import Keypair # type: ignore

from message_handlers.wallet_connection import handle_private_key
from web3.basic import get_wallet_pubkey
from postgre_sql import store_priv_key
from state import user_logs, user_states, temp_priv_key, IMPORT_NEW_ACCOUNT, IMPORT_NEW_ACCOUNT_SOLFARE


def send_wallet_buttons(update: Update, context: CallbackContext) -> None:
    try:
        chat_id = update.effective_chat.id
        message_id = update.callback_query.message.message_id
        keyboard = [
            [
                InlineKeyboardButton("Phantom/Trust Wallet",callback_data="PHANTOM_WALLET"),
                InlineKeyboardButton("Solflare Wallet", callback_data="SOLFLARE_WALLET")
            ],
            [InlineKeyboardButton("⬅️ BACK", callback_data="BACK")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.bot.delete_message(chat_id, message_id)
        context.bot.send_message(chat_id=chat_id, text="Choose the Wallet\n", reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        # context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Choose the Wallet\n", reply_markup=reply_markup, parse_mode=ParseMode.HTML)

        # Store the message ID in user_logs for potential later use
        # message_id = chat_log.message_id
        # user_logs[chat_id] = message_id
    except Exception as e:
        print("Wallet buttons has an err", e)


def connect_phantom_wallet(update: Update, context: CallbackContext) -> None:
    # Get the chat ID from the update object
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id

    query = update.callback_query
    query.answer()  # Acknowledge the callback

    # Define the inline keyboard for the back button
    keyboard = [
        [InlineKeyboardButton("⬅️ Back", callback_data="WALLET_CONNECTION")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        # Send the message prompting for the private key
        chat_log = context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Enter the Private Key of Phantom/Trust Wallet:", reply_markup=reply_markup)
        user_logs[chat_id] = chat_log.message_id
        user_states[chat_id] = IMPORT_NEW_ACCOUNT
    except Exception as e:
        # Log the error (you might want to handle logging differently)
        print(f"Error sending message to chat_id {chat_id}: {e}")


def connect_solflare_wallet(update: Update, context: CallbackContext) -> None:
    # Get the chat ID from the update object
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id

    query = update.callback_query
    query.answer()  # Acknowledge the callback

    # Define the inline keyboard for the back button
    keyboard = [
        [InlineKeyboardButton("⬅️ Back", callback_data="WALLET_CONNECTION")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        # Send the message prompting for the private key
        chat_log = context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Enter the Private Key of Solflare Wallet:", reply_markup=reply_markup)
        # message_id = chat_log.message_id
        # user_logs[chat_id] = message_id
        user_states[chat_id] = IMPORT_NEW_ACCOUNT_SOLFARE
    except Exception as e:
        print(f"Error sending message to chat_id {chat_id}: {e}")


def generate_wallet(update: Update, context: CallbackContext):
    try:
        chat_id = update.effective_chat.id
        message_id = update.callback_query.message.message_id
        new_keypair = Keypair()
        new_hex_priv_key = new_keypair.__str__()
        temp_priv_key[chat_id] = new_hex_priv_key
        new_pub_key = new_keypair.pubkey()

        text=f"<b>PUBLIC ADDRESS:</b> <code>{str(new_pub_key)}</code>\n\n<b>PRIVATE KEY:</b> <code>{str(new_hex_priv_key)}</code>\n\n⚠️Before proceeding, did you save your Private Key?"
        keyboard = [
                [InlineKeyboardButton("✅ YES", callback_data="SAVE_NEW_WALLET"),InlineKeyboardButton("⛔️ NO", callback_data="BACK")],   
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.bot.delete_message(chat_id, message_id)
        context.bot.send_message(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        # store_priv_key(chat_id, new_hex_priv_key)
        # handle_private_key(update, context, new_pub_key, chat_id)
    
    except Exception as e:
        print(e)


def save_new_wallet(update: Update, context: CallbackContext):
    try:
        chat_id = update.effective_chat.id
        store_priv_key(chat_id, temp_priv_key[chat_id])
        pubkey = get_wallet_pubkey(temp_priv_key[chat_id])
        temp_priv_key[chat_id] = ''
        handle_private_key(update, context, pubkey, chat_id, False)

    except Exception as e:
        print(e)