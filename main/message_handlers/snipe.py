import asyncio
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext

from web3.basic import get_validation_address, get_client, get_wallet_pubkey, get_token_metadata
from web3.swap import get_token_information, buy_token, snipe_token
from postgre_sql import get_priv_key

from state import user_logs, user_data, user_states, SNIPE_TOKEN_AMOUNT, SWAP_TOKEN_AMOUNT, LAMPORTS_PER_SOL


def handle_snipe_token_address(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message_id = user_logs[chat_id]
    user_input = update.message.text
    validation = get_validation_address(user_input)

    message = ""
    if validation:
        user_data[chat_id]['address'] = user_input
        token_info = get_token_information(user_input)

        if token_info == 0:
            user_states[chat_id] = SNIPE_TOKEN_AMOUNT
            message = "Enter the amount of SOL for the Snipe: "
        else:
            user_states[chat_id] = SWAP_TOKEN_AMOUNT
            message = "Token already listed.\nEnter the amount of SOL for the Snipe:"

    else:
        message = "Invalid Token Address, Kindly put the right address to snipe"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("☰ MENU", callback_data="EXIT")]
    ])

    context.bot.delete_message(chat_id, message_id)
    chatLog = context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    user_logs[chat_id] = chatLog.message_id


def handle_swap_token_amount(update: Update, context: CallbackContext):
    def swap_token_amount(update: Update, context: CallbackContext):
        chat_id = update.effective_chat.id
        user_input = update.message.text

        try:
            solana_client = get_client()
            amount = float(user_input)
            hex_priv_key = get_priv_key(chat_id)

            pubkey = get_wallet_pubkey(hex_priv_key)
            balance_lamports = solana_client.get_balance(pubkey, "confirmed").value
            balance = balance_lamports / LAMPORTS_PER_SOL

            if amount > 0 and amount <= float(balance):
                user_data[chat_id]['amount'] = amount
                _, symbol, _, _, _, _ = get_token_metadata(user_data[chat_id]['address'])
                formated_amount = f"{amount:.8f}".rstrip('0').rstrip('.')
                context.bot.send_message(chat_id, f"BUYING {formated_amount} SOL WORTH OF {symbol}\n\nRemember to check your current SOL balance for gas fees. Please wait.")

                asyncio.run(buy_token(context.bot, chat_id, user_data[chat_id]['address'], amount))
            else:
                context.bot.send_message(
                    chat_id, f"Invalid Value Try Again or more than your balance")
                pass

        except Exception as e:

            print("Some Errors in handle_swap_token_amount: ", e)


    swap_token_amount_thread = threading.Thread(target=swap_token_amount, args=(update, context), daemon=True)
    swap_token_amount_thread.start()


def handle_snipe_token_amount(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message_id = user_logs[chat_id]
    user_input = update.message.text

    try:
        solana_client = get_client()
        amount = float(user_input)
        hex_priv_key = get_priv_key(chat_id)

        pubkey = get_wallet_pubkey(hex_priv_key)
        balance_lamports = solana_client.get_balance(pubkey, "confirmed").value

        balance = balance_lamports / LAMPORTS_PER_SOL

        if amount > 0 and amount <= float(balance):
            user_data[chat_id]['amount'] = amount
            keyboard = [
                [InlineKeyboardButton("📋 MY SNIPE LIST", callback_data="ACTIVE_SNIPER")],
                [InlineKeyboardButton("☰ MENU", callback_data="EXIT")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.delete_message(chat_id, message_id)
            context.bot.send_message(chat_id, f"Token Address inserted successfully to User Snipe List", reply_markup=reply_markup)
            sniperToken_token_thread = threading.Thread(target=snipe_token, args=(context.bot, chat_id, user_data[chat_id]['address'], amount), daemon=True)
            sniperToken_token_thread.start()
        else:
            keyboard = [
                [InlineKeyboardButton("☰ MENU", callback_data="EXIT")],
            ]
            context.bot.delete_message(chat_id, message_id)
            context.bot.send_message(chat_id, f"Invalid Value Try Again or more than your balance", reply_markup=reply_markup)

    except Exception as e:

        print("Some Errors in handle_snipe_token_amount: ", e)
